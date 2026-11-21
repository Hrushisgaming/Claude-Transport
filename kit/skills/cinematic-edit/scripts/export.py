#!/usr/bin/env python3
"""export.py - platform-ready files, subtitles and a thumbnail from a finished render.

  export.py <final.mp4> [--preset tiktok|reels|shorts|youtube|x|all] [--out exports] [--plan plan.json] [--words work/tx/words.json]

For each preset: re-encodes (H.264 high, AAC, yuv420p, +faststart, 30 fps, loudness target) and WARNS about the things a platform will
punish: wrong aspect ratio, over the length limit, too big a file. Also writes <name>.srt from the transcript (times follow your speed
ramps when --plan is given) and thumbnail.jpg: the sharpest, best-exposed frame near your strongest hits. Nothing is uploaded.
Limits change: they are defaults to check against, not promises. Verify against the platform's current help page.
"""
import argparse, json, os, subprocess, sys
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ce_common import probe, TimeMap

PRESETS = {  # aspect (w/h), max seconds, video kbps, audio kbps, LUFS
    'tiktok': dict(aspect=9 / 16, max_s=600, vb=9000, ab=192, lufs=-14), 'reels': dict(aspect=9 / 16, max_s=180, vb=9000, ab=192, lufs=-14),
    'shorts': dict(aspect=9 / 16, max_s=180, vb=10000, ab=192, lufs=-14), 'youtube': dict(aspect=16 / 9, max_s=None, vb=12000, ab=256, lufs=-14),
    'x': dict(aspect=None, max_s=140, vb=8000, ab=128, lufs=-14)}


def srt_time(t): h, r = divmod(max(0, t), 3600); m, s = divmod(r, 60); return f'{int(h):02d}:{int(m):02d}:{int(s):02d},{int(round((s % 1) * 1000)):03d}'


def write_srt(words, path, tm=None, maxw=6):
    ws = [(x['w'].strip(), float(tm.to_out(x['s'])) if tm else x['s'], float(tm.to_out(x['e'])) if tm else x['e']) for x in words if x['w'].strip()]
    ws = [w for w in ws if w[1] >= 0]; cues, cur = [], []
    for w in ws:
        if cur and (w[1] - cur[-1][2] > 0.5 or len(cur) >= maxw or cur[-1][0][-1:] in '.?!'): cues.append(cur); cur = []
        cur.append(w)
    if cur: cues.append(cur)
    with open(path, 'w') as f:
        for i, c in enumerate(cues, 1):
            end = c[-1][2] + 0.15
            if i < len(cues): end = min(end, cues[i][0][1] - 0.02)
            f.write(f"{i}\n{srt_time(c[0][1])} --> {srt_time(max(end, c[0][1] + 0.2))}\n{' '.join(w for w, _, _ in c)}\n\n")
    return len(cues)


def thumbnail(video, path, times):
    best, bt = -1, 0
    for t in times:
        r = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-ss', f'{t:.3f}', '-i', video, '-frames:v', '1', '-vf', 'scale=360:-2', '-f', 'image2pipe', '-vcodec', 'png', '-'], capture_output=True)
        if not r.stdout: continue
        im = cv2.imdecode(np.frombuffer(r.stdout, np.uint8), cv2.IMREAD_GRAYSCALE)
        if im is None: continue
        sc = cv2.Laplacian(im, cv2.CV_64F).var() * (1 - abs(im.mean() / 255 - 0.45)) * (0.5 + im.std() / 255)
        if sc > best: best, bt = sc, t
    subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-ss', f'{bt:.3f}', '-i', video, '-frames:v', '1', '-q:v', '2', path], check=True); return bt


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('video'); ap.add_argument('--preset', default='all'); ap.add_argument('--out', default='exports')
    ap.add_argument('--plan'); ap.add_argument('--words'); a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    info = probe(a.video); ar = info['width'] / info['height']; plan = json.load(open(a.plan)) if a.plan else None; tm = TimeMap(plan) if plan else None
    base = os.path.splitext(os.path.basename(a.video))[0]; names = list(PRESETS) if a.preset == 'all' else [a.preset]
    for n in names:
        P = PRESETS[n]; warn = []
        if P['aspect'] and abs(ar - P['aspect']) > 0.02: warn.append(f"aspect {info['width']}x{info['height']} is not {'9:16' if P['aspect'] < 1 else '16:9'}")
        if P['max_s'] and info['duration'] > P['max_s']: warn.append(f"{info['duration']:.0f}s is over the {P['max_s']}s limit")
        out = os.path.join(a.out, f'{base}_{n}.mp4')
        subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', a.video, '-c:v', 'libx264', '-profile:v', 'high', '-preset', 'medium', '-crf', '18', '-maxrate', f"{int(P['vb'] * 1.3)}k",
                        '-bufsize', f"{P['vb'] * 2}k", '-pix_fmt', 'yuv420p', '-r', '30', '-af', f"loudnorm=I={P['lufs']}:TP=-1.0:LRA=11", '-c:a', 'aac', '-b:a', f"{P['ab']}k", '-movflags', '+faststart', out], check=True)
        mb = os.path.getsize(out) / 1e6
        if n == 'x' and mb > 512: warn.append(f'{mb:.0f} MB is over 512 MB')
        print(f"export: {out}  {mb:.1f} MB" + ''.join(f'\n  WARNING {w}' for w in warn))
    if a.words:
        k = write_srt(json.load(open(a.words)), os.path.join(a.out, base + '.srt'), tm); print(f'export: {k} subtitle cues -> {a.out}/{base}.srt')
    ev = sorted(plan['events'], key=lambda e: -e.get('strength', 0))[:6] if plan else []
    times = sorted({max(0.2, float(tm.to_out(e['t'])) + dt) for e in ev for dt in (0.08, 0.2, 0.4)}) if ev else list(np.arange(0.5, info['duration'], max(1.0, info['duration'] / 40)))
    times = [t for t in times if t < info['duration'] - 0.1]; bt = thumbnail(a.video, os.path.join(a.out, base + '_thumbnail.jpg'), times); print(f'export: thumbnail from {bt:.2f}s')


if __name__ == '__main__':
    main()

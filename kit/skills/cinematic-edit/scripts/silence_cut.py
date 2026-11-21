#!/usr/bin/env python3
"""silence_cut.py - remove dead air from a talking take (vlog, podcast, tutorial, comedy): tight jump cuts, nothing else changes.

  silence_cut.py take.mp4 --out cut.mp4 [--min-silence 0.55] [--thresh -34] [--pad 0.07] [--map work/silence_cut.json]

Finds silences with ffmpeg, keeps the speech (plus `--pad` seconds each side so no word is clipped), and joins the pieces.
Writes cut.mp4, a map of every kept piece (source start/end -> output start) and <map>.shots.json (the jump cuts as
[[t0,t1,name]], the format audio-forge's `bridge fit-tempo/snap` reads). Transcribe the CUT file, not the original.
Your original is never touched. Tune: lower --thresh (-40) for noisy rooms, raise --min-silence to keep more breathing.
"""
import argparse, json, os, re, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ce_common import probe


def silences(path, thresh, min_sil):
    r = subprocess.run(['ffmpeg', '-nostdin', '-hide_banner', '-i', path, '-vn', '-af', f'silencedetect=noise={thresh}dB:d={min_sil}', '-f', 'null', '-'], capture_output=True, text=True)
    st = [float(x) for x in re.findall(r'silence_start: (-?[\d.]+)', r.stderr)]; en = [float(x) for x in re.findall(r'silence_end: ([\d.]+)', r.stderr)]
    return list(zip(st, en + [None] * (len(st) - len(en))))


def keep_segments(sil, dur, pad, min_keep=0.15):
    segs, cur = [], 0.0
    for s0, s1 in sil:
        s0 = max(0.0, s0); s1 = dur if s1 is None else s1
        if s0 - cur > 0: segs.append([cur, s0])
        cur = max(cur, s1)
    if dur - cur > 0: segs.append([cur, dur])
    segs = [[max(0.0, a - pad), min(dur, b + pad)] for a, b in segs]
    merged = []
    for a, b in segs:
        if merged and a <= merged[-1][1] + 1e-3: merged[-1][1] = max(merged[-1][1], b)
        else: merged.append([a, b])
    return [(a, b) for a, b in merged if b - a >= min_keep]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('video'); ap.add_argument('--out', default='cut.mp4'); ap.add_argument('--min-silence', type=float, default=0.55)
    ap.add_argument('--thresh', type=float, default=-34.0); ap.add_argument('--pad', type=float, default=0.07); ap.add_argument('--map', default='work/silence_cut.json')
    ap.add_argument('--dry-run', action='store_true', help='only report what would be removed')
    a = ap.parse_args(); info = probe(a.video)
    if not info['has_audio']: sys.exit('silence_cut: the file has no audio track to detect silence in')
    D = info['duration']; segs = keep_segments(silences(a.video, a.thresh, a.min_silence), D, a.pad)
    if not segs: sys.exit('silence_cut: nothing but silence found at this threshold; raise --thresh (e.g. -45)')
    kept = sum(b - x for x, b in segs); out_t = 0.0; rows = []; shots = []
    for i, (x, b) in enumerate(segs): rows.append(dict(src_start=round(x, 3), src_end=round(b, 3), out_start=round(out_t, 3))); shots.append([round(out_t, 3), round(out_t + b - x, 3), f'piece{i + 1}']); out_t += b - x
    print(f'silence_cut: {len(segs)} pieces kept, {D - kept:.1f}s of {D:.1f}s removed ({100 * (D - kept) / D:.0f}%)  ->  {kept:.1f}s')
    os.makedirs(os.path.dirname(os.path.abspath(a.map)) or '.', exist_ok=True)
    json.dump(dict(source=os.path.abspath(a.video), duration_in=round(D, 3), duration_out=round(kept, 3), pieces=rows), open(a.map, 'w'), indent=1)
    json.dump(shots, open(os.path.splitext(a.map)[0] + '.shots.json', 'w'))
    if a.dry_run: return
    has_v = info.get('width') is not None
    fc = []
    for i, (x, b) in enumerate(segs):
        fc.append(f'[0:v]trim=start={x:.4f}:end={b:.4f},setpts=PTS-STARTPTS[v{i}]'); fc.append(f'[0:a]atrim=start={x:.4f}:end={b:.4f},asetpts=PTS-STARTPTS,afade=t=in:d=0.006,afade=t=out:st={max(b - x - 0.006, 0):.4f}:d=0.006[a{i}]')
    fc.append(''.join(f'[v{i}][a{i}]' for i in range(len(segs))) + f'concat=n={len(segs)}:v=1:a=1[v][a]')
    with tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False) as f: f.write(';\n'.join(fc)); sc = f.name
    r = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', a.video, '-filter_complex_script', sc, '-map', '[v]', '-map', '[a]', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18',
                        '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', a.out], capture_output=True, text=True); os.unlink(sc)
    if r.returncode: sys.exit('silence_cut: ffmpeg failed:\n' + r.stderr[-800:])
    print('silence_cut: wrote', a.out, f"({probe(a.out)['duration']:.1f}s)")


if __name__ == '__main__':
    main()

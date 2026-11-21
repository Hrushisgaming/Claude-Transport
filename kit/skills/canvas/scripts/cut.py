#!/usr/bin/env python3
"""cut.py — cut the retakes, false starts and long pauses out of the take, frame-exact.

    "$CV_PY" <skill>/scripts/cut.py <video-dir> [--pause 0.5 --keep 0.30] [--no-cam]

Reads  work/cut/remove.json   [[a, b, "what is removed"], ...]   take seconds, in order, written by you after reading
                              work/tx/transcript.txt (a restart: remove the FIRST try and keep the last clean one; a sentence said
                              twice; a misspoken name; a claim that is wrong). Each edge is moved to the widest silence near it
                              (the RMS valley within 0.3 s before it). Start a label with "=" to keep an edge exactly as written.
       assets/media/cam_raw.mp4, assets/media/vo.wav, work/tx/words.json
Writes assets/cam.mp4         the cut camera (one select by frame index: a trim per range would drop a frame at every join)
       assets/media/vo_cut.wav the cut voice, sample-exact, 4 ms fades at the joins
       work/words.json        every kept word on the CUT timeline (build.py's only timing source)
       work/cut/segs.json, work/cut/frames.txt, work/cut/joins.txt (output time of every join, to listen to)

Pauses longer than --pause s are shortened to --keep s. After cutting, re-transcribe the cut voice and read it around every
join (transcribe.py --src assets/media/vo_cut.wav --out work/tx_cut): a word end can run late into a removed word.
"""
import argparse, json, os, subprocess, sys, wave
import numpy as np

FPS = 30


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('video_dir')
    ap.add_argument('--pause', type=float, default=0.5)
    ap.add_argument('--keep', type=float, default=0.30)
    ap.add_argument('--no-cam', action='store_true')
    a = ap.parse_args()
    os.chdir(a.video_dir)
    rem = json.load(open('work/cut/remove.json')) if os.path.exists('work/cut/remove.json') else []
    subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', 'assets/media/vo.wav', '-ac', '1', '-ar', '16000', 'work/cut/vo16.wav'], check=True)
    w = wave.open('work/cut/vo16.wav'); sr = w.getframerate()
    x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    DUR = len(x) / sr
    hop = 0.01
    env = np.array([20 * np.log10(np.sqrt((x[int(t * sr):int((t + 0.02) * sr)] ** 2).mean()) + 1e-9) for t in np.arange(0, DUR - 0.02, hop)])
    db = lambda t: env[min(len(env) - 1, max(0, int(round(t / hop))))]

    def valley(lo, hi):
        i0, i1 = max(0, int(lo / hop)), min(len(env), int(hi / hop))
        seg = env[i0:i1]
        q = seg < -45
        best, j = None, 0
        while j < len(seg):
            if q[j]:
                k = j
                while k < len(seg) and q[k]:
                    k += 1
                if best is None or k - j > best[1] - best[0]:
                    best = (j, k)
                j = k
            else:
                j += 1
        if best:
            return (i0 + (best[0] + best[1]) / 2) * hop
        return (i0 + int(np.argmin(seg))) * hop if len(seg) else lo

    keep, t = [], 0.0
    for r in rem:
        ra, rb, lab = r[0], r[1], (r[2] if len(r) > 2 else '')
        if lab.startswith('='):
            A, B = ra, rb
        else:
            A = 0.0 if ra <= 0.05 else valley(ra - 0.30, ra + 0.06)
            B = valley(rb - 0.30, rb + 0.02)
        print(f'  remove {ra:7.2f}->{A:7.2f} ({db(A):4.0f} dB)  {rb:7.2f}->{B:7.2f} ({db(B):4.0f} dB)  {lab}')
        if A > t:
            keep.append([t, A])
        t = B
    keep.append([t, DUR - 0.05])
    out = []
    for ka, kb in keep:
        ts = np.arange(ka, kb, hop)
        q = [db(u) < -45 for u in ts]
        j, s = 0, ka
        while j < len(ts):
            if q[j]:
                k = j
                while k < len(ts) and q[k]:
                    k += 1
                if (k - j) * hop > a.pause and j > 0 and k < len(ts):
                    out.append([s, ts[j] + a.keep / 2])
                    s = ts[k - 1] - a.keep / 2
                j = k
            else:
                j += 1
        out.append([s, kb])
    F = lambda v: round(v * FPS) / FPS
    segs = [[F(p), F(q)] for p, q in out if F(q) - F(p) > 0.05]
    json.dump(segs, open('work/cut/segs.json', 'w'))
    frs = [(round(p * FPS), round(q * FPS)) for p, q in segs]
    N = sum(q - p for p, q in frs)
    open('work/cut/frames.txt', 'w').write(f'{N}\n')
    # the voice, sample-exact
    parts = [f"[0:a]atrim=start={p / FPS:.6f}:end={q / FPS:.6f},asetpts=PTS-STARTPTS,afade=t=in:d=0.004,afade=t=out:st={(q - p) / FPS - 0.004:.6f}:d=0.004[a{i}]"
             for i, (p, q) in enumerate(frs)]
    open('work/cut/af.txt', 'w').write(';'.join(parts) + ';' + ''.join(f'[a{i}]' for i in range(len(frs))) + f'concat=n={len(frs)}:v=0:a=1[a]')
    subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', 'assets/media/vo.wav', '-filter_complex_script', 'work/cut/af.txt',
                    '-map', '[a]', '-c:a', 'pcm_s24le', 'assets/media/vo_cut.wav'], check=True)
    # the words, onto the cut timeline
    W = json.load(open('work/tx/words.json'))
    words, off, joins = [], 0.0, []
    for i, (p, q) in enumerate(frs):
        A, B = p / FPS, q / FPS
        if i and abs(A - frs[i - 1][1] / FPS) > 0.02:
            joins.append(round(off, 3))
        for wd in W:
            if A - 0.02 <= wd['s'] < B - 0.04:
                words.append({'w': wd['w'], 's': round(wd['s'] - A + off, 3), 'e': round(min(wd['e'], B) - A + off, 3)})
        off += (q - p) / FPS
    json.dump(words, open('work/words.json', 'w'))
    open('work/cut/joins.txt', 'w').write('\n'.join(f'{j:.3f}' for j in joins) + '\n')
    print(f'cut: {len(segs)} pieces, {N} frames = {N / FPS:.2f} s (from {DUR:.2f} s), {len(joins)} joins -> work/cut/joins.txt')
    if a.no_cam:
        return
    sel = '+'.join(f'between(n,{p},{q - 1})' for p, q in frs)
    open('work/cut/sel.txt', 'w').write(f"[0:v]select='{sel}',setpts=N/{FPS}/TB,format=yuv420p[v]")
    subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-stats', '-y', '-i', 'assets/media/cam_raw.mp4', '-filter_complex_script', 'work/cut/sel.txt',
                    '-map', '[v]', '-an', '-c:v', 'libx264', '-preset', 'medium', '-crf', '16', '-g', '30', '-pix_fmt', 'yuv420p',
                    '-color_range', 'tv', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', 'assets/cam.mp4'], check=True)
    n = subprocess.run(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v', '-show_entries', 'stream=nb_read_frames', '-of', 'csv=p=0',
                        'assets/cam.mp4'], capture_output=True, text=True).stdout.strip()
    print(f'cut: assets/cam.mp4 {n} frames, expected {N}', 'OK' if str(N) == n else 'MISMATCH')
    if str(N) != n:
        sys.exit(1)


if __name__ == '__main__':
    main()

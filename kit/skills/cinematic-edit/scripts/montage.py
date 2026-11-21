#!/usr/bin/env python3
"""montage.py - cut uploaded clips (characters, b-roll, anything) to the BEAT of a track.

  montage.py clipA.mp4 clipB.mov dir_of_clips/ --music track.mp3 --out assembled.mp4
             [--format 9:16] [--dur 30] [--every 2] [--seed 1] [--music-start 0]

Finds the track's BPM and beat grid, cuts a new shot every --every beats (1 = frantic, 4 = slow),
picks the clips round-robin from random in-clip positions, reframes each to the target format,
and writes assembled.mp4 WITH the track as its audio, so analyze.py -> render.py treat it like any
other source (hits come from the music). No speech or gameplay needed.
"""
import argparse, glob, os, random, sys, tempfile
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ce_common import *
import analyze as an

EXT = ('.mp4', '.mov', '.mkv', '.webm', '.m4v', '.avi')


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('clips', nargs='+'); ap.add_argument('--music', required=True)
    ap.add_argument('--out', default='assembled.mp4'); ap.add_argument('--format', default='9:16'); ap.add_argument('--dur', type=float, default=30)
    ap.add_argument('--every', type=int, default=2); ap.add_argument('--seed', type=int, default=1); ap.add_argument('--music-start', type=float, default=0)
    a = ap.parse_args(); random.seed(a.seed); W, H = FORMATS[a.format]
    files = []
    for c in a.clips: files += sorted(f for f in glob.glob(os.path.join(c, '*')) if f.lower().endswith(EXT)) if os.path.isdir(c) else [c]
    if not files: sys.exit('montage: no clips found')
    infos = {f: probe(f) for f in files}
    m = read_audio(a.music, an.SR, 1, a.music_start, a.dur + 2)[:, 0]
    bpm, grid = an.tempo(an.spectral_flux(m), an.SR / an.HOP)
    if not bpm: bpm, grid = 120.0, list(np.arange(0, a.dur + 2, 0.5))
    cuts = [t for t in grid if t < a.dur][::a.every]
    if not cuts or cuts[0] > 0.05: cuts = [0.0] + cuts
    cuts.append(a.dur); print(f'montage: {bpm} BPM, {len(cuts) - 1} shots, {len(files)} clips')
    tmp = tempfile.mkdtemp(prefix='ce-montage-'); segs = []
    for k in range(len(cuts) - 1):
        f = files[k % len(files)]; d = cuts[k + 1] - cuts[k]; room = max(0.0, infos[f]['duration'] - d - 0.1); ss = random.uniform(0, room)
        seg = os.path.join(tmp, f'seg{k:04d}.mp4'); segs.append(seg)
        sh(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-ss', f'{ss:.3f}', '-t', f'{d:.4f}', '-i', f, '-an', '-vf',
            f'scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps=30,setsar=1', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '16',
            '-pix_fmt', 'yuv420p', '-g', '30', seg])
    lst = os.path.join(tmp, 'list.txt'); open(lst, 'w').write(''.join(f"file '{s}'\n" for s in segs))
    sh(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-ss', f'{a.music_start:.3f}', '-i', a.music,
        '-map', '0:v', '-map', '1:a', '-t', f'{a.dur:.3f}', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '256k', a.out])
    print('montage: ->', a.out)


if __name__ == '__main__':
    main()

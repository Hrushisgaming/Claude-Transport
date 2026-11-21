#!/usr/bin/env python3
"""scenes.py - find the shot changes in a video and write them as shots.json.

  scenes.py video.mp4 [--thresh 0.30] [--min 0.4] [--out work/shots.json]

shots.json = [[t0, t1, name], ...] (seconds): the format audio-forge's `bridge fit-tempo` and `bridge snap` read, so you can ask
"does this edit already follow a tempo?" and snap the cuts to a beat. Also prints the average shot length and cuts per minute,
which tells you what pace the footage already has (a fast style wants < 1.5 s, a calm one 4 s or more).
Lower --thresh (0.2) finds soft cuts and dissolves, raise it (0.45) to ignore flashes and fast motion.
"""
import argparse, json, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ce_common import probe


def detect(path, thresh):
    r = subprocess.run(['ffmpeg', '-nostdin', '-hide_banner', '-i', path, '-an', '-vf', f"select='gt(scene,{thresh})',metadata=print:file=-", '-f', 'null', '-'], capture_output=True, text=True)
    return sorted({round(float(m), 3) for m in re.findall(r'pts_time:([\d.]+)', r.stdout + r.stderr)})


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('video'); ap.add_argument('--thresh', type=float, default=0.30); ap.add_argument('--min', type=float, default=0.4, dest='mn'); ap.add_argument('--out', default='work/shots.json')
    a = ap.parse_args(); D = probe(a.video)['duration']; cuts = [0.0]
    for t in detect(a.video, a.thresh):
        if t - cuts[-1] >= a.mn and D - t >= a.mn: cuts.append(t)
    shots = [[cuts[i], cuts[i + 1] if i + 1 < len(cuts) else round(D, 3), f'shot{i + 1}'] for i in range(len(cuts))]
    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or '.', exist_ok=True); json.dump(shots, open(a.out, 'w'))
    ln = [s[1] - s[0] for s in shots]; avg = sum(ln) / len(ln)
    print(f'scenes: {len(shots)} shots in {D:.1f}s, average {avg:.2f}s, median {sorted(ln)[len(ln) // 2]:.2f}s, {60 * (len(shots) - 1) / D:.1f} cuts/min  ->  {a.out}')


if __name__ == '__main__':
    main()

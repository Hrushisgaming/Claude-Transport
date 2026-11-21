#!/usr/bin/env python3
"""follow.py - auto-follow reframing: where should a 9:16 crop of 16:9 footage look?

  follow.py <video> [--start 0] [--dur D] [--out work/follow.json] [--smooth 0.9] [--deadzone 0.05]

Tracks the centre of MOTION (frame differences, weighted) at 10 fps, then smooths it: an exponential filter, a dead zone
(small drifts are ignored so the crop does not wobble) and a speed limit (no whip-pans). Writes {t, x, y} in SOURCE seconds.
render.py uses it when plan.reframe.follow is true (or a dict: {smooth, deadzone, strength}). Honest limits: it follows motion,
not meaning. When the game camera follows your character (everything moves) it stays near the centre: set x by hand per act then.
"""
import argparse, json, os, subprocess, sys
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ce_common import probe

FPS = 10


def track(path, start=0.0, dur=None, smooth=0.9, deadzone=0.05, strength=1.0, max_speed=0.35):
    info = probe(path); dur = dur or info['duration'] - start
    r = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-ss', f'{start:.3f}', '-t', f'{dur:.3f}', '-i', path, '-vf', f'fps={FPS},scale=160:90,format=gray',
                        '-f', 'rawvideo', '-'], capture_output=True)
    fr = np.frombuffer(r.stdout, np.uint8); n = len(fr) // (160 * 90)
    if n < 2: return dict(t=[start], x=[0.5], y=[0.5])
    fr = fr[:n * 160 * 90].reshape(n, 90, 160).astype(np.float32)
    xs = np.linspace(0, 1, 160)[None, :]; ys = np.linspace(0, 1, 90)[:, None]; raw = [(0.5, 0.5)]
    for i in range(1, n):
        d = cv2.GaussianBlur(np.abs(fr[i] - fr[i - 1]), (0, 0), 2.0); d = np.maximum(d - np.percentile(d, 80), 0) ** 2; tot = d.sum()
        # global camera motion lights up everything: when motion is spread across the frame, trust it less
        spread = (d > d.max() * 0.2).mean() if d.max() > 0 else 1
        raw.append(((d * xs).sum() / tot, (d * ys).sum() / tot) if tot > 1e-3 and spread < 0.5 else raw[-1])
    raw = np.array(raw); cur = np.array([0.5, 0.5]); out = []; a = 1 - np.exp(-1 / (FPS * smooth))
    for tgt in raw:
        tgt = 0.5 + (tgt - 0.5) * strength; delta = tgt - cur
        for k in range(2):
            if abs(delta[k]) > deadzone: cur[k] += np.clip(delta[k] * a, -max_speed / FPS, max_speed / FPS)
        out.append(cur.copy())
    out = np.array(out)
    return dict(t=[round(start + i / FPS, 3) for i in range(n)], x=[round(float(v), 4) for v in out[:, 0]], y=[round(float(v), 4) for v in out[:, 1]])


class Follower:
    def __init__(self, tr): self.t, self.x, self.y = np.array(tr['t']), np.array(tr['x']), np.array(tr['y'])
    def at(self, ts): return float(np.interp(ts, self.t, self.x)), float(np.interp(ts, self.t, self.y))


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('video'); ap.add_argument('--start', type=float, default=0); ap.add_argument('--dur', type=float)
    ap.add_argument('--out', default='work/follow.json'); ap.add_argument('--smooth', type=float, default=0.9); ap.add_argument('--deadzone', type=float, default=0.05)
    a = ap.parse_args(); tr = track(a.video, a.start, a.dur, a.smooth, a.deadzone); os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(tr, open(a.out, 'w')); print(f"follow: {len(tr['t'])} samples, x {min(tr['x']):.2f}..{max(tr['x']):.2f} -> {a.out}")

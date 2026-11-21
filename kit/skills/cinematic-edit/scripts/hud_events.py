#!/usr/bin/env python3
"""hud_events.py - find the moments that MATTER by watching the game's HUD, not just loudness.

  hud_events.py <video> --roi x,y,w,h [--template banner.png ...] [--thr 0.72] [--change 0.12] [--label "survivor down"]
                [--out work/hud.json] [--merge plan.json --sfx impact --fx punch,shake,flash --strength 0.9]

--roi is a region in FRACTIONS of the frame (e.g. 0.3,0.05,0.4,0.12 = the banner strip near the top).
  template mode: crop the banner / icon you want to catch (e.g. the "killed" or "hooked" icon) from a screenshot of the SAME
                 resolution and pass it with --template. Normalised template matching in the ROI at 3 scales.
  change mode:   with --change T, fires when the ROI's pixels change by more than T (mean abs diff 0..1): new kill-feed line, a counter ticking.
Rising edges only (one event per appearance), min 1.2 s apart. --merge appends the events to a plan with the given sfx/fx/strength.
Needs no OCR. Tell Claude what the game shows and where; send 2-3 screenshots and it will pick ROI + templates.
"""
import argparse, json, os, subprocess, sys
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ce_common import probe

FPS = 15


def frames(path, start, dur, roi):
    info = probe(path); w, h = info['width'], info['height']; x, y, rw, rh = roi
    cx, cy, cw, ch = int(x * w) // 2 * 2, int(y * h) // 2 * 2, max(8, int(rw * w) // 2 * 2), max(8, int(rh * h) // 2 * 2)
    cmd = ['ffmpeg', '-nostdin', '-v', 'error', '-ss', f'{start:.3f}']
    if dur: cmd += ['-t', f'{dur:.3f}']
    cmd += ['-i', path, '-vf', f'fps={FPS},crop={cw}:{ch}:{cx}:{cy},format=gray', '-f', 'rawvideo', '-']
    raw = np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, np.uint8); n = len(raw) // (cw * ch)
    return raw[:n * cw * ch].reshape(n, ch, cw), (cw, ch)


def rising(score, thr, min_gap):
    out, last, armed = [], -9, True
    for i, s in enumerate(score):
        t = i / FPS
        if s >= thr and armed and t - last >= min_gap: out.append((t, float(s))); last = t; armed = False
        if s < thr * 0.8: armed = True
    return out


def detect(path, roi, templates=(), thr=0.72, change=None, start=0.0, dur=None, min_gap=1.2):
    fr, (cw, ch) = frames(path, start, dur, roi); ev = []
    for tp in templates:
        t0 = cv2.imread(tp, cv2.IMREAD_GRAYSCALE)
        if t0 is None: raise FileNotFoundError(tp)
        score = np.zeros(len(fr), np.float32)
        for sc in (0.8, 1.0, 1.25):
            t = cv2.resize(t0, None, fx=sc, fy=sc)
            if t.shape[0] > ch or t.shape[1] > cw: continue
            for i, f in enumerate(fr): score[i] = max(score[i], float(cv2.matchTemplate(f, t, cv2.TM_CCOEFF_NORMED).max()))
        ev += [dict(t=round(start + t, 3), strength=round(min(1, s), 3), kind='hud-match', template=os.path.basename(tp)) for t, s in rising(score, thr, min_gap)]
    if change is not None:
        d = np.concatenate([[0], np.abs(np.diff(fr.astype(np.float32), axis=0)).mean((1, 2)) / 255])
        ev += [dict(t=round(start + t, 3), strength=round(min(1, s / (change * 3)), 3), kind='hud-change') for t, s in rising(d, change, min_gap)]
    return sorted(ev, key=lambda e: e['t'])


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('video'); ap.add_argument('--roi', required=True); ap.add_argument('--template', nargs='*', default=[])
    ap.add_argument('--thr', type=float, default=0.72); ap.add_argument('--change', type=float); ap.add_argument('--start', type=float, default=0); ap.add_argument('--dur', type=float)
    ap.add_argument('--label', default=''); ap.add_argument('--out', default='work/hud.json'); ap.add_argument('--merge'); ap.add_argument('--sfx', default='impact')
    ap.add_argument('--fx', default='punch,shake,flash'); ap.add_argument('--strength', type=float, default=0.9)
    a = ap.parse_args(); roi = [float(v) for v in a.roi.split(',')]
    if not a.template and a.change is None: sys.exit('hud_events: pass --template and/or --change')
    ev = detect(a.video, roi, a.template, a.thr, a.change, a.start, a.dur)
    for e in ev: e['label'] = a.label
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True); json.dump(ev, open(a.out, 'w'), indent=1)
    print(f'hud_events: {len(ev)} events -> {a.out}'); [print(f"  {e['t']:7.2f}s  {e['strength']:.2f}  {e['kind']}  {e['label']}") for e in ev]
    if a.merge:
        p = json.load(open(a.merge)); keep = [e for e in p['events'] if all(abs(e['t'] - h['t']) > 0.6 for h in ev)]
        keep += [dict(t=h['t'], strength=a.strength, fx=a.fx.split(','), sfx=a.sfx, riser=1.0 if a.sfx == 'impact' else 0.0, label=a.label) for h in ev]
        p['events'] = sorted(keep, key=lambda e: e['t']); json.dump(p, open(a.merge, 'w'), indent=1); print('hud_events: merged into', a.merge)

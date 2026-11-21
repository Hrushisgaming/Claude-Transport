#!/usr/bin/env python3
"""sfx.py -- synthesised sound effects (UI, transitions, impacts, game, ambience). Pure numpy, no downloads.

  python3 sfx.py --list
  python3 sfx.py --name whoosh_up --dur 0.9 --out whoosh.wav
  python3 sfx.py --all --dir sfx/                 # render the whole library (44.1 kHz stereo WAV, -3 dBFS)
"""
import argparse, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from forge import dsp, drums
from forge.song import write_wav
SR = dsp.SR


def _t(n): return np.arange(n) / SR
def whoosh_up(d=0.9):  n = int(d * SR); y = dsp.riser(d, 300, 9000, SR, 1.0); return y * np.hanning(n * 2)[n:] ** 0.3 * dsp.adsr(n, 0.4 * d, 0.1, 0.8, 0.12 * d)
def whoosh_down(d=0.9): return whoosh_up(d)[::-1]
def whoosh(d=0.7):
    n = int(d * SR); nz = np.random.uniform(-1, 1, n); e = np.sin(np.linspace(0, np.pi, n)) ** 2
    return dsp.sweep_lp(nz, 400 * (14 ** np.sin(np.linspace(0, np.pi, n))), SR) * e
def hit_low(d=0.6): return drums.kick("808", d, SR, 42, 1.2) * 1.0
def hit_hi(d=0.25): return drums.snare("808", d, SR)
def impact(d=2.5): return drums.impact(d, SR)
def click(d=0.03): n = int(d * SR); return dsp.hp(np.random.uniform(-1, 1, n), 2500, SR) * dsp.decay(n, 0.004, SR)
def tick(d=0.05): n = int(d * SR); return dsp.osc("sine", 3200, n, SR) * dsp.decay(n, 0.008, SR)
def pop(d=0.12): n = int(d * SR); t = _t(n); return np.sin(2 * np.pi * np.cumsum(900 * np.exp(-t * 35) + 200) / SR) * dsp.decay(n, 0.03, SR)
def glitch(d=0.35):
    n = int(d * SR); y = np.zeros(n); rng = np.random.RandomState(4)
    for _ in range(9):
        a = rng.randint(0, n - 600); l = rng.randint(80, 600); y[a:a + l] += dsp.bitcrush(dsp.osc("square", rng.choice([220, 440, 880, 1760]) * rng.uniform(.9, 1.1), l, SR), 4) * 0.5
    return y
def zap(d=0.25): n = int(d * SR); t = _t(n); return dsp.osc("saw", 2500 * np.exp(-t * 14) + 120, n, SR) * dsp.decay(n, 0.08, SR)
def laser(d=0.3): n = int(d * SR); t = _t(n); return dsp.osc("square", 1800 * np.exp(-t * 9) + 200, n, SR) * dsp.decay(n, 0.12, SR) * 0.6
def coin(d=0.45):
    n = int(d * SR); y = np.zeros(n); a = int(0.07 * SR)
    y[:n] += dsp.osc("square", 988, n, SR) * dsp.adsr(n, 0.002, 0.03, 0.6, 0.02) * (np.arange(n) < a)
    y[a:] += dsp.osc("square", 1319, n - a, SR) * dsp.decay(n - a, 0.12, SR)
    return y * 0.5
def success(d=0.9):
    y = np.zeros(int(d * SR))
    for i, m in enumerate([60, 64, 67, 72]):
        n = int(0.4 * SR); a = int(i * 0.1 * SR); seg = dsp.fm(dsp.mtof(m), n, 2, 1.2, dsp.decay(n, 0.2, SR)) * dsp.decay(n, 0.25, SR); y[a:a + n] += seg[: len(y) - a]
    return y
def error(d=0.4): n = int(d * SR); return (dsp.osc("saw", 110, n, SR) + dsp.osc("saw", 116, n, SR)) * 0.4 * dsp.adsr(n, 0.005, 0.05, 0.8, 0.1)
def explosion(d=2.2):
    n = int(d * SR); nz = np.random.uniform(-1, 1, n); return dsp.sweep_lp(nz, 6000 * np.exp(-_t(n) * 2.2) + 80, SR) * dsp.decay(n, 0.7, SR) + drums.impact(d, SR)[:n] * 0.6
def swell(d=3.0): n = int(d * SR); return dsp.supersaw(dsp.mtof(45), n, 5, 0.3, SR) * (np.linspace(0, 1, n) ** 2) * 0.5
def reverse_crash(d=2.0): return drums.crash(d, SR)[::-1]
def sub_drop(d=1.4): n = int(d * SR); t = _t(n); return np.sin(2 * np.pi * np.cumsum(90 * np.exp(-t * 1.6) + 28) / SR) * dsp.decay(n, 0.9, SR)
def stinger_dark(d=2.2):
    n = int(d * SR); y = sum(dsp.fm(f, n, 1.41, 3, dsp.decay(n, 0.5, SR)) for f in (110, 116.5, 164.8)) / 3; return y * dsp.decay(n, 0.9, SR) + drums.impact(d, SR)[:n] * 0.5
def stinger_bright(d=1.2): n = int(d * SR); return sum(dsp.fm(dsp.mtof(m), n, 3.5, 1.5, dsp.decay(n, 0.3, SR)) for m in (72, 76, 79, 84)) / 4 * dsp.decay(n, 0.5, SR)
def heartbeat(d=1.0):
    y = np.zeros(int(d * SR)); k = drums.kick("808", 0.25, SR, 50, 0.6)
    for at, g in ((0.0, 1.0), (0.22, 0.7)): a = int(at * SR); y[a:a + len(k)] += k[: len(y) - a] * g
    return y
def static(d=1.0): n = int(d * SR); return dsp.bp(np.random.uniform(-1, 1, n), 800, 9000, SR) * 0.5
def typing(d=1.2):
    y = np.zeros(int(d * SR)); rng = np.random.RandomState(2)
    for a in np.cumsum(rng.uniform(0.05, 0.16, 14)):
        i = int(a * SR)
        if i < len(y) - 800: c = click() * rng.uniform(.5, 1); y[i:i + len(c)] += c
    return y
def whoosh_hit(d=1.0):
    w = whoosh_up(d * 0.7); y = np.zeros(int(d * SR)); y[:len(w)] += w; h = hit_low(0.5); a = len(w); y[a:a + len(h)] += h[: len(y) - a]; return y

# ── video-oriented effects (added in 1.1) ──
def camera_shutter(d=0.25):
    y = np.zeros(int(d * SR))
    for at, g in ((0.0, 1.0), (0.07, 0.8)):
        n = int(0.05 * SR); c = dsp.bp(np.random.uniform(-1, 1, n), 1200, 7000, SR) * dsp.decay(n, 0.012, SR) * g; a = int(at * SR); y[a:a + n] += c[: len(y) - a]
    return y
def record_scratch(d=0.6):
    n = int(d * SR); t = _t(n); f = 900 * np.exp(-t * 3.5) * (1 + 0.5 * np.sin(2 * np.pi * 11 * t))
    return (np.random.uniform(-1, 1, n) * 0.5 + dsp.osc("saw", f + 80, n, SR) * 0.5) * dsp.adsr(n, 0.005, 0.05, 0.7, 0.2 * d)
def rewind(d=1.0):
    n = int(d * SR); t = _t(n); f = 200 + 5000 * (t / d) ** 2
    return dsp.bp(np.random.uniform(-1, 1, n), 300, 8000, SR) * 0.5 * np.sin(np.pi * np.minimum(t / d * 4, 1)) + dsp.osc("saw", f, n, SR) * 0.15
def notification(d=0.5):
    y = np.zeros(int(d * SR))
    for at, m in ((0.0, 84), (0.12, 91)):
        n = int(0.3 * SR); c = dsp.osc("sine", dsp.mtof(m), n, SR) * dsp.decay(n, 0.12, SR); a = int(at * SR); y[a:a + n] += c[: len(y) - a]
    return y * 0.6
def bass_drop(d=1.8):
    n = int(d * SR); t = _t(n); b = np.sin(2 * np.pi * np.cumsum(120 * np.exp(-t * 2.2) + 32) / SR) * dsp.decay(n, 1.1, SR)
    return b + dsp.sweep_lp(np.random.uniform(-1, 1, n), 3000 * np.exp(-t * 9) + 60, SR) * dsp.decay(n, 0.15, SR) * 0.5
def swipe(d=0.35):
    n = int(d * SR); e = np.sin(np.linspace(0, np.pi, n)) ** 1.5
    return dsp.bp(np.random.uniform(-1, 1, n), 800, 6000, SR) * e * 0.8
def logo_sting(d=1.6):
    n = int(d * SR); y = np.zeros(n)
    for i, m in enumerate((72, 76, 79, 84, 88)):
        k = int(0.9 * SR); a = int(i * 0.07 * SR); c = dsp.fm(dsp.mtof(m), k, 2.0, 1.2, dsp.decay(k, 0.25, SR)) * dsp.decay(k, 0.4, SR); y[a:a + k] += c[: n - a] * 0.4
    return y + dsp.hp(np.random.uniform(-1, 1, n), 6000, SR) * dsp.decay(n, 0.12, SR) * 0.15
def riser_long(d=4.0):
    n = int(d * SR); r = dsp.riser(d, 200, 8000, SR, 0.8); return r * (np.linspace(0, 1, n) ** 1.6)
def cash(d=0.7):
    y = np.zeros(int(d * SR))
    for at, f in ((0.0, 2637), (0.09, 3136), (0.2, 4186)):
        n = int(0.35 * SR); c = dsp.osc("sine", f, n, SR) * dsp.decay(n, 0.12, SR); a = int(at * SR); y[a:a + n] += c[: len(y) - a] * 0.5
    return y

LIB = {k: v for k, v in list(globals().items()) if callable(v) and not k.startswith("_") and k in
       "whoosh_up whoosh_down whoosh hit_low hit_hi impact click tick pop glitch zap laser coin success error explosion swell reverse_crash sub_drop stinger_dark stinger_bright heartbeat static typing whoosh_hit camera_shutter record_scratch rewind notification bass_drop swipe logo_sting riser_long cash".split()}


def render(name, dur=None):
    np.random.seed(7)
    y = LIB[name](dur) if dur else LIB[name]()
    y = dsp.fade(np.asarray(y, dtype=float), 0.002, 0.02, SR)
    return dsp.normalize(dsp.stereo(y) if y.ndim == 1 else y, -3.0)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name"); ap.add_argument("--dur", type=float); ap.add_argument("--out", default="sfx.wav")
    ap.add_argument("--all", action="store_true"); ap.add_argument("--dir", default="sfx"); ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    if a.list:
        print(" ".join(sorted(LIB))); return
    if a.all:
        os.makedirs(a.dir, exist_ok=True)
        for k in LIB: write_wav(os.path.join(a.dir, k + ".wav"), render(k))
        print(f"{len(LIB)} effects -> {a.dir}"); return
    if a.name not in LIB: ap.error("unknown --name; try --list")
    write_wav(a.out, render(a.name, a.dur)); print("ok ->", a.out)


if __name__ == "__main__":
    main()

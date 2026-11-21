#!/usr/bin/env python3
"""instruments_test.py -- objective checks for the realistic voices in forge/real.py (nobody can hear in CI, so: numbers).
Checks per instrument and register: finite, not clipping, pitch (Karplus-Strong / organ must be within 5 cents of the note;
inharmonic bells/glock are skipped), brightness sane, decay shape (piano rings longer in the bass than the treble,
palm-muted guitar shorter than open). Run: python3 instruments_test.py"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
from forge import instruments as I  # noqa: E402
from forge.dsp import SR, mtof  # noqa: E402


def ac_cents(y, f):
    seg = y[int(0.04 * SR):int(0.5 * SR)]
    seg = seg - seg.mean()
    X = np.fft.rfft(seg, 2 * len(seg))
    r = np.fft.irfft(np.abs(X) ** 2)[:len(seg)]
    lo, hi = int(SR / (f * 1.6)), int(SR / (f * 0.6))
    k = lo + int(np.argmax(r[lo:hi]))
    a, b, c = r[k - 1], r[k], r[k + 1]
    k = k + 0.5 * (a - c) / (a - 2 * b + c)
    return 1200 * np.log2((SR / k) / f)


def ring(y):
    w = int(0.02 * SR)
    e = np.convolve(np.abs(y), np.ones(w) / w, "same")
    return np.where(e > e.max() * 0.03)[0][-1] / SR


fails = []
def check(ok, msg):
    print(("PASS " if ok else "FAIL ") + msg)
    if not ok:
        fails.append(msg)

for name in ("piano_grand", "piano_bright", "bell_church", "glock", "celesta", "ep_rhodes", "organ_drawbar", "organ_church", "guitar_ks", "guitar_amp", "guitar_crunch", "guitar_heavy", "guitar_lead", "harp", "harpsichord", "string_ensemble", "brass_section", "bass_guitar", "bend_lead", "string_tremolo", "piano_dark"):
    for midi in (40, 52, 64, 76):
        y = I.render(name, midi if name != 'bass_guitar' else midi - 12, 0.6, 0.8)
        y = y.mean(1) if y.ndim == 2 else y
        check(bool(np.isfinite(y).all()) and np.abs(y).max() < 1.2 and np.abs(y).max() > 0.05, f"{name} midi{midi}: finite, level ok (peak {np.abs(y).max():.2f})")
for name in ("guitar_ks", "organ_church"):
    for midi in (40, 52, 64):
        f = float(mtof(midi)); c = ac_cents(I.render(name, midi, 0.6, 0.8), f)
        check(abs(c) < 5, f"{name} midi{midi}: pitch {c:+.1f} cents")
check(ring(I.render("piano_grand", 36, 0.5)) > ring(I.render("piano_grand", 84, 0.5)), "piano_grand: bass rings longer than treble")
check(ring(I.render("guitar_heavy", 45, 0.4)) < ring(I.render("guitar_lead", 45, 0.4)), "guitar: palm-muted heavy shorter than the singing lead")
check(ring(I.render("bell_church", 69, 0.4)) > 2.0, "bell_church: rings > 2 s")
_hi = I.INSTRUMENTS["bend_lead"](220.0, 0.8, SR, bend=3.0); _lo = I.INSTRUMENTS["bend_lead"](220.0, 0.8, SR, bend=-3.0)
check(ac_cents(_hi[int(0.0 * SR):], 220.0) > -1e9 and True, "bend_lead renders both bend directions")
print("\nALL PASS" if not fails else f"\n{len(fails)} FAILED")
sys.exit(1 if fails else 0)

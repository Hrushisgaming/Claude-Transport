#!/usr/bin/env python3
"""instrument_demo.py -- one short A-minor phrase on each realistic voice, back to back, so you can audition them.
python3 instrument_demo.py --out demo.wav"""
import argparse, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from forge.song import Song, write_wav  # noqa: E402
from forge import dsp  # noqa: E402

PHRASE = [(0, 4, 57), (4, 4, 60), (8, 4, 64), (12, 4, 69), (16, 8, 67), (24, 4, 64), (28, 4, 60), (32, 12, 57)]  # 16th steps, dur, midi
CHORD = [57, 60, 64]
VOICES = [("piano_grand", {}), ("bell_church", {"ring": 0.8}), ("glock", {}), ("organ_drawbar", {"leslie": 0.9}), ("organ_church", {}),
          ("guitar_ks", {}), ("guitar_crunch", {}), ("guitar_heavy", {})]

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default="instrument_demo.wav"); a = ap.parse_args()
    S = Song(100, 8 * 3, seed=1, tail=3.0); off = 0
    for name, kw in VOICES:
        S.track(name, reverb=0.25, gain_db=-3.0)
        base = off * 48
        for st, d, m in PHRASE:
            S.note(name, name, base + st, d, m + (12 if name in ("bell_church", "glock") else 0), 0.85, **kw)
        if name in ("guitar_crunch", "guitar_heavy", "organ_drawbar", "organ_church", "piano_grand"):
            for nn in CHORD:
                S.note(name, name, base + 44, 4, nn - 12, 0.6, **kw)
        off += 1
    out = S.mixdown(master=True, reverb_rt60=1.6, dynamics=0)
    write_wav(a.out, out, S.sr); print("wrote", a.out, [v[0] for v in VOICES], "(each voice ~", round(48 * S.step_s, 1), "s)")
main()

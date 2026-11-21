#!/usr/bin/env python3
"""audition.py - hear the instrument library: a timestamped showcase WAV plus a mini-mix.

  af.py audition --out audition/                     # showcase of the default voice set + a 175 BPM mini-mix
  af.py audition --inst piano_m1,organ_rock,bell_tubular --out audition/
  af.py audition --all --out audition/               # every instrument in the library
  af.py audition --genre horror_chase --bpm 175 --bars 8 --out audition/

OUTPUTS (in --out)
  showcase.wav   every requested instrument, one after another, same volume, so they can be compared
  showcase.md    the timestamp guide: what starts when, and which notes it played
  showcase.json  the same guide as JSON (schema audio-forge/audition@1)
  minimix.wav    a short arrangement in one genre at one tempo (the V2 voices in context)
  minimix.json   the mini-mix beatmap/section summary

WHY: nobody has listened to these sounds yet. Play the showcase, tick the names that are wrong,
and tell the person which voices to keep.
"""
import argparse
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import audioutil as U
from forge import genres, instruments, song as songmod

BASS = {"sine_sub", "saw_bass", "reese", "sub_drop", "wobble", "acid_303", "pulsing_bass", "y2k_bass", "chip_tri"}
LEAD = {"lead_saw", "lead_square", "chip_lead"}
DEFAULT_SET = ["piano_m1", "piano", "organ", "organ_rock", "organ_pipe", "ep", "bell", "bell_tubular", "clock_bell",
               "guitar", "guitar_mute", "guitar_elec", "guitar_pluck", "acid_303", "saw_bass", "sine_sub",
               "y2k_bass", "pulsing_bass", "chip_lead", "lead_saw", "stab", "strings", "pad", "choir", "brass",
               "marimba", "showtime_sax", "rave_stab", "orch_hit", "clock_tick", "heartbeat"]


def base_midi(inst):
    if inst in BASS:
        return 36, (36, 43, 48)             # C2, G2, C3
    if inst in LEAD:
        return 72, (72, 79, 84)             # C5, G5, C6
    return 60, (60, 67, 72)                 # C4, G4, C5


def render_phrase(inst, sr=44100, note_s=0.55, gap_s=0.12):
    """three notes (root, fifth, octave) of one instrument -> (audio, note list)"""
    _, notes = base_midi(inst)
    chunks = []
    used = []
    for i, m in enumerate(notes):
        try:
            y = instruments.render(inst, m, note_s, 0.9, sr)
        except Exception as e:
            used.append(dict(midi=m, error=str(e)[:80])); continue
        y = np.asarray(y, dtype=np.float64)
        if y.ndim == 1:
            y = np.column_stack([y, y])
        pk = float(np.abs(y).max())
        if pk > 0:
            y = y * (0.82 / pk)
        chunks.append(y)
        used.append(dict(midi=m, seconds=round(note_s, 2)))
        if i < len(notes) - 1:
            chunks.append(np.zeros((int(gap_s * sr), 2)))
    if not chunks:
        return None, used
    return np.vstack(chunks), used


def build_showcase(names, sr=44100, lead_in=0.8, gap=0.55, note_s=0.55):
    parts = [np.zeros((int(lead_in * sr), 2))]
    guide = []
    t = lead_in
    for nm in names:
        y, used = render_phrase(nm, sr, note_s)
        if y is None:
            guide.append(dict(instrument=nm, start=round(t, 2), end=round(t, 2), ok=False, notes=used))
            continue
        parts.append(y)
        dur = len(y) / sr
        guide.append(dict(instrument=nm, start=round(t, 2), end=round(t + dur, 2), ok=True, notes=used))
        t += dur
        parts.append(np.zeros((int(gap * sr), 2)))
        t += gap
    audio = np.vstack(parts)
    return audio, guide


def build_minimix(genre, bpm, bars, seed, out_path):
    s = genres.build(genre, bars, bpm, None, None, seed, 0.75)
    audio = s.mixdown(master=True, reverb_rt60=s.rt60)
    songmod.write_wav(out_path, audio, s.sr)
    bm = s.beatmap(); bm["meta"] = s.meta
    return audio, s, bm


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="audition")
    ap.add_argument("--inst", help="comma-separated instrument keys (default: the standard voice set)")
    ap.add_argument("--all", action="store_true", help="every instrument in the library")
    ap.add_argument("--genre", default="horror_chase", help="genre for the mini-mix")
    ap.add_argument("--bpm", type=float, default=175.0)
    ap.add_argument("--bars", type=int, default=8)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--no-mix", action="store_true", help="showcase only")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    if a.all:
        names = sorted(instruments.INSTRUMENTS.keys())
    elif a.inst:
        names = [x.strip() for x in a.inst.split(",") if x.strip()]
    else:
        names = list(DEFAULT_SET)
    unknown = [n for n in names if n not in instruments.INSTRUMENTS]
    if unknown:
        raise SystemExit(f"audition: unknown instrument(s): {', '.join(unknown)}\nknown: {', '.join(sorted(instruments.INSTRUMENTS))}")
    sr = 44100
    audio, guide = build_showcase(names, sr)
    sw = os.path.join(a.out, "showcase.wav")
    U.write_wav(sw, audio, sr)
    L = ["# Instrument showcase", "", f"{len(guide)} instrument(s), {round(len(audio) / sr, 1)} s. Every voice is normalised to the same peak so you can compare them.", "",
         "| start | end | instrument | notes (MIDI) |", "|---|---|---|---|"]
    for g in guide:
        ms = ", ".join(str(n["midi"]) for n in g["notes"] if "midi" in n)
        L.append(f"| {g['start']:.2f} s | {g['end']:.2f} s | `{g['instrument']}` | {ms}{'' if g['ok'] else ' (FAILED)'} |")
    L += ["", "Play the showcase and write down which voices are wrong. Nobody has listened to this kit yet: that is what this file is for."]
    open(os.path.join(a.out, "showcase.md"), "w").write("\n".join(L) + "\n")
    rep = dict(schema="audio-forge/audition@1", showcase=os.path.abspath(sw), instruments=guide,
               showcase_seconds=round(len(audio) / sr, 2))
    mixinfo = None
    if not a.no_mix:
        mp = os.path.join(a.out, "minimix.wav")
        _, s, bm = build_minimix(a.genre, a.bpm, a.bars, a.seed, mp)
        rep["minimix"] = dict(path=os.path.abspath(mp), genre=a.genre, bpm=a.bpm, bars=a.bars,
                              sections=[dict(name=n, start_bar=sb, bars=nb) for n, sb, nb in s.sections],
                              events=len(s.events))
        mixinfo = rep["minimix"]
        json.dump(bm, open(os.path.join(a.out, "minimix.json"), "w"), indent=1)
    json.dump(rep, open(os.path.join(a.out, "showcase.json"), "w"), indent=1)
    print("\n".join(L[:8]))
    print(f"\n[showcase -> {sw}]")
    if mixinfo:
        print(f"[mini-mix {mixinfo['genre']} @ {mixinfo['bpm']:g} BPM, {mixinfo['bars']} bars -> {mixinfo['path']}]")
    print("Nobody has listened to these sounds. Play the showcase before shipping.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

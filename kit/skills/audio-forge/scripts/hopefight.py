#!/usr/bin/env python3
"""hopefight.py -- an ORIGINAL 174 BPM A-minor chase/LMS piece written in the SHAPE of "Eternal Hope, Eternal Fight"
(mainly), with a stomp section from LMSY2K and a strip-back + snare-roll build from A Grave Soul.

It copies measurements of structure only (see style-copy/library and listening-test-pack): the melodies, chords and
patterns below are written fresh. Instruments are the kit's realistic voices (forge/real.py): grand piano, tubular
bells, glockenspiel, Hammond-style and pipe organ, Karplus-Strong guitars through an amp + cabinet. Drums, sub and
riser are synthesised too. Nothing is sampled. Nobody has listened to this: audition it.

  python3 hopefight.py --out hope.wav [--seed 7] [--bpm 174] [--stems DIR] [--midi]

Layout (bars at 174 BPM = 1.38 s each; 52 bars = 71.7 s):
   1- 8 intro  half-time pulse, staccato piano riff, organ swell, bell echo, riser + snare roll into the drop
   9-24 drop A full DnB beat, palm-muted guitars, piano stabs, bass; from bar 17 bell hook + guitar lead
  25-28 stomp  half-time heavy (LMSY2K): power chords, church organ, low piano, sub boom
  29-33 drop   full beat returns; bars 32-33 strip back to a snare-roll build (A Grave Soul)
  34-49 drop C brightest: guitar lead + piano double the hook, bells an octave up, glock arps; sub booms at 38 and 48
  50-51 break  piano arpeggio + bells + church organ, no drums
     52 end    final hit then a reverb tail (hard cut)
"""
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from forge import dsp, song as songmod  # noqa: E402
from forge.song import Song  # noqa: E402

CH = {  # chord name -> (bass midi, guitar power chord, piano RH, piano LH, organ pad)
    "Am": (33, [45, 52, 57], [60, 64, 69], [45, 57], [57, 64, 69]),
    "F": (29, [41, 48, 53], [60, 65, 69], [41, 53], [53, 60, 65]),
    "C": (36, [48, 55, 60], [60, 64, 67], [36, 48], [55, 60, 64]),
    "G": (31, [43, 50, 55], [59, 62, 67], [43, 55], [55, 59, 62]),
    "Dm": (38, [50, 57, 62], [62, 65, 69], [38, 50], [57, 62, 65]),
    "E": (40, [40, 47, 52], [59, 64, 68], [40, 52], [56, 59, 64]),
}
CYC_A = ["Am", "F", "C", "G"]
CYC_B = ["Am", "F", "Dm", "E"]

# hooks as (step, dur_steps, midi) per bar; written for this piece
HOOK_A = [
    [(0, 2, 76), (2, 2, 81), (4, 2, 79), (6, 2, 76), (8, 4, 74), (12, 2, 72), (14, 2, 74)],
    [(0, 2, 72), (2, 2, 77), (4, 2, 76), (6, 2, 72), (8, 6, 69), (14, 2, 72)],
    [(0, 2, 76), (2, 2, 79), (4, 2, 76), (6, 2, 72), (8, 4, 67), (12, 2, 69), (14, 2, 72)],
    [(0, 2, 74), (2, 2, 71), (4, 2, 67), (6, 2, 71), (8, 8, 74)],
]
HOOK_B = [
    [(0, 3, 81), (3, 1, 79), (4, 2, 76), (6, 2, 72), (8, 2, 76), (10, 2, 81), (12, 4, 79)],
    [(0, 3, 84), (3, 1, 81), (4, 2, 77), (6, 2, 81), (8, 4, 77), (12, 2, 72), (14, 2, 77)],
    [(0, 2, 74), (2, 2, 77), (4, 2, 81), (6, 2, 77), (8, 4, 74), (12, 2, 77), (14, 2, 76)],
    [(0, 2, 83), (2, 2, 80), (4, 2, 76), (6, 2, 80), (8, 8, 83)],
]


def chord_of(bar):
    """bar is 1-based; alternate A and B 4-bar cycles"""
    c = (bar - 1) // 4
    cyc = CYC_A if c % 2 == 0 else CYC_B
    return cyc[(bar - 1) % 4], (bar - 1) % 4, c % 2


def build(seed=7, bpm=174.0, bars=52, kit_kick="industrial", kit_other="acoustic"):
    S = Song(bpm, bars, seed=seed, tail=3.4)
    P = lambda bar, st=0: (bar - 1) * 16 + st  # noqa: E731
    rng = np.random.RandomState(seed)

    # ── mix: levels chosen from measured stems of the first render, then compared with the reference DNA ──
    S.track("kick", gain_db=3.0)
    S.track("snare", gain_db=2.5, reverb=0.12)
    S.track("hat", gain_db=-2.5, pan=0.2, hp=500)
    S.track("ohat", gain_db=-6.0, pan=-0.2, hp=500)
    S.track("tom", gain_db=-6.0)
    S.track("fx", gain_db=-3.0, reverb=0.1)
    S.track("bass", gain_db=-6.0, hp=30, sidechain=0.35, sc_release=0.14)
    S.track("sub", gain_db=-9.0, hp=28, sidechain=0.45)
    S.track("boom", gain_db=0.0, hp=25)
    S.track("gtrL", gain_db=-10.5, pan=-0.8, hp=70, reverb=0.08)
    S.track("gtrR", gain_db=-10.5, pan=0.8, hp=70, reverb=0.08)
    S.track("lead", gain_db=-7.0, pan=0.05, reverb=0.22, delay=0.18)
    S.track("piano", gain_db=-8.5, pan=-0.12, reverb=0.28, hp=60)
    S.track("pianoL", gain_db=-12.0, pan=-0.1, reverb=0.15, hp=30)
    S.track("bell", gain_db=-8.5, pan=0.2, reverb=0.45, delay=0.2, hp=300)
    S.track("glock", gain_db=-10.0, pan=-0.3, reverb=0.4, delay=0.25, hp=500)
    S.track("organ", gain_db=-17.0, pan=0.0, reverb=0.3)
    S.track("pipe", gain_db=-17.0, pan=0.0, reverb=0.5)

    SEC = [("intro", 1, 8), ("drop", 9, 16), ("main", 25, 4), ("drop", 29, 2), ("build", 31, 2), ("drop", 33, 17),
           ("break", 50, 2), ("outro", 52, 1)]
    for name, sb, nb in SEC:
        S.mark(name, sb - 1, nb)

    def dr(track, name, bar, st, vel=1.0, kit=None):
        S.drum(track, name, P(bar, st), vel, kit or (kit_kick if name == "kick" else kit_other))

    def boom(bar, st=0, vel=1.0):
        """one-shot sub/kick impact on a bar line (the references have one about every 10 bars)"""
        S.note("boom", "sub_drop", P(bar, st), 4, 33, vel)
        S.note("boom", "sine_sub", P(bar, st), 3, 45, vel * 0.5)
        dr("fx", "impact", bar, st, 0.9)
        dr("kick", "kick", bar, st, 1.0)

    def dnb_bar(bar, density=1.0, fill=False):
        for st in (0, 10):
            dr("kick", "kick", bar, st, 1.0 if st == 0 else 0.9)
        if density > 0.6:
            dr("kick", "kick", bar, 2 if bar % 2 else 7, 0.55)
        for st in (4, 12):
            dr("snare", "snare", bar, st, 1.0)
        dr("snare", "snare", bar, 7, 0.28)
        dr("snare", "snare", bar, 15, 0.3)
        for st in range(0, 16, 2):
            dr("hat", "hat", bar, st, 0.85 if st % 4 == 0 else 0.55)
        for st in (3, 9, 13):
            dr("hat", "hat", bar, st, 0.25)
        if bar % 2 == 0:
            dr("ohat", "ohat", bar, 14, 0.7)
        if fill:
            for i, st in enumerate((12, 13, 14, 15)):
                dr("snare", "snare", bar, st, 0.55 + 0.12 * i)

    def halftime_bar(bar, hats=True):
        dr("kick", "kick", bar, 0, 1.0)
        dr("snare", "snare", bar, 8, 1.0)
        if bar % 2 == 0:
            dr("kick", "kick", bar, 6, 0.6)
        if hats:
            for st in range(0, 16, 2):
                dr("hat", "hat", bar, st, 0.6 if st % 4 == 0 else 0.35)

    def bass_bar(bar, chord, density=1.0):
        root = CH[chord][0]
        pat = [(0, 3, 0), (3, 2, 0), (6, 2, 12), (10, 3, 0), (13, 2, 7)]
        for st, d, off in pat:
            S.note("bass", "saw_bass", P(bar, st), d * 0.9, root + 12 + off if off else root + 12, 0.9, cutoff=650, drive=1.6)
        S.note("sub", "sine_sub", P(bar), 16 * 0.95, root, 0.9)

    def guitars(bar, chord, style="chug", vel=0.9):
        pw = CH[chord][1]
        if style == "chug":
            pat = [(0, 'o', 2), (2, 'm', 1), (3, 'm', 1), (4, 'm', 1), (6, 'm', 1), (7, 'm', 1), (8, 'o', 2),
                   (10, 'm', 1), (11, 'm', 1), (12, 'm', 1), (14, 'm', 1), (15, 'm', 1)]
        elif style == "stomp":
            pat = [(0, 'o', 6), (8, 'o', 4), (12, 'm', 1), (14, 'm', 1)]
        else:  # sustain
            pat = [(0, 'o', 15)]
        for st, kind, d in pat:
            for tr, off, br in (("gtrL", 0.0, 0.9), ("gtrR", 0.16, 0.8)):
                for k, nn in enumerate(pw):
                    mute = 0.85 if kind == 'm' else 0.0
                    S.note(tr, "guitar_amp", P(bar, st) + off, max(d * 0.95, 0.5), nn, vel * (1.0 if kind == 'o' else 0.85) * (0.9 if k else 1.0),
                           drive=7.5, mute=mute, bright=br)

    def piano_stabs(bar, chord, vel=0.75, pattern=((0, 3), (6, 2), (10, 3), (14, 2))):
        rh, lh = CH[chord][2], CH[chord][3]
        for st, d in pattern:
            for nn in rh:
                S.note("piano", "piano_grand", P(bar, st), d, nn, vel * (0.95 if st else 1.0))
        S.note("pianoL", "piano_grand", P(bar), 6, lh[0], vel * 0.9)
        S.note("pianoL", "piano_grand", P(bar), 6, lh[1], vel * 0.7)

    def piano_riff(bar, chord, vel=0.7):
        """staccato 16th ostinato (original): root, fifth, octave, in a syncopated pattern"""
        root = CH[chord][2][0]
        seq = [(0, 0), (2, 7), (4, 12), (5, 7), (8, 0), (10, 7), (12, 12), (14, 7), (15, 12)]
        for st, off in seq:
            S.note("piano", "piano_grand", P(bar, st), 1.2, root + off, vel * (1.0 if st % 4 == 0 else 0.8), pan=0.0)

    def organ_pad(bar, chord, d=16, vel=0.8, inst="organ_drawbar", track="organ", **kw):
        for nn in CH[chord][4]:
            S.note(track, inst, P(bar), d, nn, vel, **kw)

    def hook(bar0, cyc, track, inst, transpose=0, vel=0.85, **kw):
        hk = HOOK_A if cyc == 0 else HOOK_B
        for bi in range(4):
            for st, d, m in hk[bi]:
                S.note(track, inst, P(bar0 + bi, st), d * 0.97, m + transpose, vel * (1.0 if st % 4 == 0 else 0.88), **kw)

    def glock_arp(bar, chord, vel=0.55):
        notes = [n + 24 for n in CH[chord][2]]
        pat = [0, 1, 2, 1, 2, 1, 0, 1]
        for i, st in enumerate(range(0, 16, 2)):
            S.note("glock", "music_box", P(bar, st), 1.5, notes[pat[i] % 3], vel * (1.0 if i % 4 == 0 else 0.75), pan=-0.35 if i % 2 else 0.35)

    # ───────────────────────── intro 1-8 ─────────────────────────
    S.drum("fx", "crash", 0, 0.8, kit_other)
    S.drum("fx", "impact", 0, 1.0, kit_other)
    S.note("sub", "sub_drop", 0, 12, 33, 1.0)
    for bar in range(1, 9):
        chord, bi, cyc = chord_of(bar)
        halftime_bar(bar, hats=bar >= 3)
        piano_riff(bar, chord, 0.62 if bar < 5 else 0.72)
        organ_pad(bar, chord, 16, 0.7 if bar < 5 else 0.85, leslie=0.7)
        bass_halftime = CH[chord][0]
        S.note("sub", "sine_sub", P(bar), 14, bass_halftime, 0.85)
        if bar >= 3:
            S.note("bass", "saw_bass", P(bar), 6, bass_halftime + 12, 0.7, cutoff=500, drive=1.4)
        if bar >= 5:
            for st, d, m in (HOOK_A if cyc == 0 else HOOK_B)[bi]:
                if st % 4 == 0 or st in (6, 14):
                    S.note("bell", "bell_church", P(bar, st), d, m + 12, 0.6, ring=0.45)
        if bar == 4:
            guitars(bar, chord, "sustain", 0.5)
        if bar >= 7:
            for st in range(0, 16, 2 if bar == 7 else 1):
                S.drum("snare", "snare", P(bar, st), 0.3 + 0.7 * ((bar - 7) * 16 + st) / 32.0, kit_other)
    S.sample("fx", dsp.riser(2 * 16 * S.step_s, 250, 7500, S.sr, 0.7), P(7), 0.8)

    # ───────────────────────── drop A 9-24 ─────────────────────────
    for bar in range(9, 25):
        chord, bi, cyc = chord_of(bar)
        if bar == 9:
            S.drum("fx", "crash", P(9), 1.0, kit_other)
            boom(9)
        dnb_bar(bar, 1.0, fill=(bi == 3))
        bass_bar(bar, chord)
        guitars(bar, chord, "chug", 0.85 if bar < 17 else 0.8)
        piano_stabs(bar, chord, 0.7)
        if bar >= 13:
            organ_pad(bar, chord, 16, 0.5, leslie=0.9)
    hook(17, 0, "bell", "bell_church", 12, 0.8, ring=0.5)
    hook(21, 1, "bell", "bell_church", 12, 0.8, ring=0.5)
    hook(17, 0, "lead", "guitar_amp", 0, 0.9, drive=5.5, bright=0.9)
    hook(21, 1, "lead", "guitar_amp", 0, 0.9, drive=5.5, bright=0.9)

    # ───────────────────────── stomp 25-28 (LMSY2K) ─────────────────────────
    for bar in range(25, 29):
        chord, bi, cyc = chord_of(bar)
        halftime_bar(bar, hats=True)
        guitars(bar, chord, "stomp", 1.0)
        S.note("sub", "sine_sub", P(bar), 15, CH[chord][0], 1.0)
        S.note("bass", "saw_bass", P(bar), 6, CH[chord][0] + 12, 0.8, cutoff=480, drive=2.2)
        organ_pad(bar, chord, 16, 0.9, inst="organ_church", track="pipe")
        for nn in CH[chord][3]:
            S.note("pianoL", "piano_grand", P(bar), 8, nn, 0.95)
        rh = CH[chord][2]
        for st in (0, 8):
            S.note("piano", "piano_grand", P(bar, st), 4, rh[0], 0.8)
    hook(25, 0, "bell", "bell_church", 12, 0.7, ring=0.8)
    boom(28, 0, 1.0)

    # ───────────────────────── drop 29-30 + build 31-32 (A Grave Soul) ─────────────────────────
    for bar in range(29, 31):
        chord, bi, cyc = chord_of(bar)
        dnb_bar(bar, 1.0, fill=False)
        bass_bar(bar, chord)
        guitars(bar, chord, "chug", 0.85)
        piano_stabs(bar, chord, 0.7)
    S.drum("fx", "crash", P(29), 0.9, kit_other)
    for bar in (31, 32):
        chord, bi, cyc = chord_of(bar)
        organ_pad(bar, chord, 16, 0.9, inst="organ_church", track="pipe")
        S.note("sub", "sine_sub", P(bar), 15, CH[chord][0], 0.8)
        dr("kick", "kick", bar, 0, 0.9)
        rh = CH[chord][2]
        for i, st in enumerate(range(0, 16, 2)):
            S.note("piano", "piano_grand", P(bar, st), 1.6, rh[i % 3] + (12 if i % 2 else 0), 0.6 + 0.05 * i)
        for st in range(0, 16, 2 if bar == 31 else 1):
            S.drum("snare", "snare", P(bar, st), 0.3 + 0.7 * (((bar - 31) * 16 + st) / 32.0), kit_other)
    S.sample("fx", dsp.riser(2 * 16 * S.step_s, 300, 8500, S.sr, 0.8), P(31), 0.9)

    # ───────────────────────── drop C 33-49 ─────────────────────────
    for bar in range(33, 50):
        chord, bi, cyc = chord_of(bar)
        if bar == 33:
            S.drum("fx", "crash", P(33), 1.0, kit_other)
            boom(33)
        dnb_bar(bar, 1.0, fill=(bi == 3))
        bass_bar(bar, chord)
        guitars(bar, chord, "chug", 0.82)
        piano_stabs(bar, chord, 0.72)
        organ_pad(bar, chord, 16, 0.55, leslie=1.0)
        glock_arp(bar, chord, 0.55 if bar >= 35 else 0.4)
    # hooks start on chord-cycle starts (bars 33, 37, 41, 45); bar 49 is the last Am
    for b0 in (33, 37, 41, 45, 49):
        cyc = ((b0 - 1) // 4) % 2
        end = min(4, 50 - b0)
        hk = HOOK_A if cyc == 0 else HOOK_B
        for bi in range(end):
            for st, d, m in hk[bi]:
                S.note("lead", "guitar_amp", P(b0 + bi, st), d * 0.97, m, 0.95 * (1.0 if st % 4 == 0 else 0.88), drive=5.5, bright=0.95)
                S.note("bell", "bell_church", P(b0 + bi, st), d * 0.97, m + 12, 0.8 * (1.0 if st % 4 == 0 else 0.85), ring=0.5)
                S.note("piano", "piano_grand", P(b0 + bi, st), d * 0.97, m - 12 if m > 74 else m, 0.7)
    boom(38)
    boom(48)

    # ───────────────────────── break 50-51 ─────────────────────────
    for bar, chord in ((50, "Am"), (51, "E")):
        organ_pad(bar, chord, 16, 0.9, inst="organ_church", track="pipe")
        S.note("sub", "sine_sub", P(bar), 15, CH[chord][0], 0.7)
        rh = CH[chord][2]
        seq = [rh[0], rh[1], rh[2], rh[1] + 12 if False else rh[2] + 12, rh[2], rh[1], rh[0], rh[1]]
        for i, st in enumerate(range(0, 16, 2)):
            S.note("piano", "piano_grand", P(bar, st), 5, seq[i], 0.62 if i % 2 else 0.72)
        S.note("pianoL", "piano_grand", P(bar), 14, CH[chord][3][0], 0.7)
    for st, d, m in ((0, 6, 88), (8, 6, 84), (16, 6, 83), (24, 8, 80)):
        S.note("bell", "bell_church", P(50, st), d, m, 0.55, ring=1.0)

    # ───────────────────────── end 52 ─────────────────────────
    S.drum("fx", "crash", P(52), 1.0, kit_other)
    S.drum("fx", "impact", P(52), 1.0, kit_other)
    dr("kick", "kick", 52, 0, 1.0)
    S.note("sub", "sub_drop", P(52), 8, 33, 1.0)
    for tr in ("gtrL", "gtrR"):
        for nn in CH["Am"][1]:
            S.note(tr, "guitar_amp", P(52), 6, nn, 1.0, drive=7.5, mute=0.0, bright=0.9)
    for nn in CH["Am"][2]:
        S.note("piano", "piano_grand", P(52), 10, nn, 0.95)
    S.note("pianoL", "piano_grand", P(52), 10, 33, 0.95)
    S.note("pianoL", "piano_grand", P(52), 10, 45, 0.9)
    for nn in CH["Am"][4]:
        S.note("pipe", "organ_church", P(52), 8, nn, 0.9)
    S.note("bell", "bell_church", P(52), 6, 93, 0.8, ring=1.2)
    S.note("bell", "bell_church", P(52), 6, 81, 0.8, ring=1.2)

    S.meta = dict(genre="hopefight", bpm=bpm, key="A", scale="minor", seed=seed, bars=bars, progression="Am F C G / Am F Dm E")
    S.rt60 = 2.2
    return S


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="hopefight.wav")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--bpm", type=float, default=174.0)
    ap.add_argument("--stems", default=None)
    ap.add_argument("--midi", action="store_true")
    ap.add_argument("--dynamics", type=float, default=0.5)
    ap.add_argument("--lufs", type=float, default=-14.0)
    a = ap.parse_args()
    S = build(a.seed, a.bpm)
    audio = S.mixdown(stems_dir=a.stems, master=False, reverb_rt60=S.rt60, dynamics=a.dynamics)
    audio = dsp.hp(audio, 28, S.sr, 2)
    audio = audio + 1.0 * dsp.hp(audio, 6500, S.sr, 2)          # air shelf: the synthesised highs are duller than a mixed-down reference
    audio = dsp.compress(audio, -10, 1.35, 0.03, 0.2, 0.0, S.sr)     # light glue only: the references keep a crest factor of ~15 dB
    audio = np.tanh(audio * 1.05) / np.tanh(1.05)
    audio = dsp.limiter(audio, -1.0, sr=S.sr)
    audio = dsp.normalize(audio, -1.0)
    songmod.write_wav(a.out, audio, S.sr)
    try:
        import analyze as _A
        for _ in range(2):
            cur = _A.loudness(a.out)["lufs"]
            if cur is None or abs(cur - a.lufs) < 0.4:
                break
            audio = audio * (10 ** ((a.lufs - cur) / 20.0))
            if a.lufs > cur:
                audio = dsp.limiter(audio, -1.0, sr=S.sr)
            songmod.write_wav(a.out, audio, S.sr)
    except Exception as e:  # loudness helper is optional
        print("loudness step skipped:", e, file=sys.stderr)
    bm = S.beatmap()
    bm["meta"] = S.meta
    json.dump(bm, open(a.out + ".beatmap.json", "w"), indent=1)
    if a.midi:
        songmod.write_midi(a.out + ".mid", S)
    print(json.dumps(dict(out=a.out, seconds=round(len(audio) / S.sr, 1), **S.meta)))


if __name__ == "__main__":
    main()

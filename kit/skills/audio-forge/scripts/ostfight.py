#!/usr/bin/env python3
"""ostfight.py -- ONE original OST piece built from your reference themes by PRIORITY (not a copy of any of them).

PRIORITY 1  Eternal Hope, Eternal Fight : 174 BPM A minor, intense drum-and-bass breakbeat, half-time intro with a staccato piano riff,
            full-impact drop, sub/kick booms about every 10 bars, bright mid lead in the last third, short piano+bell breakdown, hard cut + tail.
PRIORITY 2  A Grave Soul                : the mid-round breakdown becomes a CLOCK section: ticking, quarter-hour bell chimes, hour tolls and a
            heartbeat = "just some time left", then a build (riser + snare roll) into the final drop.
LOW         everything else except Fired and Showtime (different style), one signature each:
            LMSY2K        half-time stomp with chiptune arps; clean piano/bell outro; glitch stutter before the end
            ONEBOUNCE     a 1-bar drop-out ("fill dip") before a boom; harmonic lift late (A minor -> B minor, also the key of Vigilante/Grave Soul)
            Vigilante     late short breakdown then a riser into the hard cut
            Necrobloxians hard cut with a 3 s tail
            EternityV2    riser right before the first drop
            Eternity Forsaken  long single drop, one extended breakdown (kept short here)

  python3 ostfight.py --out ost.wav [--seed 7] [--stems DIR] [--midi]
Layout at 174 BPM (1 bar = 1.379 s, 64 bars = 88.3 s + tail):
   1- 8 intro (Rhodes pad, staccato piano riff, bell echo, riser + snare roll)       9-24 drop A (breakbeat, heavy guitars, piano stabs; bell hook + lead from 17)
  25-28 stomp (half-time, chiptune arps)   29-36 CLOCK section (tick, chimes, tolls, heartbeat, strings; build 35-36)
  37-60 drop C (brightest; boom 37/47/57; drop-out bar 46; lift to B minor at 49 with brass + strings)
  61-62 breakdown (piano, bells, pipe organ, Rhodes)   63 snare roll + stutter + riser   64 final hit, hard cut, tail
Instruments: piano_bright, piano_grand, bell_church, clock_bell, clock_tick, heartbeat, glock, celesta, ep_rhodes, harp, string_ensemble,
brass_section, guitar_heavy, guitar_lead, guitar_crunch, organ_drawbar, organ_church, chip_lead, saw_bass, sine_sub. Nobody has listened to this.
"""
import argparse, json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from forge import dsp, drums, song as songmod  # noqa: E402
from forge.song import Song  # noqa: E402

CH = {  # chord -> (bass, guitar power chord, piano RH, piano LH, pad)
    "Am": (33, [45, 52, 57], [60, 64, 69], [45, 57], [57, 64, 69]),
    "F": (29, [41, 48, 53], [60, 65, 69], [41, 53], [53, 60, 65]),
    "C": (36, [48, 55, 60], [60, 64, 67], [36, 48], [55, 60, 64]),
    "G": (31, [43, 50, 55], [59, 62, 67], [43, 55], [55, 59, 62]),
    "Dm": (38, [50, 57, 62], [62, 65, 69], [38, 50], [57, 62, 65]),
    "E": (40, [40, 47, 52], [59, 64, 68], [40, 52], [56, 59, 64]),
}
CYC_A, CYC_B = ["Am", "F", "C", "G"], ["Am", "F", "Dm", "E"]
HOOK_A = [[(0, 2, 76), (2, 2, 81), (4, 2, 79), (6, 2, 76), (8, 4, 74), (12, 2, 72), (14, 2, 74)],
          [(0, 2, 72), (2, 2, 77), (4, 2, 76), (6, 2, 72), (8, 6, 69), (14, 2, 72)],
          [(0, 2, 76), (2, 2, 79), (4, 2, 76), (6, 2, 72), (8, 4, 67), (12, 2, 69), (14, 2, 72)],
          [(0, 2, 74), (2, 2, 71), (4, 2, 67), (6, 2, 71), (8, 8, 74)]]
HOOK_B = [[(0, 3, 81), (3, 1, 79), (4, 2, 76), (6, 2, 72), (8, 2, 76), (10, 2, 81), (12, 4, 79)],
          [(0, 3, 84), (3, 1, 81), (4, 2, 77), (6, 2, 81), (8, 4, 77), (12, 2, 72), (14, 2, 77)],
          [(0, 2, 74), (2, 2, 77), (4, 2, 81), (6, 2, 77), (8, 4, 74), (12, 2, 77), (14, 2, 76)],
          [(0, 2, 83), (2, 2, 80), (4, 2, 76), (6, 2, 80), (8, 8, 83)]]
CHIME = [81, 76, 77, 74]          # original four-note quarter-hour chime (A5 E5 F5 D5), not the Westminster tune
TOLL = 57                          # low bell for the hour tolls


def chord_of(bar):
    c = (bar - 1) // 4
    return (CYC_A if c % 2 == 0 else CYC_B)[(bar - 1) % 4], (bar - 1) % 4, c % 2


def T(bar):  # key lift: A minor -> B minor from bar 49 (ONEBOUNCE/Vigilante/Grave Soul keys)
    return 2 if 49 <= bar <= 62 else 0


def build(seed=7, bpm=174.0, bars=64):
    S = Song(bpm, bars, seed=seed, tail=3.4)
    P = lambda bar, st=0: (bar - 1) * 16 + st  # noqa: E731
    rng = np.random.RandomState(seed)
    K, O = "industrial", "acoustic"
    tk = dict(kick=("kick", 3.0, None), snare=("snare", 2.5, 0.12), hat=("hat", -2.5, None))
    S.track("kick", gain_db=3.0); S.track("snare", gain_db=2.5, reverb=0.12)
    S.track("hat", gain_db=-2.5, pan=0.2, hp=500); S.track("ohat", gain_db=-6.0, pan=-0.2, hp=500)
    S.track("tom", gain_db=-6.0); S.track("fx", gain_db=-3.0, reverb=0.1)
    S.track("bass", gain_db=-6.0, hp=30, sidechain=0.35, sc_release=0.14)
    S.track("sub", gain_db=-9.0, hp=28, sidechain=0.45); S.track("boom", gain_db=0.0, hp=25)
    S.track("gtrL", gain_db=-10.5, pan=-0.8, hp=70, reverb=0.08); S.track("gtrR", gain_db=-10.5, pan=0.8, hp=70, reverb=0.08)
    S.track("lead", gain_db=-7.0, reverb=0.22, delay=0.18)
    S.track("piano", gain_db=-8.5, pan=-0.12, reverb=0.28, hp=60); S.track("pianoL", gain_db=-12.0, pan=-0.1, reverb=0.15, hp=30)
    S.track("bell", gain_db=-8.5, pan=0.2, reverb=0.45, delay=0.2, hp=300)
    S.track("glock", gain_db=-10.0, pan=-0.3, reverb=0.4, delay=0.25, hp=500)
    S.track("organ", gain_db=-17.0, reverb=0.3); S.track("pipe", gain_db=-17.0, reverb=0.5)
    S.track("rhodes", gain_db=-10.0, pan=0.1, reverb=0.3)
    S.track("strings", gain_db=-12.0, reverb=0.4); S.track("brass", gain_db=-11.0, reverb=0.25)
    S.track("chip", gain_db=-14.0, pan=0.35, delay=0.2, hp=400)
    S.track("clock", gain_db=-9.0, reverb=0.25, hp=400); S.track("chime", gain_db=-8.0, reverb=0.5, delay=0.15)
    S.track("heart", gain_db=-10.0, hp=30); S.track("harp", gain_db=-11.0, pan=-0.25, reverb=0.35)
    for n, sb, nb in [("intro", 1, 8), ("drop", 9, 16), ("main", 25, 4), ("break", 29, 6), ("build", 35, 2), ("drop", 37, 24),
                      ("break", 61, 2), ("build", 63, 1), ("outro", 64, 1)]:
        S.mark(n, sb - 1, nb)

    def dr(track, name, bar, st, vel=1.0):
        S.drum(track, name, P(bar, st), vel, K if name == "kick" else O)

    def boom(bar, st=0, vel=1.0):
        S.note("boom", "sub_drop", P(bar, st), 4, 33 + T(bar), vel)
        S.note("boom", "sine_sub", P(bar, st), 3, 45 + T(bar), vel * 0.5)
        dr("fx", "impact", bar, st, 0.9); dr("kick", "kick", bar, st, 1.0)

    def breakbeat_bars(b0, nb, intensity=1.0, fills=True):
        """priority 1: V2's drum-and-bass breakbeat generator, placed on the bar grid, plus a Hope-style two-step kick"""
        ev = drums.breakbeat(nb, "dnb", np.random.RandomState(seed + b0), intensity, fill=fills)
        for st, nm, v in ev:
            tr = {"kick": "kick", "snare": "snare", "hat": "hat", "ohat": "ohat", "tom": "tom", "ride": "hat", "clap": "snare"}.get(nm, "hat")
            S.drum(tr, nm, P(b0) + st, v, K if nm == "kick" else O)

    def halftime_bar(bar, hats=True):
        dr("kick", "kick", bar, 0, 1.0); dr("snare", "snare", bar, 8, 1.0)
        if bar % 2 == 0: dr("kick", "kick", bar, 6, 0.6)
        if hats:
            for st in range(0, 16, 2): dr("hat", "hat", bar, st, 0.6 if st % 4 == 0 else 0.35)

    def bass_bar(bar, ch):
        root = CH[ch][0] + T(bar)
        for st, d, off in [(0, 3, 0), (3, 2, 0), (6, 2, 12), (10, 3, 0), (13, 2, 7)]:
            S.note("bass", "saw_bass", P(bar, st), d * 0.9, root + 12 + off, 0.9, cutoff=650, drive=1.6)
        S.note("sub", "sine_sub", P(bar), 15, root, 0.9)

    def guitars(bar, ch, style="chug", vel=0.85):
        pw = [n + T(bar) for n in CH[ch][1]]
        pat = {"chug": [(0, 'o', 2), (2, 'm', 1), (3, 'm', 1), (4, 'm', 1), (6, 'm', 1), (7, 'm', 1), (8, 'o', 2), (10, 'm', 1), (11, 'm', 1), (12, 'm', 1), (14, 'm', 1), (15, 'm', 1)],
               "stomp": [(0, 'o', 6), (8, 'o', 4), (12, 'm', 1), (14, 'm', 1)]}[style]
        for st, kind, d in pat:
            for tr, off in (("gtrL", 0.0), ("gtrR", 0.16)):
                for k, nn in enumerate(pw):
                    S.note(tr, "guitar_heavy", P(bar, st) + off, max(d * 0.95, 0.5), nn, vel * (1.0 if kind == 'o' else 0.85) * (0.9 if k else 1.0),
                           drive=12.0 if kind == 'm' else 9.0, mute=0.85 if kind == 'm' else 0.1)

    def piano_stabs(bar, ch, vel=0.72, pattern=((0, 3), (6, 2), (10, 3), (14, 2))):
        rh, lh = [n + T(bar) for n in CH[ch][2]], [n + T(bar) for n in CH[ch][3]]
        for st, d in pattern:
            for nn in rh: S.note("piano", "piano_bright", P(bar, st), d, nn, vel * (0.95 if st else 1.0))
        S.note("pianoL", "piano_grand", P(bar), 6, lh[0], vel * 0.9); S.note("pianoL", "piano_grand", P(bar), 6, lh[1], vel * 0.7)

    def piano_riff(bar, ch, vel=0.7):
        root = CH[ch][2][0] + T(bar)
        for st, off in [(0, 0), (2, 7), (4, 12), (5, 7), (8, 0), (10, 7), (12, 12), (14, 7), (15, 12)]:
            S.note("piano", "piano_bright", P(bar, st), 1.2, root + off, vel * (1.0 if st % 4 == 0 else 0.8))

    def pad(bar, ch, d=16, vel=0.8, inst="organ_drawbar", track="organ", **kw):
        for nn in CH[ch][4]: S.note(track, inst, P(bar), d, nn + T(bar), vel, **kw)

    def hook(b0, track, inst, transpose=0, vel=0.85, **kw):
        cyc = ((b0 - 1) // 4) % 2; hk = HOOK_A if cyc == 0 else HOOK_B
        for bi in range(min(4, 61 - b0)):
            for st, d, m in hk[bi]:
                S.note(track, inst, P(b0 + bi, st), d * 0.97, m + transpose + T(b0 + bi), vel * (1.0 if st % 4 == 0 else 0.88), **kw)

    def glock_arp(bar, ch, vel=0.55):
        notes = [n + 24 + T(bar) for n in CH[ch][2]]
        for i, st in enumerate(range(0, 16, 2)):
            S.note("glock", "glock", P(bar, st), 1.5, notes[[0, 1, 2, 1, 2, 1, 0, 1][i] % 3], vel * (1.0 if i % 4 == 0 else 0.75), pan=-0.35 if i % 2 else 0.35)

    # ═══ intro 1-8 (Hope: half-time, staccato riff, opening impact; EternityV2: riser into the drop) ═══
    S.drum("fx", "crash", 0, 0.8, O); S.drum("fx", "impact", 0, 1.0, O); S.note("sub", "sub_drop", 0, 12, 33, 1.0)
    for bar in range(1, 9):
        ch, bi, cyc = chord_of(bar)
        halftime_bar(bar, hats=bar >= 3); piano_riff(bar, ch, 0.62 if bar < 5 else 0.72)
        for nn in CH[ch][4]: S.note("rhodes", "ep_rhodes", P(bar), 14, nn, 0.7 if bar < 5 else 0.85, tremolo=0.6)
        S.note("sub", "sine_sub", P(bar), 14, CH[ch][0], 0.85)
        if bar >= 3: S.note("bass", "saw_bass", P(bar), 6, CH[ch][0] + 12, 0.7, cutoff=500, drive=1.4)
        if bar >= 5:
            for st, d, m in (HOOK_A if cyc == 0 else HOOK_B)[bi]:
                if st % 4 == 0 or st in (6, 14): S.note("bell", "bell_church", P(bar, st), d, m + 12, 0.6, ring=0.45)
        if bar >= 7:
            for st in range(0, 16, 2 if bar == 7 else 1):
                S.drum("snare", "snare", P(bar, st), 0.3 + 0.7 * ((bar - 7) * 16 + st) / 32.0, O)
    S.sample("fx", dsp.riser(2 * 16 * S.step_s, 250, 7500, S.sr, 0.7), P(7), 0.8)

    # ═══ drop A 9-24 (Hope: intense beats) ═══
    S.drum("fx", "crash", P(9), 1.0, O); boom(9)
    breakbeat_bars(9, 16, 1.0)
    for bar in range(9, 25):
        ch, bi, cyc = chord_of(bar)
        bass_bar(bar, ch); guitars(bar, ch, "chug", 0.85 if bar < 17 else 0.8); piano_stabs(bar, ch, 0.7)
        if bar >= 13: pad(bar, ch, 16, 0.5, leslie=0.9)
    boom(19, 0, 0.8)
    for b0 in (17, 21):
        hook(b0, "bell", "bell_church", 12, 0.8, ring=0.5); hook(b0, "lead", "guitar_lead", 0, 0.95)

    # ═══ stomp 25-28 (LMSY2K: half-time stomp + chiptune arps) ═══
    for bar in range(25, 29):
        ch, bi, cyc = chord_of(bar)
        halftime_bar(bar, True); guitars(bar, ch, "stomp", 1.0)
        S.note("sub", "sine_sub", P(bar), 15, CH[ch][0], 1.0); S.note("bass", "saw_bass", P(bar), 6, CH[ch][0] + 12, 0.8, cutoff=480, drive=2.2)
        pad(bar, ch, 16, 0.9, inst="organ_church", track="pipe")
        for nn in CH[ch][3]: S.note("pianoL", "piano_grand", P(bar), 8, nn, 0.95)
        arp = [n + 24 for n in CH[ch][2]]
        for i, st in enumerate(range(16)):
            S.note("chip", "chip_lead", P(bar, st), 0.9, arp[[0, 1, 2, 1][i % 4]] + (12 if (i // 4) % 2 else 0), 0.7)
    hook(25, "bell", "bell_church", 12, 0.7, ring=0.8)
    boom(28, 0, 1.0)

    # ═══ CLOCK section 29-36 (A Grave Soul, priority 2: mid-round clock chimes and bells = some time left) ═══
    prog = ["Am", "F", "Dm", "E", "Am", "F", "Dm", "E"]
    for k, bar in enumerate(range(29, 37)):
        ch = prog[k]; rh = CH[ch][2]
        for nn in CH[ch][4]: S.note("strings", "string_ensemble", P(bar), 15.5, nn, 0.55 + 0.04 * k)
        S.note("sub", "sine_sub", P(bar), 15, CH[ch][0], 0.7)
        for i, st in enumerate(range(0, 16, 2)):                       # soft harp arpeggio
            S.note("harp", "harp", P(bar, st), 3, [rh[0], rh[1], rh[2], rh[1] + 12][i % 4] + (12 if i > 3 else 0), 0.45 + 0.03 * k)
        if k < 4: S.note("piano", "piano_grand", P(bar, 4), 8, [81, 79, 76, 80][k] - 12, 0.6)
        for st in range(0, 16, 4 if bar < 35 else 2):                  # the clock: tick/tock, quickening in the build
            S.note("clock", "clock_tick", P(bar, st), 0.5, 76 if (st // 4) % 2 == 0 else 72, 0.9 if (st // 4) % 2 == 0 else 0.7)
        if bar in (29, 31, 33):                                        # quarter-hour chimes: 2, 3 then 4 notes
            for j, m in enumerate(CHIME[: {29: 2, 31: 3, 33: 4}[bar]]):
                S.note("chime", "clock_bell", P(bar, 0) + j * 3, 5, m, 0.85)
                S.note("bell", "bell_church", P(bar, 0) + j * 3, 5, m - 12, 0.4, ring=0.9)
        if bar >= 33:                                                  # heartbeat, getting faster
            for st in ((0, 8) if bar == 33 else (0, 4, 8, 12) if bar == 34 else tuple(range(0, 16, 2))):
                S.note("heart", "heartbeat", P(bar, st), 1, 36, 0.8)
        if bar in (34, 35, 36):                                        # hour tolls, one per bar: three strokes = three bars of time left
            S.note("chime", "bell_church", P(bar), 8, TOLL, 0.95, ring=1.6); S.note("boom", "sine_sub", P(bar), 6, 33, 0.7)
        if bar >= 35:
            for st in range(0, 16, 2 if bar == 35 else 1):
                S.drum("snare", "snare", P(bar, st), 0.25 + 0.75 * ((bar - 35) * 16 + st) / 32.0, O)
    S.sample("fx", dsp.riser(2 * 16 * S.step_s, 300, 9000, S.sr, 0.85), P(35), 0.9)

    # ═══ drop C 37-60 (Hope: brightest, booms every 10 bars; ONEBOUNCE drop-out at 46 and lift at 49; Eternity: single long drop) ═══
    S.drum("fx", "crash", P(37), 1.0, O); boom(37)
    breakbeat_bars(37, 9, 1.0)                 # 37-45
    for st, nm, v in [(0, "kick", 1.0), (8, "hat", 0.5), (12, "hat", 0.5)]:  # bar 46: the drop-out (kick + a few hats only)
        S.drum("kick" if nm == "kick" else "hat", nm, P(46) + st, v, K if nm == "kick" else O)
    breakbeat_bars(47, 14, 1.0)               # 47-60
    for bar in range(37, 61):
        ch, bi, cyc = chord_of(bar)
        if bar != 46:
            bass_bar(bar, ch); guitars(bar, ch, "chug", 0.82); piano_stabs(bar, ch, 0.72)
        else:
            S.note("sub", "sine_sub", P(bar), 14, CH[ch][0], 0.9)
        pad(bar, ch, 16, 0.55, leslie=1.0); glock_arp(bar, ch, 0.55 if bar >= 39 else 0.4)
    for b0 in (37, 41, 45, 49, 53, 57):
        hook(b0, "lead", "guitar_lead", 0, 0.98); hook(b0, "bell", "bell_church", 12, 0.8, ring=0.5)
        hook(b0, "piano", "piano_bright", -12, 0.65)
    boom(47); boom(57)
    for b0 in (49, 53, 57):                                            # key lift: brass fanfare + strings
        ch = chord_of(b0)[0]
        for nn in CH[ch][2]: S.note("brass", "brass_section", P(b0), 6, nn + 2, 0.9)
        for nn in CH[ch][4]: S.note("strings", "string_ensemble", P(b0), 60, nn + 2, 0.55)
    S.drum("fx", "crash", P(49), 0.9, O)

    # ═══ breakdown 61-62 (Hope 2-bar breakdown + LMSY2K clean piano/bell outro; Vigilante: late short breakdown) ═══
    for bar, ch in ((61, "Am"), (62, "E")):
        pad(bar, ch, 16, 0.9, inst="organ_church", track="pipe"); S.note("sub", "sine_sub", P(bar), 15, CH[ch][0] + 2, 0.7)
        rh = [n + 2 for n in CH[ch][2]]
        seq = [rh[0], rh[1], rh[2], rh[2] + 12, rh[2], rh[1], rh[0], rh[1]]
        for i, st in enumerate(range(0, 16, 2)): S.note("piano", "piano_grand", P(bar, st), 5, seq[i], 0.62 if i % 2 else 0.72)
        S.note("pianoL", "piano_grand", P(bar), 14, CH[ch][3][0] + 2, 0.7)
        for nn in CH[ch][2]: S.note("rhodes", "ep_rhodes", P(bar), 14, nn + 2, 0.6, tremolo=0.8)
    for st, d, m in ((0, 6, 90), (8, 6, 86), (16, 6, 85), (24, 8, 82)): S.note("bell", "bell_church", P(61, st), d, m, 0.55, ring=1.0)

    # ═══ 63 build + glitch stutter (LMSY2K) + riser (Vigilante) ═══
    for st in range(0, 16): S.drum("snare", "snare", P(63, st), 0.35 + 0.65 * st / 15.0, O)
    for i, st in enumerate(range(8, 16)):
        for nn in (CH["Am"][2][0] + 2, CH["Am"][2][2] + 2): S.note("piano", "piano_bright", P(63, st), 0.6, nn, 0.7 * (1 - 0.07 * i))
    S.sample("fx", dsp.riser(S.step_s * 16, 400, 10000, S.sr, 0.9), P(63), 0.9)

    # ═══ 64 final hit, hard cut + tail (Hope; Necrobloxians) ═══
    S.drum("fx", "crash", P(64), 1.0, O); S.drum("fx", "impact", P(64), 1.0, O); dr("kick", "kick", 64, 0, 1.0)
    S.note("sub", "sub_drop", P(64), 8, 35, 1.0)
    for tr in ("gtrL", "gtrR"):
        for nn in CH["Am"][1]: S.note(tr, "guitar_heavy", P(64), 6, nn + 2, 1.0, drive=9.0, mute=0.0)
    for nn in CH["Am"][2]: S.note("piano", "piano_grand", P(64), 10, nn + 2, 0.95)
    S.note("pianoL", "piano_grand", P(64), 10, 35, 0.95)
    for nn in CH["Am"][4]: S.note("pipe", "organ_church", P(64), 8, nn + 2, 0.9)
    for nn in CH["Am"][2]: S.note("brass", "brass_section", P(64), 5, nn + 2, 0.9)
    S.note("bell", "bell_church", P(64), 6, 95, 0.8, ring=1.2); S.note("bell", "bell_church", P(64), 6, 83, 0.8, ring=1.2)
    S.meta = dict(genre="ostfight", bpm=bpm, key="A minor -> B minor (bar 49)", seed=seed, bars=bars)
    S.rt60 = 2.2
    return S


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="ost.wav"); ap.add_argument("--seed", type=int, default=7); ap.add_argument("--bpm", type=float, default=174.0)
    ap.add_argument("--stems", default=None); ap.add_argument("--midi", action="store_true")
    ap.add_argument("--dynamics", type=float, default=0.5); ap.add_argument("--lufs", type=float, default=-14.0)
    a = ap.parse_args()
    S = build(a.seed, a.bpm)
    audio = S.mixdown(stems_dir=a.stems, master=False, reverb_rt60=S.rt60, dynamics=a.dynamics)
    audio = dsp.hp(audio, 28, S.sr, 2)
    audio = audio + 1.0 * dsp.hp(audio, 6500, S.sr, 2)
    audio = dsp.compress(audio, -10, 1.35, 0.03, 0.2, 0.0, S.sr)
    audio = np.tanh(audio * 1.05) / np.tanh(1.05)
    audio = dsp.limiter(audio, -1.0, sr=S.sr); audio = dsp.normalize(audio, -1.0)
    songmod.write_wav(a.out, audio, S.sr)
    try:
        import analyze as _A
        for _ in range(2):
            cur = _A.loudness(a.out)["lufs"]
            if cur is None or abs(cur - a.lufs) < 0.4: break
            audio = audio * (10 ** ((a.lufs - cur) / 20.0))
            if a.lufs > cur: audio = dsp.limiter(audio, -1.0, sr=S.sr)
            songmod.write_wav(a.out, audio, S.sr)
    except Exception as e:
        print("loudness step skipped:", e, file=sys.stderr)
    bm = S.beatmap(); bm["meta"] = S.meta
    json.dump(bm, open(a.out + ".beatmap.json", "w"), indent=1)
    if a.midi: songmod.write_midi(a.out + ".mid", S)
    print(json.dumps(dict(out=a.out, seconds=round(len(audio) / S.sr, 1), **S.meta)))


if __name__ == "__main__":
    main()

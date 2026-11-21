#!/usr/bin/env python3
"""huntfight.py -- the HUNTED OST composer, now driven by a RECIPE: everything you did not specify is varied, so two runs are never the same.

(v1.7: rebuilt after a listener called a render "tense, boss-fight action": no heroic lift, pitch-bent dark lead, cold tremolo strings, riffed guitars, accent-only low bells,
dark low piano, chopped Amen fills + reverse sweeps, reese under the sub, evolving motifs, A and C drops built differently.)

Eternal Hope Eternal Fight first (relentless breakbeat, booms, hard-cut endings), A Grave Soul second (crawl SFX, a vocal shout before the drop, a
clock section with chimes/tolls/heartbeat, tape-stop death), LMSY2K / ONEBOUNCE / Vigilante / Necrobloxians as low-priority signatures. Minor-only
harmony; no brass, organ or glockenspiel; no triumphant lift. Original music. Nobody has listened to the output: audition it.

  python3 huntfight.py --out hunt.wav                         # random recipe (different every run); writes hunt.wav.recipe.json
  python3 huntfight.py --out hunt.wav --seed 12               # reproduce a recipe from its seed
  python3 huntfight.py --out hunt.wav --lock key=D,bpm=176,ending=static_crash,drums=dnb      # lock what the user specified, vary the rest
  python3 huntfight.py --out hunt.wav --same-as other.wav.recipe.json                          # exact repeat
  python3 huntfight.py --out hunt.wav --apply feedback.json   # locks + mix changes produced by `af.py feedback` from a listener's notes
Lock names: key bpm cycle_a cycle_b drums lead bell bell_pattern piano pads sfx shout ending lift intro drop_a glitch clock drop_c breakdown
clock_on chime guitar_drive crawl_density boom_every. See TOOLS-GUIDE/HOW-TO-CREATE-MUSIC.md."""
import argparse, json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from forge import dsp, drums, song as songmod, horror_fx as HX, recipe as RC  # noqa: E402
from forge.song import Song  # noqa: E402

CH = {  # chord -> (bass, power chord, piano RH, piano LH, pad voicing), written in A minor, transposed by the recipe key
    "Am": (33, [45, 52, 57], [57, 60, 64], [45, 57], [57, 60, 64]),
    "Bb": (34, [46, 53, 58], [58, 62, 65], [46, 58], [58, 62, 65]),
    "F": (29, [41, 48, 53], [57, 60, 65], [41, 53], [57, 60, 65]),
    "Dm": (38, [50, 57, 62], [57, 62, 65], [38, 50], [57, 62, 65]),
    "E": (40, [40, 47, 52], [56, 59, 64], [40, 52], [56, 59, 64]),
    "Em": (40, [40, 47, 52], [59, 64, 67], [40, 52], [59, 64, 67]),
    "Bdim": (35, [47, 53, 59], [59, 62, 65], [47, 59], [59, 62, 65]),
}


MAJOR = {"Bb", "F", "E"}
RIFFS = {  # (step, kind, length, semitone offset of the power chord): syncopated / gallop / tritone / triplet; offsets 1 and 6 are the dissonant hits
    "syncopated": [(0, "o", 2, 0), (3, "m", 1, 0), (5, "m", 1, 0), (6, "m", 1, 1), (8, "o", 2, 0), (11, "m", 1, 0), (13, "m", 1, 6), (14, "m", 1, 0), (15, "m", 1, 0)],
    "gallop": [(0, "o", 1, 0), (1, "m", 1, 0), (2, "m", 1, 0), (4, "o", 1, 0), (5, "m", 1, 0), (6, "m", 1, 0), (8, "o", 1, 0), (9, "m", 1, 0), (10, "m", 1, 0), (12, "o", 1, 0), (13, "m", 1, 1), (14, "m", 1, 0)],
    "tritone": [(0, "o", 2, 0), (2, "m", 1, 0), (4, "o", 2, 6), (6, "m", 1, 6), (8, "o", 2, 0), (10, "m", 1, 0), (12, "o", 2, 1), (14, "m", 1, 1)],
    "triplet": [(0, "o", 2, 0), (2, "m", 1, 0), (3, "m", 1, 0), (4, "m", 1, 0), (6, "o", 1, 0), (7, "m", 1, 1), (8, "o", 2, 0), (10, "m", 1, 0), (11, "m", 1, 0), (12, "m", 1, 6), (14, "o", 1, 0), (15, "m", 1, 0)],
}


def hollow(ch, notes):
    """major triads read bright: play them hollow (root, fifth, octave: no third) so the harmony stays dark"""
    if ch in MAJOR:
        r = CH[ch][0] + 24
        return [r, r + 7, r + 12]
    return notes


def mutate(cell, rs):
    """small chromatic changes so a motif evolves instead of repeating verbatim"""
    c = [list(x) for x in cell]
    for i in rs.choice(range(1, len(c)), size=min(2, len(c) - 1), replace=False): c[i][2] += int(rs.choice([-1, 1]))
    return [tuple(x) for x in c]


def make_cell(kind, chord, rs):
    """a one-bar frantic lead cell (original, procedural): chromatic neighbours and falls around a chord tone"""
    rh = CH[chord][2]; b = int(rh[int(rs.randint(len(rh)))])
    while b < 72: b += 12
    while b > 83: b -= 12
    if kind == "descend":
        cum = [0, -1, -3, -4, -6, -8, -9, -11]
        return [(i, 1, b + c) for i, c in enumerate(cum)] + [(8, 4, b - 12 + 1), (12, 4, b - 13)]
    if kind == "stab":
        return [(0, 1, b), (3, 1, b), (6, 1, b + 12 if b + 12 < 96 else b), (8, 1, b), (10, 1, b - 1), (11, 1, b), (14, 1, b - 5), (15, 1, b - 6)]
    if kind == "tritone":
        return [(0, 1, b), (1, 1, b - 6), (2, 1, b - 1), (3, 1, b - 7), (4, 1, b), (5, 1, b - 6), (6, 1, b + 1), (7, 1, b - 5), (8, 3, b - 6), (11, 1, b - 7), (12, 4, b - 12)]
    if kind == "chromrun":
        return [(i, 1, b - 4 + i) for i in range(6)] + [(6 + i, 1, b + 1 - i) for i in range(4)] + [(10, 2, b - 3), (12, 4, b - 6)]
    if kind == "climb":
        return [(i, 1, b - 8 + i) for i in range(8)] + [(8, 4, b + 1), (12, 4, b)]
    return [(0, 1, b), (1, 1, b - 1), (2, 1, b), (3, 1, b - 5), (4, 1, b), (5, 1, b - 1), (6, 1, b), (7, 1, b - 5), (8, 3, b - 4), (11, 1, b - 5), (12, 4, b - 9)]


def build(R, ov=None):
    ov = ov or {}; mixd = ov.get("mix_db", {})
    st = R["structure"]; a, bA, g, c, d, e = (st[k] for k in ("intro", "drop_a", "glitch", "clock", "drop_c", "breakdown"))
    sA = a + 1; sG = sA + bA; sK = sG + g; sC = sK + c; sB = sC + d; sR = sB + e
    total = sR + (1 if R["ending"] == "hard_cut_tail" else 0)
    K = int(R["key"]); bpm = R["bpm"]; rs = np.random.RandomState(R["seed"] + 101)
    liftbar = sC + ((d // 2) // 4) * 4 if R["lift"] == "semitone" else 10 ** 6
    T = lambda bar: K + (1 if liftbar <= bar <= sR else 0)  # noqa: E731
    S = Song(bpm, total, seed=R["seed"] % 100000, tail=3.4 if R["ending"] == "hard_cut_tail" else 2.5)
    P = lambda bar, stp=0: (bar - 1) * 16 + stp  # noqa: E731
    seed = R["seed"]; J = R["mix_jitter_db"]; Kk, Oo = "industrial", "acoustic"

    def tr(name, db, **kw): S.track(name, gain_db=db + mixd.get(name, 0.0), **kw)
    tr("kick", 3.0); tr("snare", 2.0, reverb=0.08); tr("hat", -2.0, pan=0.2, hp=500); tr("ohat", -6.0, pan=-0.2, hp=500); tr("tom", -5.0)
    tr("fx", -3.0, reverb=0.08); tr("bass", -3.0, hp=30, sidechain=0.3, sc_release=0.14); tr("sub", -6.0, hp=28, sidechain=0.4); tr("boom", 0.0, hp=25)
    tr("gtrL", -5.0 + J["gtr"], pan=-0.6, hp=115, reverb=0.04); tr("gtrR", -5.0 + J["gtr"], pan=0.6, hp=115, reverb=0.04)
    tr("sqlead", -7.0 + J["lead"], reverb=0.1, delay=0.12, hp=300); tr("piano", -12.0 + J["piano"], pan=-0.1, reverb=0.1, hp=60); tr("pianoL", -13.0 + J["piano"], reverb=0.08, hp=30)
    tr("bell", -11.0 + J["bell"], pan=0.1, reverb=0.35, hp=100); tr("choir", -16.0 + J["pads"], reverb=0.35); tr("strings", -12.0 + J["pads"], pan=0.0, reverb=0.25); tr("pipe", -15.0, reverb=0.4); tr("brass", -12.0, reverb=0.2)
    tr("drone", -12.0, reverb=0.2, hp=30); tr("clock", -7.0, reverb=0.04, hp=500); tr("chime", -8.0, reverb=0.3); tr("heart", -9.0, hp=30)
    tr("sfx", -10.0 + J["sfx"]); tr("shout", -3.0, reverb=0.25)
    for n, s0, nb in [("intro", 1, a), ("drop", sA, bA), ("drop", sG, g), ("break", sK, c - 2), ("build", sC - 2, 2), ("drop", sC, d), ("break", sB, e), ("build", sR, 1)]:
        if nb > 0: S.mark(n, s0 - 1, nb)

    def chord_of(bar):
        cy = (R["cycle_a"], R["cycle_b"])[((bar - 1) // 4) % 2]; return cy[(bar - 1) % 4]

    def dr(track, name, bar, stp, vel=1.0): S.drum(track, name, P(bar, stp), vel, Kk if name == "kick" else Oo)

    def boom(bar, stp=0, vel=1.0):
        S.note("boom", "sub_drop", P(bar, stp), 4, 33 + T(bar), vel); S.note("boom", "sine_sub", P(bar, stp), 3, 45 + T(bar), vel * 0.5)
        if R["brass_low"]: S.note("brass", "brass_section", P(bar, stp), 3, CH[chord_of(bar)][0] + 12 + T(bar), 0.9)     # optional dark low brass stab (never a fanfare)
        dr("fx", "impact", bar, stp, 0.9); dr("kick", "kick", bar, stp, 1.0)

    def beat(b0, nb, style, skip=()):
        for stp, nm, v in drums.breakbeat(nb, style, np.random.RandomState(seed % 9973 + b0), 1.0, fill=True):
            if (b0 + stp // 16, stp % 16) in skip: continue
            t_ = {"kick": "kick", "snare": "snare", "hat": "hat", "ohat": "ohat", "tom": "tom", "ride": "hat", "clap": "snare"}.get(nm, "hat")
            S.drum(t_, nm, P(b0) + stp, v, Kk if nm == "kick" else Oo)

    def stutter(bar, s0, name="snare", n=8, v0=0.9, track="snare"):
        for k in range(n): S.drum(track, name, P(bar, s0) + k * 0.5, v0 * (1 - 0.06 * k), Oo)

    cells = {ch: make_cell(R["motif_kinds"][i % len(R["motif_kinds"])], ch, rs) for i, ch in enumerate(sorted(CH))}
    cells_c = {ch: make_cell(R["motif_kinds"][(i + 2) % len(R["motif_kinds"])], ch, np.random.RandomState(R["seed"] + 303)) for i, ch in enumerate(sorted(CH))}   # drop C gets its own motifs

    def fill(bar, kind=None):
        """bar-end fills (a listener missed dynamic fills and break stutters): a different one each time"""
        k = kind or ["roll", "stutter", "tomroll", "hatburst", "kickstutter"][int(np.random.RandomState(R["seed"] + bar * 7).randint(5))]
        if k == "roll":
            for stp in range(8, 16): S.drum("snare", "snare", P(bar, stp), 0.35 + 0.65 * (stp - 8) / 7.0, Oo)
        elif k == "stutter": stutter(bar, 12, "snare", 8, 0.85)
        elif k == "tomroll":
            for i, stp in enumerate(range(8, 16)): S.drum("tom", "tom", P(bar, stp), 0.6 + 0.04 * i, Oo)
        elif k == "hatburst":
            for j in range(10): S.drum("hat", "hat", P(bar, 12) + j * 0.4, 0.4 + 0.06 * j, Oo)
            dr("snare", "snare", bar, 14, 0.9)
        else: stutter(bar, 12, "kick", 8, 0.9, "kick")

    def rev_crash(bar):
        """reverse cymbal swell that lands on the downbeat of `bar` (transition riser)"""
        y = drums.hit("crash", Oo, 1.0); y = y if y.ndim == 1 else y.mean(1)
        y = y[::-1] * np.linspace(0.0, 1.0, len(y)) ** 1.5
        stp = P(bar) - len(y) / S.sr / S.step_s
        if stp > 0: S.sample("fx", np.stack([y, y], 1), stp, 0.7)

    def bass_bar(bar, ch):
        r = CH[ch][0] + T(bar)
        for stp, dd, off in [(0, 2, 0), (2, 1, 0), (3, 2, 12), (6, 2, 0), (8, 2, 0), (10, 2, 1 if ch in ("Am", "Dm", "Em") else 0), (12, 2, 0), (14, 1, 7), (15, 1, 0)]:
            S.note("bass", "saw_bass", P(bar, stp), dd * 0.9, r + 12 + off, 0.9, cutoff=800, drive=2.2)
        S.note("sub", "sine_sub", P(bar), 15, r, 0.9)
        if R["reese"]: S.note("bass", "reese", P(bar), 15, r + 12, 0.45)       # gritty distorted reese on top of the sub (it was buried under guitar fuzz)

    def guitars(bar, ch, vel=0.95):
        pw = [n + T(bar) for n in CH[ch][1]]; dv = R["guitar_drive"]
        riff = RIFFS[R["riff_a"] if bar < sC else R["riff_c"]]                   # drop A and drop C get different riffs
        for stp, kind, dd, so in riff:
            for t_, off in (("gtrL", 0.0), ("gtrR", 0.16)):
                for k, nn in enumerate(pw):
                    S.note(t_, "guitar_heavy", P(bar, stp) + off, max(dd * 0.95, 0.5), nn + so, vel * (1.0 if kind == 'o' else 0.88) * (0.9 if k else 1.0),
                           drive=dv if kind == 'm' else dv * 0.75, mute=0.85 if kind == 'm' else 0.1)

    def piano_stabs(bar, ch, vel=0.8):
        rh = [n + T(bar) for n in hollow(ch, CH[ch][2])]; dark = R["piano"] == "piano_dark"
        for stp, dd in (((0, 2), (10, 2)) if dark else ((0, 2), (6, 2), (10, 2), (14, 1))):
            for nn in rh: S.note("piano", R["piano"], P(bar, stp), dd, nn + (0 if dark else 12), vel * (0.95 if stp else 1.0))
        S.note("pianoL", "piano_grand", P(bar), 6, CH[ch][3][0] + T(bar), vel)

    def sqlead(bar, ch, vel=0.85, octave=0):
        base = (cells_c if bar >= sC else cells)[ch]
        cell = mutate(base, np.random.RandomState(R["seed"] + bar // 4)) if (bar // 4) % 2 else base     # every other 4-bar cycle the motif shifts a little
        brs = np.random.RandomState(R["seed"] + bar)
        for stp, dd, m in cell:
            kw = {"bend": float(brs.choice([1, -1, 2, 0, -2, 1]))} if R["lead"] == "bend_lead" else {}
            S.note("sqlead", R["lead"], P(bar, stp), dd * 0.9, m + T(bar) + octave, vel * (1.0 if stp % 4 == 0 else 0.85), **kw)

    def doom_bell(bar, ch, vel=0.9):
        stp = 0
        if R["bell"] in ("bell_tubular", "both"): S.note("bell", "bell_tubular", P(bar, stp), 8, CH[ch][0] + 12 + T(bar), vel * 0.8)
        if R["bell"] in ("bell_church", "both"): S.note("bell", "bell_church", P(bar, stp), 8, CH[ch][0] + 12 + T(bar), vel, ring=1.4)

    booms_at = set([sA, sC, liftbar if R["lift"] == "semitone" else -1, sA + R["boom_every"], sC + R["boom_every"], sC + 2 * R["boom_every"], sC + 3 * R["boom_every"], sK - 1] + list(range(sB, sR)))

    def bell_on(bar, rel):      # low church bell on terror accents only: section starts and the bar before a boom (+ every 8 bars for "accents+off")
        return rel == 0 or (bar + 1) in booms_at or (R["bell_pattern"] == "accents+off" and rel % 8 == 4)

    def pads(bar, ch, vel=0.8, d_=16):
        if R["pads"] in ("choir", "both"):
            for nn in hollow(ch, CH[ch][4]): S.note("choir", "choir", P(bar), d_, nn + T(bar), vel)
        if R["pads"] in ("trem_strings", "both", "strings"):
            root = CH[ch][0] + 24 + T(bar)                                       # cold tremolo strings: a root with a rubbing minor second, plus a bare fifth
            S.note("strings", "string_tremolo", P(bar), d_ - 0.5, root, vel, cluster=0.6); S.note("strings", "string_tremolo", P(bar), d_ - 0.5, root + 7, vel * 0.7, cluster=0.0)

    def shout(bar, stp, f0, seed_, lvl=1.0): S.sample("shout", HX.shout_ha(S.sr, f0, 0.5, seed_), P(bar, stp), lvl)

    # ═══ intro ═══
    S.drum("fx", "impact", 0, 1.0, Oo); S.note("sub", "sub_drop", 0, 12, 33 + K, 1.0)
    if R["sfx"] in ("crawl", "both"): S.sample("sfx", HX.crawl((a - 1) * 16 * S.step_s, S.sr, density=R["crawl_density"], seed=seed % 97), P(1), 1.0)
    if R["sfx"] in ("static", "both"): S.sample("sfx", HX.static(2.5, S.sr, seed=seed % 89), P(max(2, a // 2)), 0.6)
    S.note("drone", "drone", P(1), 16 * a - 2, 33 + K, 0.7)
    for bar in range(1, a + 1):
        ch = chord_of(bar)
        for stp in range(0, 16, 2): dr("hat", "hat", bar, stp, 0.16 + 0.025 * min(bar, 8))
        if bar >= 3:
            for stp in (0, 4, 8, 12): dr("kick", "kick", bar, stp, 0.5)
            dr("snare", "snare", bar, 8, 0.5)
        arp = [n + 24 + T(bar) for n in CH[ch][2]]
        for i in range(16): S.note("sqlead", R["lead"], P(bar, i), 0.9, arp[[0, 1, 2, 1][i % 4]] + (12 if i % 8 == 7 else 0), 0.18 + 0.03 * min(bar, 8), **({"bend": 0.0} if R["lead"] == "bend_lead" else {}))
        for stp, off in ((0, 0), (3, 7), (6, 0), (10, 7), (14, 12)): S.note("piano", R["piano"], P(bar, stp), 1.0, CH[ch][2][0] + (0 if R["piano"] == "piano_dark" else 12) + off + T(bar), 0.45)   # low and cold, not a bright music box
        S.note("sub", "sine_sub", P(bar), 14, CH[ch][0] + T(bar), 0.55)
        if bar >= a - 1: doom_bell(bar, ch, 0.5)
    for stp in range(0, 12): S.drum("snare", "snare", P(a, stp), 0.2 + 0.6 * stp / 11.0, Oo)
    S.sample("fx", dsp.riser(2 * 16 * S.step_s, 250, 7500, S.sr, 0.7), P(a - 1), 0.8)
    if R["shout"] != "none": shout(a, 12, 165, 1)
    if R["shout"] == "ha2": shout(a, 14, 120, 6, 0.7)

    # ═══ drop A ═══
    S.drum("fx", "crash", P(sA), 1.0, Oo); S.drum("fx", "crash", P(sA), 1.0, Oo); boom(sA); S.note("boom", "sub_drop", P(sA), 6, 33 + K, 1.0)
    beat(sA, bA, R["drums_a"])
    for bar in range(sA, sG):
        ch = chord_of(bar); bass_bar(bar, ch); guitars(bar, ch); piano_stabs(bar, ch)
        if bar >= sA + 2: sqlead(bar, ch, 0.8)
        if bell_on(bar, bar - sA): doom_bell(bar, ch)
        if bar >= sA + 8: pads(bar, ch, 0.7)
        if (bar - sA) % 4 == 3 and bar != sG - 1: fill(bar)
    if sA + R["boom_every"] < sG - 1: boom(sA + R["boom_every"], 0, 0.8)
    for b_ in (sA, sK, sC) + ((liftbar,) if R["lift"] == "semitone" else ()) + (sB,): rev_crash(b_)
    stutter(sG - 1, 12, "snare", 8, 0.8)

    # ═══ glitch drop (LMSY2K interruption + vocal chops) ═══
    if g:
        beat(sG, g, "amen", skip={(sK - 2, 12), (sK - 2, 13), (sK - 2, 14), (sK - 2, 15)})
        for bar in range(sG, sK):
            ch = chord_of(bar); bass_bar(bar, ch); guitars(bar, ch, 1.0); sqlead(bar, ch, 0.9, 12 if bar >= sK - 2 else 0)
            if bar != sK - 2: piano_stabs(bar, ch)
        if R["shout"] != "none":
            shout(sK - 2, 12, 140, 2, 0.9); shout(sK - 1, 6, 190, 4, 0.6)
        stutter(sK - 1, 12, "kick", 8, 0.9, "kick"); boom(sK - 1, 0, 0.9)

    # ═══ clock / dread section ═══
    if R["sfx"] in ("crawl", "both"): S.sample("sfx", HX.crawl(c * 16 * S.step_s, S.sr, density=R["crawl_density"] * 0.65, seed=seed % 83, level=0.45), P(sK), 1.0)
    else: S.sample("sfx", HX.static(c * 16 * S.step_s * 0.6, S.sr, seed=seed % 83, level=0.35), P(sK), 0.7)
    S.note("drone", "drone", P(sK), 16 * c, 33 + K, 1.0)
    chime_bars = [sK + 2 * i for i in range(3 if c == 8 else 5)]; chime_n = [2, 3, 4, 4, 4]
    for k, bar in enumerate(range(sK, sC)):
        ch = chord_of(bar); left = sC - bar
        pads(bar, ch, 0.55 + 0.04 * min(k, 8), 16); S.note("sub", "sine_sub", P(bar), 15, CH[ch][0] + T(bar), 0.7)
        if R["organ_low"]: S.note("pipe", "organ_church", P(bar), 15.5, CH[ch][0] + 12 + T(bar), 0.8)      # optional low cathedral organ sustain for gothic dread
        if k < c - 2: S.note("piano", "piano_grand", P(bar, 4), 10, CH[ch][2][0] + (12 if k % 2 else 0) + T(bar), 0.55)
        if R["clock_on"]:
            for stp in range(0, 16, 4 if left > 2 else 2): S.note("clock", "clock_tick", P(bar, stp), 0.5, 76 if (stp // 4) % 2 == 0 else 70, 0.95 if (stp // 4) % 2 == 0 else 0.75)
            if bar in chime_bars:
                n = chime_n[chime_bars.index(bar)]
                for j, off in enumerate(R["chime"][:n]): S.note("chime", "clock_bell", P(bar) + j * 3, 5, 76 + K + off, 0.85)
            if left <= 3:
                S.note("chime", "bell_church", P(bar), 10, 45 + K, 1.0, ring=1.8); S.note("boom", "sine_sub", P(bar), 6, 33 + K, 0.75)
        if left <= 5:
            for stp in ((0, 8) if left == 5 else (0, 4, 8, 12) if left in (4, 3) else tuple(range(0, 16, 2))): S.note("heart", "heartbeat", P(bar, stp), 1, 36, 0.9)
        if left <= 2:
            for stp in range(0, 16, 2 if left == 2 else 1): S.drum("snare", "snare", P(bar, stp), 0.25 + 0.75 * ((2 - left) * 16 + stp) / 32.0, Oo)
    S.sample("fx", dsp.riser(2 * 16 * S.step_s, 300, 9000, S.sr, 0.85), P(sC - 2), 0.9)

    # ═══ drop C ═══
    S.drum("fx", "crash", P(sC), 1.0, Oo); boom(sC)
    b2 = sC + R["boom_every"]; dip = b2 - 1
    beat(sC, dip - sC, R["drums_c"])
    for stp, nm, v in [(0, "kick", 1.0), (8, "hat", 0.5), (12, "hat", 0.5)]: S.drum("kick" if nm == "kick" else "hat", nm, P(dip) + stp, v, Kk if nm == "kick" else Oo)
    beat(b2, sB - b2, R["drums_c"])
    for bar in range(sC, sB):
        ch = chord_of(bar)
        if bar != dip: bass_bar(bar, ch); guitars(bar, ch); piano_stabs(bar, ch)
        else: S.note("sub", "sine_sub", P(bar), 14, CH[ch][0] + T(bar), 0.9)
        sqlead(bar, ch, 0.9, 12 if bar >= sC + 4 else 0); pads(bar, ch, 0.85)
        if bell_on(bar, bar - sC): doom_bell(bar, ch)
        if (bar - sC) % 4 == 3 and bar < sB - 4: fill(bar)
    for k in range(2, 4):
        if sC + k * R["boom_every"] < sB - 2: boom(sC + k * R["boom_every"])
    boom(b2)
    if R["lift"] == "semitone": S.drum("fx", "crash", P(liftbar), 0.9, Oo)
    scale = [57, 59, 60, 62, 64, 65, 68, 69]
    for bar in range(sB - 4, sB):
        for i in range(16):
            m = scale[(i if bar % 2 else 15 - i) % 8] + 12 * (1 + (i // 8)) + 1 + T(bar)
            S.note("sqlead", R["lead"], P(bar, i), 0.9, m, 0.8); S.note("piano", R["piano"], P(bar, i), 0.9, m - 12, 0.55)

    # ═══ cold-piano breakdown (LMSY2K) ═══
    S.sample("sfx", HX.static(e * 1.35, S.sr, seed=seed % 79), P(sB), 0.8)
    for k in range(e):
        bar = sB + k; ch = ("Am", "E")[k % 2]; r = CH[ch][0] + T(bar)
        S.note("pianoL", "piano_dark", P(bar), 14, r + 12, 0.9)
        for i, stp in enumerate((0, 3, 6, 10)): S.note("piano", "piano_dark", P(bar, stp), 4, hollow(ch, CH[ch][2])[i % 3] + T(bar), 0.7)
        S.note("piano", "piano_dark", P(bar, 8), 6, r + 25, 0.55)                  # a rubbing minor second: no calm, bittersweet pause
        S.note("strings", "string_tremolo", P(bar), 15, r + 24, 0.7, cluster=0.8)
        if R["organ_low"]: S.note("pipe", "organ_church", P(bar), 15.5, r + 12, 0.8)
        S.note("bell", "bell_church", P(bar, 8), 8, 45 + T(bar), 0.9, ring=1.5); boom(bar, 0, 1.0)
    # ═══ roll ═══
    for stp in range(16): S.drum("snare", "snare", P(sR, stp), 0.35 + 0.65 * stp / 15.0, Oo)
    S.sample("fx", dsp.riser(S.step_s * 16, 400, 10000, S.sr, 0.9), P(sR), 0.9)
    if R["ending"] == "hard_cut_tail":
        fb = sR + 1
        S.drum("fx", "crash", P(fb), 1.0, Oo); S.drum("fx", "impact", P(fb), 1.0, Oo); dr("kick", "kick", fb, 0, 1.0); S.note("sub", "sub_drop", P(fb), 8, 35 + K, 1.0)
        for t_ in ("gtrL", "gtrR"):
            for nn in CH["Am"][1]: S.note(t_, "guitar_heavy", P(fb), 6, nn + T(sR), 1.0, drive=R["guitar_drive"] * 0.7, mute=0.0)
        for nn in CH["Am"][2]: S.note("piano", "piano_grand", P(fb), 10, nn + 12 + T(sR), 0.95)
    S.meta = dict(genre="huntfight", bpm=bpm, key_offset_from_A=K, bars=total, structure_bars=dict(sA=sA, sG=sG, sK=sK, sC=sC, sB=sB, sR=sR), ending=R["ending"])
    S.sR = sR
    return S


def finish(S, audio, R):
    bar_s = 16 * S.step_s; sr = S.sr; end = R["ending"]
    st = lambda x: x if x.ndim == 2 else np.stack([x, x], 1)  # noqa: E731
    audio = st(audio)
    if end == "hard_cut_tail":
        return audio
    audio = audio[: int((S.sR * bar_s + 0.1) * sr)]
    if end == "tape_stop_hit":
        audio = HX.tape_stop(audio, sr, (S.sR - 1) * bar_s + 8 * S.step_s, 1.4)
        n_pad = int(1.1 * sr); tt = np.arange(n_pad) / sr
        rum = (0.05 * np.sin(2 * np.pi * 33 * tt) + 0.02 * np.sin(2 * np.pi * 49.5 * tt)) * np.exp(-tt / 0.5)
        hiss = dsp.lp(np.random.RandomState(5).uniform(-1, 1, n_pad), 900, sr, 2) * 0.012 * np.exp(-tt / 0.35)
        pad = np.stack([rum + hiss, rum + np.roll(hiss, 40)], axis=1)
        return np.concatenate([audio, pad, HX.blunt_hit(sr) * 0.95], axis=0)
    if end == "static_crash":                                                   # system-failure cutoff (LMSY2K): the last slice stutters, then static, then dead
        sl = audio[-int(0.16 * sr):]; rep = np.concatenate([sl * (0.85 ** i) for i in range(5)], axis=0)
        stat = HX.static(0.55, sr, seed=7, level=0.6) * np.linspace(1.0, 0.7, int(0.55 * sr))[:, None]
        return np.concatenate([audio[: -int(0.16 * sr)], rep, stat], axis=0)
    # fade_dark: the mix sinks into a low rumble and dies
    n = int(3.2 * sr); ramp = np.linspace(1.0, 0.0, min(n, len(audio)))[:, None] ** 1.5
    audio = audio.copy(); audio[-len(ramp):] *= ramp
    tt = np.arange(n) / sr; rum = 0.04 * np.sin(2 * np.pi * 33 * tt) * np.exp(-tt / 1.4)
    return np.concatenate([audio, np.stack([rum, rum], 1)], axis=0)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="hunt.wav"); ap.add_argument("--seed", type=int, default=None, help="omit for a fresh random recipe")
    ap.add_argument("--lock", default="", help="choices the user specified, e.g. key=D,bpm=176,ending=static_crash")
    ap.add_argument("--same-as", default=None, help="a *.recipe.json to repeat exactly"); ap.add_argument("--apply", default=None, help="overrides json from `af.py feedback`")
    ap.add_argument("--no-history", action="store_true"); ap.add_argument("--stems", default=None); ap.add_argument("--midi", action="store_true")
    ap.add_argument("--dynamics", type=float, default=0.5); ap.add_argument("--lufs", type=float, default=-14.0)
    a = ap.parse_args()
    ov = json.load(open(a.apply)) if a.apply else {}
    locks = dict(RC.parse_locks(a.lock)); locks.update(ov.get("locks", {}))
    R = RC.upgrade_recipe(json.load(open(a.same_as))) if a.same_as else RC.make_recipe("hunted", a.seed, locks, avoid_history=not a.no_history)
    R.update(ov.get("recipe", {}))                     # recipe-level changes from `af.py feedback` (e.g. lift=none, lead=bend_lead)
    if ov.get("bpm_delta") and not a.same_as and "bpm" not in locks: R["bpm"] = float(R["bpm"] + ov["bpm_delta"])
    S = build(R, ov)
    audio = S.mixdown(stems_dir=a.stems, master=False, reverb_rt60=1.6, dynamics=a.dynamics)
    audio = dsp.hp(audio, 28, S.sr, 2); audio = audio + 1.0 * dsp.hp(audio, 6500, S.sr, 2)
    audio = dsp.compress(audio, -10, 1.35, 0.03, 0.2, 0.0, S.sr); audio = np.tanh(audio * 1.05) / np.tanh(1.05)
    audio = dsp.limiter(audio, -1.0, sr=S.sr); audio = dsp.normalize(audio, -1.0)
    audio = finish(S, audio, R); audio = audio / max(1.0, np.abs(audio).max() * 1.02)
    songmod.write_wav(a.out, audio, S.sr)
    try:
        import analyze as _A
        for _ in range(2):
            cur = _A.loudness(a.out)["lufs"]
            if cur is None or abs(cur - a.lufs) < 0.4: break
            audio = audio * (10 ** ((a.lufs - cur) / 20.0)); audio = audio / max(1.0, np.abs(audio).max() * 1.02); songmod.write_wav(a.out, audio, S.sr)
    except Exception as ex:
        print("loudness step skipped:", ex, file=sys.stderr)
    json.dump(R, open(a.out + ".recipe.json", "w"), indent=1)
    bm = S.beatmap(); bm["meta"] = S.meta; json.dump(bm, open(a.out + ".beatmap.json", "w"), indent=1)
    if a.midi: songmod.write_midi(a.out + ".mid", S)
    if not a.same_as and not a.no_history: RC.record(R)
    names = ["A", "Bb", "B", "C", "C#", "D", "Eb", "E", "F", "F#", "G", "G#"]
    print(json.dumps(dict(out=a.out, seconds=round(len(audio) / S.sr, 1), seed=R["seed"], key=names[R["key"] % 12] + " minor", bpm=R["bpm"], drums=[R["drums_a"], R["drums_c"]],
                          ending=R["ending"], lift=R["lift"], structure=R["structure"], locked=R.get("locked", []))))


if __name__ == "__main__":
    main()

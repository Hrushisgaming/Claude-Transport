"""genres.py -- data-driven genre specs + the arranger.

A spec is a plain dict, so a profile from analyze.py (or the user, or the agent) can tweak any part of it.
Rhythm strings are 16 chars = one bar of 16th notes:  X accent  x normal  o ghost  . rest  - sustain
Bass rhythm chars: x root  o octave-up  f fifth  t third  b flat-7  e octave-down  w walking tone  m muted root
"""
import copy
import numpy as np
from . import theory, drums, dsp
from .song import Song

VEL = {"X": 1.0, "x": 0.8, "o": 0.42, "m": 0.8}

GENRES = {
    "chiptune": dict(
        bpm=(128, 158), scales=["major", "pent_major", "mixolydian"], kit="chip", swing=0,
        drums=dict(kick="x.......x.......", snare="....x.......x...", hat="x.x.x.x.x.x.x.x."),
        bass=dict(inst="chip_tri", oct=2, rhythm="x.x.o.x.x.x.o.xf"),
        arp=dict(inst="lead_square", oct=4, rate=1, pattern="updown", kind="triad", kw=dict(duty=0.25)),
        lead=dict(inst="lead_square", oct=5, density=0.6, contour="arch", kw=dict(duty=0.5)),
        chords=dict(inst="lead_square", oct=3, rhythm="x-x-x-x-x-x-x-x-", kind="triad", kw=dict(duty=0.125)),
        mix=dict(lead=dict(crush=6, gain_db=-8), arp=dict(gain_db=-13, crush=6), chords=dict(gain_db=-15, crush=5),
                 hat=dict(gain_db=-15), kick=dict(gain_db=-2), reverb=0.0),
        layers=dict(intro=["arp", "hat", "bass"], build=["arp", "kick", "hat", "bass", "snare_roll", "chords"],
                    drop=["kick", "snare", "hat", "bass", "arp", "lead", "chords"], break_=["arp", "chords", "lead"],
                    outro=["kick", "hat", "bass", "arp"]),
    ),
    "synthwave": dict(
        bpm=(96, 118), scales=["minor", "dorian"], kit="808", swing=0, chord_len=1, fills=True, impact=True,
        drums=dict(kick="x...x...x...x...", snare="....x.......x...", clap="....x.......x...",
                   hat="x.x.x.x.x.x.x.x.", ohat="..x...x...x...x."),
        bass=dict(inst="saw_bass", oct=2, rhythm="xxoxxxoxxxoxxxox"),
        chords=dict(inst="pad", oct=3, rhythm="x---------------", kind="seventh"),
        arp=dict(inst="pluck", oct=4, rate=1, pattern="updown", kind="seventh"),
        lead=dict(inst="lead_saw", oct=5, density=0.5, contour="arch"),
        mix=dict(kick=dict(gain_db=-1), bass=dict(sidechain=0.5, lp=2500), chords=dict(sidechain=0.55, reverb=0.4, widen=0.014),
                 lead=dict(reverb=0.3, delay=0.25, chorus=0.4), arp=dict(reverb=0.2, delay=0.3), snare=dict(reverb=0.35)),
    ),
    "lofi": dict(
        bpm=(70, 88), scales=["dorian", "minor", "mixolydian"], kit="acoustic", swing=0.3, chord_len=1, vinyl=True,
        drums=dict(kick="x.....o..x.o....", snare="....x.......x...", hat="x.xoxoxox.xoxoxo"),
        bass=dict(inst="sine_sub", oct=2, rhythm="x-----..x-f-----"),
        chords=dict(inst="ep", oct=3, rhythm="x-----..x-------", kind="seventh"),
        lead=dict(inst="piano", oct=5, density=0.32, contour="arch", rest=0.4),
        layers=dict(intro=["chords", "hat", "vinyl"], drop=["kick", "snare", "hat", "bass", "chords", "lead", "vinyl"],
                    break_=["chords", "bass", "vinyl"], outro=["chords", "kick", "vinyl"],
                    build=["chords", "hat", "kick", "vinyl"]),
        plan=[("intro", .1), ("drop", .3), ("break_", .12), ("drop", .3), ("outro", .18)],
        mix=dict(hat=dict(lp=9000, gain_db=-14), chords=dict(lp=4500, reverb=0.3, chorus=0.4, gain_db=-8), lead=dict(reverb=0.3, lp=6000),
                 kick=dict(lp=4000), snare=dict(lp=6000, reverb=0.2), bass=dict(gain_db=-3)),
    ),
    "boombap": dict(
        bpm=(82, 96), scales=["minor", "dorian", "phrygian"], kit="acoustic", swing=0.22, chord_len=2, vinyl=True,
        drums=dict(kick="x.....x..x......", snare="....X.......X...", hat="x.x.x.x.x.x.x.xo"),
        bass=dict(inst="sine_sub", oct=2, rhythm="x.....x..x......"),
        chords=dict(inst="ep", oct=3, rhythm="x-------x-------", kind="seventh"),
        lead=dict(inst="music_box", oct=5, density=0.3, contour="fall", rest=0.4),
        mix=dict(chords=dict(lp=4000, reverb=0.25), kick=dict(drive=1.5), snare=dict(reverb=0.15)),
    ),
    "house": dict(
        bpm=(120, 126), scales=["minor", "dorian"], kit="808", swing=0.06, chord_len=1, impact=True,
        drums=dict(kick="x...x...x...x...", clap="....x.......x...", hat="..x...x...x...x.", ohat="..x...x...x...x.",
                   perc="o..o..o..o..o.o."),
        bass=dict(inst="saw_bass", oct=2, rhythm="..x...x...x...x."),
        chords=dict(inst="piano_m1", oct=3, rhythm="..x....x..x....x", kind="seventh"),
        organ=dict(inst="organ", oct=3, rhythm="..x....x..x....x", kind="triad"),
        lead=dict(inst="pluck", oct=5, density=0.45, contour="arch"),
        mix=dict(bass=dict(sidechain=0.6, lp=1800), chords=dict(sidechain=0.5, reverb=0.25, delay=0.2),
                 ohat=dict(gain_db=-13), lead=dict(delay=0.3, reverb=0.2)),
    ),
    "techno": dict(
        bpm=(128, 140), scales=["minor", "phrygian"], kit="industrial", swing=0, chord_len=2, fills=True,
        drums=dict(kick="x...x...x...x...", hat="..x...x...x...x.", ohat="..x...x...x...x.", perc="..o..o....o.o...",
                   clap="....x.......x..."),
        bass=dict(inst="acid_303", oct=2, rhythm="xxxxxxxxxxxxxxxx"),
        chords=dict(inst="drone", oct=2, rhythm="x---------------", kind="power"),
        stab=dict(inst="stab", oct=4, rhythm="..x....x..x...x.", kind="triad"),
        lead=dict(inst="pluck", oct=5, density=0.3, contour="flat", leap=0.4),
        layers=dict(intro=["kick", "hat", "perc"], build=["kick", "hat", "perc", "bass", "snare_roll", "riser"],
                    drop=["kick", "hat", "ohat", "perc", "clap", "bass", "chords", "stab", "lead"],
                    break_=["chords", "perc", "stab"], outro=["kick", "hat", "perc"]),
        mix=dict(bass=dict(sidechain=0.55), chords=dict(reverb=0.35, gain_db=-14), stab=dict(reverb=0.3, delay=0.3),
                 kick=dict(drive=1.5)),
    ),
    "dnb": dict(
        bpm=(170, 176), scales=["minor", "phrygian", "dorian"], kit="acoustic", swing=0, chord_len=2, fills=True, impact=True,
        breakbeat="dnb",
        drums=dict(kick="x.........x.....", snare="....X.......X...", hat="x.x.x.x.x.x.x.xo", ohat="......o.......o."),
        bass=dict(inst="reese", oct=1, rhythm="x.......x.x....."),
        chords=dict(inst="strings", oct=3, rhythm="x---------------", kind="seventh"),
        lead=dict(inst="pluck", oct=5, density=0.4, contour="arch"),
        mix=dict(bass=dict(sidechain=0.35, gain_db=-2), chords=dict(reverb=0.4, widen=0.012), lead=dict(reverb=0.25, delay=0.3)),
    ),
    "trap": dict(
        bpm=(136, 150), scales=["minor", "phrygian", "harmonic_minor"], kit="808", swing=0, chord_len=2, fills=True,
        drums=dict(kick="x.....x...x.....", snare="........X.......", clap="........x.......",
                   hat="xoxoxoxoxoxoxxxx", ohat="......o.......o."),
        bass=dict(inst="sub_drop", oct=1, rhythm="x-----x---x-----"),
        chords=dict(inst="bell", oct=4, rhythm="x---------------", kind="triad"),
        lead=dict(inst="music_box", oct=5, density=0.4, contour="fall", leap=0.3),
        mix=dict(bass=dict(gain_db=0, drive=1.3), hat=dict(gain_db=-12), chords=dict(reverb=0.35, gain_db=-12), lead=dict(reverb=0.3, delay=0.25)),
    ),
    "edm": dict(
        bpm=(126, 150), scales=["minor", "major"], kit="808", swing=0, chord_len=1, impact=True, fills=True,
        drums=dict(kick="x...x...x...x...", clap="....x.......x...", hat="..x...x...x...x.", ohat="..x...x...x...x.", perc="o..o..o..o..o.o."),
        bass=dict(inst="sine_sub", oct=2, rhythm="..x...x...x...x."),
        chords=dict(inst="stab", oct=3, rhythm="x..x..x..x..x...", kind="triad"),
        lead=dict(inst="lead_saw", oct=5, density=0.6, contour="arch"),
        strings=dict(inst="pad", oct=3, rhythm="x---------------", kind="triad"),
        layers=dict(intro=["hat", "strings"], build=["kick", "hat", "snare_roll", "riser", "strings", "chords"],
                    drop=["kick", "clap", "hat", "ohat", "bass", "chords", "lead", "strings", "perc", "impact"],
                    break_=["strings", "lead"], outro=["kick", "hat", "strings"]),
        mix=dict(bass=dict(sidechain=0.7), chords=dict(sidechain=0.65, reverb=0.3, widen=0.015), strings=dict(sidechain=0.6, reverb=0.4),
                 lead=dict(reverb=0.3, delay=0.25, chorus=0.4)),
    ),
    "dubstep": dict(
        bpm=(138, 146), scales=["minor", "phrygian"], kit="industrial", swing=0, chord_len=2, impact=True, fills=True,
        drums=dict(kick="x.......x.......", snare="........X.......", hat="x.x.x.x.x.x.x.xo", clap="........x......."),
        bass=dict(inst="wobble", oct=1, rhythm="x---------------", lfo_per_beat=2),
        chords=dict(inst="pad", oct=3, rhythm="x---------------", kind="triad"),
        lead=dict(inst="lead_saw", oct=5, density=0.4, contour="fall"),
        mix=dict(bass=dict(gain_db=-2), chords=dict(reverb=0.4, sidechain=0.4), lead=dict(reverb=0.3)),
    ),
    "horror_chase": dict(  # survival-horror / "chase theme" energy: relentless pulse, distorted guitars, brass stabs, risers
        bpm=(150, 176), scales=["phrygian", "harmonic_minor", "minor"], kit="industrial", swing=0, chord_len=1, impact=True, fills=True,
        breakbeat="horror",
        plan=[("intro", .1), ("build", .1), ("chase", .3), ("break_", .1), ("chase", .3), ("outro", .1)],
        drums=dict(kick="x..xx...x..xx.x.", snare="....X.......X...", hat="x.x.x.x.x.x.x.x.", ohat="..o...o...o...o.",
                   metal="......o.......o.o.", tom="..............oo"),
        bass=dict(inst="saw_bass", oct=1, rhythm="xxmxxmxxmxxmxxoo", kw=dict(cutoff=900, drive=3.2)),
        guitar=dict(inst="guitar", oct=2, rhythm="x.mx.mx.x.mx.m.m", kind="power"),
        chords=dict(inst="strings", oct=3, rhythm="x---------------", kind="triad"),
        stab=dict(inst="brass", oct=3, rhythm="x..x..x...x.....", kind="power"),
        lead=dict(inst="lead_saw", oct=5, density=0.42, contour="arch", leap=0.35, kw=dict(detune=0.2)),
        choir=dict(inst="choir", oct=4, rhythm="x---------------", kind="triad"),
        organ=dict(inst="organ_rock", oct=3, rhythm="x---------------", kind="triad"),
        drone=dict(inst="drone", oct=1),
        layers=dict(intro=["drone", "metal", "hat", "strings"], build=["drone", "kick", "hat", "snare_roll", "riser", "strings", "bass"],
                    chase=["kick", "snare", "hat", "ohat", "metal", "tom", "bass", "guitar", "stab", "lead", "strings", "organ", "impact"],
                    break_=["drone", "choir", "strings", "metal"], outro=["drone", "kick", "metal", "strings"]),
        mix=dict(kick=dict(gain_db=-1, drive=1.5), bass=dict(drive=1.3, gain_db=-2, sidechain=0.25), guitar=dict(gain_db=-8, widen=0.012),
                 stab=dict(gain_db=-10, reverb=0.25), lead=dict(reverb=0.3, delay=0.2, gain_db=-8), strings=dict(reverb=0.3, gain_db=-12),
                 choir=dict(reverb=0.5, gain_db=-12), drone=dict(reverb=0.3, gain_db=-16), metal=dict(reverb=0.3, gain_db=-12),
                 organ=dict(reverb=0.3, gain_db=-14)),
    ),
    "dark_ambient": dict(
        bpm=(56, 76), scales=["phrygian", "minor", "locrian"], kit="industrial", swing=0, chord_len=4, impact=True,
        drums=dict(), plan=[("intro", .25), ("build", .15), ("main", .35), ("break_", .1), ("outro", .15)],
        chords=dict(inst="pad", oct=2, rhythm="x---------------", kind="sus2"),
        drone=dict(inst="drone", oct=1), choir=dict(inst="choir", oct=3, rhythm="x---------------", kind="triad", kw=dict(vowel="o")),
        lead=dict(inst="bell", oct=5, density=0.08, contour="fall", rest=0.6),
        layers=dict(intro=["drone"], build=["drone", "chords", "riser"], main=["drone", "chords", "choir", "lead", "impact"],
                    break_=["drone", "lead"], outro=["drone", "chords"]),
        mix=dict(drone=dict(gain_db=-10, reverb=0.35), chords=dict(reverb=0.5, gain_db=-12), choir=dict(reverb=0.6, gain_db=-12),
                 lead=dict(reverb=0.7, delay=0.4, gain_db=-12), reverb_rt60=4.5),
    ),
    "cinematic": dict(
        bpm=(72, 100), scales=["minor", "harmonic_minor", "major"], kit="acoustic", swing=0, chord_len=1, impact=True, fills=True,
        plan=[("intro", .15), ("build", .2), ("climax", .35), ("break_", .12), ("outro", .18)],
        drums=dict(tom="x..x..x.x..x..x.", metal="x...............", ride=""),
        chords=dict(inst="strings", oct=3, rhythm="x---------------", kind="triad"),
        bass=dict(inst="sub_drop", oct=1, rhythm="x---------------"),
        stab=dict(inst="brass", oct=3, rhythm="x-------x-------", kind="power"),
        arp=dict(inst="piano", oct=4, rate=2, pattern="updown", kind="triad"),
        lead=dict(inst="strings", oct=5, density=0.25, contour="arch", rest=0.3),
        choir=dict(inst="choir", oct=4, rhythm="x---------------", kind="triad"),
        layers=dict(intro=["arp", "chords"], build=["arp", "chords", "bass", "tom", "riser", "strings"],
                    climax=["chords", "stab", "bass", "tom", "metal", "choir", "lead", "arp", "impact"],
                    break_=["arp", "chords", "lead"], outro=["chords", "arp"]),
        mix=dict(chords=dict(reverb=0.4, gain_db=-8), tom=dict(reverb=0.4, gain_db=-5), stab=dict(reverb=0.35, gain_db=-8),
                 arp=dict(reverb=0.35, gain_db=-12), choir=dict(reverb=0.5, gain_db=-11), lead=dict(reverb=0.4, gain_db=-9), reverb_rt60=3.0),
    ),
    "rock": dict(
        bpm=(110, 148), scales=["minor", "pent_minor", "mixolydian"], kit="acoustic", swing=0, chord_len=1, fills=True,
        drums=dict(kick="x.......x.x.....", snare="....X.......X...", hat="x.x.x.x.x.x.x.x.", ride=""),
        bass=dict(inst="saw_bass", oct=1, rhythm="x.x.x.x.x.x.x.x.", kw=dict(cutoff=1200, drive=2.2)),
        guitar=dict(inst="guitar", oct=2, rhythm="x.x.x.x.x.x.x.x.", kind="power"),
        lead=dict(inst="guitar", oct=5, density=0.35, contour="arch", kw=dict(drive=5.0)),
        mix=dict(guitar=dict(gain_db=-7, widen=0.014), lead=dict(reverb=0.2, delay=0.2, gain_db=-8), kick=dict(gain_db=-1), snare=dict(reverb=0.2)),
    ),
    "metal": dict(
        bpm=(150, 190), scales=["phrygian", "harmonic_minor", "minor"], kit="industrial", swing=0, chord_len=1, fills=True, impact=True,
        breakbeat="metal",
        drums=dict(kick="x.x.x.x.x.x.x.x.", snare="....X.......X...", hat="x.x.x.x.x.x.x.x.", ohat="..............o.",
                   tom="..............xx"),
        bass=dict(inst="saw_bass", oct=1, rhythm="xxmxxmxxmxxmxxmx", kw=dict(cutoff=1400, drive=3.0)),
        guitar=dict(inst="guitar", oct=2, rhythm="xxmxxmxxmxxmxxmx", kind="power", kw=dict(drive=14.0)),
        lead=dict(inst="guitar", oct=5, density=0.55, contour="arch", leap=0.3, kw=dict(drive=8.0)),
        layers=dict(drop=["kick", "snare", "hat", "ohat", "tom", "bass", "guitar", "lead", "impact"],
                    intro=["guitar", "hat"], build=["guitar", "kick", "snare_roll", "bass"], break_=["guitar", "lead"], outro=["guitar", "kick"]),
        mix=dict(guitar=dict(gain_db=-8, widen=0.016), kick=dict(drive=1.6, gain_db=-1), lead=dict(reverb=0.2, delay=0.2, gain_db=-8)),
    ),
    "jazz": dict(
        bpm=(96, 150), scales=["dorian", "mixolydian", "major"], kit="acoustic", swing=0.34, swing_grid=2, chord_len=1,
        drums=dict(ride="X.x.xX.x.x.xX.x.", hat="....x.......x...", kick="o.......o....o.."),
        bass=dict(inst="sine_sub", oct=2, rhythm="w...w...w...w...", kw={}),
        chords=dict(inst="ep", oct=3, rhythm="..x.......x.....", kind="seventh"),
        lead=dict(inst="piano", oct=5, density=0.5, contour="arch", leap=0.35, rest=0.3),
        layers=dict(intro=["ride", "bass", "chords"], drop=["ride", "hat", "kick", "bass", "chords", "lead"],
                    break_=["bass", "chords", "ride"], outro=["ride", "bass", "chords"], build=["ride", "bass", "chords"]),
        plan=[("intro", .12), ("drop", .38), ("break_", .12), ("drop", .38)],
        mix=dict(ride=dict(gain_db=-11), bass=dict(gain_db=-2, lp=2200), chords=dict(reverb=0.2, gain_db=-9), lead=dict(reverb=0.25)),
    ),
}

ALIASES = {"forsaken": "horror_chase", "chase": "horror_chase", "roblox": "horror_chase", "horror": "horror_chase",
           "8bit": "chiptune", "chip": "chiptune", "retro": "synthwave", "outrun": "synthwave", "lo-fi": "lofi",
           "hiphop": "boombap", "hip-hop": "boombap", "boom_bap": "boombap", "drum_and_bass": "dnb", "d&b": "dnb",
           "future_bass": "edm", "pop": "edm", "ambient": "dark_ambient", "drone": "dark_ambient", "orchestral": "cinematic",
           "epic": "cinematic", "trailer": "cinematic", "heavy": "metal", "punk": "rock", "swing": "jazz", "tech": "techno",
           "wobble": "dubstep", "brostep": "dubstep", "industrial": "techno"}

DEFAULT_LAYERS = dict(
    intro=["chords", "arp", "hat", "drone", "vinyl", "strings"],
    build=["chords", "arp", "kick", "hat", "bass", "snare_roll", "riser", "strings"],
    drop=None, verse=["kick", "snare", "clap", "hat", "bass", "chords", "arp", "vinyl", "strings"],
    break_=["chords", "lead", "drone", "choir", "strings", "vinyl", "arp"],
    outro=["chords", "kick", "hat", "vinyl", "arp", "strings"],
)
DROP_LIKE = {"drop", "chase", "climax", "main", "chorus", "verse"}

DEFAULT_PLAN = [("intro", .12), ("build", .12), ("drop", .26), ("break_", .12), ("drop", .26), ("outro", .12)]

DEFAULT_MIX = dict(
    kick=dict(gain_db=0), snare=dict(gain_db=-2), clap=dict(gain_db=-4, reverb=0.15), hat=dict(gain_db=-10, pan=0.25),
    ohat=dict(gain_db=-12, pan=-0.25), perc=dict(gain_db=-12, pan=0.35), ride=dict(gain_db=-12, pan=0.3), tom=dict(gain_db=-6),
    metal=dict(gain_db=-10), bass=dict(gain_db=-3, hp=28), chords=dict(gain_db=-9, widen=0.01), arp=dict(gain_db=-11),
    lead=dict(gain_db=-8), guitar=dict(gain_db=-7), strings=dict(gain_db=-12, reverb=0.3), choir=dict(gain_db=-12, reverb=0.4),
    drone=dict(gain_db=-14), stab=dict(gain_db=-9), fx=dict(gain_db=-10), vinyl=dict(gain_db=-28),
)


def resolve(name):
    n = name.lower().strip().replace(" ", "_")
    n = ALIASES.get(n, n)
    if n not in GENRES:
        raise SystemExit(f"unknown genre '{name}'. choices: {', '.join(sorted(GENRES))} (aliases: {', '.join(sorted(ALIASES))})")
    return n


def deep_merge(a, b):
    a = copy.deepcopy(a)
    for k, v in (b or {}).items():
        if isinstance(v, dict) and isinstance(a.get(k), dict):
            a[k] = deep_merge(a[k], v)
        else:
            a[k] = copy.deepcopy(v)
    return a


def make_plan(bars, plan):
    """split `bars` into sections following the fractions in `plan`; sizes always sum to exactly `bars`"""
    plan = [list(p) for p in (plan or DEFAULT_PLAN)]
    if bars < 6:
        return [("main", 0, bars)]
    mn = 2 if bars >= 16 else 1
    while len(plan) * mn > bars:  # too many sections for this length: drop the smallest (keep first and last)
        inner = range(1, len(plan) - 1) if len(plan) > 2 else range(len(plan))
        plan.pop(min(inner, key=lambda i: plan[i][1]))
    tot = sum(p[1] for p in plan)
    raw = [bars * p[1] / tot for p in plan]
    sizes = [max(mn, int(r)) for r in raw]
    while sum(sizes) < bars:  # hand out leftover bars by largest remainder
        i = max(range(len(sizes)), key=lambda k: raw[k] - sizes[k])
        sizes[i] += 1
    while sum(sizes) > bars:
        i = max((k for k in range(len(sizes)) if sizes[k] > mn), key=lambda k: sizes[k] - raw[k])
        sizes[i] -= 1
    out, at = [], 0
    for (name, _), sz in zip(plan, sizes):
        out.append((name, at, sz))
        at += sz
    return out


def _pat(s):
    return [VEL.get(c, 0.0) for c in s.ljust(16, ".")[:16]]


def build(genre, bars=32, bpm=None, key=None, scale=None, seed=0, intensity=0.75, overrides=None, plan=None, swing=None):
    g = resolve(genre)
    spec = deep_merge(GENRES[g], overrides or {})
    rng = np.random.RandomState(seed)
    bpm = float(bpm) if bpm else float(rng.randint(spec["bpm"][0], spec["bpm"][1] + 1))
    scale = scale or spec["scales"][rng.randint(len(spec["scales"]))]
    root_pc = theory.key_to_pc(key) if key else int(rng.randint(0, 12))
    song = Song(bpm, bars, swing=swing if swing is not None else spec.get("swing", 0), seed=seed)
    song.swing_grid = spec.get("swing_grid", 1)
    kit = spec.get("kit", "808")
    progs = theory.PROGRESSIONS.get(scale, theory.PROGRESSIONS["minor"])
    prog = progs[rng.randint(len(progs))]
    if spec.get("progression"):
        prog = list(spec["progression"])
    clen = spec.get("chord_len", 1)
    mix = deep_merge(DEFAULT_MIX, spec.get("mix", {}))
    rt60 = mix.pop("reverb_rt60", 1.8)
    mix.pop("reverb", None)
    for name, fx in mix.items():
        song.track(name, **fx)
    secs = make_plan(bars, plan or spec.get("plan"))
    prev_name = None
    lead_seed = int(rng.randint(1, 10 ** 6))

    for name, sb, nb in secs:
        song.mark(name.rstrip("_"), sb, nb)
        lname = name
        layers = spec.get("layers", {}).get(lname) or DEFAULT_LAYERS.get(lname)
        if layers is None:  # drop-like with no explicit list = everything the spec defines
            layers = [k for k in ["kick", "snare", "clap", "hat", "ohat", "perc", "ride", "tom", "metal", "bass", "chords", "arp", "lead",
                                  "guitar", "strings", "choir", "stab", "drone", "vinyl"]
                      if k in spec.get("drums", {}) or k in spec]
            if spec.get("impact"):
                layers.append("impact")
        if intensity < 0.45:
            layers = [l for l in layers if l not in ("perc", "ohat", "stab", "tom", "metal")]
        if spec.get("vinyl") and "vinyl" not in layers and lname not in DROP_LIKE:
            layers = layers + ["vinyl"]
        chord_of = lambda lb: prog[(lb // clen) % len(prog)]  # noqa: E731  (lb = bar index within section)
        rng_s = np.random.RandomState(lead_seed)
        last_notes = [None]

        for lb in range(nb):
            bar = sb + lb
            s0 = bar * 16
            deg = chord_of(lb)
            last_bar = lb == nb - 1

            # drums: a generated breakbeat carries the groove when the spec asks for one,
            # static patterns still supply the extra colour (metal/perc/tom) around it.
            bb = spec.get("breakbeat")
            bb_names = {"kick", "snare", "hat", "ohat", "ride", "tom"} if bb else set()
            if bb:
                lset = set(layers)
                for st, nm, v in drums.breakbeat(nb, bb, rng_s, intensity, fill=bool(spec.get("fills", True))):
                    if st // 16 != lb or nm not in lset:
                        continue
                    if v < 0.25 and intensity < 0.5:
                        continue
                    trk, hname = nm, nm
                    if nm == "hat" and v < 0.30 and "ohat" in lset:
                        trk, hname = "ohat", "ohat"
                    song.drum(trk, hname, s0 + st, v * (0.82 + 0.18 * intensity), kit,
                              pan=mix.get(trk, {}).get("pan", 0.0))
            for dn, pat in spec.get("drums", {}).items():
                if dn not in layers or not pat or dn in bb_names:
                    continue
                for i, v in enumerate(_pat(pat)):
                    if v <= 0:
                        continue
                    if v < 0.5 and intensity < 0.5:
                        continue
                    hname = "ohat" if dn == "ohat" else dn
                    if dn in ("tom", "metal") or hname in drums.KIT_HITS:
                        song.drum(dn, hname, s0 + i, v * (0.85 + 0.15 * intensity), kit, pan=mix.get(dn, {}).get("pan", 0.0))
            if "snare_roll" in layers and nb >= 2 and lb >= nb - 2:
                rate = 2 if lb == nb - 2 else 1
                for i in range(0, 16, rate):
                    v = 0.35 + 0.65 * ((lb - (nb - 2)) * 16 + i) / 32.0
                    song.drum("snare", "snare", s0 + i, v, kit)
            if spec.get("fills") and last_bar and lname in DROP_LIKE:
                for i, nm in zip(range(12, 16), ["tom_hi", "tom", "tom_lo", "snare"]):
                    song.drum("tom", nm if nm != "snare" else "snare", s0 + i, 0.8, kit)
                song.drum("tom", "snare", s0 + 15, 0.9, kit)

            # bass
            if "bass" in layers and "bass" in spec:
                b = spec["bass"]
                kw = dict(b.get("kw", {}))
                if b["inst"] == "wobble":
                    kw["lfo"] = bpm / 60.0 * b.get("lfo_per_beat", 2)
                rh = b["rhythm"].ljust(16, ".")[:16]
                i = 0
                while i < 16:
                    c = rh[i]
                    if c in ".-":
                        i += 1
                        continue
                    j = i + 1
                    while j < 16 and rh[j] == "-":
                        j += 1
                    dur = (j - i) * (0.35 if c == "m" else 0.9)
                    r_deg = deg
                    m = theory.scale_note(root_pc, scale, r_deg, b.get("oct", 2))
                    if c == "o":
                        m += 12
                    elif c == "e":
                        m -= 12
                    elif c == "f":
                        m = theory.scale_note(root_pc, scale, r_deg + 4, b.get("oct", 2))
                    elif c == "t":
                        m = theory.scale_note(root_pc, scale, r_deg + 2, b.get("oct", 2))
                    elif c == "b":
                        m = theory.scale_note(root_pc, scale, r_deg + 6, b.get("oct", 2))
                    elif c == "w":
                        m = theory.scale_note(root_pc, scale, r_deg + int(rng_s.choice([0, 2, 4, 1, 3, 5, 6])), b.get("oct", 2))
                    song.note("bass", b["inst"], s0 + i, dur, m, VEL.get(c, 0.85) + 0.1, **kw)
                    i = j
            # sub layer, if present
            # chord-type layers
            for lay in ("chords", "strings", "choir", "stab", "guitar"):
                if lay not in layers or lay not in spec:
                    continue
                c = spec[lay]
                kind = c.get("kind", "triad")
                notes = theory.chord(root_pc, scale, deg, c.get("oct", 3), kind)
                # smooth voice leading: choose the inversion closest to the previous chord
                prev = last_notes[0] if lay == "chords" else None
                if prev is not None and kind != "power":
                    best = min(range(len(notes)), key=lambda inv: abs(np.mean(theory.chord(root_pc, scale, deg, c.get("oct", 3), kind, inv)) - prev))
                    notes = theory.chord(root_pc, scale, deg, c.get("oct", 3), kind, best)
                if lay == "chords":
                    last_notes[0] = float(np.mean(notes))
                rh = c["rhythm"].ljust(16, ".")[:16]
                i = 0
                while i < 16:
                    ch = rh[i]
                    if ch in ".-":
                        i += 1
                        continue
                    j = i + 1
                    while j < 16 and rh[j] == "-":
                        j += 1
                    inst = c["inst"]
                    if lay == "guitar" and ch == "m":
                        inst = "guitar_mute"
                    dur = (j - i) * (0.95 if ch != "m" else 0.4)
                    vsc = VEL.get(ch, 0.8) * (0.75 + 0.25 * intensity)
                    for k, nn in enumerate(notes):
                        song.note(lay, inst, s0 + i, dur, nn, vsc * (0.8 if lay in ("chords", "strings", "choir") else 1.0),
                                  pan=(-0.25 + 0.5 * k / max(len(notes) - 1, 1)) if lay in ("chords", "strings") else 0.0,
                                  **c.get("kw", {}))
                    i = j
            # arpeggio
            if "arp" in layers and "arp" in spec:
                a = spec["arp"]
                notes = theory.chord(root_pc, scale, deg, a.get("oct", 4), a.get("kind", "triad"))
                notes = notes + [n + 12 for n in notes]
                pat = a.get("pattern", "up")
                seq = {"up": notes, "down": notes[::-1], "updown": notes + notes[-2:0:-1],
                       "random": list(rng_s.permutation(notes))}.get(pat, notes)
                rate = a.get("rate", 1)
                for k, i in enumerate(range(0, 16, rate)):
                    song.note("arp", a["inst"], s0 + i, rate * 0.85, seq[k % len(seq)], 0.6 + 0.2 * (k % 4 == 0),
                              pan=0.35 * (1 if k % 2 else -1), **a.get("kw", {}))
            # sustained drone: one long note per section, on first bar
            if "drone" in layers and "drone" in spec and lb == 0:
                d = spec["drone"]
                song.note("drone", d["inst"], s0, nb * 16 * 0.97, theory.scale_note(root_pc, scale, prog[0], d.get("oct", 1)), 0.8)
            # riser: one per build section, ending exactly at its end
            if "riser" in layers and lb == 0:
                dur = nb * 16 * song.step_s
                r = dsp.riser(dur, 250, 7000, song.sr, 0.7)
                song.sample("fx", r, s0, 0.8)
            # impact + crash on the first bar of a drop-like section that follows a quieter one
            if lb == 0 and (spec.get("impact") or "impact" in layers) and lname in DROP_LIKE and prev_name is not None:
                song.drum("fx", "impact", s0, 0.9, kit)
                song.drum("fx", "crash", s0, 0.7, kit)
            if "vinyl" in layers and lb == 0:
                n = int(nb * 16 * song.step_s * song.sr)
                hiss = dsp.hp(np.random.uniform(-1, 1, n), 3500, song.sr) * 0.1
                crackle = (np.random.rand(n) > 0.9997) * np.random.uniform(-1, 1, n) * 0.8
                song.sample("vinyl", np.stack([hiss + crackle, hiss + np.roll(crackle, 300)], 1), s0, 1.0)

        # lead melody for the section (same seed => same hook every time the section repeats)
        if "lead" in layers and "lead" in spec:
            L = spec["lead"]
            bar_prog = [chord_of(i) for i in range(nb)]
            mel = theory.melody(np.random.RandomState(lead_seed), root_pc, scale, nb, 16, L.get("oct", 5),
                                L.get("density", 0.5) * (0.6 + 0.6 * intensity), bar_prog, L.get("contour", "arch"),
                                2 if nb >= 2 else 1, L.get("leap", 0.2), L.get("rest", 0.25))
            for st, dur, m, v in mel:
                song.note("lead", L["inst"], sb * 16 + st, dur * 0.95, m, v, **L.get("kw", {}))
        prev_name = lname

    song.meta = dict(genre=g, bpm=bpm, key=theory.NOTE_NAMES[root_pc], scale=scale, seed=seed, bars=bars, progression=prog,
                     intensity=intensity)
    song.rt60 = rt60
    return song


# ── video-oriented genres (added in 1.1): derived from the base specs, so every instrument/pattern already exists ──
def _derive(name, base, **over):
    GENRES[name] = deep_merge(GENRES[base], over)


# bright, steady, unobtrusive: product films, explainers, tutorials, corporate, real estate
_derive("corporate", "edm", bpm=(98, 122), scales=["major", "mixolydian"], impact=False, fills=False, swing=0.0,
        drums=dict(kick="x.......x.......", clap="....x.......x...", hat="x.x.x.x.x.x.x.x.", ohat="", perc=""),
        bass=dict(inst="sine_sub", oct=2, rhythm="x-------x-------"),
        chords=dict(inst="piano", oct=3, rhythm="x-------x-------", kind="triad"),
        arp=dict(inst="pluck", oct=4, rate=2, pattern="updown", kind="triad"),
        lead=dict(inst="bell", oct=5, density=0.35, contour="arch", rest=0.4),
        layers=dict(intro=["chords", "arp"], verse=["kick", "hat", "bass", "chords", "arp", "strings"],
                    build=["chords", "arp", "kick", "hat", "bass", "strings"],
                    drop=["kick", "clap", "hat", "bass", "chords", "arp", "lead", "strings"],
                    break_=["chords", "arp", "strings"], outro=["chords", "arp"]),
        plan=[("intro", .12), ("verse", .2), ("build", .1), ("drop", .3), ("break_", .1), ("outro", .18)])

# warm, slow, nostalgic: vlogs, weddings, memories, travel montages, slow documentary
_derive("warm_piano", "lofi", bpm=(66, 90), scales=["major", "mixolydian", "dorian"], vinyl=False, swing=0.1,
        chords=dict(inst="piano", oct=3, rhythm="x-------x-------", kind="seventh"),
        lead=dict(inst="music_box", oct=5, density=0.3, contour="arch", rest=0.45),
        drums=dict(kick="x.......x.......", snare="", hat="x...x...x...x..."),
        layers=dict(intro=["chords"], drop=["kick", "hat", "bass", "chords", "lead"], break_=["chords", "lead"],
                    outro=["chords", "lead"], build=["chords", "hat", "kick"]),
        plan=[("intro", .14), ("drop", .32), ("break_", .14), ("drop", .26), ("outro", .14)])

# big trailer: long tension, one huge hit, taiko-like toms; for trailers, hype reels, sport and gaming highlights
_derive("epic_trailer", "cinematic", bpm=(80, 110), scales=["minor", "harmonic_minor"],
        plan=[("intro", .12), ("build", .26), ("climax", .30), ("break_", .08), ("build", .08), ("climax", .16)],
        drums=dict(tom="x.x.x.xxx.x.xxxx", metal="x...............", ride=""),
        layers=dict(intro=["drone", "arp"], build=["arp", "chords", "bass", "tom", "riser", "strings"],
                    climax=["chords", "stab", "bass", "tom", "metal", "choir", "lead", "arp", "impact"],
                    break_=["arp", "chords", "lead"], outro=["chords", "arp"]))

# soft bed that stays out of the way of speech: podcasts, interviews, tutorials, documentaries (low density, no drums)
_derive("soft_ambient", "dark_ambient", bpm=(60, 80), scales=["major", "lydian", "dorian"],
        layers=dict(intro=["drone", "strings"], drop=["drone", "strings", "chords"], break_=["drone", "strings"],
                    outro=["drone", "strings"], build=["drone", "strings", "chords"]))

ALIASES.update({"product": "corporate", "tutorial": "corporate", "explainer": "corporate", "vlog": "warm_piano",
                "wedding": "warm_piano", "travel": "warm_piano", "memories": "warm_piano", "hype": "epic_trailer",
                "podcast": "soft_ambient", "interview": "soft_ambient", "documentary": "soft_ambient"})


# ── custom + shipped JSON genres (1.2): {"base": "metal", "override": {...}} ; layers/drums/mix dicts merge, lists/tuples replace ──
def load_custom_genres():
    import glob, json, os
    dirs = [os.path.join(os.path.dirname(os.path.abspath(__file__)), "genres.d"), os.path.expanduser(os.environ.get("AUDIO_FORGE_GENRES", "~/.config/audio-forge/genres"))]
    for d in dirs:
        for f in sorted(glob.glob(os.path.join(d, "*.json"))):
            try:
                j = json.load(open(f)); name = j.get("name") or os.path.splitext(os.path.basename(f))[0]
                base = j.get("base")
                if base not in GENRES: continue
                spec = deep_merge(GENRES[base], j.get("override", {}))
                for k in ("bpm",):
                    if k in spec: spec[k] = tuple(spec[k])
                if "plan" in spec: spec["plan"] = [tuple(x) for x in spec["plan"]]
                GENRES[name] = spec
                for a in j.get("aliases", []): ALIASES[a] = name
            except Exception as e:
                import sys; print(f"audio-forge: skipped custom genre {f}: {e}", file=sys.stderr)


load_custom_genres()

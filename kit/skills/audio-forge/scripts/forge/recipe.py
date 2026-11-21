"""recipe.py -- variation by default, mood knowledge in one place.

A *recipe* is every creative choice a composer makes (key, tempo, chord cycles, drum style, palette, ending, structure, SFX, ...).
`make_recipe(mood, seed=None, locks=None)`: anything NOT in `locks` is chosen at random, so two runs are different. Anything the user
specified goes in `locks` (CLI: --lock key=D,bpm=176) and is never changed. The recipe is saved next to the audio (`*.recipe.json`) and
recorded in a history file so the next recipe differs from the last few in at least 3 big choices.

MOODS['hunted'] encodes what listening feedback (Hydrogen, 2026-11-20, see skills/roblox-ost/references/hunted-vs-heroic.md) said separates a
"hunted to death, last one standing" theme from a heroic one. MOODS['heroic'] is kept for contrast and as a data example; only huntfight.py uses a mood today.
"""
import json
import os
import time

import numpy as np

HIST = os.path.expanduser("~/.config/audio-forge/recipes.json")

# progression cycles are 4 bars of chord names (chord table lives in huntfight.py: Am Bb F Dm E Em Bdim; A-based, transposed by the key)
MOODS = {
    "hunted": dict(
        bpm=(168, 180),
        keys=list(range(-5, 7)),                     # semitone offset from A minor; every minor key is allowed
        cycles=[["Am", "Bb", "Am", "E"], ["Am", "F", "Dm", "E"], ["Am", "Bb", "F", "E"], ["Am", "Am", "Bb", "E"],
                ["Am", "Dm", "Bdim", "E"], ["Am", "Bb", "Bdim", "E"], ["Am", "F", "Bb", "E"], ["Am", "Em", "F", "E"]],
        forbidden_chords=["C", "G", "A", "D"],       # major-key lifts read as happy/heroic
        drums=[("amen", 0.7), ("metal", 0.14), ("horror", 0.10), ("dnb", 0.06)],   # a stiff DnB loop was heard as mechanical, not panicked
        lead=["bend_lead", "bend_lead", "bend_lead", "chip_lead"],                   # pitch-bent distorted saw; the retro arcade square is rare now
        bell=["bell_church", "bell_church", "bell_tubular"], bell_pattern=["accents", "accents", "accents+off"],   # low church bell on terror accents, not every downbeat
        piano=["piano_dark", "piano_dark", "piano_grand"], pads=["trem_strings", "trem_strings", "both", "choir"],   # cold tremolo clusters, not a warm choir
        riffs=["syncopated", "gallop", "tritone", "triplet"], reese=0.75, organ_low=0.25, brass_low=0.25,
        sfx=["crawl", "static", "both"], shout=["ha", "ha2", "none"],
        ending=[("tape_stop_hit", 0.45), ("static_crash", 0.2), ("hard_cut_tail", 0.2), ("fade_dark", 0.15)],
        lift=[("none", 0.88), ("semitone", 0.12)],   # the +1 semitone lift was heard as heroic
        intro=[8, 12], drop_a=[12, 16, 20], glitch=[0, 4, 8], clock=[8, 12], drop_c=[16, 20, 24], breakdown=[2, 4],
        clock_on=0.85, chime_sets=[[0, -1, 0, -5], [0, -6, -1, -7], [0, -1, -6, -5], [0, 1, 0, -6]],
        guitar_drive=(11.0, 15.0), motif_kinds=["shake", "descend", "stab", "climb", "tritone", "tritone", "chromrun"],
        never=["glockenspiel", "celesta", "heroic lift", "warm choir pad", "arcade square lead as the main voice", "bright chimes on every downbeat", "stiff DnB loop", "bright music-box intro", "calm bittersweet piano pause"],
        note_brass_organ="A Grave Soul had no brass or organ; a later listener suggested LOW dark organ / brass stabs for dread. Both are optional (25% each), never warm or fanfare-like.",
    ),
    "heroic": dict(bpm=(160, 176), cycles=[["Am", "F", "C", "G"], ["Am", "F", "Dm", "E"]], never=["static crash", "tape stop"],
                   note="data only: ostfight.py is the heroic composer"),
}


def _pick(rs, items, weights=None):
    if items and isinstance(items[0], tuple):
        weights = [w for _, w in items]; items = [i for i, _ in items]
    w = None if weights is None else np.array(weights, float) / np.sum(weights)
    return items[int(rs.choice(len(items), p=w))]


def _load_hist():
    try:
        return json.load(open(HIST))
    except Exception:
        return []


def signature(r):
    return {"key": r["key"], "bpm": int(round(r["bpm"] / 4)), "prog": (tuple(r["cycle_a"]), tuple(r["cycle_b"])), "drums": r["drums_a"],
            "ending": r["ending"], "lift": r["lift"], "structure": tuple(r["structure"].values()), "lead": r["lead"]}


def distance(a, b):
    sa, sb = signature(a), signature(b)
    return sum(1 for k in sa if sa[k] != sb[k])


def make_recipe(mood="hunted", seed=None, locks=None, avoid_history=True):
    M = MOODS[mood]; locks = dict(locks or {})
    base_seed = int(seed) if seed is not None else int.from_bytes(os.urandom(4), "little")
    hist = _load_hist()[-3:] if avoid_history else []
    best = None
    for attempt in range(40):
        rs = np.random.RandomState((base_seed + attempt * 7919) % (2 ** 31 - 1))
        L = lambda k, f: locks[k] if k in locks else f()  # noqa: E731
        r = dict(mood=mood, seed=base_seed, attempt=attempt)
        r["key"] = int(L("key", lambda: int(rs.choice(M["keys"]))))
        r["bpm"] = float(L("bpm", lambda: float(rs.randint(M["bpm"][0], M["bpm"][1] + 1))))
        ca = L("cycle_a", lambda: M["cycles"][int(rs.randint(len(M["cycles"])))])
        cb = L("cycle_b", lambda: [c for c in M["cycles"] if c != ca][int(rs.randint(len(M["cycles"]) - 1))])
        r["cycle_a"], r["cycle_b"] = list(ca), list(cb)
        r["drums_a"] = L("drums", lambda: _pick(rs, M["drums"])); r["drums_c"] = L("drums", lambda: r["drums_a"] if rs.rand() < 0.75 else _pick(rs, [d for d in M["drums"] if d[0] != "dnb"]))
        for k in ("lead", "bell", "bell_pattern", "piano", "pads", "sfx", "shout"):
            r[k] = L(k, lambda k=k: _pick(rs, M[k]))
        r["ending"] = L("ending", lambda: _pick(rs, M["ending"])); r["lift"] = L("lift", lambda: _pick(rs, M["lift"]))
        r["structure"] = {k: int(L(k, lambda k=k: _pick(rs, M[k]))) for k in ("intro", "drop_a", "glitch", "clock", "drop_c", "breakdown")}
        r["clock_on"] = bool(L("clock_on", lambda: rs.rand() < M["clock_on"]))
        r["chime"] = list(L("chime", lambda: M["chime_sets"][int(rs.randint(len(M["chime_sets"])))]))
        r["guitar_drive"] = float(L("guitar_drive", lambda: rs.uniform(*M["guitar_drive"])))
        r["crawl_density"] = float(L("crawl_density", lambda: rs.uniform(7, 14)))
        r["boom_every"] = int(L("boom_every", lambda: int(rs.choice([8, 10, 12]))))
        r["motif_kinds"] = [str(L("motif", lambda: _pick(rs, M["motif_kinds"]))) for _ in range(5)]
        r["riff_a"] = L("riff_a", lambda: _pick(rs, M["riffs"])); r["riff_c"] = L("riff_c", lambda: _pick(rs, [x for x in M["riffs"] if x != r["riff_a"]]))
        r["reese"] = bool(L("reese", lambda: rs.rand() < M["reese"])); r["organ_low"] = bool(L("organ_low", lambda: rs.rand() < M["organ_low"])); r["brass_low"] = bool(L("brass_low", lambda: rs.rand() < M["brass_low"]))
        r["mix_jitter_db"] = {t: float(round(rs.uniform(-1.2, 1.2), 2)) for t in ("lead", "bell", "pads", "piano", "gtr", "sfx")}
        if not avoid_history or all(distance(r, h) >= 3 for h in hist if "key" in h):
            best = r; break
        best = best or r
    best["locked"] = sorted(locks)
    return best


def record(r):
    try:
        os.makedirs(os.path.dirname(HIST), exist_ok=True)
        h = _load_hist()[-20:] + [dict(r, recorded=time.strftime("%Y-%m-%d %H:%M"))]
        json.dump(h, open(HIST, "w"), indent=1)
    except Exception:
        pass


def parse_locks(s):
    """'key=D,bpm=176,ending=static_crash,drums=dnb' -> dict (keys may be note names)"""
    out = {}
    names = {"A": 0, "A#": 1, "BB": 1, "B": 2, "C": 3, "C#": 4, "DB": 4, "D": 5, "D#": 6, "EB": 6, "E": -5, "F": -4, "F#": -3, "GB": -3, "G": -2, "G#": -1, "AB": -1}
    for part in [p for p in (s or "").split(",") if p.strip()]:
        k, _, v = part.partition("="); k, v = k.strip(), v.strip()
        if k == "key":
            out[k] = names[v.upper()] if v.upper() in names else int(v)
        elif k in ("bpm", "guitar_drive", "crawl_density"):
            out[k] = float(v)
        elif k in ("intro", "drop_a", "glitch", "clock", "drop_c", "breakdown", "boom_every"):
            out[k] = int(v)
        elif k == "clock_on":
            out[k] = v.lower() in ("1", "true", "yes", "on")
        elif k in ("cycle_a", "cycle_b", "chime"):
            out[k] = [x if k != "chime" else int(x) for x in v.split("/")]
        else:
            out[k] = v
    return out


def upgrade_recipe(R):
    """recipes saved by an older version get the newer fields (deterministic from their seed), so --same-as keeps working"""
    M = MOODS[R.get("mood", "hunted")]; rs = np.random.RandomState((int(R["seed"]) + 999) % (2 ** 31 - 1))
    R.setdefault("riff_a", _pick(rs, M["riffs"])); R.setdefault("riff_c", _pick(rs, [x for x in M["riffs"] if x != R["riff_a"]]))
    R.setdefault("reese", bool(rs.rand() < M["reese"])); R.setdefault("organ_low", bool(rs.rand() < M["organ_low"])); R.setdefault("brass_low", bool(rs.rand() < M["brass_low"]))
    return R

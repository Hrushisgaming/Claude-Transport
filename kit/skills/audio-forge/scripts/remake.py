"""remake.py -- turn an analyze.py profile into compose.py parameters + a genre-spec override.

Style transfer here means: same tempo, key/mode, chord progression (as scale degrees), groove (kick/snare/hat
pattern), swing, density, section structure and energy contour -- rendered with the synth engine as an ORIGINAL piece.
Melodies, samples and recordings from the reference are never copied.
"""
import json, os, sys
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from forge import theory, genres

SEC_MAP = {"intro": "intro", "build": "build", "drop": "drop", "break": "break_", "outro": "outro", "verse": "verse"}


def _chord_root_pc(label):
    name = label[:2] if len(label) > 1 and label[1] == "#" else label[:1]
    return theory.NOTE_NAMES.index(name)


def degrees_from_chords(chords, key_pc, scale):
    sc = theory.SCALES[scale]
    out = []
    for c in chords:
        off = (_chord_root_pc(c) - key_pc) % 12
        d = min(range(len(sc)), key=lambda i: min((sc[i] - off) % 12, (off - sc[i]) % 12))
        out.append(d)
    return out


def find_progression(degs):
    if len(degs) < 4:
        return None
    for L in (1, 2, 4, 8):
        if len(degs) < L * 2:
            continue
        mism = sum(1 for i, d in enumerate(degs) if d != degs[i % L])
        # take the most common degree at each position mod L (robust to a few wrong bars)
        prog = [Counter(degs[p::L]).most_common(1)[0][0] for p in range(L)]
        mism = sum(1 for i, d in enumerate(degs) if d != prog[i % L])
        if mism / len(degs) <= 0.3:
            return prog
    return [Counter(degs[p::4]).most_common(1)[0][0] for p in range(4)]


def params_from_profile(p, genre=None):
    guess = [g for g in p.get("genre_guess", []) if "genre" in g]
    g = genre or (guess[0]["genre"] if guess else "synthwave")
    key = p["key"]["best"]["key"]
    mode = p["key"]["best"]["mode"]
    scale = "minor" if mode == "minor" else "major"
    bpm = p["tempo"]["bpm"]
    bpb = p["meter"]["beats_per_bar"]
    dur = p.get("analyzed_seconds", 90)
    bars = int(max(8, min(128, round(dur / (bpb * 60.0 / bpm) / 2) * 2)))
    op = p.get("onsets_per_sec", 4)
    params = dict(genre=g, bpm=bpm, key=key, scale=scale, bars=bars, swing=p.get("swing", 0.0),
                  intensity=round(min(0.95, 0.45 + 0.5 * min(op / 8.0, 1.0)), 2))
    ov = {}
    pat = p.get("pattern", {})
    dr = {}
    for src, dst in (("kick", "kick"), ("snare", "snare"), ("hat", "hat")):
        s = pat.get(src, "")
        if sum(1 for c in s if c in "xX") >= 2 and len(s) == 16:
            dr[dst] = s
    if dr:
        ov["drums"] = dr
        if "snare" in dr:
            ov["drums"]["clap"] = dr["snare"] if "clap" in genres.GENRES[genres.resolve(g)].get("drums", {}) else None
            if ov["drums"]["clap"] is None:
                del ov["drums"]["clap"]
    chords = [c["chord"] for c in p.get("chords_per_bar", []) if c.get("score", 0) > 0.55]
    if len(chords) >= 8:
        prog = find_progression(degrees_from_chords(chords, theory.key_to_pc(key), scale))
        if prog:
            ov["progression"] = prog
            ov["chord_len"] = 1
    secs = p.get("sections", [])
    if secs:
        total = sum(s["bars"] for s in secs) or 1
        plan = []
        for s in secs:
            name = SEC_MAP.get(s["label"], "drop")
            if plan and plan[-1][0] == name:
                plan[-1][1] += s["bars"] / total
            else:
                plan.append([name, s["bars"] / total])
        ov["plan"] = [tuple(x) for x in plan][:8]
    return params, ov


if __name__ == "__main__":
    pr = json.load(open(sys.argv[1]))
    a, b = params_from_profile(pr)
    print(json.dumps(dict(params=a, overrides=b), indent=1, default=list))

#!/usr/bin/env python3
"""compare.py - how close is a candidate track to a reference style, in NUMBERS (for models that cannot hear).

  af.py compare cand.wav styles/roblox-guitar-cover/dna.json        candidate audio vs a saved Style DNA
  af.py compare cand.wav ref.mp3                                    candidate vs another audio file (measured the same way)
  af.py compare a.dna.json b.dna.json

Prints each measure with reference, candidate, difference, a verdict (OK / CLOSE / OFF) and, when OFF, WHICH KNOB to change.
Closeness is a heuristic from measurements, never proof that it sounds the same: the person's ears decide. Change ONE knob per round.
"""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import study as S


def dna_of(p):
    if p.lower().endswith(".json"): return json.load(open(p))
    d, _ = S.study(p); return d


def corr(a, b):
    a, b = np.array(a, float), np.array(b, float)
    if a.std() < 1e-9 or b.std() < 1e-9: return 0.0
    return float(np.corrcoef(a, b)[0, 1])


def resample(v, n):
    v = np.array(v, float); return np.interp(np.linspace(0, len(v) - 1, n), np.arange(len(v)), v)


def rows(ref, c):
    R = []
    def add(name, rv, cv, tol_ok, tol_close, knob, unit="", rel=False):
        diff = (cv - rv) / (abs(rv) + 1e-9) * 100 if rel else cv - rv; a = abs(diff)
        lim = (tol_ok, tol_close); v = "OK" if a <= lim[0] else "CLOSE" if a <= lim[1] else "OFF"
        R.append((name, rv, cv, diff, v, knob if v == "OFF" else "", unit + ("%" if rel else "")))
    rb, cb = ref["tempo"]["bpm"], c["tempo"]["bpm"]
    alts = [rb] + list(ref["tempo"].get("alt_octaves") or [])
    best = min(alts, key=lambda x: abs(x - cb) / x); add("tempo (octave-aware)", best, cb, 2, 5, "compose --bpm", rel=True)
    NOTES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    def _rel(k):                                   # relative major/minor share all seven notes: A minor == C major (the analyzer cannot always tell which is 'home')
        try: pc = NOTES.index(k["tonic"].replace("Db", "C#").replace("Eb", "D#").replace("Gb", "F#").replace("Ab", "G#").replace("Bb", "A#"))
        except ValueError: return None
        return (pc + 3) % 12 if k["mode"] == "minor" else pc
    same = (ref["key"]["tonic"], ref["key"]["mode"]) == (c["key"]["tonic"], c["key"]["mode"]); relative = (not same) and _rel(ref["key"]) is not None and _rel(ref["key"]) == _rel(c["key"])
    R.append(("key", f"{ref['key']['tonic']} {ref['key']['mode']}", f"{c['key']['tonic']} {c['key']['mode']}", "", "OK" if same else "CLOSE" if relative else "OFF", "" if same else "same notes as the relative key: fine unless the tonic must be exact" if relative else "compose --key/--scale", ""))
    add("loudness", ref["mix"]["lufs"], c["mix"]["lufs"], 1.0, 2.5, "master gain / mix.master target", " LUFS")
    add("crest factor", ref["mix"]["crest_db"], c["mix"]["crest_db"], 1.5, 3.0, "less limiting (higher) or more compression (lower): spec.mix", " dB")
    add("spectral centroid", ref["timbre"]["centroid_hz"], c["timbre"]["centroid_hz"], 12, 25, "brighter: more drive/bright or lp cutoff up; darker: the reverse", rel=True)
    add("85% rolloff", ref["timbre"]["rolloff85_hz"], c["timbre"]["rolloff85_hz"], 15, 30, "lp cutoff / guitar bright", rel=True)
    add("flatness (distortion/noise)", ref["timbre"]["flatness"], c["timbre"]["flatness"], 0.08, 0.2, "guitar kw drive (more = flatter), drums hat level", "")
    for b in ("sub", "bass", "low_mid", "mid", "high_mid", "air"):
        add(f"band {b}", ref["timbre"]["bands_db"][b], c["timbre"]["bands_db"][b], 2.0, 4.0, f"EQ/level of the layers living in the {b} band", " dB")
    add("stereo side/mid", ref["mix"]["side_to_mid_db"], c["mix"]["side_to_mid_db"], 2.0, 4.0, "spec.mix widen / double-tracking", " dB")
    add("attacks per beat", ref["rhythm"]["onsets_per_beat"], c["rhythm"]["onsets_per_beat"], 0.25, 0.6, "guitar/drum rhythm pattern density", "")
    if ref["rhythm"].get("sustain_ms") and c["rhythm"].get("sustain_ms"): add("sustain", ref["rhythm"]["sustain_ms"], c["rhythm"]["sustain_ms"], 25, 60, "guitar kw mute (more = shorter notes)", " ms", rel=True)
    a_, b_ = ref["rhythm"]["step16_density"], c["rhythm"]["step16_density"]; rc = max(corr(a_, list(np.roll(b_, 4 * k))) for k in range(4))   # beat-shift tolerant: the analyzer may place the downbeat a beat off
    R.append(("rhythm fingerprint correlation", 1.0, round(rc, 2), round(rc - 1, 2), "OK" if rc >= 0.8 else "CLOSE" if rc >= 0.55 else "OFF", "change the 16-step rhythm strings (genre guitar.rhythm / drums)" if rc < 0.55 else "", ""))
    n = 32; ec = corr(resample(ref["structure"]["energy_per_bar_db"], n), resample(c["structure"]["energy_per_bar_db"], n))
    R.append(("energy-curve correlation", 1.0, round(ec, 2), round(ec - 1, 2), "OK" if ec >= 0.8 else "CLOSE" if ec >= 0.5 else "OFF", "change spec.plan section proportions / layers per section" if ec < 0.5 else "", ""))
    rd, cd = ref.get("deep"), c.get("deep")
    if rd and cd:                                   # hard points, form and loop (style-copy/audio-dna@2)
        rh, ch = rd["hard_points"], cd["hard_points"]
        def first(h): return h["drops"][0]["pct"] if h["drops"] else None
        if first(rh) is not None and first(ch) is not None: add("first drop position", first(rh), first(ch), 5, 12, "spec.plan: move the first drop (intro+build share of the track)", " pts")
        elif first(rh) is not None: R.append(("first drop position", first(rh), "none", "", "OFF", "candidate has no clear drop: make the entrance bigger (impact, bass entry, cut before it)", ""))
        add("drops", len(rh["drops"]), len(ch["drops"]), 0, 1, "spec.plan: number of drop sections", "")
        add("hard hits per minute", rh["hits_per_min"], ch["hits_per_min"], 2, 5, "genre impact=True / more fills and stabs on section starts", "")
        add("hard stops per minute", rh["stops_per_min"], ch["stops_per_min"], 0.4, 1.0, "add a short cut (silence) right before the drop", "")
        add("risers", len(rh["risers"]), len(ch["risers"]), 0, 1, "add a riser (layers: riser) in the build", "")
        if rd["form"]["chord_cycle_bars"] and cd["form"]["chord_cycle_bars"]: add("chord cycle (bars)", rd["form"]["chord_cycle_bars"], cd["form"]["chord_cycle_bars"], 0, 4, "genre chord_len / progression length", " bars")
        add("mid lead layer share", rd["lead_layer"]["share_of_bars"], cd["lead_layer"]["share_of_bars"], 0.12, 0.25, "lead density / when the lead plays", "")
        a_, b_ = len(rd["layer_moves"]), len(cd["layer_moves"]); add("section changes", a_, b_, 1, 3, "spec.plan: number of sections / layers changing between them", "")
        # rev 4: transitions the energy-only rows above do not see
        def n_of(d, k): return len((d.get("hard_points") or {}).get(k) or [])
        add("breakdowns", n_of(rd, "breakdowns"), n_of(cd, "breakdowns"), 0, 1, "spec.plan: add/remove a quieter break_ section", "")
        add("builds", n_of(rd, "builds"), n_of(cd, "builds"), 0, 1, "spec.plan: add a build section with a riser + snare_roll", "")
        add("tone shifts", n_of(rd, "tone_shifts"), n_of(cd, "tone_shifts"), 0, 2, "change the arrangement's timbre between sections (instrument swap, lp/HP, layer drop-out)", "")
        add("1-2 bar fills", n_of(rd, "fill_dips"), n_of(cd, "fill_dips"), 0, 2, "spec.fills=True / add tom+snare fills at phrase ends", "")
        add("half-bar snare rolls", n_of(rd, "snare_rolls"), n_of(cd, "snare_rolls"), 1, 3, "spec.fills=True or a tighter snare/tom pattern in the last two beats", "")
        rt_, ct_ = rd.get("tail"), cd.get("tail")
        rk, ck = (rt_ or {}).get("kind", "no cut/fade"), (ct_ or {}).get("kind", "no cut/fade")
        same_tail = (rt_ is None and ct_ is None) or (rt_ and ct_ and rk == ck)
        R.append(("ending", rk, ck, "", "OK" if same_tail else "CLOSE" if (rt_ and ct_) else "OFF",
                  "" if same_tail else "end the track the same way: hard cut vs fade (spec.plan last section / explicit stop)" if (rt_ or ct_) else "", ""))
    return R


def main():
    if len(sys.argv) < 3 or sys.argv[1] in ("-h", "--help"): sys.exit(__doc__)
    cand, ref = dna_of(sys.argv[1]), dna_of(sys.argv[2]); R = rows(ref, cand)
    print(f"{'measure':34s} {'reference':>12s} {'candidate':>12s} {'diff':>10s}  verdict   change this");
    for name, rv, cv, diff, v, knob, unit in R:
        f = lambda x: (f"{x:.2f}" if isinstance(x, float) else str(x))
        print(f"{name:34s} {f(rv):>12s} {f(cv):>12s} {(f(round(diff, 2)) + unit if diff != '' else ''):>10s}  {v:7s}   {knob}")
    pts = {"OK": 1.0, "CLOSE": 0.5, "OFF": 0.0}; score = 100 * sum(pts[r[4]] for r in R) / len(R); off = [r[0] for r in R if r[4] == "OFF"]
    print(f"\ncloseness {score:.0f}/100 (a heuristic from {len(R)} measurements, not hearing). Still OFF: {', '.join(off) or 'none'}.")
    print("Change ONE knob, rebuild, compare again (max 5 rounds). Then tell the person which numbers match and that you have not listened.")


if __name__ == "__main__":
    main()

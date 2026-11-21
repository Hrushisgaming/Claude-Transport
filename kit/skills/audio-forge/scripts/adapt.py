#!/usr/bin/env python3
"""adapt.py - compose -> measure -> compare -> adjust, up to 5 rounds, towards a reference.

  af.py adapt --genre horror_chase --reference ref.wav --out adapted.wav
  af.py adapt --reference styles/lms-family/dna.json --out adapted.wav --rounds 5
  af.py adapt --state chase --reference ref.wav --out chase.wav --bpm 178 --key A --scale minor
  af.py adapt --reference ref.wav --out adapted.wav --json

HOW IT WORKS
  round 1: read the reference (audio or a saved dna.json), then compose a first candidate with
           parameters derived from it (tempo, key, loudness, section plan, rhythm strings, drive)
  round N: measure the candidate with the same analyzer, compare it to the reference with
           af.py compare's own rules, change the knobs the comparison flagged, compose again
  it stops when nothing is OFF any more, or after --rounds rounds (default 5, the guidance says
  change ONE knob per round, so this stays small and explainable)

OUTPUTS
  --out              the best candidate (highest closeness score)
  adapt-log.json     every round: the rows, the verdict, the knob that changed, the new value
  adapt-log.md       the same as a readable table

HONESTY: closeness is a heuristic from measurements, not hearing. Nobody has listened to the
result. Report the numbers and say that the person's ears decide.
"""
import argparse
import json
import os
import shutil
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import audioutil as U
import compare as CMP
import study as S
from forge import genres, song as songmod

STATES = {
    "lobby": dict(genre="dark_ambient", plan=[["main", 1.0]], intensity=0.3, lufs=-16.0),
    "tension": dict(genre="horror_chase", plan=[["chase", 1.0]], intensity=0.45, lufs=-15.0),
    "chase": dict(genre="horror_chase", plan=[["chase", 1.0]], intensity=0.9, lufs=-14.0),
    "lms": dict(genre="horror_chase", plan=[["chase", 1.0]], intensity=1.0, lufs=-14.0),
}


# ── reference ────────────────────────────────────────────────────────────────
def load_reference(path):
    if path.lower().endswith(".json"):
        return json.load(open(path)), "dna.json"
    dna, _ = S.study(path)
    return dna, os.path.basename(path)


def pick_bpm(ref, genre, forced=None):
    if forced:
        return float(forced)
    rb = float(ref["tempo"]["bpm"])
    alts = [rb] + [float(x) for x in (ref["tempo"].get("alt_octaves") or [])]
    lo, hi = genres.GENRES[genres.resolve(genre)]["bpm"]
    mid = (lo + hi) / 2.0
    # absolute distance to the genre's tempo window: a 234 BPM analyzer octave of a 117 BPM track
    # is further from a 160 BPM game track than 117 BPM is
    return float(min(alts, key=lambda b: abs(b - mid)))


def pattern_from_density(v, max_notes=8):
    """16-step rhythm string from a measured step16 density (keeps the busiest steps only)"""
    v = list(v)
    order = np.argsort(v)[::-1]
    keep = set(int(i) for i in order[:max_notes])
    thr = float(np.percentile(v, 55)) if v else 0.0
    out = []
    for i, x in enumerate(v):
        if i in keep and x >= 0.8:
            out.append("X")
        elif i in keep and x >= thr:
            out.append("x")
        elif i in keep and x >= 0.2:
            out.append("o")
        else:
            out.append(".")
    return "".join(out)


def initial_state(ref, args):
    genre = args.genre or (STATES[args.state]["genre"] if args.state else "horror_chase")
    st = STATES.get(args.state, {})
    bpm = pick_bpm(ref, genre, args.bpm)
    key = args.key or ref["key"]["tonic"]
    mode = (args.scale or ref["key"]["mode"] or "minor").lower()
    if mode in ("minor", "major", "dorian", "phrygian", "lydian", "mixolydian", "harmonic_minor", "locrian", "pent_minor", "pent_major", "blues"):
        scale = mode
    else:
        scale = "minor" if "min" in mode else "major"
    bars = args.bars
    if not bars:
        sec = float(ref.get("seconds") or 0)
        bars = int(np.clip(round(sec / (240.0 / bpm)), 8, 64))
    plan = st.get("plan")
    if not plan:
        plan = S.plan_from_energy(ref["structure"]["energy_per_bar_db"])
    ov = dict(plan=plan)
    if ref.get("mix", {}).get("lufs"):
        ov["lufs"] = round(float(ref["mix"]["lufs"]), 1)
    elif st.get("lufs"):
        ov["lufs"] = st["lufs"]
    r = ref["rhythm"]
    low_pat = pattern_from_density(r.get("low_step16_density") or r["step16_density"])
    mid_pat = pattern_from_density(r.get("mid_step16_density") or r["step16_density"])
    if low_pat.count("x") + low_pat.count("X") >= 2:
        ov.setdefault("bass", {}).setdefault("inst", "sine_sub")
        ov["bass"]["rhythm"] = low_pat
    if mid_pat.count("x") + mid_pat.count("X") >= 2:
        ov.setdefault("guitar", {}).setdefault("inst", "guitar_pluck")
        ov["guitar"]["rhythm"] = mid_pat
    ov.setdefault("lead", {}).setdefault("inst", "bell")
    ov["lead"]["density"] = round(float(np.clip(r.get("onsets_per_beat", 1.5) / 3.0, 0.15, 0.9)), 2)
    ov.setdefault("lead", {})["density"] = round(float(np.clip(r.get("onsets_per_beat", 1.5) / 3.0, 0.15, 0.9)), 2)
    dist = ref["timbre"]["flatness"] > 0.5 or ref["timbre"].get("hf_ratio_db", -12) > -6
    ov.setdefault("guitar", {})["kw"] = dict(drive=10.0 if dist else 1.0)
    ov["chord_len"] = 1 if ref["harmony"].get("chord_changes_per_bar", 0.3) >= 0.5 else 2
    if args.override:
        ov = genres.deep_merge(ov, json.load(open(args.override)) if os.path.exists(args.override) else json.loads(args.override))
    return dict(genre=genre, bpm=bpm, key=key, scale=scale, bars=bars, seed=args.seed,
                intensity=st.get("intensity", 0.75), override=ov, plan=plan)


# ── rendering ────────────────────────────────────────────────────────────────
def render(state, out_wav, workdir):
    ov = dict(state["override"])
    ov.pop("plan", None)
    s = genres.build(state["genre"], state["bars"], state["bpm"], state["key"], state["scale"], state["seed"],
                     state["intensity"], ov, state["plan"])
    audio = s.mixdown(master=True, reverb_rt60=s.rt60)
    target = state["override"].get("lufs")
    if target:
        import analyze as A
        from forge import dsp as D
        songmod.write_wav(out_wav, audio, s.sr)
        for _ in range(2):
            cur = A.loudness(out_wav)["lufs"]
            if cur is None or abs(cur - target) < 0.4:
                break
            audio = audio * (10 ** ((target - cur) / 20.0))
            if target > cur:
                audio = D.limiter(audio, -1.0, sr=s.sr)
            songmod.write_wav(out_wav, audio, s.sr)
    else:
        songmod.write_wav(out_wav, audio, s.sr)
    return s, audio


def candidate_dna(path, with_deep=True):
    dna, _ = S.study(path, with_deep=with_deep)
    return dna


def score_rows(rows):
    pts = {"OK": 1.0, "CLOSE": 0.5, "OFF": 0.0}
    return round(100 * sum(pts[r[4]] for r in rows) / max(len(rows), 1), 1)


# ── the adjustment rules ─────────────────────────────────────────────────────
def _mix_gain(ov, layer, delta_db):
    m = ov.setdefault("mix", {})
    cur = float(m.get(layer, {}).get("gain_db", 0.0))
    m.setdefault(layer, {})["gain_db"] = round(max(-40.0, min(12.0, cur + delta_db)), 1)


BAND_LAYER = {"sub": "bass", "bass": "bass", "low_mid": "chords", "mid": "lead", "high_mid": "hat", "air": "hat"}


def adjust(state, ref, cand, rows):
    """one round of changes. returns (list of change descriptions, new state)"""
    changes = []
    bright = []
    ov = state["override"]
    off = [r for r in rows if r[4] == "OFF"]
    close = [r for r in rows if r[4] == "CLOSE"]
    for name, rv, cv, diff, verdict, knob, unit in off + close:
        if name.startswith("tempo"):
            nb = pick_bpm(ref, state["genre"], round(float(rv)))
            if abs(nb - state["bpm"]) > 0.5:
                changes.append(f"tempo {state['bpm']:g} -> {nb:g} BPM")
                state["bpm"] = nb
        elif name == "key":
            t, m = str(rv).split()[0], str(rv).split()[1]
            if (t, m) != (state["key"], state["scale"]):
                changes.append(f"key {state['key']} {state['scale']} -> {t} {m}")
                state["key"], state["scale"] = t, m
            # else: the candidate already uses the reference key - the analyzer is ambiguous between
            # relative major/minor, so this row cannot be closed by changing a knob
        elif name == "loudness":
            ov["lufs"] = round(float(rv), 1)
            changes.append(f"lufs -> {rv}")
        elif name == "crest factor":
            d = float(ref["mix"]["crest_db"]) - float(cand["mix"]["crest_db"])
            cur = float(ov.get("dynamics", 1.0))
            ov["dynamics"] = round(float(np.clip(cur * (1 + d / 12.0), 0.3, 1.6)), 2)
            changes.append(f"dynamics {cur} -> {ov['dynamics']} (crest {cand['mix']['crest_db']} vs ref {rv})")
        elif name in ("spectral centroid", "85% rolloff"):
            # one brightness decision for both rows (they must not fight each other)
            rel = ((float(rv) - float(cv)) / max(abs(float(rv)), 1e-9))
            bright.append(rel)
            if len(bright) >= 2:
                rel = float(np.mean(bright)); bright.clear()
                g = ov.setdefault("mix", {})
                for layer in ("guitar", "lead", "stab"):
                    cur = g.get(layer, {}).get("lp")
                    if rel > 0:                       # candidate too dark -> open it up
                        if cur:
                            g[layer]["lp"] = int(min(16000, cur * 1.5))
                        else:
                            g.setdefault(layer, {}).setdefault("kw", {})["bright"] = 0.5
                    else:                            # candidate too bright -> close it down
                        g.setdefault(layer, {})["lp"] = int(min(9000, (cur or 14000) * 0.7))
                changes.append(f"mix {'brighter' if rel > 0 else 'darker'} by {abs(rel) * 100:.0f}% (lp / bright knobs)")
        elif name.startswith("flatness"):
            dist = float(cv) > float(rv)
            cur = float(ov.get("guitar", {}).get("kw", {}).get("drive", 2.0))
            nd = float(np.clip(cur * (1.6 if dist else 0.6), 0.5, 20.0))
            ov.setdefault("guitar", {}).setdefault("kw", {})["drive"] = round(nd, 2)
            changes.append(f"guitar drive {cur} -> {round(nd, 2)}")
        elif name.startswith("band "):
            band = name.split()[1]
            layer = BAND_LAYER.get(band, "lead")
            delta = float(rv) - float(cv)
            _mix_gain(ov, layer, delta)
            now = ov.get("mix", {}).get(layer, {}).get("gain_db")
            changes.append(f"band {band} {cv} -> target {rv} dB (mix.{layer}.gain_db {delta:+.1f} dB, now {now})")
        elif name == "stereo side/mid":
            delta = float(rv) - float(cv)
            g = ov.setdefault("mix", {})
            cur = float(g.get("guitar", {}).get("widen", 0.008))
            g.setdefault("guitar", {})["widen"] = round(float(np.clip(cur + delta / 400.0, 0.0, 0.05)), 4)
            changes.append(f"width {cur} -> {g['guitar']['widen']} (side/mid delta {delta:+.1f} dB)")
        elif name == "attacks per beat":
            ov.setdefault("lead", {})["density"] = round(float(np.clip(float(rv) / 3.0, 0.15, 0.9)), 2)
            changes.append(f"lead density -> {ov['lead']['density']} (target {rv} attacks/beat)")
        elif name == "sustain":
            # the guitar layer has a separate muted voice: shorten the notes with 'm' in the rhythm string
            rh = ov.get("guitar", {}).get("rhythm", "x-x-x-x-x-x-x-x-")
            if float(cv) > float(rv):
                nr = rh.replace("x", "m").replace("X", "x")
                changes.append(f"guitar hits muted (sustain {cv} vs {rv} ms): {rh} -> {nr}")
            else:
                nr = rh.replace("m", "x")
                changes.append(f"guitar hits opened (sustain {cv} vs {rv} ms): {rh} -> {nr}")
            ov.setdefault("guitar", {})["rhythm"] = nr
        elif name == "rhythm fingerprint correlation":
            low = pattern_from_density(ref["rhythm"].get("low_step16_density") or ref["rhythm"]["step16_density"])
            mid = pattern_from_density(ref["rhythm"].get("mid_step16_density") or ref["rhythm"]["step16_density"])
            ov.setdefault("bass", {})["rhythm"] = low
            ov.setdefault("guitar", {})["rhythm"] = mid
            changes.append(f"rhythm strings from the reference: bass {low} | guitar {mid}")
        elif name == "energy-curve correlation":
            plan = S.plan_from_energy(ref["structure"]["energy_per_bar_db"])
            state["plan"] = plan
            changes.append(f"plan -> {plan}")
        elif name == "first drop position":
            frac = float(rv) / 100.0
            state["plan"] = [["intro", round(max(0.02, frac * 0.5), 3)], ["build", round(max(0.02, frac * 0.5), 3)], ["drop", round(1 - frac, 3)]]
            changes.append(f"plan -> {state['plan']} (first drop at {rv}%)")
        elif name in ("drops", "section changes", "builds", "breakdowns"):
            plan = state["plan"]
            nm = "drop" if name == "drops" else ("build" if name == "builds" else "break_")
            if len(plan) < 2:
                plan = [["intro", 0.15], [nm, 0.85]]
            else:
                plan = [[nm if p[0] in ("verse", "main") else p[0], p[1]] for p in plan]
            tot = sum(p[1] for p in plan) or 1.0
            state["plan"] = [[p[0], round(p[1] / tot, 3)] for p in plan]
            changes.append(f"plan -> {state['plan']} ({name})")
        elif name == "risers":
            ov["fills"] = True
            changes.append("fills on (riser + snare roll in the build)")
        elif name in ("1-2 bar fills", "half-bar snare rolls"):
            ov["fills"] = True
            changes.append("fills on (tom/snare fills)")
        elif name == "hard hits per minute":
            ov["impact"] = True
            changes.append("impact hits on")
        elif name == "ending":
            if "fade" in str(cv).lower():
                state["plan"] = [[p[0] for p in state["plan"]]] and [list(p) for p in state["plan"]]
                state["plan"][-1][0] = "outro"
            changes.append(f"ending shape -> {state['plan']}")
    # keep at most a handful of changes per round so the log stays readable
    changes = [c for c in changes if c]
    if len(changes) > 4:
        changes = changes[:4]
    return changes


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--reference", required=True, help="reference audio or a saved dna.json")
    ap.add_argument("--out", default="adapted.wav")
    ap.add_argument("--genre")
    ap.add_argument("--state", choices=sorted(STATES), help="preset (lobby / tension / chase / lms)")
    ap.add_argument("--bpm", type=float)
    ap.add_argument("--key")
    ap.add_argument("--scale")
    ap.add_argument("--bars", type=int)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--rounds", type=int, default=5)
    ap.add_argument("--override", help="extra JSON merged into the genre spec (string or file)")
    ap.add_argument("--work", help="folder for the round files (default: <out>_work)")
    ap.add_argument("--fast", action="store_true", help="skip the deep (section/hard-point) analysis of each candidate")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if not os.path.exists(a.reference):
        raise SystemExit(f"adapt: no such reference: {a.reference}")
    outdir = a.work or (os.path.splitext(a.out)[0] + "_work")
    os.makedirs(outdir, exist_ok=True)
    ref, ref_name = load_reference(a.reference)
    state = initial_state(ref, a)
    log = dict(schema="audio-forge/adapt@1", reference=os.path.abspath(a.reference), reference_name=ref_name,
               genre=state["genre"], state=a.state, rounds=[], start=dict(bpm=state["bpm"], key=state["key"], scale=state["scale"],
               bars=state["bars"], intensity=state["intensity"], plan=state["plan"], override=state["override"]))
    best = None
    stale = 0
    for rnd in range(1, max(1, a.rounds) + 1):
        wav = os.path.join(outdir, f"round{rnd}.wav")
        s, audio = render(state, wav, outdir)
        cand = candidate_dna(wav, with_deep=not a.fast)
        rows = CMP.rows(ref, cand)
        sc = score_rows(rows)
        off = [r[0] for r in rows if r[4] == "OFF"]
        changes = []
        if off and rnd < a.rounds:
            changes = adjust(state, ref, cand, rows)
        rec = dict(round=rnd, file=wav, score=sc, off=off,
                   rows=[dict(measure=r[0], reference=r[1], candidate=r[2], diff=r[3], verdict=r[4], knob=r[5]) for r in rows],
                   changes=changes, state=dict(bpm=state["bpm"], key=state["key"], scale=state["scale"], bars=state["bars"],
                                               intensity=state["intensity"], plan=state["plan"], override=state["override"]))
        log["rounds"].append(rec)
        print(f"round {rnd}: closeness {sc}/100, {len(off)} OFF" + (f" ({', '.join(off)})" if off else "") +
              (f" | changed: {'; '.join(changes)}" if changes else ""), flush=True)
        if best is None or sc > best[0]:
            best = (sc, wav, rnd); stale = 0
        else:
            stale += 1
        if not off or not changes or stale >= 2:
            if stale >= 2:
                print("  (no improvement for two rounds: stopping early, keeping the best round)", flush=True)
            break
    shutil.copyfile(best[1], a.out)
    log["best"] = dict(round=best[2], score=best[0], file=os.path.abspath(a.out))
    log["final_state"] = log["rounds"][-1]["state"]
    json.dump(log, open(os.path.join(outdir, "adapt-log.json"), "w"), indent=1)
    L = ["# Adapt log", "", f"Reference: {ref_name} | genre: {state['genre']}" + (f" | state: {a.state}" if a.state else ""), "",
         f"Best: round {best[2]}, closeness {best[0]}/100 -> {os.path.abspath(a.out)}", "",
         "| round | closeness | OFF measures | changes |", "|---|---|---|---|"]
    for r in log["rounds"]:
        L.append(f"| {r['round']} | {r['score']}/100 | {', '.join(r['off']) or 'none'} | {'; '.join(r['changes']) or '-'} |")
    L += ["", "## Final knobs", "```json", json.dumps(log["final_state"], indent=1), "```", "",
          "Closeness is a heuristic from measurements, not hearing. Nobody has listened to the result: the person's ears decide."]
    open(os.path.join(outdir, "adapt-log.md"), "w").write("\n".join(L) + "\n")
    if a.json:
        print(json.dumps(dict(best=log["best"], rounds=[dict(round=r["round"], score=r["score"], off=r["off"], changes=r["changes"]) for r in log["rounds"]],
                              log=os.path.join(outdir, "adapt-log.json")), indent=1))
    else:
        print("\n".join(L))
    return 0


if __name__ == "__main__":
    sys.exit(main())

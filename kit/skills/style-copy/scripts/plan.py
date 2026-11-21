#!/usr/bin/env python3
"""plan.py - turn a studied style (one track or a blended family) into a BAR-BY-BAR build plan.

  copy.py plan NAME [--bars 64] [--bpm 178]        (or: plan.py STYLE_DIR --bars 64)

Writes <style dir>/plan.md and plan.json: sections scaled to your bar count, energy targets, the layers that enter/leave at each boundary, and the hard points
(riser, cut, impact, bass entry, hits) placed at the SAME PERCENT positions as in the reference, plus a ready `af.py compose --plan` string.
Positions are style (proportions and anatomy). Nothing here is a note, melody or lyric of the reference."""
import argparse, json, math, os

NAME = {"intro": "intro", "build": "build", "drop": "drop", "break": "break_", "outro": "outro", "verse": "verse"}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter); ap.add_argument("style_dir"); ap.add_argument("--bars", type=int, default=64); ap.add_argument("--bpm", type=float); ap.add_argument("--out")
    a = ap.parse_args(); dna = json.load(open(os.path.join(a.style_dir, "dna.json"))); dp = dna.get("deep")
    if not dp: raise SystemExit("this style has no deep data (study it again with the current kit: copy.py study REF)")
    bpm = a.bpm or dp["tempo_feel"]["feel_bpm"]; bar_s = 240.0 / bpm; N = a.bars; dur = N * bar_s; secs = dp["form"]["sections"]; tot = sum(q["pct"] for q in secs) or 100.0
    # scale sections to N bars (largest remainder so they sum exactly)
    raw = [q["pct"] / tot * N for q in secs]; base = [max(1, int(math.floor(r))) for r in raw]
    while sum(base) > N: base[base.index(max(base))] -= 1
    order = sorted(range(len(raw)), key=lambda i: -(raw[i] - math.floor(raw[i])))
    k = 0
    while sum(base) < N: base[order[k % len(order)]] += 1; k += 1
    rows = []; pos = 1
    for q, n in zip(secs, base):
        lm = next((m for m in dp["layer_moves"] if m["bar"] == q.get("start_bar")), None)
        rows.append(dict(label=q["label"], compose=NAME.get(q["label"], "verse"), start_bar=pos, bars=n, energy_rel_db=q["energy_rel_db"], form=q["form"], layers=(lm["moves"] if lm else []))); pos += n
    ev = []; hp = dp["hard_points"]
    for d in hp["drops"]:
        b = max(1, min(N, int(round(d["pct"] / 100 * N)) + 1)); parts = []
        if d["has_riser"]: parts.append(f"riser over bars {max(1, b - 2)}-{b - 1} (high bands up about +{next((r['rise_db'] for r in hp['risers'] if abs(r['pct'] - d['pct']) < 8), 15):.0f} dB)")
        if d["has_cut"]: parts.append("hard cut (silence ~0.1-0.3 s) right before the downbeat")
        if d["impact"]: parts.append(f"{d['impact']} ON the downbeat of bar {b}")
        parts.append(f"bass/sub entry about {d['bass_jump_db']:+.0f} dB")
        ev.append(dict(bar=b, kind="DROP", detail="; ".join(parts), reference_anatomy=d["anatomy"]))
    for r in hp["risers"]:
        b = max(1, min(N, int(round(r["pct"] / 100 * N)) + 1)); 
        if not any(abs(e["bar"] - b) <= 2 for e in ev): ev.append(dict(bar=b, kind="riser", detail=f"high-band sweep about {r['dur_s']} s, +{r['rise_db']:.0f} dB"))
    for s_ in hp["stops"]:
        b = max(1, min(N, int(round(s_["pct"] / 100 * N)) + 1))
        if not any(abs(e["bar"] - b) <= 1 and e["kind"] == "DROP" for e in ev): ev.append(dict(bar=b, kind="stop", detail=f"cut of {s_['dur_s']} s" + (f", then {s_['then']}" if s_["then"] else "")))
    for q in hp.get("breakdowns", []):
        b = max(1, min(N, int(round(q["pct"] / 100 * N)) + 1)); ev.append(dict(bar=b, kind="breakdown", detail=f"strip back for about {max(2, min(q['bars'], N // 6))} bars: energy about {q['depth_db']:.0f} dB under the sections around it, bass about {q['bass_drop_db']:.0f} dB down" + ("; it leads into a drop" if q["leads_into_drop"] else "")))
    for q in hp.get("builds", []):
        b = max(1, min(N, int(round(q["pct"] / 100 * N)) + 1)); ev.append(dict(bar=b, kind="build", detail=f"{max(2, min(q['bars'], 4))}-bar build before the drop: denser drum hits (about {q['onset_density_rise']:+.1f} per beat) and a slowly rising level"))
    for q in hp.get("tone_shifts", []):
        b = max(1, min(N, int(round(q["pct"] / 100 * N)) + 1)); ev.append(dict(bar=b, kind="tone_shift", detail=f"texture/timbre shift: {q.get('detail', 'spectrum shifts')}"))
    for q in hp.get("fill_dips", []):
        b = max(1, min(N, int(round(q["pct"] / 100 * N)) + 1)); ev.append(dict(bar=b, kind="fill", detail=f"short drum fill / dip before impact: {q.get('detail', 'level dips')}"))
    for q in hp.get("chroma_changes", []):
        b = max(1, min(N, int(round(q["pct"] / 100 * N)) + 1)); ev.append(dict(bar=b, kind="harmonic_shift", detail=f"harmonic shift: {q.get('detail', 'chord voicing changes')}"))
    if hp.get("tail"):
        q = hp["tail"]; ev.append(dict(bar=max(1, N - max(1, round(q["tail_s"] / bar_s))), kind="end", detail=f"{q['kind']}: last full-level music, then about {q['tail_s']} s of tail. For a LOOP, do not copy this ending; make the last bar lead back into bar 1."))
    ev.sort(key=lambda e: e["bar"]); hits_total = round(hp["hits_per_min"] * dur / 60.0)
    plan_arg = json.dumps([[r["compose"], round(r["bars"] / N, 3)] for r in rows]); key = f"{dna['key']['tonic']} {dna['key']['mode']}"
    out = dict(style=dna.get("name"), bpm=round(bpm, 1), key=key, bars=N, seconds=round(dur, 1), sections=rows, events=ev, hard_hits_total=hits_total, compose_plan=plan_arg,
               command=f"python3 af.py compose --genre {str(dna.get('name') or 'style').replace('-', '_')} --bars {N} --bpm {round(bpm)} --plan '{plan_arg}' --out cand.wav")
    od = a.out or a.style_dir; json.dump(out, open(os.path.join(od, "plan.json"), "w"), indent=1)
    L = [f"# Build plan from style `{dna.get('name')}`", "", f"{N} bars at {round(bpm, 1)} BPM = {dur:.0f} s, key {key}. Positions are the reference's PROPORTIONS; section labels are energy heuristics." + (f" Structure comes from the most typical family member `{dna['family']['medoid']}`; the shared habits and ranges are in brief.md." if dna.get("family") else ""), "",
         "| bars | section | energy | layers entering/leaving |", "|---|---|---|---|"] + [f"| {r['start_bar']}-{r['start_bar'] + r['bars'] - 1} | {r['label']} ({r['compose']}) | {r['energy_rel_db']} dB | {', '.join(r['layers']) or '-'} |" for r in rows]
    L += ["", "## Hard points to place (bar numbers in YOUR track)"] + [f"- bar {e['bar']}: **{e['kind']}**: {e['detail']}" for e in ev] + [f"- about {hits_total} other hard accents/hits across the track (the reference had {hp['hits_per_min']} per minute); put them on bar lines or the 16th grid ({int(round((hp['hits_on_16th_grid_share'] or 0) * 100))}% of the reference's did)",
         "", "## Compose it", f"`{out['command']}`", "", "Then: `af.py deep cand.wav` to see YOUR hard points and loop check, and `af.py compare cand.wav <style dir>/dna.json` to compare with the reference numbers. Say plainly that nobody has listened."]
    open(os.path.join(od, "plan.md"), "w").write("\n".join(L) + "\n"); print("\n".join(L))


if __name__ == "__main__":
    main()

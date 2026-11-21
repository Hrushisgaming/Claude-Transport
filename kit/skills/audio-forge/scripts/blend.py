#!/usr/bin/env python3
"""blend.py - turn SEVERAL studied tracks into one style FAMILY: what they all share, what varies, and ranges to stay inside.

  af.py blend styles/a styles/b styles/c --name lms-family [--out styles/lms-family]

Each input is a folder with dna.json (from `af.py study` / `copy.py study`). Output folder:
  dna.json      the family as a normal dna (every number = the MEDIAN of the members) plus  family{members, ranges, consensus, tempo_clusters, key_votes}
                so `af.py compare cand.wav styles/lms-family/dna.json` works unchanged and judges 'inside the range' instead of 'equal to one track'
  brief.md      what all members do (copy this), what varies (free choice), ranges, then the usual measured brief
  genre.json    draft genre from the median

One reference teaches one sound; several references teach a STYLE: the shared habits are the style, the differences are your room to be original.
Only measurements are blended; no notes, melodies or lyrics exist in the inputs.
"""
import argparse, copy, json, os, sys
from collections import Counter
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import study as S

SKIP = ("seconds",)


def leaves(o, path=()):
    if isinstance(o, dict):
        for k, v in o.items(): yield from leaves(v, path + (k,))
    elif isinstance(o, bool): return
    elif isinstance(o, (int, float)): yield path, float(o)
    elif isinstance(o, list) and o and all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in o): yield path, [float(x) for x in o]


def get(o, path):
    for k in path:
        if not isinstance(o, dict) or k not in o: return None
        o = o[k]
    return o


def setp(o, path, v):
    for k in path[:-1]: o = o[k]
    o[path[-1]] = v


def medoid(dnas, flat):
    keys = [k for k in flat[0] if all(k in f and not isinstance(f[k], list) for f in flat) and k[-1] not in SKIP]
    M = np.array([[f[k] for k in keys] for f in flat]); sd = M.std(0) + 1e-9; Z = (M - np.median(M, 0)) / sd
    return int(np.argmin(np.abs(Z).sum(1)))


def cluster_tempo(vals, tol=0.08):
    cl = []
    for v in sorted(vals):
        if cl and abs(v - np.mean(cl[-1])) / np.mean(cl[-1]) <= tol: cl[-1].append(v)
        else: cl.append([v])
    return [dict(bpm=round(float(np.median(c)), 1), members=len(c), range=[round(min(c), 1), round(max(c), 1)]) for c in sorted(cl, key=len, reverse=True)]


def blend(paths, name):
    dnas = [json.load(open(os.path.join(p, "dna.json") if os.path.isdir(p) else p)) for p in paths]
    if any(d.get("kind") != "audio" for d in dnas): sys.exit("blend works on audio styles only")
    flat = [dict(leaves(d)) for d in dnas]; mi = medoid(dnas, flat); fam = copy.deepcopy(dnas[mi]); ranges = {}
    for path in flat[mi]:
        if path[-1] in SKIP: continue
        vs = [f[path] for f in flat if path in f]
        if len(vs) < 2: continue
        if isinstance(vs[0], list):
            if len({len(v) for v in vs}) != 1: continue
            arr = np.array(vs); med = np.median(arr, 0).tolist(); setp(fam, path, [round(x, 3) for x in med]); continue
        a = np.array(vs); setp(fam, path, round(float(np.median(a)), 3) if not float(vs[0]).is_integer() or any(not float(v).is_integer() for v in vs) else int(np.median(a)))
        ranges[".".join(path)] = [round(float(a.min()), 3), round(float(np.median(a)), 3), round(float(a.max()), 3)]
    # tempo: use the FEEL tempo when known (octave-resolved), cluster it
    feel = [d["deep"]["tempo_feel"]["feel_bpm"] if d.get("deep") else d["tempo"]["bpm"] for d in dnas]; clusters = cluster_tempo(feel)
    fam["tempo"]["bpm"] = clusters[0]["bpm"]; fam["tempo"]["ambiguous"] = False; fam["tempo"]["alt_octaves"] = [round(clusters[0]["bpm"] * 2, 1), round(clusters[0]["bpm"] / 2, 1)]
    votes = Counter(f"{d['key']['tonic']} {d['key']['mode']}" for d in dnas); fam["key"] = dict(tonic=votes.most_common(1)[0][0].split()[0], mode=votes.most_common(1)[0][0].split()[1], relative=fam["key"].get("relative"))
    cons = dict(members_with_drop=0)
    deeps = [d["deep"] for d in dnas if d.get("deep")]
    if deeps:
        with_drop = [x for x in deeps if x["hard_points"]["drops"]]; cons["members_with_drop"] = len(with_drop)
        if with_drop:
            allp = [p for x in with_drop for p in x["hard_points"]["drops"]]; cons["first_drop_pct"] = [round(float(v), 1) for v in (min(x["hard_points"]["drops"][0]["pct"] for x in with_drop), np.median([x["hard_points"]["drops"][0]["pct"] for x in with_drop]), max(x["hard_points"]["drops"][0]["pct"] for x in with_drop))]
            cons["drop_has_cut_share"] = round(float(np.mean([p["has_cut"] for p in allp])), 2); cons["drop_has_riser_share"] = round(float(np.mean([p["has_riser"] for p in allp])), 2)
            cons["drop_has_impact_share"] = round(float(np.mean([p["impact"] is not None for p in allp])), 2); cons["drops_per_track"] = [min(len(x["hard_points"]["drops"]) for x in deeps), max(len(x["hard_points"]["drops"]) for x in deeps)]
        share = {}
        for x in deeps:                                           # one value per TRACK: the total share of each label in that track
            tot_ = {}
            for sct in x["form"]["sections"]: tot_[sct["label"]] = tot_.get(sct["label"], 0.0) + sct["pct"]
            for lab_, v_ in tot_.items(): share.setdefault(lab_, []).append(v_)
        cons["section_pct_median"] = {k: dict(median_pct=round(float(np.median(v)), 1), in_tracks=len(v)) for k, v in share.items()}
        cons["tracks_starting_hot"] = sum(1 for x in deeps if x["hard_points"]["starts_hot"]); cons["chord_cycles_bars"] = sorted(x["form"]["chord_cycle_bars"] for x in deeps if x["form"]["chord_cycle_bars"])
        lm = Counter(tok.split()[0] for x in deeps for m in x["layer_moves"] if m["section"] == "drop" for tok in m["moves"]); cons["layers_entering_at_drops"] = {k: v for k, v in lm.most_common(8)}
        cons["loop_ready_tracks"] = sum(1 for x in deeps if x["loop"]["loop_ready"]); cons["roles"] = dict(Counter(x["role_guess"]["role"] for x in deeps))
        cons["hits_per_min"] = [round(min(x["hard_points"]["hits_per_min"] for x in deeps), 1), round(max(x["hard_points"]["hits_per_min"] for x in deeps), 1)]
        # a family 'deep' block that compare.py can use: median drop position, medians of rates; keep medoid structure for the lists
        fam["deep"]["hard_points"]["hits_per_min"] = round(float(np.median([x["hard_points"]["hits_per_min"] for x in deeps])), 1); fam["deep"]["hard_points"]["stops_per_min"] = round(float(np.median([x["hard_points"]["stops_per_min"] for x in deeps])), 1)
        fam["deep"]["tempo_feel"]["feel_bpm"] = clusters[0]["bpm"]
    fam["name"] = name; fam["schema"] = "style-copy/audio-dna@2"; fam["seconds"] = round(float(np.median([d["seconds"] for d in dnas])), 1)
    fam["family"] = dict(members=[d.get("name") for d in dnas], medoid=dnas[mi].get("name"), ranges=ranges, consensus=cons, tempo_clusters=clusters, key_votes=dict(votes),
                         note="every number is the MEDIAN of the members; ranges give [min, median, max]. Lists inside deep (drops, sections) come from the member closest to the median.")
    return fam, dnas


def family_brief(fam, name):
    f = fam["family"]; c = f["consensus"]; L = [f"# Style family: {name}", "", f"Members ({len(f['members'])}): " + ", ".join(f["members"]) + f". Most typical member: **{f['medoid']}**.", "",
         "## What they ALL share (this is the style: copy it)",
         f"- Tempo clusters (feel BPM): " + "; ".join(f"{t['bpm']} BPM x{t['members']} (range {t['range'][0]}-{t['range'][1]})" for t in f["tempo_clusters"]) + ". Pick one cluster; do not average clusters.",
         f"- Key votes: {f['key_votes']}."]
    if c.get("first_drop_pct"): L.append(f"- First drop at {c['first_drop_pct'][1]}% of the track (range {c['first_drop_pct'][0]}-{c['first_drop_pct'][2]}%); {c['members_with_drop']} of {len(f['members'])} have a clear drop; drops per track {c['drops_per_track'][0]}-{c['drops_per_track'][1]}.")
    if "drop_has_impact_share" in c: L.append(f"- Anatomy of a drop: impact on it in {int(c['drop_has_impact_share'] * 100)}%, a cut right before in {int(c['drop_has_cut_share'] * 100)}%, a riser before in {int(c['drop_has_riser_share'] * 100)}% of drops.")
    if c.get("layers_entering_at_drops"): L.append(f"- Layers that enter at drops (count of drops): {c['layers_entering_at_drops']}.")
    if c.get("section_pct_median"): L.append("- Typical share of the track (median %, in how many tracks that section exists): " + ", ".join(f"{k} {v['median_pct']}% ({v['in_tracks']}/{len(f['members'])})" for k, v in c["section_pct_median"].items()) + ". Section labels are energy heuristics.")
    if c.get("chord_cycles_bars"): L.append(f"- Chord cycles seen (bars): {c['chord_cycles_bars']}.")
    L += ["", "## What VARIES (your room to be original)", "| measure | min | median | max |", "|---|---|---|---|"]
    show = ["mix.lufs", "mix.crest_db", "mix.side_to_mid_db", "timbre.centroid_hz", "timbre.flatness", "rhythm.onsets_per_beat", "deep.hard_points.hits_per_min", "deep.hard_points.stops_per_min", "deep.lead_layer.share_of_bars"]
    for k in show:
        if k in f["ranges"]: L.append(f"| {k} | {f['ranges'][k][0]} | {f['ranges'][k][1]} | {f['ranges'][k][2]} |")
    L += ["", f"Loop-ready members: {c.get('loop_ready_tracks', '?')} of {len(f['members'])} (finished rips rarely are; yours must be). Role guesses: {c.get('roles')}.",
          "", "Compare your build with `af.py compare cand.wav <this folder>/dna.json`: a number INSIDE the member range is fine, you do not have to hit the median.", "", "---", "", "# Median measurements (same format as a single-track brief)", ""]
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("styles", nargs="+"); ap.add_argument("--name", required=True); ap.add_argument("--out")
    a = ap.parse_args(); out = a.out or os.path.join("styles", a.name); os.makedirs(out, exist_ok=True)
    fam, dnas = blend(a.styles, a.name); json.dump(fam, open(os.path.join(out, "dna.json"), "w"), indent=1)
    json.dump(S.draft_genre(fam, a.name.replace("-", "_")), open(os.path.join(out, "genre.json"), "w"), indent=1)
    open(os.path.join(out, "brief.md"), "w").write(family_brief(fam, a.name) + S.brief_md(fam, a.name))
    print(open(os.path.join(out, "brief.md")).read()[:6000]); print(f"[wrote {out}/dna.json, brief.md, genre.json from {len(dnas)} tracks]", file=sys.stderr)


if __name__ == "__main__":
    main()

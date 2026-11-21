#!/usr/bin/env python3
"""at.py - what is happening around a time? (bar map slice + events), so you can settle an 'AI says X at 0:36' question without opening a DAW.

  af.py at deep.json 36            bars around 0:36 (+-3 bars) with every band, and the events inside them
  af.py at deep.json 36 --bars 6
"""
import argparse, json
ap = argparse.ArgumentParser(); ap.add_argument("deep_json"); ap.add_argument("t", type=float); ap.add_argument("--bars", type=int, default=3); a = ap.parse_args()
d = json.load(open(a.deep_json)); rows = d["bars"]; i = max(range(len(rows)), key=lambda k: -abs(rows[k]["t"] - a.t) if rows[k]["t"] <= a.t else -1e9)
print(f"{'bar':>4} {'time':>7} {'total':>6} {'sub':>5} {'bass':>5} {'mid':>5} {'hmid':>5} {'air':>5} {'cent':>5} {'ons/beat':>8}")
for r in rows[max(0, i - a.bars):i + a.bars + 1]:
    print(f"{r['bar']:>4} {r['t']:>7.2f} {r['total_db']:>6.1f} {r['sub']:>5.1f} {r['bass']:>5.1f} {r['mid']:>5.1f} {r['highmid']:>5.1f} {r['air']:>5.1f} {r['centroid_hz']:>5} {r['onsets_per_beat']:>8}" + ("   <--" if r is rows[i] else ""))
hp = d["hard_points"]; lo, hi = rows[max(0, i - a.bars)]["t"], rows[min(len(rows) - 1, i + a.bars)]["t"] + d["grid"]["bar_s"]
for k in ("hits", "stops", "risers", "drops", "breakdowns", "builds"):
    for q in hp.get(k, []):
        if lo <= q["t"] <= hi: print(f"  {k[:-1]} at {q['t']} s (bar {q['bar']})")
if hp.get("tail") and lo <= hp["tail"]["t_cut"] <= hi: print(f"  end cut at {hp['tail']['t_cut']} s")

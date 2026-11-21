#!/usr/bin/env python3
"""recipe_test.py -- variation by default, locks honoured, no forbidden chords, same seed reproduces. Run: python3 recipe_test.py"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
from forge import recipe as R  # noqa: E402
fails = []
def check(ok, msg):
    print(("PASS " if ok else "FAIL ") + msg)
    if not ok: fails.append(msg)
rs = [R.make_recipe("hunted", seed=s, avoid_history=False) for s in range(60)]
check(len({str(R.signature(r)) for r in rs}) >= 58, "60 seeds give (almost) 60 different recipes")
check(len({r["key"] for r in rs}) >= 8, "many keys used: %d" % len({r["key"] for r in rs}))
check(len({r["ending"] for r in rs}) == 4, "all four endings appear")
bad = [c for r in rs for c in r["cycle_a"] + r["cycle_b"] if c in R.MOODS["hunted"]["forbidden_chords"]]
check(not bad, "no forbidden (major/heroic) chords in any cycle")
l = R.make_recipe("hunted", seed=3, locks=R.parse_locks("key=D,bpm=176,ending=static_crash,drums=dnb,clock_on=1"), avoid_history=False)
check(l["key"] == 5 and l["bpm"] == 176 and l["ending"] == "static_crash" and l["drums_a"] == "dnb" and l["clock_on"] is True, "locks honoured")
check(R.make_recipe("hunted", seed=9, avoid_history=False) == R.make_recipe("hunted", seed=9, avoid_history=False), "same seed reproduces the recipe")
u = [R.make_recipe("hunted", seed=None, avoid_history=False)["seed"] for _ in range(5)]
check(len(set(u)) == 5, "no seed = fresh random each time")
print("\nALL PASS" if not fails else "\n%d FAILED" % len(fails)); sys.exit(1 if fails else 0)

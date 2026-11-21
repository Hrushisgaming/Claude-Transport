#!/usr/bin/env python3
"""huntfight_smoke_test.py -- builds (does not render) 12 random recipes through the full composer: catches crashes in every option combination
(leads, pads, riffs, bell patterns, optional organ/brass, all structure lengths, lifts). Run: python3 huntfight_smoke_test.py"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import huntfight as H  # noqa: E402
from forge import recipe as RC  # noqa: E402
fails = 0
seen = set()
for sd in range(12):
    R = RC.make_recipe("hunted", seed=sd, avoid_history=False)
    try:
        S = H.build(R)
        n = len(S.events); ok = n > 800
        seen |= {R["lead"], R["pads"], R["riff_a"], R["riff_c"], R["ending"], "organ" if R["organ_low"] else "", "brass" if R["brass_low"] else ""}
        print(("PASS" if ok else "FAIL"), "seed", sd, "events", n, R["lead"], R["pads"], R["riff_a"] + "/" + R["riff_c"], R["ending"])
        fails += not ok
    except Exception as e:
        print("FAIL seed", sd, repr(e)[:120]); fails += 1
print("option values exercised:", len(seen - {""}))
print("\nALL PASS" if not fails else "\n%d FAILED" % fails); sys.exit(1 if fails else 0)

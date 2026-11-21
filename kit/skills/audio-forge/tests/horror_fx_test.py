#!/usr/bin/env python3
"""horror_fx_test.py -- objective checks for forge/horror_fx.py (crawl pans left<->right, tape_stop slows and ends silent, blunt_hit is short and loud)."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
from forge import horror_fx as H  # noqa: E402
from forge.dsp import SR  # noqa: E402
fails = []
def check(ok, msg):
    print(("PASS " if ok else "FAIL ") + msg)
    if not ok: fails.append(msg)
c = H.crawl(4.0, SR, seed=3); seg = len(c) // 8
bal = [np.sqrt((c[i * seg:(i + 1) * seg, 0] ** 2).mean()) - np.sqrt((c[i * seg:(i + 1) * seg, 1] ** 2).mean()) for i in range(8)]
check(c.ndim == 2 and np.isfinite(c).all(), "crawl: stereo and finite")
check(max(bal) > 0.005 and min(bal) < -0.005, "crawl: pans to both sides over time (%.3f .. %.3f)" % (min(bal), max(bal)))
x = np.sin(2 * np.pi * 440 * np.arange(SR * 4) / SR)[:, None].repeat(2, 1) * 0.5
t = H.tape_stop(x, SR, 2.0, 1.2)
y = t[int(2.0 * SR):int(2.2 * SR), 0]; z = t[int(3.1 * SR):int(3.2 * SR), 0]
zc = lambda v: np.count_nonzero(np.diff(np.signbit(v)))
check(zc(t[int(3.0 * SR):int(3.2 * SR), 0]) < zc(y) * 0.5, "tape_stop: pitch falls (zero crossings %d -> %d)" % (zc(y), zc(t[int(3.0 * SR):int(3.2 * SR), 0])))
check(np.abs(z).max() < 0.05, "tape_stop: ends near silent")
h = H.shout_ha(); check(h.shape[0] < SR and np.abs(h).max() > 0.5, "shout_ha: short and loud")
b = H.blunt_hit(); check(b.shape[0] < 0.5 * SR and abs(b[-1]).max() < 0.05 and np.abs(b).max() > 0.5, "blunt_hit: short, loud, ends cut")
print("\nALL PASS" if not fails else "\n%d FAILED" % len(fails)); sys.exit(1 if fails else 0)

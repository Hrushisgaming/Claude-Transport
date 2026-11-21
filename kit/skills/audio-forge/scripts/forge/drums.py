"""drums.py -- synthesised drum hits. Each returns a mono array. Kits: 808 acoustic chip industrial.

V2 (2026-11-19): tight sub-sweep kicks with a separate click transient, layered
185 Hz snares, metallic hats, and a breakbeat / Amen-style pattern generator
(ghost snares, rolls, syncopated rides) for dnb / horror_chase / metal.
"""
import numpy as np
from . import dsp
from .dsp import SR


def kick(kind="808", length=0.35, sr=SR, pitch=48.0, punch=1.0):
    """Tight sub sweep + a punchy click transient (no samples)."""
    n = max(2, int(length * sr))
    t = np.arange(n) / sr
    if kind == "chip":
        f = pitch * 2.4 * np.exp(-t * 46) + pitch
        body = dsp.osc("tri", f, n, sr) * np.exp(-t * 14.0)
        click = dsp.osc("sine", 2200, n, sr) * np.exp(-t * 400.0) * 0.25
        return dsp.distort(body + click, 1.3) * 0.95
    if kind == "industrial":
        f = pitch * 3.6 * np.exp(-t * 60) + pitch * 0.9
        body = np.sin(dsp.TAU * np.cumsum(f) / sr) * np.exp(-t * 8.0)
        click = dsp.bp(np.random.uniform(-1, 1, n), 2200, 7000, sr) * np.exp(-t * 260.0) * 0.65
        tick = dsp.osc("sine", 3400, n, sr) * np.exp(-t * 500.0) * 0.20
        return dsp.distort(body * 1.4 + click + tick, 3.2, "asym") * 0.92
    if kind == "808":
        f = pitch * (1.0 + 3.0 * np.exp(-t * 34.0 * punch)) + pitch * 0.02
        body = np.sin(dsp.TAU * np.cumsum(f) / sr) * np.exp(-t * (4.2 if length > 0.3 else 6.5))
        click = dsp.bp(np.random.uniform(-1, 1, n), 1600, 6500, sr) * np.exp(-t * 380.0) * 0.28
        click += dsp.osc("sine", 3100, n, sr) * np.exp(-t * 520.0) * 0.12
        return dsp.distort(body * 1.15 + click, 1.35) * 0.95
    # acoustic / default punchy kick
    f = pitch * (1.0 + 3.8 * np.exp(-t * 52.0 * punch)) + pitch * 0.03
    body = np.sin(dsp.TAU * np.cumsum(f) / sr) * np.exp(-t * 7.5)
    click = dsp.bp(np.random.uniform(-1, 1, n), 1800, 6200, sr) * np.exp(-t * 330.0) * 0.55
    beater = dsp.osc("sine", 1250, n, sr) * np.exp(-t * 220.0) * 0.22
    return dsp.distort(body + click + beater, 1.5) * 0.95


def snare(kind="808", length=0.3, sr=SR):
    """Multi-layer snare: 185 Hz body + crisp band-pass/HPF noise tail."""
    n = max(2, int(length * sr))
    t = np.arange(n) / sr
    rng = np.random.RandomState(23)
    nz = rng.uniform(-1, 1, n)
    if kind == "chip":
        body = dsp.osc("square", 210, n, sr) * np.exp(-t * 30.0) * 0.35
        noise = dsp.bitcrush(nz, 4) * np.exp(-t * 24.0) * 0.6
        return dsp.distort(body + noise, 1.4) * 0.8
    f_body = 185.0 * (1.0 + 0.45 * np.exp(-t * 55.0))
    body = np.sin(dsp.TAU * np.cumsum(f_body) / sr) * np.exp(-t * 15.0) * 0.55
    body += np.sin(dsp.TAU * 320.0 * t) * np.exp(-t * 26.0) * 0.18
    crack = dsp.bp(nz, 1600, 7500, sr) * np.exp(-t * 18.0) * 0.75
    sizzle = dsp.hp(nz, 8000, sr) * np.exp(-t * 26.0) * 0.35
    y = body + crack + sizzle
    if kind == "industrial":
        y = dsp.distort(y * 1.6, 4.0, "tanh")
    return y


def clap(length=0.28, sr=SR):
    n = int(length * sr)
    nz = dsp.bp(np.random.uniform(-1, 1, n), 900, 3800, sr)
    env = np.zeros(n)
    for off, g in ((0, 1.0), (0.011, 0.8), (0.022, 0.65)):
        o = int(off * sr)
        env[o:] += dsp.decay(n - o, 0.009, sr) * g
    env += dsp.decay(n, 0.10, sr) * 0.55
    return nz * env


def hat(open_=False, length=None, sr=SR, bright=1.0):
    """Metallic 808-style hat: six detuned squares + noise, band-passed."""
    length = length or (0.30 if open_ else 0.055)
    n = max(2, int(length * sr))
    base = [205.3, 304.4, 369.6, 522.7, 540.0, 800.0]
    y = sum(dsp.osc("square", f * bright, n, sr) for f in base) / 6
    y += np.random.uniform(-1, 1, n) * 0.55
    y = dsp.bp(y, 6500 * bright, min(15000.0, 13000 * bright + 2000), sr)
    y += 0.25 * dsp.hp(np.random.uniform(-1, 1, n), 11000, sr)
    return y * np.exp(-np.arange(n) / ((0.11 if open_ else 0.014) * sr))


def ride(length=0.9, sr=SR):
    n = int(length * sr)
    t = np.arange(n) / sr
    y = dsp.hp(np.random.uniform(-1, 1, n), 5200, sr) * 0.40
    for mult, amp in ((1.0, 0.25), (1.47, 0.18), (2.09, 0.12), (2.61, 0.08)):
        y += amp * np.sin(dsp.TAU * 520.0 * mult * t)
    y = dsp.bp(y, 3500, 14000, sr)
    return y * np.exp(-t / 0.38)


def crash(length=2.2, sr=SR):
    n = int(length * sr)
    t = np.arange(n) / sr
    y = dsp.hp(np.random.uniform(-1, 1, n), 3800, sr) * np.exp(-t / 0.75)
    shimmer = sum(np.sin(dsp.TAU * f * t) for f in (1320, 1975, 2630, 3480, 4410)) * 0.04
    return (y + dsp.hp(shimmer, 3000, sr) * np.exp(-t / 1.0)) * 0.75


def tom(freq=110, length=0.4, sr=SR):
    n = int(length * sr)
    t = np.arange(n) / sr
    f = freq * (1 + 0.8 * np.exp(-t * 22))
    y = np.sin(dsp.TAU * np.cumsum(f) / sr) * np.exp(-t * 7.0)
    y += dsp.bp(np.random.uniform(-1, 1, n), 400, 2400, sr) * np.exp(-t * 60.0) * 0.25
    return y


def rim(sr=SR):
    n = int(0.05 * sr)
    return (dsp.osc("sine", 1700, n, sr) + dsp.osc("sine", 520, n, sr)) * 0.5 * dsp.decay(n, 0.008, sr)


def perc(freq=800, sr=SR, length=0.12):
    n = int(length * sr)
    return dsp.fm(freq, n, 1.41, 2.5, sr=sr) * dsp.decay(n, 0.03, sr)


def metal_hit(sr=SR, length=0.5):
    """industrial anvil / pipe hit"""
    n = int(length * sr)
    t = np.arange(n) / sr
    y = sum(dsp.osc("sine", f, n, sr) * a for f, a in [(233, 1), (421, .7), (689, .5), (1071, .4), (1620, .3)])
    y += dsp.hp(np.random.uniform(-1, 1, n), 3000, sr) * np.exp(-t * 90.0) * 2
    return y * dsp.decay(n, 0.18, sr) * 0.4


def impact(length=2.5, sr=SR):
    n = int(length * sr)
    t = np.arange(n) / sr
    sub = np.sin(dsp.TAU * np.cumsum(55 * np.exp(-t * 0.8) + 25) / sr) * dsp.decay(n, 0.9, sr)
    nz = dsp.lp(np.random.uniform(-1, 1, n), 3000, sr) * dsp.decay(n, 0.5, sr)
    crack = dsp.hp(np.random.uniform(-1, 1, n), 2500, sr) * np.exp(-t * 90.0) * 0.7
    return dsp.distort(sub * 0.9 + nz * 0.5 + crack, 1.5) * 0.9


KIT_HITS = {"kick", "snare", "clap", "hat", "ohat", "ride", "crash", "tom", "tom_hi", "tom_lo", "rim", "perc", "metal", "impact"}
_cache = {}


def hit(name, kit="808", vel=1.0):
    """cached drum hit with velocity scaling (also darkens quiet hits)"""
    key = (name, kit)
    if key not in _cache:
        if name == "kick":
            y = kick(kit)
        elif name == "snare":
            y = snare(kit)
        elif name == "clap":
            y = clap()
        elif name == "hat":
            y = hat(False, bright=0.9 if kit == "acoustic" else 1.0)
        elif name == "ohat":
            y = hat(True)
        elif name == "ride":
            y = ride()
        elif name == "crash":
            y = crash()
        elif name == "tom":
            y = tom(110)
        elif name == "tom_hi":
            y = tom(180)
        elif name == "tom_lo":
            y = tom(80)
        elif name == "rim":
            y = rim()
        elif name == "perc":
            y = perc()
        elif name == "metal":
            y = metal_hit()
        elif name == "impact":
            y = impact()
        else:
            raise ValueError(name)
        y = dsp.fade(y, 0.0004, 0.008, SR)
        _cache[key] = y / (np.abs(y).max() + 1e-9)
    return _cache[key] * vel


# ── breakbeat / Amen-style generator ───────────────────────────────────────
# Patterns are a two-bar (32 sixteenth-step) cycle of (step, velocity).
# Ghost notes are low-velocity snares; the generator adds rolls and rides.
_BREAKS = {
    "amen": dict(  # classic shuffle: kick on 1, the 'and' of 2, 3 and the pushed 4
        kick=[(0, 1.0), (3, 0.55), (10, 0.85), (16, 0.95), (19, 0.5), (22, 0.72), (26, 0.9)],
        snare=[(4, 1.0), (12, 1.0), (20, 0.98), (28, 0.95), (7, 0.20), (14, 0.26), (23, 0.18), (30, 0.34), (31, 0.42)],
        hat=[(0, .55), (2, .35), (4, .30), (6, .40), (8, .55), (10, .30), (12, .45), (14, .38),
             (16, .55), (18, .35), (20, .30), (22, .42), (24, .55), (26, .30), (28, .45), (30, .40)],
        ride=[(6, .22), (14, .20), (22, .22), (30, .26)]),
    "dnb": dict(  # two-step with a rolling second bar
        kick=[(0, 1.0), (10, 0.9), (16, 0.95), (22, 0.75), (26, 0.85)],
        snare=[(8, 1.0), (24, 1.0), (11, 0.22), (15, 0.25), (27, 0.28), (30, 0.38), (31, 0.50)],
        hat=[(0, .5), (2, .3), (4, .45), (6, .3), (8, .5), (10, .3), (12, .45), (14, .3),
             (16, .5), (18, .3), (20, .45), (22, .3), (24, .5), (26, .3), (28, .45), (30, .35)],
        ride=[(3, .20), (11, .18), (19, .20), (27, .18)]),
    "horror": dict(  # driving chase: kick doubles, snare on 2/4, tom/ride stabs
        kick=[(0, 1.0), (3, 0.6), (6, 0.85), (10, 0.9), (16, 0.95), (19, 0.55), (22, 0.8), (26, 0.9)],
        snare=[(4, 1.0), (12, 1.0), (20, 1.0), (28, 1.0), (7, 0.25), (15, 0.30), (23, 0.22), (31, 0.55)],
        hat=[(0, .5), (2, .35), (4, .45), (6, .35), (8, .5), (10, .35), (12, .45), (14, .35),
             (16, .5), (18, .35), (20, .45), (22, .35), (24, .5), (26, .35), (28, .45), (30, .45)],
        ride=[(2, .26), (6, .22), (10, .26), (14, .22), (18, .26), (22, .22), (26, .26), (30, .3)]),
    "metal": dict(  # double-kick feel + snare backbeat + fast hats
        kick=[(i, 0.95 if i % 4 == 0 else 0.72) for i in range(0, 32, 2)],
        snare=[(4, 1.0), (12, 1.0), (20, 1.0), (28, 1.0), (7, 0.18), (15, 0.22), (23, 0.18), (31, 0.45)],
        hat=[(i, 0.45 if i % 4 else 0.55) for i in range(0, 32, 2)],
        ride=[(2, .18), (10, .18), (18, .18), (26, .18)]),
}


def breakbeat(bars=1, style="amen", rng=None, intensity=1.0, fill=True):
    """Return [(step, drum_name, velocity), ...] on a 16th grid for `bars` bars.

    Ghost snares, a snare roll at the end of every 4-bar phrase and syncopated
    rides/hats are generated from the two-bar seed patterns above.
    """
    rng = rng or np.random.RandomState(0)
    pat = _BREAKS.get(style, _BREAKS["amen"])
    out = []
    total = int(bars) * 16
    for base in range(0, total, 32):
        for name, evs in pat.items():
            for step, vel in evs:
                if base + step >= total:
                    continue
                v = float(np.clip(vel * (0.75 + 0.25 * intensity) * (0.9 + 0.2 * rng.rand()), 0.05, 1.0))
                out.append((base + step, name, round(v, 3)))
    # phrasing: a short snare/tom roll in the last beat of every 4 bars
    if fill:
        for end in range(64, total + 1, 64):
            for k, i in enumerate(range(12, 16)):
                step = end - 16 + i
                if 0 <= step < total:
                    out.append((step, "snare", round(0.35 + 0.1 * k, 2)))
            if end - 16 + 15 < total:
                out.append((end - 16 + 15, "tom", 0.55))
    # de-duplicate same step/name, keep the louder
    best = {}
    for step, name, vel in out:
        key = (step, name)
        if key not in best or vel > best[key]:
            best[key] = vel
    return sorted((s, n, v) for (s, n), v in best.items())

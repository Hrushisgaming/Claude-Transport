#!/usr/bin/env python3
"""synth.py - the sound kit, synthesised in code (no samples, no third-party audio, free to use).

  synth.py [outdir]     writes the kit as wavs (the mixer also builds these on demand)

get(name, length=None) -> float32 array (n, 2) at 48 kHz.
names: impact boom tick riser whoosh swish heartbeat drone glitch reverse sweepdown subdrop
"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ce_common import write_wav

SR = 48000
rng = np.random.default_rng(7)


def t_(d):  return np.arange(int(d * SR)) / SR
def noise(d):  return rng.standard_normal(int(d * SR)).astype(np.float32)


def onepole(x, fc):
    """one-pole low-pass; fc may be scalar or per-sample array"""
    fc = np.broadcast_to(np.asarray(fc, np.float32), x.shape)
    a = 1 - np.exp(-2 * np.pi * fc / SR); y = np.empty_like(x); s = 0.0
    for i in range(len(x)):
        s += a[i] * (x[i] - s); y[i] = s
    return y


def reverb(x, tail=1.4, wet=0.35):
    n = int(tail * SR); ir = noise(tail) * np.exp(-t_(tail) * 4.2); ir = onepole(ir, 3500)
    L = len(x) + n; X = np.fft.rfft(x, L); H = np.fft.rfft(ir, L)
    y = np.fft.irfft(X * H, L)[:L]; y /= (np.abs(y).max() + 1e-9)
    out = np.zeros(L, np.float32); out[:len(x)] += x * (1 - wet); out += y * wet * np.abs(x).max(); return out


def stereo(x, width=0.0):
    """width 0 = mono; >0 decorrelates the sides with a short delay, keeping the mono sum intact"""
    if not width:
        return np.stack([x, x], 1)
    d = max(1, int((0.004 + 0.009 * min(width, 1.0)) * SR))
    r = np.concatenate([np.zeros(d, np.float32), x[:-d]])
    m, sd = (x + r) * 0.5, (x - r) * 0.5 * float(width)
    return np.stack([m + sd, m - sd], 1).astype(np.float32)


def low_mono(x, hz=130.0):
    """fold everything below `hz` to mono (keeps a club/phone-safe low end)"""
    if x.ndim == 1:
        return x
    a = 1 - np.exp(-2 * np.pi * hz / SR); lo = np.empty_like(x); s0 = 0.0; s1 = 0.0
    for i in range(len(x)):
        s0 += a * (x[i, 0] - s0); s1 += a * (x[i, 1] - s1); lo[i, 0] = s0; lo[i, 1] = s1
    mid = lo.mean(1, keepdims=True)
    return (x - lo + mid).astype(np.float32)


def norm(x, peak=0.9):  return (x / (np.abs(x).max() + 1e-9) * peak).astype(np.float32)


def impact(length=1.9):
    """trailer hit: 30-80 Hz pitch-dropping sub, 180 Hz body, 2-9 kHz crack, short stereo tail"""
    t = t_(length)
    f = 30 + 55 * np.exp(-t * 6) + 8 * np.exp(-t * 40)                  # starts ~93 Hz, settles at 30
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.0)
    thump = np.sin(2 * np.pi * 180 * t) * np.exp(-t * 12) * 0.55
    n = noise(length)
    crack = (onepole(n, 9000) - onepole(n, 1800)) * np.exp(-t * 55) * 1.1
    body = onepole(n, 420) * np.exp(-t * 8) * 0.9
    x = sub * 1.25 + thump + crack + body
    x = np.tanh(x * 1.8) / np.tanh(1.8)
    wet = reverb(x, 1.35, 0.28)[:int(length * SR)]
    out = np.stack([x, x], 1).astype(np.float32) * 0.85 + np.stack([wet, np.roll(wet, 37)], 1) * 0.35
    return low_mono(norm(out.astype(np.float32), 0.96))


def boom(length=0.9):
    t = t_(length); f = 48 + 60 * np.exp(-t * 14)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 4.5) + onepole(noise(length), 300) * np.exp(-t * 18) * 0.6
    return stereo(norm(np.tanh(x * 1.4)), 1)


def tick(length=0.07):
    t = t_(length); x = onepole(noise(length), 7000) * np.exp(-t * 160) + np.sin(2 * np.pi * 1700 * t) * np.exp(-t * 220) * 0.5
    return stereo(norm(x, 0.7))


def subdrop(length=1.6):
    t = t_(length); f = 90 * np.exp(-t * 1.8) + 28
    return stereo(norm(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.5)))


def riser(length=1.2):
    """tension riser: rising saw stack + upward noise sweep, stereo width opens toward the cut"""
    t = t_(length); u = t / length
    pitch = 90 * (2 ** (3.6 * u ** 1.6))                                # 90 Hz -> ~1.1 kHz
    ph = 2 * np.pi * np.cumsum(pitch) / SR
    stack = sum(np.sin(ph * k) / k for k in (1, 2, 3, 4, 5)) * 0.22
    n = noise(length)
    fc = 250 + 8500 * u ** 2
    band = (onepole(n, fc * 1.7) - onepole(n, fc * 0.55)) * 1.4
    env = (u ** 1.7) * (1 - np.exp(-t * 50))
    x = (stack + band) * env
    x[-int(0.012 * SR):] *= np.linspace(1, 0, int(0.012 * SR))
    # build the stereo image from two decorrelated noise tails
    d = int(0.010 * SR); r = np.concatenate([np.zeros(d, np.float32), x[:-d]])
    w = 0.15 + 0.7 * u
    L = x * (1 - 0.25 * w) + r * 0.25 * w
    R = r * (1 - 0.25 * w) + x * 0.25 * w
    return norm(np.stack([L, R], 1).astype(np.float32), 0.82)


def whoosh(length=0.55):
    """pass-by whoosh: band-pass sweep with a left-to-right pan, two independent noise channels"""
    t = t_(length); u = t / length
    env = np.sin(np.pi * u) ** 2
    out = []
    for ch in range(2):
        n = noise(length)
        pan = u if ch == 0 else 1 - u                            # L leads, R trails
        fc = 320 + 5200 * np.sin(np.pi * u) ** 1.4
        band = (onepole(n, fc * 1.8) - onepole(n, fc * 0.5))
        out.append(band * env * (0.35 + 0.65 * pan))
    return norm(np.stack(out, 1).astype(np.float32), 0.85)


def swish(length=0.3):  return whoosh(length)


def sweepdown(length=0.8):
    t = t_(length); u = t / length
    return stereo(norm(onepole(noise(length), 9000 * (1 - u) ** 2 + 200) * (1 - u) ** 1.2, 0.7), 1)


def heartbeat(length=0.9):
    t = t_(length); x = np.zeros_like(t)
    for off, g in ((0.0, 1.0), (0.2, 0.7)):
        tt = np.maximum(t - off, 0) * (t >= off)
        x += np.sin(2 * np.pi * (52 + 30 * np.exp(-tt * 40)) * tt) * np.exp(-tt * 20) * g * (t >= off)
    return stereo(norm(np.tanh(x * 1.5), 0.85))


def drone(length=8.0):
    """seamless loop: integer-cycle sines, slow beating between detuned layers"""
    t = t_(length); x = np.zeros_like(t)
    for f, g in ((55, 1.0), (55.25, 0.8), (82.5, 0.35), (110.125, 0.25), (164.75, 0.12), (220.25, 0.07)):
        x += np.sin(2 * np.pi * f * t) * g
    x *= 0.6 + 0.4 * np.sin(2 * np.pi * (1 / length) * 2 * t)
    return stereo(norm(np.tanh(x), 0.5), 0)


def glitch(length=0.22):
    n = noise(length); step = int(0.012 * SR); x = np.zeros_like(n)
    for i in range(0, len(n), step):
        if rng.random() < 0.6: x[i:i + step] = np.round(n[i:i + step] * 3) / 3 * rng.uniform(0.4, 1)
    return stereo(norm(x * np.exp(-t_(length) * 6), 0.7))


def reverse(length=1.2):
    return impact(length + 0.7)[::-1][:int(length * SR)].copy()


KIT = dict(impact=impact, boom=boom, tick=tick, subdrop=subdrop, riser=riser, whoosh=whoosh, swish=swish,
           sweepdown=sweepdown, heartbeat=heartbeat, drone=drone, glitch=glitch, reverse=reverse)
_cache = {}


def get(name, length=None):
    key = (name, length)
    if key not in _cache:
        _cache[key] = KIT[name](length) if length else KIT[name]()
    return _cache[key]


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else 'sfx'; os.makedirs(out, exist_ok=True)
    for n in KIT:
        x = get(n); write_wav(f'{out}/{n}.wav', x); print(f'{n:10s} {len(x) / SR:5.2f}s peak {np.abs(x).max():.2f}')

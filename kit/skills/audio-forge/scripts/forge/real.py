"""real.py -- physically-motivated instruments (no samples, no downloads).

Replaces the "electronic humming" voices (6-sine piano, 2-op FM bell, static-sine organ, additive guitar) with:
  piano_grand   inharmonic stiff-string partials, 2-3 detuned strings per note (beating), per-partial decay,
                hammer thump + felt noise, velocity-dependent brightness, soundboard resonances
  bell_tubular  church / tubular bell: measured-style inharmonic partial series (hum, prime, tierce, quint, nominal ...),
                each with its own decay, strike click, slow beating from a split mode
  glock         glockenspiel / music-box tine: few bright inharmonic partials, short ring
  organ_drawbar Hammond-style: 9 drawbars, key click, percussion (2nd / 3rd harmonic), tonewheel leakage, Leslie
  organ_church  pipe organ: 8' + 4' + 2' + mixture, chiff and wind noise, slow attack
  guitar_ks     Karplus-Strong plucked string (loop-filter lowpass, pick-position comb, fractional tuning), acoustic body
  guitar_amp    electric: KS string -> pre-EQ -> 3 gain stages of asymmetric clipping -> cab (HP, mid hump, 4-5 kHz roll-off)
Every function returns a mono float array including its release tail, like instruments.py.
"""
import numpy as np
from scipy.signal import lfilter
from . import dsp
from .dsp import SR, TAU


def _rng(f, salt=0):
    return np.random.RandomState((int(f * 13) + salt * 7919) % 100003)


def _pitch_inharm(f):
    """stiff-string inharmonicity B grows with pitch (bass strings are long, treble short and stiff)"""
    m = 12 * np.log2(max(f, 20.0) / 440.0) + 69
    return float(np.clip(0.00008 * np.exp(0.055 * (m - 40)), 0.00006, 0.012))


def piano_grand(f, dur, sr=SR, vel=0.8, **kw):
    rel = 0.35
    n = int((dur + rel + 1.2) * sr)
    t = np.arange(n) / sr
    B = _pitch_inharm(f)
    kmax = int(min(32, (sr * 0.42) / f))
    v = float(np.clip(kw.get("vel", vel), 0.2, 1.0))
    bright = 0.35 + 0.65 * v
    # note-dependent sustain: low notes ring long, high notes die fast
    m = 12 * np.log2(f / 440.0) + 69
    base_tau = float(np.clip(7.5 * np.exp(-0.028 * (m - 36)), 0.5, 7.5))
    y = np.zeros(n)
    detunes = [0.0, 0.00055, -0.0007] if m > 42 else [0.0, 0.0004]  # unison strings: slightly detuned -> beating, chorus-like warmth
    rs = _rng(f)
    for k in range(1, kmax + 1):
        fk = k * f * np.sqrt(1 + B * k * k)
        if fk > sr * 0.45:
            break
        # hammer strikes at ~1/8 of the string: partials near multiples of 8 are weak
        hammer = abs(np.sin(np.pi * k / 8.0)) * 0.85 + 0.15
        amp = hammer / (k ** (1.3 - 0.5 * bright)) * (1.0 if k < 14 else 0.6)
        # two-stage decay: prompt sound fast, after-sound slow; higher partials die faster
        tau_f = base_tau / (1 + 0.55 * (k - 1) ** 0.85)
        tau_s = tau_f * 3.2
        env = 0.72 * np.exp(-t / tau_f) + 0.28 * np.exp(-t / tau_s)
        for d in detunes:
            y += (amp / len(detunes)) * np.sin(TAU * fk * (1 + d) * t + rs.uniform(0, TAU)) * env
    # hammer: short band-limited thump + felt noise (louder with velocity)
    nb = int(0.045 * sr)
    noise = rs.uniform(-1, 1, nb)
    thump = dsp.bp(noise, 60, min(900, f * 3), sr) * np.exp(-np.arange(nb) / (0.012 * sr)) * 0.7
    tick = dsp.bp(noise, 1500, 7000, sr) * np.exp(-np.arange(nb) / (0.004 * sr)) * 0.35 * v
    y[:nb] += (thump + tick)[: n]
    # soundboard / cabinet body: gentle resonances
    y = dsp.peak_eq(y, 180, 2.5, 1.0, sr)
    y = dsp.peak_eq(y, 2200, 1.5, 0.9, sr)
    y = dsp.lp(y, 3200 + 6500 * v, sr)
    # key release (damper) after dur
    nd = int(dur * sr)
    rel_env = np.ones(n)
    k0 = min(nd, n - 1)
    rel_env[k0:] = np.exp(-np.arange(n - k0) / (0.09 * sr)) if dur < 6 else 1.0
    y = y * rel_env * np.minimum(t / 0.0012, 1.0)
    return y * 0.55


# church / tubular bell partial ratios (relative to the strike note), amplitude, decay seconds
_BELL = [(0.5, 0.55, 5.5), (1.0, 1.0, 4.2), (1.183, 0.75, 3.4), (1.506, 0.6, 3.0), (2.0, 0.65, 2.6),
         (2.514, 0.5, 2.0), (2.662, 0.35, 1.8), (3.011, 0.4, 1.5), (4.166, 0.3, 1.1), (5.433, 0.22, 0.8), (6.796, 0.15, 0.6)]


def bell_tubular(f, dur, sr=SR, vel=0.8, ring=1.0, **kw):
    n = int((max(dur, 0.5) + 4.5 * ring) * sr)
    t = np.arange(n) / sr
    rs = _rng(f, 3)
    y = np.zeros(n)
    for r, a, tau in _BELL:
        fk = f * r
        if fk > sr * 0.45:
            continue
        tau *= ring * float(np.clip(1.6 - 0.00035 * f, 0.5, 1.6))
        # each mode is a split pair (slightly different frequencies) -> slow beating shimmer
        beat = 0.9 + 1.2 * rs.rand()
        y += a * np.exp(-t / tau) * (np.sin(TAU * fk * t + rs.uniform(0, TAU)) +
                                     0.6 * np.sin(TAU * (fk + beat) * t + rs.uniform(0, TAU))) * 0.6
    nb = int(0.02 * sr)
    clap = dsp.bp(rs.uniform(-1, 1, nb), 1200, 9000, sr) * np.exp(-np.arange(nb) / (0.004 * sr)) * 0.5
    y[:nb] += clap[: n]
    y = dsp.hp(y, 90, sr)
    return y * 0.32 * np.minimum(t / 0.0007, 1.0)


def glock(f, dur, sr=SR, vel=0.8, **kw):
    """glockenspiel / music box: bright, short, a few inharmonic bar modes"""
    n = int((max(dur, 0.3) + 1.8) * sr)
    t = np.arange(n) / sr
    rs = _rng(f, 5)
    y = np.zeros(n)
    for r, a, tau in [(1.0, 1.0, 1.4), (2.76, 0.55, 0.55), (5.40, 0.3, 0.24), (8.93, 0.14, 0.12)]:
        fk = f * r
        if fk > sr * 0.45:
            continue
        y += a * np.exp(-t / tau) * np.sin(TAU * fk * t + rs.uniform(0, TAU))
    nb = int(0.008 * sr)
    y[:nb] += dsp.hp(rs.uniform(-1, 1, nb), 3000, sr) * np.exp(-np.arange(nb) / (0.0015 * sr)) * 0.3
    return y * 0.4 * np.minimum(t / 0.0006, 1.0)


def _leslie(y, sr, speed=0.8, depth=0.0035, am=0.18):
    """rotary speaker: pitch wobble (doppler) + amplitude wobble"""
    n = len(y)
    t = np.arange(n) / sr
    d = depth * sr * (1 + np.sin(TAU * speed * 6.7 * t / 6.7)) * 0.5
    idx = np.clip(np.arange(n) - d, 0, n - 1)
    out = np.interp(idx, np.arange(n), y)
    return out * (1 - am + am * np.sin(TAU * speed * t + 1.1))


# drawbar footages as harmonic numbers of the 8' fundamental: 16' 5 1/3' 8' 4' 2 2/3' 2' 1 3/5' 1 1/3' 1'
_DRAWBAR_H = [0.5, 1.5, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 8.0]


def organ_drawbar(f, dur, sr=SR, vel=0.8, bars=(8, 8, 8, 6, 0, 4, 0, 0, 3), perc=1.0, leslie=0.9, drive=1.4, **kw):
    rel = 0.06
    n = int((dur + rel) * sr)
    t = np.arange(n) / sr
    y = np.zeros(n)
    for h, b in zip(_DRAWBAR_H, bars):
        if b <= 0 or f * h > sr * 0.45:
            continue
        a = 10 ** (-(8 - b) * 3.0 / 20)
        y += a * np.sin(TAU * f * h * t + 0.3 * h)
    # tonewheel leakage: a faint, inharmonic whisper
    y += 0.02 * np.sin(TAU * f * 1.0145 * t) + 0.015 * np.sin(TAU * f * 2.97 * t)
    # percussion: 3rd harmonic, fast decay (classic "ping" at the start of each key)
    if perc:
        y += perc * 0.55 * np.sin(TAU * f * 3.0 * t) * np.exp(-t / 0.11)
    nb = int(0.006 * sr)
    click = dsp.bp(_rng(f, 9).uniform(-1, 1, nb), 800, 6000, sr) * np.exp(-np.arange(nb) / (0.0012 * sr)) * 0.5
    y[:nb] += click[: n]
    env = dsp.adsr(n, 0.004, 0.02, 1.0, rel, sr)
    y = np.tanh(y * drive * 0.35) / max(np.tanh(drive * 0.35), 1e-6) * env
    if leslie:
        y = _leslie(y, sr, speed=leslie)
    return y * 0.38


def organ_church(f, dur, sr=SR, vel=0.8, **kw):
    rel = 0.3
    n = int((dur + rel) * sr)
    t = np.arange(n) / sr
    y = np.zeros(n)
    for h, a in [(1.0, 1.0), (2.0, 0.6), (3.0, 0.32), (4.0, 0.42), (6.0, 0.2), (8.0, 0.16)]:
        if f * h < sr * 0.45:
            y += a * np.sin(TAU * f * h * (1 + 0.0004 * np.sin(TAU * 4.8 * t + h)) * t)
    # chiff: breathy attack noise at the pipe's own pitch region
    nb = int(0.08 * sr)
    rs = _rng(f, 11)
    chiff = dsp.bp(rs.uniform(-1, 1, nb), f * 1.5, f * 6 + 800, sr) * np.exp(-np.arange(nb) / (0.02 * sr)) * 0.6
    y[:nb] += chiff[: n]
    wind = dsp.lp(rs.uniform(-1, 1, n), 4000, sr) * 0.02
    env = dsp.adsr(n, 0.035, 0.05, 1.0, rel, sr)
    return (y + wind) * env * 0.3


def _ks(f, n, sr, damp=0.5, decay=0.996, pick=0.2, bright=0.8, seed=0):
    """Karplus-Strong via IIR comb: y[n] = x[n] + g * ((1-d)*y[n-N] + d*y[n-N-1]) with fractional tuning by resampling"""
    f_eff = f * 1.0
    N = int(sr / f_eff - 0.5)
    N = max(N, 4)
    frac = (sr / f_eff) / (N + damp)  # loop delay of the 2-tap average is N+damp samples
    L = int(n / frac) + N + 8
    rs = np.random.RandomState(seed)
    x = np.zeros(L)
    nz = rs.uniform(-1, 1, N + 1)
    for _ in range(2):
        pole = 0.9 - 0.4 * bright
        nz = lfilter([1 - pole], [1, -pole], nz)  # tame excitation brightness (2 poles)
    # pick position comb (notches at multiples of 1/pick)
    pk = max(int(pick * N), 1)
    nz = nz - np.concatenate([np.zeros(pk), nz[:-pk]])
    x[: N + 1] = nz
    a = np.zeros(N + 2)
    a[0] = 1.0
    a[N] = -decay * (1 - damp)
    a[N + 1] = -decay * damp
    y = lfilter([1.0], a, x)
    # fractional tuning: read the loop output at `frac` speed
    idx = np.arange(n) * (1.0 / frac)
    y = np.interp(idx, np.arange(L), y)
    return y


def guitar_ks(f, dur, sr=SR, vel=0.8, bright=0.8, sustain=1.0, body=True, **kw):
    rel = 0.35
    n = int((dur + rel + 0.6) * sr)
    # decay constant chosen so the note rings about 1.2*sustain seconds (low strings longer)
    per_s = 1.0 / f
    ring = float(np.clip(2.2 * sustain * (110.0 / max(f, 60.0)) ** 0.25, 0.4, 4.0))
    decay = float(np.exp(-per_s / ring))
    y = _ks(f, n, sr, damp=0.5 - 0.1 * bright, decay=min(decay, 0.99995), pick=0.17, bright=bright, seed=int(f * 5) % 9973)
    y = y / (np.max(np.abs(y)) + 1e-9)
    if body:
        y = dsp.peak_eq(y, 110, 3.0, 1.2, sr)
        y = dsp.peak_eq(y, 215, 2.0, 1.4, sr)
        y = dsp.peak_eq(y, 2800, 1.5, 1.0, sr)
    t = np.arange(n) / sr
    env = np.minimum(t / 0.0012, 1.0)
    nd = int(dur * sr)
    if nd < n:
        env[nd:] *= np.exp(-np.arange(n - nd) / (0.07 * sr))
    pickn = int(0.006 * sr)
    y[:pickn] += dsp.hp(_rng(f, 13).uniform(-1, 1, pickn), 2500, sr) * 0.12
    return y * env * 0.7


def guitar_amp(f, dur, sr=SR, vel=0.8, drive=7.0, mute=0.0, bright=0.9, **kw):
    """electric: KS string -> amp stages -> cabinet. mute 0..1 palm mute (shorter, darker)"""
    d = dur * (1.0 - 0.75 * mute)
    y = guitar_ks(f, d, sr, vel=vel, bright=bright * (1 - 0.4 * mute), sustain=2.2 * (1 - 0.7 * mute) + 0.15, body=False)
    y = dsp.hp(y, 70, sr)
    # pre-EQ: tighten lows into the clipper, push upper mids
    y = dsp.peak_eq(y, 900, 4.0, 0.9, sr)
    for g in (drive * 0.9, drive * 0.5, drive * 0.3):
        y = np.tanh(y * g * 0.35 + 0.12) - np.tanh(0.12)  # asymmetric: even harmonics like a tube stage
        y = dsp.lp(y, 7500, sr, 1)
    # cabinet: HP ~85, hump 1.8k, notch near 5k, roll-off 5.2k
    y = dsp.hp(y, 85, sr)
    y = dsp.peak_eq(y, 1800, 3.0, 0.8, sr)
    y = dsp.peak_eq(y, 120, 2.0, 1.0, sr)
    y = dsp.lp(y, 5200 - 1300 * mute, sr, 3)
    y = y / max(1.0, float(np.max(np.abs(y))) * 1.05)
    return y * 0.8


NEW = dict(piano_grand=piano_grand, bell_church=bell_tubular, glock=glock, organ_drawbar=organ_drawbar,
           organ_church=organ_church, guitar_ks=guitar_ks, guitar_amp=guitar_amp)

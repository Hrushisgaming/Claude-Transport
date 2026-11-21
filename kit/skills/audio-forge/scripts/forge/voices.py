"""voices.py -- more realistic voices (1.3.1), written from a listening AI's description of the user's reference themes:
bright percussive clean piano, warm low-passed Rhodes, glockenspiel/celesta doubling, harp or harpsichord plucks,
crunchy mid-focused rhythm guitar vs massive palm-muted guitar vs warm singing lead guitar, picked/fingered electric bass,
string section, brass section. No samples. Same contract as instruments.py: fn(f, dur, sr, **kw) -> mono array incl. release tail.
"""
import numpy as np
from . import dsp, real
from .dsp import SR, TAU


def _norm(y, peak=0.62):
    p = float(np.max(np.abs(y))) if len(y) else 0.0
    return y * (peak / p) if p > 1e-9 else y


def _rs(f, salt):
    return np.random.RandomState((int(f * 17) + salt * 4099) % 100003)


def _warp(y, sr, ratio):
    """resample y by a time-varying pitch ratio array (1.0 = unchanged) -> vibrato / scoops"""
    pos = np.cumsum(ratio) - ratio[0]
    return np.interp(pos, np.arange(len(y)), y)


def _vibrato_ratio(n, sr, rate=5.4, cents=15.0, delay=0.25, ramp=0.4):
    t = np.arange(n) / sr
    depth = np.clip((t - delay) / ramp, 0, 1) * cents
    return 2 ** (depth * np.sin(TAU * rate * t) / 1200.0)


# ───────────────────────── keys ─────────────────────────
def piano_bright(f, dur, sr=SR, vel=1.0, **kw):
    """clean, bright, percussive piano (the references' piano is 'bright, percussive, slightly digital', not woody)"""
    y = real.piano_grand(f, dur, sr, vel=1.0)
    y = dsp.peak_eq(y, 3200, 3.5, 0.9, sr)
    y = dsp.peak_eq(y, 6500, 2.0, 0.8, sr)
    return y * 0.8


def ep_rhodes(f, dur, sr=SR, vel=0.8, tremolo=0.0, **kw):
    """Rhodes-style electric piano: tine + tonebar FM, 'bark' that fades, pickup asymmetry, soft low-pass"""
    rel = 0.35
    n = int((dur + rel + 1.6) * sr)
    t = np.arange(n) / sr
    m = 12 * np.log2(f / 440.0) + 69
    tau = float(np.clip(3.2 * np.exp(-0.022 * (m - 40)), 0.45, 3.2))
    bark = np.exp(-t / 0.18) * (0.6 + 0.8 * vel)
    mod = np.sin(TAU * f * 1.0 * t) * (0.9 + 2.4 * bark)
    car = np.sin(TAU * f * t + mod)
    tine = np.sin(TAU * f * 14.0 * t + 0.4 * np.sin(TAU * f * 7.0 * t)) * np.exp(-t / 0.035) * 0.28 * vel
    bar = np.sin(TAU * f * 2.0 * t + 0.3 * mod) * 0.22 * np.exp(-t / (tau * 0.5))
    y = (car * np.exp(-t / tau) + bar + tine)
    y = np.tanh(y * 1.35) / np.tanh(1.35)  # asymmetric-ish pickup drive -> warm even harmonics
    y = dsp.lp(y, 2600 + 3500 * vel, sr, 2)
    if tremolo:
        y = y * (1 - 0.18 * tremolo + 0.18 * tremolo * np.sin(TAU * 4.8 * t))
    nd = int(dur * sr)
    env = np.minimum(t / 0.0015, 1.0)
    if nd < n:
        env[nd:] *= np.exp(-np.arange(n - nd) / (0.12 * sr))
    return y * env * 0.5


def celesta(f, dur, sr=SR, vel=0.8, **kw):
    """celesta / bell-piano: soft, sweet, fewer partials than the glockenspiel"""
    n = int((max(dur, 0.3) + 2.2) * sr)
    t = np.arange(n) / sr
    rs = _rs(f, 21)
    y = np.zeros(n)
    for r, a, tau in [(1.0, 1.0, 1.8), (2.0, 0.22, 0.9), (4.05, 0.38, 0.45), (6.3, 0.12, 0.2), (9.9, 0.08, 0.1)]:
        fk = f * r
        if fk < sr * 0.45:
            y += a * np.exp(-t / tau) * np.sin(TAU * fk * t + rs.uniform(0, TAU))
    nb = int(0.01 * sr)
    y[:nb] += dsp.bp(rs.uniform(-1, 1, nb), 800, 5000, sr) * np.exp(-np.arange(nb) / (0.002 * sr)) * 0.25
    return y * 0.45 * np.minimum(t / 0.0008, 1.0)


# ───────────────────────── plucks ─────────────────────────
def harp(f, dur, sr=SR, vel=0.8, **kw):
    """concert harp: soft finger pluck, long ring, hollow wooden body"""
    rel = 0.4
    y = real.guitar_ks(f, dur, sr, vel=vel, bright=0.45, sustain=1.9, body=False)
    y = dsp.hp(y, 110, sr)
    y = dsp.peak_eq(y, 420, 2.5, 1.0, sr)
    y = dsp.peak_eq(y, 1500, 1.5, 0.9, sr)
    return y * 0.8


def harpsichord(f, dur, sr=SR, vel=0.8, **kw):
    """harpsichord: two plucked strings (8' + 4'), jack click, nasal body, abrupt damping"""
    d = min(dur, 1.4)
    a = real.guitar_ks(f, d, sr, vel=vel, bright=1.0, sustain=0.55, body=False)
    b = real.guitar_ks(f * 2.0, d, sr, vel=vel, bright=1.0, sustain=0.4, body=False) if f * 2.0 < 3500 else 0.0
    y = a[: len(a)] + (0.55 * b[: len(a)] if not np.isscalar(b) else 0.0)
    y = dsp.peak_eq(y, 1300, 4.0, 1.2, sr)
    y = dsp.hp(y, 140, sr)
    nb = int(0.004 * sr)
    y[:nb] += dsp.hp(_rs(f, 25).uniform(-1, 1, nb), 3500, sr) * 0.25
    return y * 0.7


def chip_pluck(f, dur, sr=SR, vel=0.8, duty=0.25, **kw):
    """retro game pluck: 25% pulse, fast decay (the 'chiptune pluck' in the references)"""
    n = int((min(dur, 0.35) + 0.12) * sr)
    y = dsp.osc("square", f, n, sr, pw=duty)
    y = y * dsp.decay(n, 0.09, sr) * np.minimum(np.arange(n) / (0.001 * sr), 1.0)
    return dsp.lp(y, 7000, sr, 1) * 0.35


# ───────────────────────── sections ─────────────────────────
def string_ensemble(f, dur, sr=SR, vel=0.8, voices=6, **kw):
    """bowed string section: detuned saws with independent vibrato, bow-noise attack, violin-body resonances"""
    rel = 0.45
    n = int((dur + rel) * sr)
    t = np.arange(n) / sr
    rs = _rs(f, 31)
    y = np.zeros(n)
    for v in range(voices):
        cents = rs.uniform(-9, 9)
        vr = _vibrato_ratio(n, sr, rate=rs.uniform(4.6, 5.8), cents=rs.uniform(7, 13), delay=rs.uniform(0.15, 0.4), ramp=0.5)
        base = dsp.osc("saw", f * 2 ** (cents / 1200.0), n, sr, phase0=rs.uniform(0, 1))
        y += _warp(base, sr, vr)
    y /= voices
    cutoff = np.minimum(f * 6.0, 5200.0) * (0.55 + 0.45 * np.minimum(t / 0.35, 1.0))
    y = dsp.sweep_lp(y, cutoff, sr, block=256)
    y = dsp.peak_eq(y, 300, 3.0, 1.0, sr)    # violin air resonance region
    y = dsp.peak_eq(y, 2800, 2.5, 1.2, sr)   # bridge hill
    nb = int(0.25 * sr)
    bow = dsp.bp(rs.uniform(-1, 1, nb), f * 2, f * 8 + 1000, sr) * np.exp(-np.arange(nb) / (0.07 * sr)) * 0.12
    y[:nb] += bow
    env = dsp.adsr(n, 0.14, 0.2, 0.85, rel, sr)
    return y * env * 0.9


def brass_section(f, dur, sr=SR, vel=0.8, **kw):
    """brass/horn section: detuned saws, 'blat' filter swell, pitch scoop, formants around 500 and 1500 Hz"""
    rel = 0.18
    n = int((dur + rel) * sr)
    t = np.arange(n) / sr
    rs = _rs(f, 37)
    scoop = 2 ** ((-35.0 * np.exp(-t / 0.04)) / 1200.0) * _vibrato_ratio(n, sr, 5.2, 9.0, delay=0.35, ramp=0.5)
    y = np.zeros(n)
    for cents in (-7, 0, 6):
        y += _warp(dsp.osc("saw", f * 2 ** (cents / 1200.0), n, sr, phase0=rs.uniform(0, 1)), sr, scoop)
    y /= 3
    cutoff = f * (2.2 + 8.0 * np.minimum(t / 0.11, 1.0) ** 0.7)
    cutoff = np.minimum(cutoff, 7000)
    y = dsp.sweep_lp(y, cutoff, sr, block=128)
    y = dsp.peak_eq(y, 520, 4.0, 1.2, sr)
    y = dsp.peak_eq(y, 1500, 3.0, 1.0, sr)
    env = dsp.adsr(n, 0.045, 0.1, 0.88, rel, sr)
    return _norm(y * env)


# ───────────────────────── bass ─────────────────────────
def bass_guitar(f, dur, sr=SR, vel=0.8, pick=0.6, **kw):
    """electric bass: plucked string, pick attack (0 = fingerstyle warmth, 1 = picked/metallic), light compression"""
    y = real.guitar_ks(f, dur, sr, vel=vel, bright=0.25 + 0.5 * pick, sustain=2.6, body=False)
    y = dsp.lp(y, 1800 + 3200 * pick, sr, 2)
    y = dsp.peak_eq(y, 90, 3.0, 1.0, sr)
    y = dsp.peak_eq(y, 600, -3.0, 0.8, sr)   # scooped mids
    nb = int(0.012 * sr)
    y[:nb] += dsp.bp(_rs(f, 41).uniform(-1, 1, nb), 1500, 5500, sr) * np.exp(-np.arange(nb) / (0.004 * sr)) * (0.05 + 0.3 * pick)
    y = np.tanh(y * 1.8) / np.tanh(1.8)       # compressor-ish
    return y * 0.8


# ───────────────────────── guitars ─────────────────────────
def guitar_crunch(f, dur, sr=SR, vel=0.8, drive=3.2, mute=0.0, **kw):
    """crunchy mid-focused rhythm guitar: tucked behind synths (lower gain than the heavy sound, mids pushed)"""
    y = real.guitar_amp(f, dur, sr, vel=vel, drive=drive, mute=mute, bright=0.8)
    y = dsp.peak_eq(y, 1100, 3.0, 0.9, sr)
    return _norm(y)


def guitar_heavy(f, dur, sr=SR, vel=0.8, drive=14.0, mute=0.85, **kw):
    """massive, over-saturated, palm-muted: high gain, tight low end, short"""
    y = real.guitar_amp(f, dur, sr, vel=vel, drive=drive, mute=mute, bright=0.9)
    y = dsp.peak_eq(y, 120, 2.0, 1.0, sr)
    y = dsp.peak_eq(y, 3000, 2.0, 1.2, sr)
    return _norm(y, 0.7)


def guitar_lead(f, dur, sr=SR, vel=0.8, drive=4.5, **kw):
    """warm singing lead: moderate gain, long sustain, delayed vibrato, rounded top"""
    y = real.guitar_amp(f, dur, sr, vel=vel, drive=drive, mute=0.0, bright=0.6)
    y = _warp(y, sr, _vibrato_ratio(len(y), sr, 5.6, 22.0, delay=0.28, ramp=0.35))
    y = dsp.lp(y, 4200, sr, 2)
    y = dsp.peak_eq(y, 750, 2.5, 0.9, sr)
    # swell instead of a hard pick on long notes
    t = np.arange(len(y)) / sr
    y = y * (0.85 + 0.15 * np.minimum(t / 0.3, 1.0))
    return _norm(y)


# ───────────────────────── dread voices (v1.7, from listening notes on a hunted render) ─────────────────────────
def bend_lead(f, dur, sr=SR, vel=0.8, bend=1.0, drive=6.0, vib=1.0, **kw):
    """pitch-bent, distorted saw lead (replaces the 'retro arcade square'): each note dives in from `bend` semitones away (+up / -down) and
    rides a late, uneasy vibrato; two saws a few cents apart through hard clipping, then a cold band-limit."""
    n = int((dur + 0.14) * sr)
    t = np.arange(n) / sr
    ratio = 1.0 + (2 ** (bend / 12.0) - 1.0) * np.exp(-t / 0.07)
    ratio = ratio * (1.0 + 0.004 * vib * np.clip((t - 0.12) / 0.3, 0, 1) * np.sin(TAU * 6.3 * t))
    y = np.zeros(n)
    for cents, ph in ((0.0, 0.0), (9.0, 0.37)):
        phase = np.cumsum(f * 2 ** (cents / 1200.0) * ratio) / sr + ph
        y += 2.0 * (phase % 1.0) - 1.0
    y = np.tanh(y * 0.5 * drive * 0.6) / np.tanh(drive * 0.3)
    y = dsp.hp(y, 220, sr)
    y = dsp.lp(y, 4800, sr, 2)
    y = dsp.peak_eq(y, 1700, 2.5, 1.0, sr)
    env = dsp.adsr(n, 0.004, 0.05, 0.85, 0.09, sr)
    return _norm(y * env, 0.55)


def string_tremolo(f, dur, sr=SR, vel=0.8, cluster=0.6, rate=11.0, **kw):
    """cold tremolo strings with a minor-second cluster: bowed saws, tremolo amplitude wobble, no warm body, a rubbing semitone above the root"""
    rel = 0.35
    n = int((dur + rel) * sr)
    t = np.arange(n) / sr
    rs = _rs(f, 51)
    y = np.zeros(n)
    for ratio, amp in ((1.0, 1.0), (2 ** (1 / 12.0), cluster), (1.5, 0.45)):
        for cents in (-6.0, 5.0):
            y += amp * dsp.osc("saw", f * ratio * 2 ** (cents / 1200.0), n, sr, phase0=rs.uniform(0, 1))
    y = dsp.sweep_lp(y, np.full(n, min(f * 5.0, 3600.0)), sr, block=512)
    y = dsp.hp(y, 140, sr)
    trem = 0.55 + 0.45 * np.sin(TAU * rate * t + 0.5) ** 2
    nb = int(0.18 * sr)
    y[:nb] += dsp.bp(rs.uniform(-1, 1, nb), f * 2, f * 7 + 800, sr) * np.exp(-np.arange(nb) / (0.05 * sr)) * 0.1
    env = dsp.adsr(n, 0.22, 0.2, 0.85, rel, sr)
    return _norm(y * trem * env, 0.5)


def piano_dark(f, dur, sr=SR, vel=0.6, **kw):
    """the grand piano pulled down: low-passed, softer, a touch of detune (a second copy a few cents sharp) - sparse, cold, close"""
    y = real.piano_grand(f, dur, sr, vel=0.55)
    y2 = real.piano_grand(f * 2 ** (6 / 1200.0), dur, sr, vel=0.55)
    m = min(len(y), len(y2))
    y = 0.65 * y[:m] + 0.35 * y2[:m]
    y = dsp.lp(y, 2300, sr, 2)
    return _norm(y, 0.5)


NEW = dict(bend_lead=bend_lead, string_tremolo=string_tremolo, piano_dark=piano_dark, piano_bright=piano_bright, ep_rhodes=ep_rhodes, celesta=celesta, harp=harp, harpsichord=harpsichord,
           chip_pluck=chip_pluck, string_ensemble=string_ensemble, brass_section=brass_section, bass_guitar=bass_guitar,
           guitar_crunch=guitar_crunch, guitar_heavy=guitar_heavy, guitar_lead=guitar_lead)

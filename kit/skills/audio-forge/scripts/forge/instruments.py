#!/usr/bin/env python3
"""
instruments.py - Acoustic-Grade & LMS-Inspired Instrument Synthesis Engine.

Eliminates the "electronic buzz" and excessive vibrato of naive waveform generators by using:
  - PolyBLEP anti-aliased oscillators (zero harsh high-frequency aliasing)
  - Karplus-Strong physical string modeling + oversampled tube amp & cabinet IR for electric guitars
  - Multi-voice formant-filtered bowed string ensembles with independent slow drift (no beehive buzz)
  - Stiff-string inharmonicity + hammer-felt noise transients for dark & crystalline ice pianos
  - 5-rank stop additive synthesis with pipe "chiff" air transients for gothic pipe organs
  - Risset inharmonic tubular/church/clock bell partials with clapper strike transients
  - Formant-filtered choir pads & double-hit ("HA-HA") maniacal laugh generator
  - Y2K / 2008 Roblox retro electronic instruments (FM slap/growl bass, acid lead, tracker arp)
"""

from __future__ import annotations

import math
from typing import Callable, Dict, List

import numpy as np
from scipy import signal


def _polyblep(t: np.ndarray, dt: float) -> np.ndarray:
    blep = np.zeros_like(t)
    m1 = t < dt
    if np.any(m1):
        x = t[m1] / dt
        blep[m1] = x + x - x * x - 1.0
    m2 = t > (1.0 - dt)
    if np.any(m2):
        x = (t[m2] - 1.0) / dt
        blep[m2] = x * x + x + x + 1.0
    return blep


def polyblep_saw(freq: float | np.ndarray, n_samples: int, sr: int = 44100, phase0: float = 0.0) -> np.ndarray:
    if np.ndim(freq) == 0:
        dt = float(freq) / sr
        phase = (phase0 + np.arange(n_samples, dtype=np.float64) * dt) % 1.0
        out = 2.0 * phase - 1.0 - _polyblep(phase, dt)
        return out.astype(np.float32)
    f_arr = np.asarray(freq, dtype=np.float64)
    dt_arr = f_arr / sr
    phase = (phase0 + np.cumsum(dt_arr)) % 1.0
    out = 2.0 * phase - 1.0
    for i in range(n_samples):
        dt = dt_arr[i]
        p = phase[i]
        if p < dt:
            x = p / dt
            out[i] -= (2.0 * x - x * x - 1.0)
        elif p > 1.0 - dt:
            x = (p - 1.0) / dt
            out[i] -= (x * x + 2.0 * x + 1.0)
    return out.astype(np.float32)


def polyblep_square(freq: float, n_samples: int, sr: int = 44100, duty: float = 0.5, phase0: float = 0.0) -> np.ndarray:
    dt = float(freq) / sr
    phase = (phase0 + np.arange(n_samples, dtype=np.float64) * dt) % 1.0
    out = np.where(phase < duty, 1.0, -1.0)
    out += _polyblep(phase, dt)
    out -= _polyblep((phase - duty) % 1.0, dt)
    return out.astype(np.float32)


def biquad_filter(x: np.ndarray, ftype: str, cutoff: float, q: float = 0.707, sr: int = 44100) -> np.ndarray:
    nyq = 0.49 * sr
    fc = float(np.clip(cutoff, 20.0, nyq))
    sos = signal.butter(2, fc / (0.5 * sr), btype=ftype, output="sos")
    return signal.sosfilt(sos, x).astype(np.float32)


def peaking_eq(x: np.ndarray, freq: float, q: float, gain_db: float, sr: int = 44100) -> np.ndarray:
    w0 = 2.0 * math.pi * float(np.clip(freq, 25.0, 0.48 * sr)) / sr
    alpha = math.sin(w0) / (2.0 * max(q, 0.1))
    A = 10.0 ** (gain_db / 40.0)
    b0 = 1.0 + alpha * A
    b1 = -2.0 * math.cos(w0)
    b2 = 1.0 - alpha * A
    a0 = 1.0 + alpha / A
    a1 = -2.0 * math.cos(w0)
    a2 = 1.0 - alpha / A
    sos = np.array([[b0 / a0, b1 / a0, b2 / a0, 1.0, a1 / a0, a2 / a0]], dtype=np.float64)
    return signal.sosfilt(sos, x).astype(np.float32)


def adsr_env(n: int, sr: int, attack: float, decay: float, sustain: float, release: float) -> np.ndarray:
    a = max(1, int(attack * sr))
    d = max(1, int(decay * sr))
    r = max(1, int(release * sr))
    s_len = max(0, n - a - d - r)
    env = np.concatenate([
        np.linspace(0.0, 1.0, a, endpoint=False),
        np.linspace(1.0, sustain, d, endpoint=False),
        np.full(s_len, sustain),
        np.linspace(sustain, 0.0, r, endpoint=True),
    ])
    if len(env) > n:
        env = env[:n]
    elif len(env) < n:
        env = np.pad(env, (0, n - len(env)))
    return env.astype(np.float32)


def stereoize(mono: np.ndarray, width: float = 0.45, delay_ms: float = 11.0, sr: int = 44100) -> np.ndarray:
    """Create natural stereo image without metallic comb-buzz."""
    d_samp = max(1, int(delay_ms * 0.001 * sr))
    delayed = np.pad(mono, (d_samp, 0))[: len(mono)]
    delayed = biquad_filter(delayed, "lowpass", 6500.0, sr=sr)
    left = mono + width * 0.5 * (mono - delayed)
    right = mono - width * 0.5 * (mono - delayed)
    return np.column_stack([left, right]).astype(np.float32)


def synth_electric_guitar(
    freq: float,
    duration: float,
    velocity: float = 0.85,
    sr: int = 44100,
    palm_mute: float = 0.0,
    gain: float = 5.5,
    power_chord: bool = True,
) -> np.ndarray:
    """
    Karplus-Strong plucked string model + tube amp saturation + 4x12 guitar cabinet IR.
    Eliminates the synthetic sawtooth buzz of naive rock synths.
    """
    n_samples = max(1, int(duration * sr))

    def pluck_string(f0: float, mute_amt: float) -> np.ndarray:
        period = max(4, int(round(sr / max(f0, 27.5))))
        rng = np.random.default_rng(int(f0 * 100) % 99991)
        exc = rng.uniform(-1.0, 1.0, period).astype(np.float64)
        pick_pos = max(1, period // 6)
        exc[pick_pos:] -= 0.75 * exc[:-pick_pos]
        exc = biquad_filter(exc.astype(np.float32), "lowpass", 3400.0 - 1600.0 * mute_amt, sr=sr).astype(np.float64)

        out = np.zeros(n_samples, dtype=np.float64)
        out[: min(period, n_samples)] = exc[: min(period, n_samples)]

        base_decay = 0.9965 - 0.022 * mute_amt
        lp_coeff = 0.48 - 0.24 * mute_amt
        prev = 0.0
        for i in range(period, n_samples):
            raw = out[i - period]
            filtered = (1.0 - lp_coeff) * raw + lp_coeff * prev
            prev = filtered
            out[i] = base_decay * filtered
        return out.astype(np.float32)

    sig = pluck_string(freq, palm_mute)
    if power_chord:
        sig += 0.72 * pluck_string(freq * (2.0 ** (7.0 / 12.0)), palm_mute)
        sig += 0.42 * pluck_string(freq * 2.0, palm_mute)

    drive = sig * (gain * (0.75 + 0.45 * velocity))
    amp = np.where(drive >= 0.0, np.tanh(drive * 1.15), np.tanh(drive * 0.85) * 0.92)

    cab = biquad_filter(amp.astype(np.float32), "highpass", 75.0, sr=sr)
    cab = peaking_eq(cab, freq=125.0, q=1.8, gain_db=4.5, sr=sr)
    cab = peaking_eq(cab, freq=420.0, q=1.2, gain_db=-3.0, sr=sr)
    cab = peaking_eq(cab, freq=2100.0, q=1.5, gain_db=4.0, sr=sr)
    cab = biquad_filter(cab, "lowpass", 4300.0, sr=sr)
    cab = biquad_filter(cab, "lowpass", 5200.0, sr=sr)

    env = adsr_env(n_samples, sr, attack=0.004, decay=0.12, sustain=0.88, release=0.06)
    return stereoize(cab * env * velocity * 0.55, width=0.55, delay_ms=14.0, sr=sr)


def synth_strings(
    freq: float,
    duration: float,
    velocity: float = 0.8,
    sr: int = 44100,
    tremolo: bool = False,
) -> np.ndarray:
    """8-voice bowed ensemble with wood-body formant filtering and gentle bow-hair rolloff."""
    n_samples = max(1, int(duration * sr))
    t = np.arange(n_samples, dtype=np.float64) / sr
    detunes_cents = [-11.0, -6.5, -2.5, 0.0, 2.8, 6.2, 10.5, -4.0]
    pans = [-0.8, -0.5, -0.2, 0.0, 0.2, 0.5, 0.8, -0.3]

    left = np.zeros(n_samples, dtype=np.float32)
    right = np.zeros(n_samples, dtype=np.float32)

    for idx, (cents, pan) in enumerate(zip(detunes_cents, pans)):
        drift = 1.8 * np.sin(2.0 * math.pi * (0.35 + 0.06 * idx) * t + idx)
        f_inst = freq * (2.0 ** ((cents + drift) / 1200.0))
        voice = polyblep_saw(f_inst, n_samples, sr=sr, phase0=(idx * 0.13) % 1.0)
        if tremolo:
            bow = 0.72 + 0.28 * np.sin(2.0 * math.pi * 9.5 * t + idx * 1.1)
            voice = voice * bow.astype(np.float32)

        l_gain = math.sqrt(0.5 * (1.0 - pan))
        r_gain = math.sqrt(0.5 * (1.0 + pan))
        left += voice * l_gain
        right += voice * r_gain

    left /= len(detunes_cents)
    right /= len(detunes_cents)

    for ch_idx, ch in enumerate([left, right]):
        ch = biquad_filter(ch, "highpass", 110.0, sr=sr)
        ch = peaking_eq(ch, freq=290.0, q=2.0, gain_db=3.5, sr=sr)
        ch = peaking_eq(ch, freq=620.0, q=1.8, gain_db=2.2, sr=sr)
        ch = peaking_eq(ch, freq=2400.0, q=1.6, gain_db=-2.5, sr=sr)
        ch = biquad_filter(ch, "lowpass", 3900.0, sr=sr)
        if ch_idx == 0:
            left = ch
        else:
            right = ch

    atk = 0.06 if tremolo else 0.16
    env = adsr_env(n_samples, sr, attack=atk, decay=0.25, sustain=0.85, release=0.22)
    out = np.column_stack([left * env, right * env]) * velocity * 0.65
    return out.astype(np.float32)


def synth_piano(
    freq: float,
    duration: float,
    velocity: float = 0.85,
    sr: int = 44100,
    style: str = "dark",
) -> np.ndarray:
    """Stiff-string inharmonic piano & crystalline bell-piano model with hammer-felt transient."""
    n_samples = max(1, int(duration * sr))
    t = np.arange(n_samples, dtype=np.float64) / sr

    if style == "harpsichord":
        sig = polyblep_saw(freq, n_samples, sr=sr) * 0.55 + polyblep_square(freq * 2.0, n_samples, sr=sr, duty=0.25) * 0.35
        decay_t = np.exp(-t * 3.8).astype(np.float32)
        sig = biquad_filter(sig * decay_t, "highpass", 140.0, sr=sr)
        sig = biquad_filter(sig, "lowpass", 5800.0, sr=sr)
        env = adsr_env(n_samples, sr, attack=0.002, decay=0.22, sustain=0.18, release=0.08)
        return stereoize(sig * env * velocity * 0.55, width=0.45, delay_ms=9.0, sr=sr)

    B = 0.00028 if style == "dark" else 0.00065
    n_partials = 8 if style == "dark" else 7
    sig = np.zeros(n_samples, dtype=np.float64)

    for n in range(1, n_partials + 1):
        fn = n * freq * math.sqrt(1.0 + B * (n ** 2))
        if fn >= 0.45 * sr:
            break
        rate = (1.35 + 0.55 * n) if style == "dark" else (0.95 + 0.38 * n)
        amp_n = (1.0 / (n ** (1.35 if style == "dark" else 1.1))) * np.exp(-t * rate)
        w1 = np.sin(2.0 * math.pi * fn * t)
        w2 = np.sin(2.0 * math.pi * (fn * 1.00075) * t + 0.4)
        sig += amp_n * (0.55 * w1 + 0.45 * w2)

    rng = np.random.default_rng(int(freq * 37) % 65535)
    hammer = rng.normal(0.0, 1.0, n_samples).astype(np.float32) * np.exp(-t * 140.0).astype(np.float32)
    hammer = biquad_filter(hammer, "lowpass", 1400.0 if style == "dark" else 3600.0, sr=sr)

    body = sig.astype(np.float32) + 0.22 * velocity * hammer
    if style == "dark":
        body = peaking_eq(body, freq=180.0, q=1.5, gain_db=3.5, sr=sr)
        body = biquad_filter(body, "lowpass", 3200.0, sr=sr)
    else:
        body = biquad_filter(body, "highpass", 240.0, sr=sr)
        body = peaking_eq(body, freq=3200.0, q=1.4, gain_db=3.0, sr=sr)

    env = adsr_env(n_samples, sr, attack=0.003, decay=0.35, sustain=0.30, release=0.25)
    return stereoize(body * env * velocity * 0.65, width=0.55 if style == "ice" else 0.35, delay_ms=13.0, sr=sr)


def synth_pipe_organ(
    freq: float,
    duration: float,
    velocity: float = 0.85,
    sr: int = 44100,
    low_register: bool = True,
) -> np.ndarray:
    """Multi-rank pipe organ (16', 8', 4', 2-2/3', 2') with authentic air-pipe chiff."""
    n_samples = max(1, int(duration * sr))
    t = np.arange(n_samples, dtype=np.float64) / sr

    ranks = [
        (0.5, 0.85 if low_register else 0.45),
        (1.0, 1.00),
        (2.0, 0.55 if low_register else 0.75),
        (3.0, 0.22 if low_register else 0.38),
        (4.0, 0.14 if low_register else 0.28),
    ]
    sig = np.zeros(n_samples, dtype=np.float64)
    for mult, weight in ranks:
        f_r = freq * mult
        if f_r < 0.45 * sr:
            sig += weight * np.sin(2.0 * math.pi * f_r * t + mult * 0.3)

    rng = np.random.default_rng(int(freq * 19) % 32767)
    chiff = rng.normal(0.0, 1.0, n_samples).astype(np.float32) * np.exp(-t * 55.0).astype(np.float32)
    chiff = biquad_filter(chiff, "bandpass", min(freq * 3.0, 2400.0), sr=sr)

    out = biquad_filter(sig.astype(np.float32) + 0.18 * chiff, "lowpass", 3600.0, sr=sr)
    env = adsr_env(n_samples, sr, attack=0.025, decay=0.10, sustain=0.92, release=0.14)
    return stereoize(out * env * velocity * 0.55, width=0.50, delay_ms=15.0, sr=sr)


def synth_bell(
    freq: float,
    duration: float,
    velocity: float = 0.85,
    sr: int = 44100,
    bell_type: str = "church",
) -> np.ndarray:
    """Risset inharmonic bell synthesis with bronze clapper strike transient."""
    n_samples = max(1, int(duration * sr))
    t = np.arange(n_samples, dtype=np.float64) / sr

    partials = [
        (0.50, 0.85, 0.55),
        (1.00, 1.00, 0.75),
        (1.183, 0.78, 1.05),
        (1.506, 0.62, 1.35),
        (2.00, 0.55, 1.80),
        (2.514, 0.32, 2.50),
        (3.011, 0.22, 3.20),
        (4.166, 0.12, 4.40),
    ]
    if bell_type == "clock_bell":
        partials[0] = (0.50, 1.15, 0.48)
        partials[2] = (1.183, 0.90, 0.95)

    sig = np.zeros(n_samples, dtype=np.float64)
    for ratio, weight, dec in partials:
        f_p = freq * ratio
        if f_p < 0.45 * sr:
            sig += weight * np.exp(-t * dec) * np.sin(2.0 * math.pi * f_p * t)

    rng = np.random.default_rng(int(freq * 53) % 44444)
    clapper = rng.normal(0.0, 1.0, n_samples).astype(np.float32) * np.exp(-t * 95.0).astype(np.float32)
    clapper = biquad_filter(clapper, "bandpass", min(freq * 4.5, 4200.0), sr=sr)

    out = sig.astype(np.float32) + 0.30 * clapper
    out = biquad_filter(out, "lowpass", 5500.0, sr=sr)
    env = adsr_env(n_samples, sr, attack=0.002, decay=0.4, sustain=0.65, release=0.4)
    return stereoize(out * env * velocity * 0.52, width=0.65, delay_ms=18.0, sr=sr)


def synth_clock_tick(
    duration: float = 0.18,
    velocity: float = 0.75,
    sr: int = 44100,
    is_tock: bool = False,
) -> np.ndarray:
    """2-stage mechanical escapement tick/tock (woody impulse + micro gear rebound)."""
    n_samples = max(1, int(duration * sr))
    t = np.arange(n_samples, dtype=np.float64) / sr
    rng = np.random.default_rng(101 if not is_tock else 202)

    click1 = rng.normal(0.0, 1.0, n_samples).astype(np.float32) * np.exp(-t * 260.0).astype(np.float32)
    f_res = 2350.0 if not is_tock else 1980.0
    click1 = biquad_filter(click1, "bandpass", f_res, sr=sr)

    rebound_t = np.maximum(0.0, t - 0.032)
    click2 = rng.normal(0.0, 1.0, n_samples).astype(np.float32) * np.exp(-rebound_t * 320.0).astype(np.float32)
    click2[t < 0.032] = 0.0
    click2 = 0.45 * biquad_filter(click2, "bandpass", f_res * 1.25, sr=sr)

    out = (click1 + click2) * velocity * 1.4
    return stereoize(out.astype(np.float32), width=0.18, delay_ms=4.0, sr=sr)


def synth_choir_pad(
    freq: float,
    duration: float,
    velocity: float = 0.75,
    sr: int = 44100,
    vowel: str = "ooh",
) -> np.ndarray:
    """Ghostly vocal formant choir pad (ASG / Eternity Forsakened style)."""
    n_samples = max(1, int(duration * sr))

    src = (
        polyblep_saw(freq * 0.997, n_samples, sr=sr)
        + polyblep_saw(freq, n_samples, sr=sr)
        + polyblep_saw(freq * 1.003, n_samples, sr=sr)
    ) / 3.0

    formants = (
        [(360.0, 6.0, 1.0), (780.0, 7.5, 0.65), (2450.0, 9.0, 0.25)]
        if vowel == "ooh"
        else [(720.0, 6.0, 1.0), (1180.0, 7.0, 0.75), (2600.0, 9.0, 0.30)]
    )
    vocal = np.zeros(n_samples, dtype=np.float32)
    for f_hz, q_val, gain_w in formants:
        sos = signal.iirpeak(f_hz / (0.5 * sr), q_val)
        vocal += gain_w * signal.sosfilt(sos, src).astype(np.float32)

    rng = np.random.default_rng(777)
    breath = biquad_filter(rng.normal(0.0, 0.08, n_samples).astype(np.float32), "bandpass", 1800.0, sr=sr)
    vocal = biquad_filter(vocal + breath, "lowpass", 3400.0, sr=sr)

    env = adsr_env(n_samples, sr, attack=0.22, decay=0.30, sustain=0.82, release=0.30)
    return stereoize(vocal * env * velocity * 0.42, width=0.72, delay_ms=19.0, sr=sr)


def synth_double_laugh(
    base_freq: float = 165.0,
    duration: float = 0.68,
    velocity: float = 0.90,
    sr: int = 44100,
) -> np.ndarray:
    """Two-syllable formant-synthesized maniacal 'HA - HA!' laugh timed to drop on beats."""
    n_samples = max(1, int(duration * sr))
    out = np.zeros(n_samples, dtype=np.float32)

    syllables = [
        (0.00, 0.24, base_freq * 1.12, base_freq * 0.94),
        (0.28, 0.34, base_freq * 0.98, base_freq * 0.76),
    ]
    rng = np.random.default_rng(666)

    for start_s, dur_s, f_start, f_end in syllables:
        i0 = int(start_s * sr)
        n_syl = min(int(dur_s * sr), n_samples - i0)
        if n_syl <= 16:
            continue
        ts = np.arange(n_syl, dtype=np.float64) / sr
        f_contour = np.linspace(f_start, f_end, n_syl)
        glottal = polyblep_saw(f_contour, n_syl, sr=sr)

        f1 = signal.sosfilt(signal.iirpeak(760.0 / (0.5 * sr), 5.5), glottal)
        f2 = 0.8 * signal.sosfilt(signal.iirpeak(1240.0 / (0.5 * sr), 6.5), glottal)
        f3 = 0.35 * signal.sosfilt(signal.iirpeak(2550.0 / (0.5 * sr), 8.0), glottal)

        h_breath = rng.normal(0.0, 1.0, n_syl).astype(np.float32) * np.exp(-ts * 38.0).astype(np.float32)
        h_breath = biquad_filter(h_breath, "bandpass", 1450.0, sr=sr)

        syl_env = adsr_env(n_syl, sr, attack=0.015, decay=0.08, sustain=0.65, release=0.07)
        syl = (f1 + f2 + f3 + 0.55 * h_breath).astype(np.float32) * syl_env
        syl = np.tanh(syl * 1.6)
        out[i0 : i0 + n_syl] += syl

    out = biquad_filter(out, "highpass", 110.0, sr=sr)
    out = biquad_filter(out, "lowpass", 4600.0, sr=sr)
    return stereoize(out * velocity * 0.62, width=0.38, delay_ms=11.0, sr=sr)


def synth_reese_bass(
    freq: float,
    duration: float,
    velocity: float = 0.9,
    sr: int = 44100,
) -> np.ndarray:
    """Deep dark neuro/DnB reese bass with locked sub-sine and warm low-pass (no buzz)."""
    n_samples = max(1, int(duration * sr))
    t = np.arange(n_samples, dtype=np.float64) / sr

    sub = np.sin(2.0 * math.pi * freq * t).astype(np.float32)
    saws = (
        polyblep_saw(freq * 0.994, n_samples, sr=sr)
        + polyblep_saw(freq, n_samples, sr=sr)
        + polyblep_saw(freq * 1.006, n_samples, sr=sr)
    ) / 3.0

    mid_grit = np.tanh(saws * 2.4).astype(np.float32)
    mid_grit = biquad_filter(mid_grit, "highpass", 85.0, sr=sr)
    mid_grit = biquad_filter(mid_grit, "lowpass", 1450.0, sr=sr)

    env = adsr_env(n_samples, sr, attack=0.012, decay=0.15, sustain=0.90, release=0.08)
    st = stereoize(mid_grit * env * velocity * 0.45, width=0.50, delay_ms=10.0, sr=sr)
    st[:, 0] += 0.65 * sub * env * velocity * 0.72
    st[:, 1] += 0.65 * sub * env * velocity * 0.72
    return st.astype(np.float32)


def synth_y2k_electronic(
    freq: float,
    duration: float,
    velocity: float = 0.85,
    sr: int = 44100,
    patch: str = "fm_bass",
) -> np.ndarray:
    """Y2K / 2008-era electronic & EHEF soaring lead instruments with clean band-limited edges."""
    n_samples = max(1, int(duration * sr))
    t = np.arange(n_samples, dtype=np.float64) / sr

    if patch == "fm_bass":
        mod_env = 2.8 * np.exp(-t * 11.0) + 0.45
        mod = mod_env * np.sin(2.0 * math.pi * (freq * 2.0) * t)
        car = np.sin(2.0 * math.pi * freq * t + mod).astype(np.float32)
        car = biquad_filter(car, "lowpass", 2200.0, sr=sr)
        env = adsr_env(n_samples, sr, attack=0.004, decay=0.18, sustain=0.65, release=0.06)
        return stereoize(car * env * velocity * 0.70, width=0.25, delay_ms=7.0, sr=sr)

    if patch == "tracker_arp":
        sq = polyblep_square(freq, n_samples, sr=sr, duty=0.25)
        sq = biquad_filter(sq, "lowpass", 4200.0, sr=sr)
        env = adsr_env(n_samples, sr, attack=0.003, decay=0.09, sustain=0.35, release=0.04)
        return stereoize(sq * env * velocity * 0.48, width=0.45, delay_ms=11.0, sr=sr)

    detunes = [-7.0, -2.5, 2.5, 7.0]
    lead = np.zeros(n_samples, dtype=np.float32)
    for idx, c in enumerate(detunes):
        f_v = freq * (2.0 ** (c / 1200.0))
        lead += polyblep_saw(f_v, n_samples, sr=sr, phase0=idx * 0.23)
    lead /= len(detunes)
    if patch == "acid_lead":
        lead = np.tanh(lead * 2.1).astype(np.float32)
        lead = peaking_eq(lead, freq=min(freq * 3.5, 3200.0), q=4.5, gain_db=7.0, sr=sr)

    lead = biquad_filter(lead, "highpass", 150.0, sr=sr)
    lead = biquad_filter(lead, "lowpass", 4800.0, sr=sr)
    env = adsr_env(n_samples, sr, attack=0.015, decay=0.18, sustain=0.80, release=0.14)
    return stereoize(lead * env * velocity * 0.55, width=0.65, delay_ms=14.0, sr=sr)


INSTRUMENTS: Dict[str, Callable[..., np.ndarray]] = {
    "guitar": lambda f, d, v=0.85, sr=44100, **kw: synth_electric_guitar(f, d, v, sr, palm_mute=kw.get("palm_mute", 0.0), power_chord=True),
    "guitars": lambda f, d, v=0.85, sr=44100, **kw: synth_electric_guitar(f, d, v, sr, palm_mute=kw.get("palm_mute", 0.25), power_chord=True),
    "power_guitar": lambda f, d, v=0.85, sr=44100, **kw: synth_electric_guitar(f, d, v, sr, palm_mute=0.0, gain=6.5, power_chord=True),
    "palm_guitar": lambda f, d, v=0.85, sr=44100, **kw: synth_electric_guitar(f, d, v, sr, palm_mute=0.72, gain=6.0, power_chord=True),
    "strings": lambda f, d, v=0.80, sr=44100, **kw: synth_strings(f, d, v, sr, tremolo=False),
    "trem_strings": lambda f, d, v=0.80, sr=44100, **kw: synth_strings(f, d, v, sr, tremolo=True),
    "piano": lambda f, d, v=0.85, sr=44100, **kw: synth_piano(f, d, v, sr, style="dark"),
    "piano_dark": lambda f, d, v=0.85, sr=44100, **kw: synth_piano(f, d, v, sr, style="dark"),
    "ice_piano": lambda f, d, v=0.85, sr=44100, **kw: synth_piano(f, d, v, sr, style="ice"),
    "music_box": lambda f, d, v=0.80, sr=44100, **kw: synth_piano(f, d, v, sr, style="ice"),
    "harpsichord": lambda f, d, v=0.85, sr=44100, **kw: synth_piano(f, d, v, sr, style="harpsichord"),
    "bell": lambda f, d, v=0.85, sr=44100, **kw: synth_bell(f, d, v, sr, bell_type="church"),
    "bells": lambda f, d, v=0.85, sr=44100, **kw: synth_bell(f, d, v, sr, bell_type="church"),
    "church_bells": lambda f, d, v=0.85, sr=44100, **kw: synth_bell(f, d, v, sr, bell_type="church"),
    "clock_bell": lambda f, d, v=0.90, sr=44100, **kw: synth_bell(f, d, v, sr, bell_type="clock_bell"),
    "clock_tick": lambda f, d, v=0.75, sr=44100, **kw: synth_clock_tick(d, v, sr, is_tock=kw.get("is_tock", False)),
    "organ": lambda f, d, v=0.85, sr=44100, **kw: synth_pipe_organ(f, d, v, sr, low_register=False),
    "organ_low": lambda f, d, v=0.85, sr=44100, **kw: synth_pipe_organ(f, d, v, sr, low_register=True),
    "pipe_organ": lambda f, d, v=0.85, sr=44100, **kw: synth_pipe_organ(f, d, v, sr, low_register=True),
    "choir": lambda f, d, v=0.75, sr=44100, **kw: synth_choir_pad(f, d, v, sr, vowel="ooh"),
    "choir_pad": lambda f, d, v=0.75, sr=44100, **kw: synth_choir_pad(f, d, v, sr, vowel=kw.get("vowel", "ooh")),
    "ha_laugh": lambda f, d, v=0.90, sr=44100, **kw: synth_double_laugh(f, d, v, sr),
    "bass": lambda f, d, v=0.90, sr=44100, **kw: synth_reese_bass(f, d, v, sr),
    "sub_bass": lambda f, d, v=0.90, sr=44100, **kw: synth_reese_bass(f, d, v, sr),
    "reese": lambda f, d, v=0.90, sr=44100, **kw: synth_reese_bass(f, d, v, sr),
    "reese_growl": lambda f, d, v=0.90, sr=44100, **kw: synth_reese_bass(f, d, v, sr),
    "lead": lambda f, d, v=0.85, sr=44100, **kw: synth_y2k_electronic(f, d, v, sr, patch="lead_soar"),
    "synth_lead": lambda f, d, v=0.85, sr=44100, **kw: synth_y2k_electronic(f, d, v, sr, patch="lead_soar"),
    "y2k_fm_bass": lambda f, d, v=0.85, sr=44100, **kw: synth_y2k_electronic(f, d, v, sr, patch="fm_bass"),
    "y2k_acid_lead": lambda f, d, v=0.85, sr=44100, **kw: synth_y2k_electronic(f, d, v, sr, patch="acid_lead"),
    "y2k_arp": lambda f, d, v=0.80, sr=44100, **kw: synth_y2k_electronic(f, d, v, sr, patch="tracker_arp"),
}


def list_instruments() -> List[str]:
    return sorted(INSTRUMENTS.keys())


def synthesize_note(
    instrument: str,
    freq: float,
    duration: float,
    velocity: float = 0.85,
    sr: int = 44100,
    **kwargs,
) -> np.ndarray:
    fn = INSTRUMENTS.get(instrument.lower(), INSTRUMENTS["lead"])
    return fn(freq, duration, velocity, sr, **kwargs)

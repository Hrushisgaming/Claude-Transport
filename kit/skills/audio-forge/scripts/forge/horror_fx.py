#!/usr/bin/env python3
"""
horror_fx.py - Hunted / Unsettling Chase Sound Design & Dread FX Engine.

Implements concrete horror/chase techniques modeled from A Grave Soul, Eternal Hope Eternal Fight,
and 2008 UNARCHIVED Roblox aesthetics:
  - 1.0-second mechanical clock ticks (with subtle spring jitter so it feels alive, not robotic)
  - 5.0-second resonant tower clock bell chimes (e.g., 0:35 to 0:50 middle breakdown)
  - Double-hit maniacal "HA-HA!" laugh timed onto beat drops
  - Sudden dead-silence chokes / drop-outs (150-350 ms) with optional reverse suction before hits
  - Left-to-right stereo crawling noise bursts
  - Tape-stop pitch dive & abrupt cut-off with hollow decaying drone tail
  - Occasional 2008 UNARCHIVED Roblox digital glitch / bit-drop artifacts
"""

from __future__ import annotations

import math
from typing import Any, Dict, Optional

import numpy as np

from .instruments import biquad_filter, stereoize, synth_bell, synth_clock_tick, synth_double_laugh


def db_to_lin(db_val: float) -> float:
    return float(10.0 ** (db_val / 20.0))


def generate_clock_tick_layer(
    total_duration: float,
    sr: int = 44100,
    interval_sec: float = 1.0,
    jitter_ms: float = 9.0,
    level_db: float = -13.0,
    mute_windows: Optional[list[tuple[float, float]]] = None,
) -> np.ndarray:
    """Generate an audible-but-balanced 1-second clock tick-tock layer across the track."""
    n_total = int(math.ceil(total_duration * sr))
    out = np.zeros((n_total, 2), dtype=np.float32)
    rng = np.random.default_rng(2008)
    gain = db_to_lin(level_db)

    t = 0.0
    step_idx = 0
    while t < total_duration - 0.2:
        muted = False
        if mute_windows:
            for w0, w1 in mute_windows:
                if w0 <= t <= w1:
                    muted = True
                    break
        if not muted:
            jitter = rng.uniform(-jitter_ms, jitter_ms) * 0.001
            pos = max(0, int((t + jitter) * sr))
            tick = synth_clock_tick(duration=0.18, velocity=0.80, sr=sr, is_tock=(step_idx % 2 == 1))
            end = min(n_total, pos + len(tick))
            out[pos:end] += tick[: end - pos] * gain
        t += interval_sec
        step_idx += 1

    return out


def generate_clock_bell_layer(
    total_duration: float,
    start_sec: float = 35.0,
    end_sec: float = 50.0,
    interval_sec: float = 5.0,
    freq: float = 146.83,
    sr: int = 44100,
    level_db: float = -7.5,
) -> np.ndarray:
    """Noticeable, resonant clock bell every 5 seconds in the middle breakdown (35s - 50s)."""
    n_total = int(math.ceil(total_duration * sr))
    out = np.zeros((n_total, 2), dtype=np.float32)
    gain = db_to_lin(level_db)

    t = start_sec
    while t <= end_sec + 1e-4 and t < total_duration:
        pos = int(t * sr)
        bell = synth_bell(freq=freq, duration=4.6, velocity=0.90, sr=sr, bell_type="clock_bell")
        end = min(n_total, pos + len(bell))
        out[pos:end] += bell[: end - pos] * gain
        t += interval_sec

    return out


def generate_stereo_crawl(
    total_duration: float,
    sr: int = 44100,
    rate_hz: float = 0.24,
    level_db: float = -17.0,
) -> np.ndarray:
    """Filtered granular noise bursts that crawl back and forth across the L-R stereo field."""
    n_total = int(math.ceil(total_duration * sr))
    t = np.arange(n_total, dtype=np.float64) / sr
    rng = np.random.default_rng(909)

    raw = rng.normal(0.0, 1.0, n_total).astype(np.float32)
    gate = np.maximum(0.0, np.sin(2.0 * math.pi * 6.3 * t) * np.sin(2.0 * math.pi * 1.7 * t)) ** 2
    bursts = biquad_filter(raw * gate.astype(np.float32), "bandpass", 3400.0, sr=sr)

    pan = np.sin(2.0 * math.pi * rate_hz * t)
    l_gain = np.sqrt(0.5 * (1.0 - pan)).astype(np.float32)
    r_gain = np.sqrt(0.5 * (1.0 + pan)).astype(np.float32)
    gain = db_to_lin(level_db)

    return np.column_stack([bursts * l_gain * gain, bursts * r_gain * gain]).astype(np.float32)


def generate_roblox_2008_glitches(
    total_duration: float,
    timestamps: list[float],
    sr: int = 44100,
    level_db: float = -12.5,
) -> np.ndarray:
    """Subtle, occasional 2008 UNARCHIVED retro digital artifacts (sample-rate drop / square blip / static tear)."""
    n_total = int(math.ceil(total_duration * sr))
    out = np.zeros((n_total, 2), dtype=np.float32)
    gain = db_to_lin(level_db)

    for idx, ts in enumerate(timestamps):
        if ts >= total_duration - 0.3:
            continue
        dur = 0.16
        n_g = int(dur * sr)
        t = np.arange(n_g, dtype=np.float64) / sr
        stepped_f = 880.0 * (0.5 ** np.floor(t * 28.0))
        wave_g = np.sign(np.sin(2.0 * math.pi * stepped_f * t)).astype(np.float32)
        wave_g = np.round(wave_g * 16.0) / 16.0
        wave_g = biquad_filter(wave_g, "bandpass", 1600.0, sr=sr)
        env = np.exp(-t * 14.0).astype(np.float32)
        st = stereoize(wave_g * env * gain, width=0.75 if idx % 2 == 0 else -0.75, delay_ms=8.0, sr=sr)

        pos = int(ts * sr)
        end = min(n_total, pos + n_g)
        out[pos:end] += st[: end - pos]

    return out


def apply_silence_choke(
    audio: np.ndarray,
    choke_start_sec: float,
    choke_dur_sec: float = 0.28,
    sr: int = 44100,
    reverse_suction: bool = True,
) -> np.ndarray:
    """Cut all audio abruptly before a major hit, optionally replacing with a faint reverse-suction swell."""
    out = audio.copy()
    i0 = max(0, int(choke_start_sec * sr))
    i1 = min(len(out), int((choke_start_sec + choke_dur_sec) * sr))
    if i1 <= i0:
        return out

    fade = min(int(0.008 * sr), i1 - i0)
    out[i0 : i0 + fade] *= np.linspace(1.0, 0.0, fade)[:, None]
    out[i0 + fade : i1] = 0.0

    if reverse_suction:
        n_suc = i1 - i0
        rng = np.random.default_rng(313)
        noise = rng.normal(0.0, 0.14, n_suc).astype(np.float32)
        noise = biquad_filter(noise, "bandpass", 1900.0, sr=sr)
        ramp = (np.linspace(0.0, 1.0, n_suc) ** 3).astype(np.float32)
        out[i0:i1, 0] += noise * ramp
        out[i0:i1, 1] += noise * ramp

    return out


def apply_tape_stop(audio: np.ndarray, start_sec: float, stop_dur_sec: float = 0.50, sr: int = 44100) -> np.ndarray:
    """Smooth vinyl/tape deceleration pitch-dive."""
    out = audio.copy()
    i0 = max(0, int(start_sec * sr))
    i1 = min(len(out), int((start_sec + stop_dur_sec) * sr))
    n = i1 - i0
    if n <= 32:
        return out

    u = np.linspace(0.0, 1.0, n)
    read_pos = i0 + np.cumsum(1.0 - 0.88 * (u ** 1.6))
    read_pos = np.clip(read_pos, 0, len(audio) - 1)
    idx_floor = np.floor(read_pos).astype(int)
    frac = (read_pos - idx_floor)[:, None]
    idx_ceil = np.minimum(idx_floor + 1, len(audio) - 1)

    stopped = (1.0 - frac) * audio[idx_floor] + frac * audio[idx_ceil]
    fade = np.linspace(1.0, 0.0, n)[:, None]
    out[i0:i1] = (stopped * fade).astype(np.float32)
    return out


def apply_dread_fx(audio: np.ndarray, sr: int = 44100, config: Optional[Dict[str, Any]] = None) -> np.ndarray:
    """Master hook for recipe.py / song.py: applies clock ticks, 5s middle bells, double HA-HA laugh, etc."""
    cfg = config or {}
    total_dur = len(audio) / sr
    out = audio.copy()

    for d in cfg.get("dropouts", []):
        out = apply_silence_choke(
            out,
            choke_start_sec=float(d["start_sec"]),
            choke_dur_sec=float(d.get("duration_sec", 0.28)),
            sr=sr,
            reverse_suction=bool(d.get("reverse_suction", True)),
        )

    for laugh in cfg.get("laughs", []):
        pos = int(float(laugh["time_sec"]) * sr)
        ha = synth_double_laugh(
            base_freq=float(laugh.get("pitch_hz", 165.0)),
            duration=0.68,
            velocity=float(laugh.get("velocity", 0.90)),
            sr=sr,
        )
        end = min(len(out), pos + len(ha))
        if end > pos:
            out[pos:end] += ha[: end - pos]

    if cfg.get("clock_tick", {}).get("enabled", True):
        tc = cfg.get("clock_tick", {})
        out += generate_clock_tick_layer(
            total_duration=total_dur,
            sr=sr,
            interval_sec=float(tc.get("interval_sec", 1.0)),
            jitter_ms=float(tc.get("jitter_ms", 8.0)),
            level_db=float(tc.get("level_db", -13.5)),
        )

    if cfg.get("clock_bell", {}).get("enabled", True):
        bc = cfg.get("clock_bell", {})
        out += generate_clock_bell_layer(
            total_duration=total_dur,
            start_sec=float(bc.get("start_sec", 35.0)),
            end_sec=float(bc.get("end_sec", 50.0)),
            interval_sec=float(bc.get("interval_sec", 5.0)),
            freq=float(bc.get("freq_hz", 146.83)),
            sr=sr,
            level_db=float(bc.get("level_db", -7.5)),
        )

    if cfg.get("stereo_crawl", {}).get("enabled", True):
        sc = cfg.get("stereo_crawl", {})
        out += generate_stereo_crawl(
            total_duration=total_dur,
            sr=sr,
            rate_hz=float(sc.get("rate_hz", 0.24)),
            level_db=float(sc.get("level_db", -17.5)),
        )

    glitches = cfg.get("roblox_glitches", [6.5, 21.8, 39.2, 58.4])
    if glitches:
        out += generate_roblox_2008_glitches(total_dur, timestamps=glitches, sr=sr, level_db=-13.0)

    peak = float(np.max(np.abs(out)))
    if peak > 0.96:
        out *= 0.96 / peak
    return out.astype(np.float32)

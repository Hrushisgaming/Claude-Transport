#!/usr/bin/env python3
"""
hear.py - High-Resolution Audio Diagnostic & Perceptual Analyzer for Text-Only AIs.

Designed so text-only LLMs can "see" every musical, harmonic, timbral, rhythmic,
stereo, and emotional detail of an audio track without needing audio perception.

Outputs:
  1. Executive Summary (Perceived Genre, Hunted/Dread Score 0-10, BPM, Key/Mode, Tuning Drift)
  2. Mix & Synthesis Health Diagnostics (Electronic Buzz/Aliasing detector, Vibrato/Wobble detector, Mud/Clipping)
  3. Structural Segmentation & Transition Map (Intro, Drops, Breakdowns, Silence Drop-outs, Ending Type)
  4. High-Resolution Time-Aligned Timeline ("Audio X-Ray" every N seconds)
  5. Harmony, Melody & Interval Tension Analysis (Tritones, Minor 2nds, Phrase Resolution)
  6. Rhythm, Drum Groove Grid (16-step) & Periodic Event Detection (1s Clock Ticks, 5s Bells, Laughs/Stutters)
  7. Stereo Field & Dry/Wet Contrast Analysis
  8. Full Machine-Readable JSON Payload
"""

import argparse
import json
import math
import os
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

import numpy as np
from scipy import signal
from scipy.fft import rfft, rfftfreq


NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

SCALE_PROFILES = {
    "Minor (Aeolian)":     np.array([1.0, 0.0, 0.7, 0.9, 0.0, 0.7, 0.0, 0.9, 0.7, 0.0, 0.7, 0.0]),
    "Phrygian (Dark b2)":  np.array([1.0, 0.85, 0.0, 0.9, 0.0, 0.7, 0.0, 0.9, 0.75, 0.0, 0.7, 0.0]),
    "Harmonic Minor":      np.array([1.0, 0.0, 0.7, 0.9, 0.0, 0.7, 0.0, 0.9, 0.8, 0.0, 0.0, 0.85]),
    "Locrian (Tritone)":   np.array([1.0, 0.8, 0.0, 0.85, 0.0, 0.7, 0.9, 0.0, 0.75, 0.0, 0.7, 0.0]),
    "Major (Ionian)":      np.array([1.0, 0.0, 0.7, 0.0, 0.9, 0.7, 0.0, 0.9, 0.0, 0.7, 0.0, 0.8]),
}


def fmt_time(sec: float) -> str:
    sec = max(0.0, float(sec))
    m = int(sec // 60)
    s = sec - m * 60
    return f"{m}:{s:05.2f}"


def fmt_time_short(sec: float) -> str:
    sec = max(0.0, float(sec))
    m = int(sec // 60)
    s = int(round(sec - m * 60))
    if s == 60:
        m += 1
        s = 0
    return f"{m}:{s:02d}"


def db(val: float, floor: float = -90.0) -> float:
    return float(max(floor, 20.0 * math.log10(max(val, 1e-12))))


def load_audio(filepath: str, target_sr: int = 44100) -> tuple[np.ndarray, int]:
    """Load WAV natively or decode MP3/OGG/M4A/FLAC via ffmpeg into float32 stereo (N, 2)."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {filepath}")

    ext = path.suffix.lower()
    wav_path = None
    cleanup = False

    if ext == ".wav":
        wav_path = str(path)
    else:
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp.close()
        wav_path = tmp.name
        cleanup = True
        cmd = [
            "ffmpeg", "-y", "-v", "error",
            "-i", str(path),
            "-ar", str(target_sr),
            "-ac", "2",
            "-sample_fmt", "s16",
            wav_path,
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            if os.path.exists(wav_path):
                os.remove(wav_path)
            raise RuntimeError(f"ffmpeg failed to decode {filepath}: {res.stderr}")

    try:
        with wave.open(wav_path, "rb") as wf:
            n_channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            sr = wf.getframerate()
            n_frames = wf.getnframes()
            raw = wf.readframes(n_frames)

        if sampwidth == 2:
            data = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
        elif sampwidth == 4:
            data = np.frombuffer(raw, dtype=np.int32).astype(np.float32) / 2147483648.0
        elif sampwidth == 1:
            data = (np.frombuffer(raw, dtype=np.uint8).astype(np.float32) - 128.0) / 128.0
        else:
            raise ValueError(f"Unsupported WAV sample width: {sampwidth}")

        if n_channels == 1:
            stereo = np.column_stack([data, data])
        else:
            stereo = data.reshape(-1, n_channels)[:, :2]
        return stereo, sr
    finally:
        if cleanup and wav_path and os.path.exists(wav_path):
            os.remove(wav_path)


def estimate_tempo_and_grid(mono: np.ndarray, sr: int) -> dict:
    """Estimate BPM (including DnB/breakcore 150-185 BPM range), confidence, and 16-step groove."""
    hop = 512
    frame_len = 2048
    n_frames = max(1, (len(mono) - frame_len) // hop)
    win = np.hanning(frame_len)
    prev_mag = None
    flux = np.zeros(n_frames, dtype=np.float32)
    low_flux = np.zeros(n_frames, dtype=np.float32)
    mid_flux = np.zeros(n_frames, dtype=np.float32)
    high_flux = np.zeros(n_frames, dtype=np.float32)

    freqs = rfftfreq(frame_len, 1.0 / sr)
    low_mask = (freqs >= 35) & (freqs < 150)
    mid_mask = (freqs >= 150) & (freqs < 2500)
    high_mask = (freqs >= 4000) & (freqs < 14000)

    for i in range(n_frames):
        seg = mono[i * hop : i * hop + frame_len] * win
        mag = np.abs(rfft(seg))
        if prev_mag is not None:
            diff = np.maximum(0.0, mag - prev_mag)
            flux[i] = np.sum(diff)
            low_flux[i] = np.sum(diff[low_mask])
            mid_flux[i] = np.sum(diff[mid_mask])
            high_flux[i] = np.sum(diff[high_mask])
        prev_mag = mag

    env = flux - np.mean(flux)
    if np.std(env) < 1e-8 or len(env) < 32:
        return {"bpm": 120.0, "confidence": "low", "half_time_bpm": 60.0, "drum_grid_16": {}}

    autocorr = signal.correlate(env, env, mode="full")[len(env) - 1 :]
    fps = sr / hop
    min_lag = int(fps * 60.0 / 195.0)
    max_lag = int(fps * 60.0 / 75.0)
    max_lag = min(max_lag, len(autocorr) - 1)

    search = autocorr[min_lag:max_lag].copy()
    lags = np.arange(min_lag, max_lag)
    bpms = 60.0 * fps / np.maximum(lags, 1)

    prior = np.exp(-0.5 * ((bpms - 165.0) / 38.0) ** 2) * 0.25 + 0.75
    weighted = search * prior
    best_idx = int(np.argmax(weighted))
    best_lag = lags[best_idx]
    bpm = float(60.0 * fps / best_lag)

    if 80.0 <= bpm <= 95.0:
        half_lag = int(round(best_lag / 2.0))
        if half_lag >= min_lag and autocorr[half_lag] > 0.55 * autocorr[best_lag]:
            bpm *= 2.0
            best_lag = half_lag

    peak_ratio = float(autocorr[best_lag] / max(autocorr[0], 1e-8))
    confidence = "high" if peak_ratio > 0.35 else ("medium" if peak_ratio > 0.18 else "low")

    bar_frames = int(round(best_lag * 4))
    drum_grid = {}
    if bar_frames >= 16 and len(low_flux) >= bar_frames * 2:
        for name, band_env in [("kick", low_flux), ("snare", mid_flux), ("hat", high_flux)]:
            n_bars = len(band_env) // bar_frames
            folded = band_env[: n_bars * bar_frames].reshape(n_bars, bar_frames).mean(axis=0)
            steps = np.array([folded[int(s * bar_frames / 16) : int((s + 1) * bar_frames / 16)].mean() for s in range(16)])
            s_max = float(np.max(steps)) + 1e-8
            norm_steps = steps / s_max
            chars = []
            for v in norm_steps:
                if v >= 0.58:
                    chars.append("x")
                elif v >= 0.30:
                    chars.append("g")
                else:
                    chars.append(".")
            drum_grid[name] = "".join(chars)

    return {
        "bpm": round(bpm, 1),
        "half_time_bpm": round(bpm / 2.0, 1),
        "confidence": confidence,
        "periodicity_strength": round(peak_ratio, 3),
        "drum_grid_16": drum_grid,
    }


def analyze_harmony_and_tuning(mono: np.ndarray, sr: int) -> dict:
    """Compute chromagram, key/mode, tuning cents offset (A4=440Hz), and dissonance profile."""
    hop = 4096
    frame_len = 8192
    n_frames = max(1, (len(mono) - frame_len) // hop)
    win = np.hanning(frame_len)
    freqs = rfftfreq(frame_len, 1.0 / sr)
    valid = (freqs >= 55.0) & (freqs <= 3520.0)
    v_freqs = freqs[valid]
    midi_exact = 69.0 + 12.0 * np.log2(v_freqs / 440.0)
    midi_nearest = np.round(midi_exact)
    cents_diff = (midi_exact - midi_nearest) * 100.0
    pitch_classes = (midi_nearest.astype(int)) % 12

    chroma = np.zeros(12, dtype=np.float64)
    cents_hist = np.zeros(100, dtype=np.float64)
    frame_chromas = []

    step = max(1, n_frames // 160)
    for i in range(0, n_frames, step):
        seg = mono[i * hop : i * hop + frame_len] * win
        mag = np.abs(rfft(seg))[valid] ** 1.5
        fc = np.zeros(12, dtype=np.float64)
        for pc in range(12):
            fc[pc] = np.sum(mag[pitch_classes == pc])
        chroma += fc
        frame_chromas.append(fc / (np.sum(fc) + 1e-9))

        c_bins = np.clip(np.round(cents_diff + 50.0).astype(int), 0, 99)
        np.add.at(cents_hist, c_bins, mag)

    chroma /= np.sum(chroma) + 1e-9
    tuning_offset_cents = float(np.argmax(cents_hist) - 50.0)
    tuning_spread = float(
        np.sqrt(np.sum(((np.arange(100) - 50.0 - tuning_offset_cents) ** 2) * (cents_hist / (np.sum(cents_hist) + 1e-9))))
    )

    best_score = -1.0
    best_root = 0
    best_scale = "Minor (Aeolian)"
    for root in range(12):
        rolled = np.roll(chroma, -root)
        for s_name, prof in SCALE_PROFILES.items():
            score = float(np.dot(rolled, prof) / (np.linalg.norm(rolled) * np.linalg.norm(prof) + 1e-9))
            if score > best_score:
                best_score = score
                best_root = root
                best_scale = s_name

    rel = np.roll(chroma, -best_root)
    minor_2nd_weight = float(rel[1] / (rel[0] + 1e-6))
    tritone_weight = float(rel[6] / (rel[0] + 1e-6))
    dissonance_index = min(10.0, round((minor_2nd_weight + tritone_weight) * 5.2, 2))

    resolution_ratio = 0.5
    if len(frame_chromas) >= 8:
        fc_arr = np.array(frame_chromas)
        tonic_fifth = fc_arr[:, best_root] + fc_arr[:, (best_root + 7) % 12]
        boundaries = tonic_fifth[::4]
        resolution_ratio = float(np.mean(boundaries) / (np.mean(tonic_fifth) + 1e-6))

    in_tune_status = "clean"
    if abs(tuning_offset_cents) > 18:
        in_tune_status = f"OFF-TUNE ({tuning_offset_cents:+.0f} cents from A4=440Hz)"
    elif tuning_spread > 24:
        in_tune_status = f"DETUNED / PITCH DRIFT (spread +/-{tuning_spread:.0f} cents)"

    return {
        "estimated_key": f"{NOTE_NAMES[best_root]} {best_scale}",
        "key_confidence": "high" if best_score > 0.86 else ("medium" if best_score > 0.78 else "low"),
        "tuning_offset_cents": round(tuning_offset_cents, 1),
        "pitch_spread_cents": round(tuning_spread, 1),
        "tuning_health": in_tune_status,
        "minor_2nd_presence": round(minor_2nd_weight, 3),
        "tritone_presence": round(tritone_weight, 3),
        "dissonance_0_to_10": dissonance_index,
        "cadence_resolution_ratio": round(resolution_ratio, 3),
        "top_pitch_classes": [
            {"note": NOTE_NAMES[i], "weight": round(float(chroma[i]), 3)}
            for i in np.argsort(chroma)[::-1][:5]
        ],
    }


def analyze_timbre_and_health(stereo: np.ndarray, sr: int) -> dict:
    """Detect electronic buzz/aliasing, excessive vibrato/wobble, low-mid mud, and dry/wet contrast."""
    mono = np.mean(stereo, axis=1)
    side = 0.5 * (stereo[:, 0] - stereo[:, 1])
    mid = 0.5 * (stereo[:, 0] + stereo[:, 1])

    n_fft = min(len(mono), 131072)
    start = max(0, len(mono) // 4)
    chunk = mono[start : start + n_fft]
    spec = np.abs(rfft(chunk * np.hanning(len(chunk))))
    freqs = rfftfreq(len(chunk), 1.0 / sr)

    def band_energy(f_lo: float, f_hi: float) -> float:
        m = (freqs >= f_lo) & (freqs < f_hi)
        return float(np.sqrt(np.mean(spec[m] ** 2))) if np.any(m) else 1e-9

    sub_e = band_energy(25, 80)
    bass_e = band_energy(80, 250)
    mud_e = band_energy(250, 600)
    mid_e = band_energy(600, 2000)
    pres_e = band_energy(2000, 5000)
    buzz_e = band_energy(5000, 11000)
    air_e = band_energy(11000, 18000)
    total_e = band_energy(25, 18000)

    buzz_ratio = buzz_e / (mid_e + 1e-8)
    buzz_flatness = float(
        np.exp(np.mean(np.log(spec[(freqs >= 5000) & (freqs < 11000)] + 1e-9)))
        / (np.mean(spec[(freqs >= 5000) & (freqs < 11000)]) + 1e-9)
    )
    electronic_buzz_score = min(10.0, round(buzz_ratio * 14.0 * (1.0 - 0.4 * buzz_flatness), 2))

    sos_pres = signal.butter(3, [1200, 4500], btype="bandpass", fs=sr, output="sos")
    pres_sig = signal.sosfilt(sos_pres, chunk)
    env = np.abs(signal.hilbert(pres_sig))
    ds = max(1, sr // 100)
    env_ds = env[::ds] - np.mean(env[::ds])
    env_spec = np.abs(rfft(env_ds * np.hanning(len(env_ds))))
    env_freqs = rfftfreq(len(env_ds), ds / sr)
    vib_band = env_spec[(env_freqs >= 4.5) & (env_freqs <= 8.5)]
    base_band = env_spec[(env_freqs >= 0.5) & (env_freqs < 4.5)]
    wobble_ratio = float(np.max(vib_band) / (np.mean(base_band) + 1e-8)) if len(vib_band) else 0.0
    vibrato_wobble_score = min(10.0, round(wobble_ratio * 2.4, 2))

    stereo_width = float(np.sqrt(np.mean(side ** 2)) / (np.sqrt(np.mean(mid ** 2)) + 1e-8))
    win_s = int(0.25 * sr)
    widths = []
    for pos in range(0, len(mono) - win_s, win_s):
        m_rms = np.sqrt(np.mean(mid[pos : pos + win_s] ** 2)) + 1e-8
        s_rms = np.sqrt(np.mean(side[pos : pos + win_s] ** 2))
        widths.append(s_rms / m_rms)
    dry_wet_contrast = float(np.std(widths) / (np.mean(widths) + 1e-6)) if widths else 0.0

    peak = float(np.max(np.abs(stereo)))
    rms = float(np.sqrt(np.mean(stereo ** 2)))
    crest_db = round(db(peak) - db(rms), 2)
    clipped_samples = int(np.sum(np.abs(stereo) >= 0.995))

    warnings = []
    if electronic_buzz_score >= 5.5:
        warnings.append(
            f"HIGH ELECTRONIC BUZZ ({electronic_buzz_score}/10): Strong static/aliased harmonics in 5-11 kHz; instruments sound synthetic/buzzy rather than acoustic."
        )
    if vibrato_wobble_score >= 5.0:
        warnings.append(
            f"EXCESSIVE VIBRATO/WOBBLE ({vibrato_wobble_score}/10): Strong 5-8 Hz amplitude/pitch oscillation makes instruments sound 'vibrating' or seasick."
        )
    if mud_e / (bass_e + 1e-8) > 1.15:
        warnings.append(
            "LOW-MID MUD (250-600 Hz): Heavy frequency masking between bass, guitars, organ, and strings."
        )
    if dry_wet_contrast < 0.25:
        warnings.append(
            "UNIFORM ROOM REVERB: Little contrast between bone-dry close hits and distant wet tails (makes chase music feel flat)."
        )
    if clipped_samples > 20:
        warnings.append(f"DIGITAL CLIPPING: {clipped_samples} samples hit >= -0.04 dBFS.")

    return {
        "overall_rms_dbfs": round(db(rms), 2),
        "peak_dbfs": round(db(peak), 2),
        "crest_factor_db": crest_db,
        "band_balance_relative": {
            "sub_25_80hz": round(sub_e / (total_e + 1e-8), 3),
            "bass_80_250hz": round(bass_e / (total_e + 1e-8), 3),
            "low_mid_250_600hz": round(mud_e / (total_e + 1e-8), 3),
            "mid_600_2000hz": round(mid_e / (total_e + 1e-8), 3),
            "presence_2_5khz": round(pres_e / (total_e + 1e-8), 3),
            "buzz_5_11khz": round(buzz_e / (total_e + 1e-8), 3),
            "air_11_18khz": round(air_e / (total_e + 1e-8), 3),
        },
        "electronic_buzz_0_to_10": electronic_buzz_score,
        "vibrato_wobble_0_to_10": vibrato_wobble_score,
        "stereo_width_ratio": round(stereo_width, 3),
        "dry_wet_contrast_index": round(dry_wet_contrast, 3),
        "health_warnings": warnings,
    }


def detect_periodic_events_and_structure(stereo: np.ndarray, sr: int, bpm: float) -> dict:
    """Detect silence drop-outs, 1s clock ticks, 5s clock bells, sudden cuts, and section boundaries."""
    mono = np.mean(stereo, axis=1)
    duration = len(mono) / sr

    win_50ms = int(0.05 * sr)
    n_50 = len(mono) // win_50ms
    rms_50 = np.array([np.sqrt(np.mean(mono[i * win_50ms : (i + 1) * win_50ms] ** 2)) for i in range(n_50)])
    db_50 = np.array([db(x) for x in rms_50])

    dropouts = []
    in_drop = False
    drop_start = 0.0
    for i in range(1, n_50 - 1):
        lo = max(0, i - 15)
        hi = min(n_50, i + 15)
        local_med = float(np.median(db_50[lo:hi]))
        if db_50[i] < local_med - 14.0 and local_med > -36.0:
            if not in_drop:
                in_drop = True
                drop_start = i * 0.05
        else:
            if in_drop:
                dur_ms = int(round((i * 0.05 - drop_start) * 1000))
                if dur_ms >= 80:
                    dropouts.append({
                        "start": fmt_time(drop_start),
                        "end": fmt_time(i * 0.05),
                        "duration_ms": dur_ms,
                    })
                in_drop = False

    sos_tick = signal.butter(3, [1800, 6500], btype="bandpass", fs=sr, output="sos")
    tick_env = np.abs(signal.hilbert(signal.sosfilt(sos_tick, mono)))
    ds_100 = max(1, sr // 100)
    t_env = tick_env[::ds_100]
    t_ac = signal.correlate(t_env - np.mean(t_env), t_env - np.mean(t_env), mode="full")[len(t_env) - 1 :]
    lag_1s = 100
    clock_tick_score = 0.0
    if len(t_ac) > lag_1s + 5:
        local_peak = float(np.max(t_ac[lag_1s - 3 : lag_1s + 4]))
        clock_tick_score = round(local_peak / max(float(t_ac[0]), 1e-8), 3)

    sos_bell = signal.butter(3, [350, 1600], btype="bandpass", fs=sr, output="sos")
    bell_env = np.abs(signal.hilbert(signal.sosfilt(sos_bell, mono)))[::ds_100]
    b_ac = signal.correlate(bell_env - np.mean(bell_env), bell_env - np.mean(bell_env), mode="full")[len(bell_env) - 1 :]
    lag_5s = 500
    clock_bell_5s_score = 0.0
    if len(b_ac) > lag_5s + 10:
        b_peak = float(np.max(b_ac[lag_5s - 8 : lag_5s + 9]))
        clock_bell_5s_score = round(b_peak / max(float(b_ac[0]), 1e-8), 3)

    tail_sec = min(4.0, duration * 0.25)
    tail = mono[-int(tail_sec * sr) :]
    tail_chunks = np.array_split(tail, 8)
    tail_dbs = [db(float(np.sqrt(np.mean(c ** 2)))) for c in tail_chunks]
    if tail_dbs[-1] < tail_dbs[0] - 24.0 and tail_dbs[2] < tail_dbs[0] - 15.0:
        ending_type = "abrupt cut-off into hollow decaying tail"
    elif tail_dbs[-1] > tail_dbs[0] - 6.0:
        ending_type = "hard abrupt cut-off at peak energy"
    elif tail_dbs[-1] < tail_dbs[0] - 14.0:
        ending_type = "gradual fade / cool-down decay"
    else:
        ending_type = "sustained chord release / tape-stop tail"

    n_sec = max(1, int(math.floor(duration)))
    sec_rms = []
    sec_sub = []
    sec_pan = []
    sos_sub = signal.butter(2, 95, btype="lowpass", fs=sr, output="sos")
    sub_sig = signal.sosfilt(sos_sub, mono)

    for s in range(n_sec):
        sl = slice(s * sr, (s + 1) * sr)
        sec_rms.append(db(float(np.sqrt(np.mean(mono[sl] ** 2)))))
        sec_sub.append(db(float(np.sqrt(np.mean(sub_sig[sl] ** 2)))))
        l_e = float(np.sqrt(np.mean(stereo[sl, 0] ** 2))) + 1e-8
        r_e = float(np.sqrt(np.mean(stereo[sl, 1] ** 2))) + 1e-8
        sec_pan.append(round((r_e - l_e) / (r_e + l_e), 3))

    med_db = float(np.median(sec_rms))
    sections = []
    cur_label = None
    cur_start = 0
    for s in range(n_sec):
        if sec_rms[s] >= med_db - 1.5 and sec_sub[s] >= np.median(sec_sub) - 2.5:
            lbl = "HIGH-ENERGY DROP / CHASE WALL"
        elif sec_rms[s] < med_db - 4.0:
            lbl = "SPARSE / TENSION BREAKDOWN"
        else:
            lbl = "BUILD / TRANSITION"
        if lbl != cur_label:
            if cur_label is not None:
                bars_est = round((s - cur_start) * (bpm / 60.0) / 4.0, 1)
                sections.append({
                    "start": fmt_time_short(cur_start),
                    "end": fmt_time_short(s),
                    "duration_sec": s - cur_start,
                    "estimated_bars": bars_est,
                    "role": cur_label,
                })
            cur_label = lbl
            cur_start = s
    if cur_label is not None:
        bars_est = round((n_sec - cur_start) * (bpm / 60.0) / 4.0, 1)
        sections.append({
            "start": fmt_time_short(cur_start),
            "end": fmt_time_short(n_sec),
            "duration_sec": n_sec - cur_start,
            "estimated_bars": bars_est,
            "role": cur_label,
        })

    return {
        "duration_sec": round(duration, 2),
        "duration_fmt": fmt_time_short(duration),
        "sections": sections,
        "silence_dropouts": dropouts[:12],
        "periodic_1s_clock_tick_score": clock_tick_score,
        "periodic_5s_clock_bell_score": clock_bell_5s_score,
        "ending_type": ending_type,
        "stereo_pan_drift_std": round(float(np.std(sec_pan)), 3),
    }


def build_timeline(stereo: np.ndarray, sr: int, step_sec: float = 2.0) -> list[dict]:
    """Generate a dense second-by-second / step-by-step Audio X-Ray for text-only AI reading."""
    mono = np.mean(stereo, axis=1)
    side = 0.5 * (stereo[:, 0] - stereo[:, 1])
    mid = 0.5 * (stereo[:, 0] + stereo[:, 1])
    duration = len(mono) / sr
    n_steps = int(math.ceil(duration / step_sec))

    timeline = []
    for idx in range(n_steps):
        t0 = idx * step_sec
        t1 = min(duration, (idx + 1) * step_sec)
        seg = mono[int(t0 * sr) : int(t1 * sr)]
        if len(seg) < 64:
            continue
        m_seg = mid[int(t0 * sr) : int(t1 * sr)]
        s_seg = side[int(t0 * sr) : int(t1 * sr)]

        rms_val = float(np.sqrt(np.mean(seg ** 2)))
        peak_val = float(np.max(np.abs(seg)))
        crest = round(db(peak_val) - db(rms_val), 1)
        width = round(float(np.sqrt(np.mean(s_seg ** 2)) / (np.sqrt(np.mean(m_seg ** 2)) + 1e-8)), 2)

        spec = np.abs(rfft(seg * np.hanning(len(seg))))
        freqs = rfftfreq(len(seg), 1.0 / sr)
        centroid = float(np.sum(freqs * spec) / (np.sum(spec) + 1e-8))

        mel_mask = (freqs >= 180) & (freqs <= 1600)
        if np.any(mel_mask) and np.max(spec[mel_mask]) > 0:
            dom_f = float(freqs[mel_mask][int(np.argmax(spec[mel_mask]))])
            midi_n = int(round(69 + 12 * math.log2(max(dom_f, 20.0) / 440.0)))
            dom_note = f"{NOTE_NAMES[midi_n % 12]}{midi_n // 12 - 1}"
        else:
            dom_note = "-"

        tags = []
        if db(rms_val) < -32.0:
            tags.append("QUIET/SPARSE")
        elif db(rms_val) > -11.5:
            tags.append("LOUD_WALL")
        if crest > 15.5:
            tags.append("PUNCHY_TRANSIENTS")
        elif crest < 8.5:
            tags.append("COMPRESSED/DENSE")
        if width > 0.55:
            tags.append("WIDE_WET")
        elif width < 0.22:
            tags.append("DRY_CENTER")
        if centroid > 2600:
            tags.append("BRIGHT/HARSH")
        elif centroid < 950:
            tags.append("DARK_SUB")

        timeline.append({
            "time": f"{fmt_time_short(t0)}-{fmt_time_short(t1)}",
            "rms_db": round(db(rms_val), 1),
            "crest_db": crest,
            "centroid_hz": int(round(centroid)),
            "stereo_w": width,
            "dom_pitch": dom_note,
            "cues": tags,
        })

    return timeline


def compute_hunted_unsettling_score(harmony: dict, timbre: dict, struct: dict) -> dict:
    """Compute an objective 0-10 Hunted/Unsettling score with transparent breakdown."""
    score = 2.0
    reasons = []

    diss = harmony["dissonance_0_to_10"]
    score += min(2.5, diss * 0.35)
    if diss >= 4.5:
        reasons.append(f"+Strong tritone/minor-2nd tension ({diss}/10)")
    else:
        reasons.append(f"-Low harmonic dissonance ({diss}/10); leans heroic/safe")

    n_drops = len(struct["silence_dropouts"])
    if n_drops >= 2:
        score += 1.5
        reasons.append(f"+{n_drops} sudden silence drop-outs/chokes create dread")
    else:
        reasons.append("-Few/no sudden drop-outs before hits")

    dwc = timbre["dry_wet_contrast_index"]
    if dwc >= 0.38:
        score += 1.3
        reasons.append(f"+Strong dry-vs-wet spatial contrast ({dwc:.2f})")
    else:
        reasons.append(f"-Uniform reverb space ({dwc:.2f}); lacks close-vs-distant shock")

    if struct["periodic_1s_clock_tick_score"] >= 0.12 or struct["periodic_5s_clock_bell_score"] >= 0.12:
        score += 1.2
        reasons.append("+Audible periodic clock/bell dread markers")

    if harmony["cadence_resolution_ratio"] < 0.95:
        score += 1.0
        reasons.append("+Melodic phrases avoid comfortable tonic resolution")
    else:
        reasons.append("-Phrases resolve neatly on tonic/fifth (feels like action victory)")

    if timbre["electronic_buzz_0_to_10"] >= 6.5:
        score -= 0.7
        reasons.append("-Harsh static buzz reduces acoustic realism")

    final_score = round(float(np.clip(score, 0.0, 10.0)), 1)
    verdict = (
        "HUNTED / UNSETTLING HORROR CHASE"
        if final_score >= 6.8
        else ("TENSE HYBRID (PARTIAL HORROR, PARTIAL ACTION)" if final_score >= 4.8 else "ENERGETIC ACTION / HEROIC BATTLE (NOT UNSETTLING ENOUGH)")
    )
    return {
        "unsettling_0_to_10": final_score,
        "verdict": verdict,
        "breakdown": reasons,
    }


def analyze_audio(filepath: str, step_sec: float = 2.0) -> dict:
    stereo, sr = load_audio(filepath)
    mono = np.mean(stereo, axis=1)

    tempo_info = estimate_tempo_and_grid(mono, sr)
    harmony_info = analyze_harmony_and_tuning(mono, sr)
    timbre_info = analyze_timbre_and_health(stereo, sr)
    struct_info = detect_periodic_events_and_structure(stereo, sr, tempo_info["bpm"])
    timeline = build_timeline(stereo, sr, step_sec=step_sec)
    unsettling_info = compute_hunted_unsettling_score(harmony_info, timbre_info, struct_info)

    return {
        "file": os.path.basename(filepath),
        "sample_rate": sr,
        "perceptual_summary": unsettling_info,
        "tempo_and_rhythm": tempo_info,
        "harmony_and_tuning": harmony_info,
        "timbre_and_mix_health": timbre_info,
        "structure_and_events": struct_info,
        "timeline": timeline,
    }


def format_report(data: dict) -> str:
    p = data["perceptual_summary"]
    t = data["tempo_and_rhythm"]
    h = data["harmony_and_tuning"]
    m = data["timbre_and_mix_health"]
    s = data["structure_and_events"]
    fence = "`" * 3

    lines = [
        f"# AUDIO X-RAY REPORT: `{data['file']}`",
        f"- **Duration**: `{s['duration_fmt']}` ({s['duration_sec']}s) | **Sample Rate**: `{data['sample_rate']} Hz`",
        f"- **Verdict**: **{p['verdict']}** (Unsettling Score: **{p['unsettling_0_to_10']}/10**)",
        f"- **Tempo**: **{t['bpm']} BPM** (half-time: {t['half_time_bpm']} BPM, confidence: `{t['confidence']}`)",
        f"- **Key & Mode**: **{h['estimated_key']}** (confidence: `{h['key_confidence']}`) | **Tuning**: `{h['tuning_health']}`",
        "",
        "## 1. Hunted vs. Action Breakdown",
    ]
    for r in p["breakdown"]:
        lines.append(f"- {r}")

    lines.extend([
        "",
        "## 2. Synthesis & Mix Health Diagnostics",
        f"- **Loudness**: RMS `{m['overall_rms_dbfs']} dBFS` | Peak `{m['peak_dbfs']} dBFS` | Crest Factor `{m['crest_factor_db']} dB`",
        f"- **Electronic Buzz / Aliasing Score**: `{m['electronic_buzz_0_to_10']}/10`",
        f"- **Vibrato / Pitch-Wobble Score**: `{m['vibrato_wobble_0_to_10']}/10`",
        f"- **Stereo Width**: `{m['stereo_width_ratio']}` | **Dry/Wet Contrast Index**: `{m['dry_wet_contrast_index']}`",
    ])
    if m["health_warnings"]:
        lines.append("- **Warnings**:")
        for w in m["health_warnings"]:
            lines.append(f"  - [WARNING] {w}")
    else:
        lines.append("- **Warnings**: None (clean synthesis & balanced dynamics)")

    lines.extend([
        "",
        "## 3. Harmony, Dissonance & Interval Profile",
        f"- **Dissonance Score**: `{h['dissonance_0_to_10']}/10` (Minor 2nd weight: `{h['minor_2nd_presence']}`, Tritone weight: `{h['tritone_presence']}`)",
        f"- **Phrase Resolution Ratio**: `{h['cadence_resolution_ratio']}` (<0.95 = unresolved/tense, >1.0 = resolves cleanly)",
        "- **Dominant Pitch Classes**: " + ", ".join(f"{x['note']} ({x['weight']})" for x in h["top_pitch_classes"]),
        "",
        "## 4. Structure, Silence Drop-Outs & Periodic Cues",
        f"- **Ending Behavior**: `{s['ending_type']}`",
        f"- **1.0s Clock Tick Score**: `{s['periodic_1s_clock_tick_score']}` | **5.0s Clock Bell Score**: `{s['periodic_5s_clock_bell_score']}`",
        "### Sections:",
    ])
    for sec in s["sections"]:
        lines.append(f"- `{sec['start']} - {sec['end']}` ({sec['duration_sec']}s, ~{sec['estimated_bars']} bars): **{sec['role']}**")

    if s["silence_dropouts"]:
        lines.append("### Sudden Silence Drop-Outs / Chokes:")
        for d in s["silence_dropouts"]:
            lines.append(f"- `{d['start']} - {d['end']}` ({d['duration_ms']} ms)")
    else:
        lines.append("### Sudden Silence Drop-Outs / Chokes:
- None detected")

    if t.get("drum_grid_16"):
        lines.extend(["", "## 5. Extracted 16-Step Drum Groove (`x`=hit, `g`=ghost, `.`=rest)"])
        for part, grid in t["drum_grid_16"].items():
            lines.append(f"- `{part:<6}`: `{grid}`")

    lines.extend([
        "",
        "## 6. Second-by-Second Audio X-Ray Timeline",
        "| Time | RMS (dB) | Crest | Centroid | Width | Pitch | Sonic Cues |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :--- |",
    ])
    for row in data["timeline"]:
        cues = ", ".join(row["cues"]) if row["cues"] else "-"
        lines.append(
            f"| `{row['time']}` | {row['rms_db']} | {row['crest_db']} | {row['centroid_hz']} Hz | {row['stereo_w']} | {row['dom_pitch']} | {cues} |"
        )

    lines.extend([
        "",
        "## 7. Machine-Readable JSON",
        f"{fence}json",
        json.dumps(data, indent=2),
        f"{fence}",
    ])
    return "
".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="High-resolution audio diagnostic analyzer for text-only AIs.")
    parser.add_argument("audio", nargs="+", help="Path(s) to audio file(s) (.wav, .mp3, .ogg, .m4a)")
    parser.add_argument("--step", type=float, default=2.0, help="Timeline resolution in seconds (default: 2.0)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON only")
    parser.add_argument("-o", "--out", type=str, default="", help="Optional output file path")
    args = parser.parse_args()

    results = [analyze_audio(path, step_sec=args.step) for path in args.audio]

    if args.json:
        payload = results[0] if len(results) == 1 else {"tracks": results}
        output = json.dumps(payload, indent=2)
    else:
        output = "

---

".join(format_report(r) for r in results)

    if args.out:
        Path(args.out).write_text(output, encoding="utf-8")
        print(f"Saved Audio X-Ray report to {args.out}")
    else:
        print(output)


if __name__ == "__main__":
    main()

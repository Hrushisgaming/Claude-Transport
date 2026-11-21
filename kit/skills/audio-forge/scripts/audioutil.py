#!/usr/bin/env python3
"""audioutil.py - shared audio IO + measurement helpers for the audio-forge V2 tools.

Used by loop_doctor.py, stem_mix.py, audition.py and adapt.py. It is an internal
helper, not a command: everything a person needs is reachable through af.py.

Everything here is numpy/scipy only (plus ffmpeg for non-WAV decoding and loudness).
"""
import json
import os
import re
import subprocess
import tempfile

import numpy as np

try:
    from scipy.io import wavfile
except Exception:                                   # pragma: no cover
    wavfile = None


# ── IO ───────────────────────────────────────────────────────────────────────
def read_audio(path, sr=None, max_seconds=None):
    """-> (x float64 [n, channels], sample_rate). WAV via scipy, anything else via ffmpeg."""
    path = str(path)
    x, rate = None, None
    if path.lower().endswith(".wav") and wavfile is not None:
        try:
            rate, d = wavfile.read(path)
            if d.dtype == np.int16:
                x = d.astype(np.float64) / 32768.0
            elif d.dtype == np.int32:
                x = d.astype(np.float64) / 2147483648.0
            elif d.dtype == np.uint8:
                x = (d.astype(np.float64) - 128.0) / 128.0
            else:
                x = d.astype(np.float64)
        except Exception:
            x = None
    if x is None:                                   # ffmpeg fallback (mp3/m4a/flac/ogg/24-bit wav)
        cmd = ["ffmpeg", "-nostdin", "-v", "error", "-i", path, "-f", "f32le", "-acodec", "pcm_f32le", "-"]
        if sr:
            cmd += ["-ar", str(int(sr))]
        r = subprocess.run(cmd, capture_output=True)
        if r.returncode or not r.stdout:
            raise SystemExit(f"audioutil: could not decode {path}: {r.stderr.decode('utf-8', 'replace')[-200:]}")
        x = np.frombuffer(r.stdout, "<f4").astype(np.float64)
        rate = sr or 44100
        if not sr:
            probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries",
                                    "stream=sample_rate,channels", "-of", "json", path], capture_output=True, text=True)
            try:
                j = json.loads(probe.stdout or "{}"); st = (j.get("streams") or [{}])[0]
                rate = int(st.get("sample_rate") or 44100)
            except Exception:
                rate = 44100
    if x.ndim == 1:
        x = x[:, None]
    if sr and rate != sr:
        x = resample(x, rate, sr); rate = sr
    if max_seconds:
        x = x[:int(max_seconds * rate)]
    return x, int(rate)


def resample(x, sr_in, sr_out):
    from scipy.signal import resample_poly
    from math import gcd
    g = gcd(int(sr_out), int(sr_in))
    return resample_poly(x, sr_out // g, sr_in // g, axis=0)


def write_wav(path, x, sr=44100, bits=16):
    """write a WAV; x is [n, channels] float or mono 1-D"""
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    x = np.asarray(x, dtype=np.float64)
    if x.ndim == 1:
        x = x[:, None]
    if x.shape[1] == 1:
        x = np.repeat(x, 2, axis=1)
    x = np.clip(x, -1.0, 1.0)
    if bits == 16:
        d = (x * 32767.0).astype("<i2")
    elif bits == 24:
        d = np.clip(np.round(x * 8388607.0), -8388608, 8388607).astype("<i4")
        b = d.tobytes()
        d = np.frombuffer(b, dtype=np.uint8).reshape(-1, 3)
        raw = bytearray()
        for row in d:
            v = int(row[0]) | (int(row[1]) << 8) | (int(row[2]) << 16)
            raw += int(v).to_bytes(3, "little", signed=True)
        with open(path, "wb") as f:
            f.write(_wav_header(x.shape[0], sr, 2, 3))
            f.write(bytes(raw))
        return path
    else:
        d = x.astype("<f4")
    with open(path, "wb") as f:
        f.write(_wav_header(x.shape[0], sr, x.shape[1], 2 if bits == 16 else 4))
        f.write(d.tobytes())
    return path


def _wav_header(n, sr, ch, bytes_per_sample):
    import struct
    bits = bytes_per_sample * 8
    byte_rate = sr * ch * bytes_per_sample
    block = ch * bytes_per_sample
    data = n * block
    hdr = b"RIFF" + struct.pack("<I", 36 + data) + b"WAVEfmt " + struct.pack("<IHHIIHH", 16, 1, ch, sr, byte_rate, block, bits) \
        + b"data" + struct.pack("<I", data)
    return hdr


def to_stereo(x):
    x = np.asarray(x, dtype=np.float64)
    if x.ndim == 1:
        return np.column_stack([x, x])
    if x.shape[1] == 1:
        return np.repeat(x, 2, axis=1)
    return x[:, :2]


def fit_length(x, n):
    """pad with silence or cut so x has exactly n frames"""
    x = np.asarray(x)
    if len(x) == n:
        return x
    if len(x) > n:
        return x[:n]
    return np.vstack([x, np.zeros((n - len(x), x.shape[1]))])


# ── measurement ──────────────────────────────────────────────────────────────
def rms_db(x):
    x = np.asarray(x, float)
    return float(20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12))


def peak_db(x):
    return float(20 * np.log10(np.abs(np.asarray(x, float)).max() + 1e-12))


def low_corr(x, sr, hz=110.0):
    """L/R correlation in the sub-bass region; 1.0 = mono low end."""
    x = to_stereo(x)
    if x.shape[1] < 2:
        return 1.0
    try:
        from scipy.signal import butter, sosfilt
        sos = butter(6, hz / (sr / 2.0), "low", output="sos")
        a, b = sosfilt(sos, x[:, 0]), sosfilt(sos, x[:, 1])
        if a.std() < 1e-9 or b.std() < 1e-9:
            return 1.0
        return float(np.corrcoef(a, b)[0, 1])
    except Exception:
        return 1.0


def lufs_peak(path):
    """(integrated LUFS, true peak dBFS) via ffmpeg ebur128; (None, None) if unavailable."""
    try:
        r = subprocess.run(["ffmpeg", "-v", "info", "-nostats", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"],
                           capture_output=True, text=True).stderr
        I = re.findall(r"I:\s+(-?[\d.]+) LUFS", r)
        P = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", r)
        return (float(I[-1]) if I else None), (float(P[-1]) if P else None)
    except Exception:
        return None, None


def measure(path):
    """one-shot measurement bundle for a file"""
    x, sr = read_audio(path)
    m = to_stereo(x)
    mono = m.mean(1)
    I, P = lufs_peak(path)
    return dict(file=os.path.basename(path), path=os.path.abspath(path), seconds=round(len(m) / sr, 3), sr=sr,
                channels=int(m.shape[1]), peak_dbfs=round(peak_db(m), 2), rms_db=round(rms_db(mono), 2),
                lufs=I, true_peak_db=P, dc_offset=round(float(mono.mean()), 5),
                low_corr=round(low_corr(m, sr), 3),
                clipped_samples=int((np.abs(m) >= 0.999).sum()))


def bpm_of(path, bpm_range=None):
    """tempo estimate through the analyzer (numpy/scipy only)"""
    import analyze as A
    prof = A.analyze(path, quiet=True, bpm_range=bpm_range)
    return float(prof["tempo"]["bpm"]), prof


def ffprobe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration,size:stream=sample_rate,channels,codec_name",
                        "-of", "json", path], capture_output=True, text=True)
    try:
        j = json.loads(r.stdout or "{}")
    except Exception:
        return {}
    s = (j.get("streams") or [{}])[0]
    f = j.get("format", {})
    return dict(seconds=float(f.get("duration", 0)), mb=float(f.get("size", 0)) / 1e6,
                sr=int(s.get("sample_rate", 0)), channels=int(s.get("channels", 0)), codec=s.get("codec_name"))


def temp_wav(x, sr):
    fd, p = tempfile.mkstemp(suffix=".wav", prefix="af-")
    os.close(fd)
    write_wav(p, x, sr)
    return p

# roblox-ost — `af.py ost check`

Roblox upload checks plus a **strict loop check** (`--loop`): seam click, edge silence, whole bars, mono sub-bass, headroom, DC and clipping. Works on wav (loop check needs WAV); ogg/mp3/flac are checked for the upload limits.

## Exact command

```
af.py ost check FILE.wav [FILE2 ...] [--bpm 178] [--loop]
```

### Flags

| Flag | Meaning |
|---|---|
| `FILE...` | one or more audio files (wav/ogg/mp3/flac). |
| `--bpm` | tempo for the whole-bar loop check. |
| `--loop` | strict loop mode: seam click, head/tail silence, whole bars at BPM, mono sub (<140 Hz), headroom, DC, clipping. |

## What check verifies

- format is mp3/ogg/wav/flac
- length ≤ 7 minutes, size < 20 MB, sample rate ≤ 48 kHz
- loudness (LUFS) within −9 / −26 bounds (target about −14 for a music bed)
- true peak > −1.0 dBFS fails (keep ≤ −1.5 dBFS headroom for game SFX and re-encoding)
- DC offset, clipped samples (wav only)
- low-band correlation below 140 Hz ≥ 0.85 (wav only; a stereo sub cancels on phone speakers)
- **with `--loop`**: ends not in near-silence (pump/gap), seam jump ≤ 1.5× the normal sample step, whole number of bars at the BPM, mp3 loop-padding warning

## Outputs

One JSON object per file, printed to stdout:

```json
{
  "file": "lobby.wav",
  "seconds": 21.57,
  "mb": 3.81,
  "sample_rate": 44100,
  "channels": 2,
  "lufs": -14.0,
  "peak_dbfs": -4.2,
  "dc_offset": 0.00004,
  "clipped_samples": 0,
  "low_corr_below_140hz": 0.934,
  "seam_jump_vs_normal_step": 0.52,
  "bars": 16.0,
  "issues": [],
  "ready": true
}
```

`ready: true` means no issues. `issues` lists each problem with a plain-English fix.

## Step-by-step tutorial

1. After `ost build`, verify every loop file:
   ```
   af.py ost check myost/lobby.wav myost/tension.wav myost/chase.wav myost/lms.wav --bpm 178 --loop
   ```
2. Every loop file should show `"ready": true` and `"issues": []`. Bars should be a whole number (16.0, 24.0, …).
3. Non-looping stingers (win/lose) don't need `--loop`, but still check headroom and LUFS:
   ```
   af.py ost check myost/win.wav myost/lose.wav
   ```
4. Fix any issue (re-render with `loop_doctor --repair`, or adjust the master) and re-check before uploading.

## Honesty

`ost check` measures upload limits and objective loop properties. It does not prove the loop is musically satisfying, and it has not been run in Roblox Studio — verify there before shipping.

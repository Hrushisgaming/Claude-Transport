# audio-forge — `loop_doctor`

Diagnose and repair a music loop (Roblox Sound, game bed, video loop). It measures; it does not judge — whether the loop sounds good is the person's call. Listen to the repaired loop twice in a row before shipping it.

## Exact command

```
# diagnose only
af.py loop_doctor LOOP.wav [--bpm BPM] [--bars BARS] [--json]

# diagnose + repair
af.py loop_doctor LOOP.wav --bpm 178 --repair FIXED.wav
af.py loop_doctor LOOP.wav --bpm 178 --repair FIXED.wav --xfade 3 --target-peak -1.5 --no-fold
```

### Flags

| Flag | Meaning |
|---|---|
| `LOOP.wav` | the loop file. |
| `--bpm` | tempo (needed for the whole-bar check; if omitted, `loop_doctor` estimates it with the analyzer). |
| `--bars` | how many bars the loop should hold (validates against the measured length). |
| `--repair OUT` | write the repaired loop here (implies diagnosis). |
| `--xfade MS` | micro-fade at both edges in ms (default 3). |
| `--target-peak` | peak of the repaired file in dBFS (default −1.5). |
| `--no-fold` | do not fold the tail back onto the start. |
| `--json` | print the report as JSON. |

## What it checks

- **seam click** — distance between the last and first sample vs the file's own largest normal sample step (>1.5× = risk)
- **head/tail silence** — a loop that fades out pumps every cycle
- **whole-bar length** — at the given BPM a loop must be a whole number of bars or the grid drifts
- **DC offset, clipping, true peak, sub-bass mono compatibility** (a stereo sub cancels on phone speakers)
- **tail overlap** — reverb/decay spilling past the loop point (repaired by folding it back onto the start)

## Repairs (`--repair`)

1. Snap to a whole number of bars at the given BPM (or keep the length when `--bars` is not given).
2. Fold the tail back onto the start so the decay plays on instead of being cut.
3. Optional micro-fade (default 3 ms) at both edges to kill a click.
4. Remove DC, then peak-normalise to `--target-peak` (default −1.5 dBFS).

## Outputs

- `--repair OUT` — the repaired loop WAV.
- Diagnosis report: seam jump vs normal step, head/tail/body RMS, DC offset, clipped samples, true peak, bars exact/rounded, issues list, `ready` flag.
- With `--repair`, also an "after" re-diagnosis of the repaired file.

## Step-by-step tutorial

1. Diagnose an existing loop:
   ```
   af.py loop_doctor chase.wav --bpm 178
   ```
   Read the issues (seam click risk, near-silence at the ends, not-a-whole-number-of-bars, sub not mono, clipping).
2. Repair it:
   ```
   af.py loop_doctor chase.wav --bpm 178 --repair chase_fixed.wav
   ```
3. Re-check the repaired file:
   ```
   af.py loop_doctor chase_fixed.wav --bpm 178
   ```
   Confirm `ready: true` / no remaining issues.
4. **Listen to the repaired loop twice in a row** before shipping — the tool catches objective problems, not musical ones.

## Honesty

`loop_doctor` catches objective loop problems (clicks, grid drift, DC, clipping, sub cancellation). It cannot tell you whether the loop is musically satisfying. Always audition it.

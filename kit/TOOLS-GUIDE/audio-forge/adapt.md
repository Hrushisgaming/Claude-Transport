# audio-forge — `adapt`

Compose → measure → compare → adjust, up to 5 rounds, towards a reference. Round 1 derives parameters from the reference (tempo, key, loudness, section plan, rhythm strings, drive). Each later round measures the candidate, compares it with `af.py compare`'s rules, changes the knobs the comparison flagged, and composes again. Stops when nothing is OFF, or after `--rounds` (default 5). One knob per round per change type keeps it small and explainable.

## Exact command

```
af.py adapt --reference REFERENCE [--out OUT.wav]
    [--genre GENRE] [--state {chase,lms,lobby,tension}]
    [--bpm BPM] [--key KEY] [--scale SCALE] [--bars BARS]
    [--seed SEED] [--rounds N] [--override OVERRIDE]
    [--work WORKDIR] [--fast] [--json]
```

### Flags

| Flag | Meaning |
|---|---|
| `--reference REFERENCE` | required: reference audio **or** a saved `dna.json`. |
| `--out OUT.wav` | the best candidate (highest closeness score). |
| `--genre GENRE` | genre for the candidate. |
| `--state` | preset: `lobby` / `tension` / `chase` / `lms` (sets genre, plan, intensity, loudness). |
| `--bpm / --key / --scale / --bars / --seed` | override the derived values. |
| `--rounds N` | max adjustment rounds (default 5). |
| `--override OVERRIDE` | extra JSON (string or file) merged into the genre spec. |
| `--work WORKDIR` | folder for round files (default `<out>_work`). |
| `--fast` | skip the deep (section/hard-point) analysis of each candidate. |
| `--json` | print a JSON summary to stdout. |

## Outputs

- `--out` — the best candidate WAV.
- `<work>/adapt-log.json` — every round: rows, verdict, knob changed, new value (schema `audio-forge/adapt@1`).
- `<work>/adapt-log.md` — the same as a readable table.

## How a round works

1. Compose a candidate from the current state.
2. Measure it with the same analyzer used on the reference.
3. `compare.rows(reference, candidate)` → per-measure verdicts (OK / CLOSE / OFF).
4. `adjust()` applies **one grouped knob change per row type** (tempo, key, loudness, dynamics, brightness, band gain, width, density, sustain/mute via `m` rhythm chars, rhythm strings, plan, risers, fills, impacts, ending).
5. Keeps the best-scoring round; stops after 2 non-improving rounds. Logs every round.

**Guitar muting is expressed with `m` rhythm characters / the `guitar_mute` voice, not a `kw.mute` argument.**

## Step-by-step tutorial

1. Pick a reference (a game chase loop, a lms-family DNA, …):
   ```
   af.py adapt --genre horror_chase --reference ref.wav --out adapted.wav --rounds 5
   ```
2. Watch the per-round output: `round N: closeness X/100, Y OFF (…)`.
3. When it stops, `adapted.wav` is the best-scoring candidate and `adapt_log/*` shows exactly what changed each round.
4. Report the numbers truthfully (e.g. "round 1 = 50/100 → round 2 = 66.7/100 → best round kept"). Closeness is a heuristic from measurements, not hearing.

## Honesty

Closeness is a heuristic from measurements, not hearing. Nobody has listened to the result. Report the numbers and say the person's ears decide. Tempo selection uses absolute distance to the genre's BPM window (so an analyzer octave like 234 BPM is not preferred over 117 BPM for a 160 BPM game track).

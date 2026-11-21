# audio-forge — `compare`

Score a candidate track against a reference style, in NUMBERS — for models that cannot hear. Prints each measure with reference value, candidate value, difference, a verdict (OK / CLOSE / OFF) and, when OFF, **which knob to change**.

## Exact command

```
# candidate audio vs a saved Style DNA
af.py compare CANDIDATE.wav STYLE/dna.json

# candidate vs another audio file (both measured the same way)
af.py compare CANDIDATE.wav REFERENCE.mp3

# two DNAs against each other
af.py compare A.dna.json B.dna.json
```

## What it compares

Rows include: tempo, key, loudness (LUFS), crest factor, spectral centroid, 85% rolloff, flatness, band levels (sub/bass/low-mid/mid/high-mid/air), stereo side/mid, attacks per beat, sustain, rhythm-fingerprint correlation (beat-shift tolerant), energy-curve correlation, and (when both sides have `deep`) hard points — first drop position, drops, section changes, builds, breakdowns, end cut, risers, fills, hard hits per minute. Plus an ending row.

Verdicts: `OK` (within tolerance), `CLOSE` (near), `OFF` (needs a knob change). Each OFF row names the knob (e.g. `mix.lead.gain_db`, `guitar.drive`, `plan`, `bass.rhythm`) and a suggested direction.

A candidate compared with its own DNA is 100/100 — that's the ceiling, not a target.

## Outputs

Stdout table: `measure | reference | candidate | diff | verdict | knob | unit`. No file is written by default.

## Step-by-step tutorial

1. Study a reference: `af.py study ref.mp3 --name my-style` → `styles/my-style/dna.json`.
2. Compose a candidate: `af.py compose --genre my-style --out cand.wav`.
3. Compare: `af.py compare cand.wav styles/my-style/dna.json`.
4. For each OFF row, change the named knob in a `--override` blob (or `--plan`, `--bpm`, `--intensity`), re-render, re-compare. **One knob per round.**
5. Stop when nothing is OFF, or after 5 rounds. Keep the best-scoring candidate. Report the numbers honestly: closeness is a heuristic from measurements, not proof it sounds the same — the person's ears decide.

## Honesty

`compare` measures production style only. It cannot tell you whether a melody is good, whether a mix "hits", or whether two tracks are musically alike in a way humans care about. Never claim a candidate "sounds like" the reference based on this score.

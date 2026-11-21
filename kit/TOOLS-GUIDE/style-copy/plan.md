# style-copy — `copy.py plan`

Turn a studied style into a bar-by-bar arrangement plan.

## Exact command

```
python3 copy.py plan NAME [--bars 64] [--bpm BPM]
```

`NAME` is a studied style folder (with `dna.json`) or a prebuilt style (see `copy.py list`; prebuilt audio genre `roblox_guitar_cover`, video style `roblox-edit`).

## What it does

Reads the style DNA (tempo, key/mode, rhythmic density, arrangement shape, section proportions) and emits a bar-by-bar plan: section sequence with bar counts, chord-change rate, rhythm density per layer, and intensity arc. This is the bridge from "what the reference does" to "what to compose".

## Outputs

Stdout / a plan JSON: sections `[{name, start_bar, bars}]`, chord changes per bar, suggested rhythm strings per layer, and intensity per section.

## Step-by-step tutorial

1. Study a reference: `copy.py study ref.mp3 --name my-style`.
2. Make a plan: `copy.py plan my-style --bars 64 --bpm 124`.
3. Compose to the plan: `af.py compose --genre my-style --bars 64 --bpm 124 --plan '[["intro",0.12],["build",0.12],["drop",0.26],["break",0.12],["drop",0.26],["outro",0.12]]' --out mytrack.wav`.
4. Score against the style: `copy.py compare mytrack.wav styles/my-style/dna.json`.

## Honesty

The plan is derived from measured arrangement shape (heuristic labels intro/build/drop/break/outro), not a transcription. Adjust bar counts by ear.

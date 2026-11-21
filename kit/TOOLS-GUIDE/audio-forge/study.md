# audio-forge — `study`

Measure the **production style** of a reference track and write a Style DNA + a plain-text brief any model can follow (even one that cannot hear). Copies style only: tempo, key/mode, rhythmic density, brightness, distortion, stereo width, loudness, arrangement shape, instrument-type hints. The notes, melody, riffs, lyrics and audio of the reference are **not** stored or reproduced.

## Exact command

```
python3 af.py study AUDIO [--name NAME] [--out OUT_DIR]
    [--bpm-range LO HI] [--no-deep]
```

### Flags

| Flag | Meaning |
|---|---|
| `AUDIO` | the reference file. |
| `--name NAME` | style name (used as the folder name under `--out`). |
| `--out OUT_DIR` | output root (default creates `styles/<name>/`). |
| `--bpm-range LO HI` | force the tempo octave. |
| `--no-deep` | skip the deep (hard-points/sections) analysis. |

## Outputs (in `<out>/<name>/`)

- `dna.json` — `style-copy/audio-dna@1`: tempo, key/mode, rhythmic density, brightness, distortion, stereo width, loudness, arrangement shape, instrument hints; with `deep` it also stores hard points, form, layers and loop info (schema `audio-dna@2`).
- `brief.md` — what to build, with numbers (human- and model-readable).
- `spectrogram.png` (if Pillow exists).
- `genre.json` — a draft audio-forge custom genre: copy it to `~/.config/audio-forge/genres/` to use with `af.py compose --genre NAME`.

## Step-by-step tutorial

1. Study the reference:
   ```
   af.py study ref.mp3 --name my-style --out styles/my-style
   ```
2. Read `styles/my-style/brief.md` — it gives you tempo, key, loudness, rhythm density and arrangement shape with numbers.
3. Copy `styles/my-style/genre.json` to `~/.config/audio-forge/genres/my-style.json` to compose in this style:
   ```
   af.py compose --genre my-style --out mytrack.wav
   ```
4. Build a candidate, then `af.py compare cand.wav styles/my-style/dna.json` to score it and see which knob to turn. Change ONE knob per round, max 5 rounds.

## Honesty

Heuristic guesses (instrument family, drums present) are labelled as guesses — confirm with the person if it matters. The chord line is reduced to mode + vocabulary + chord-change rate; the example loop is flavour only — write a NEW progression. Nobody has listened to the reference.

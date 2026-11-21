# audio-forge — `separate`

Split audio into stems (vocals / everything else, or a two-stem split). Needs an optional separation model part — installed only when asked.

## Exact command

```
python3 af.py separate AUDIO [--out STEMS_DIR] [--model MODEL]
    [--two-stems TWO_STEMS] [--device DEVICE]
```

### Flags

| Flag | Meaning |
|---|---|
| `AUDIO` | the file to split. |
| `--out STEMS_DIR` | where the stems are written. |
| `--model` | separation model to use. |
| `--two-stems` | e.g. `vocals` → writes `vocals.wav` + `no_vocals.wav`. |
| `--device` | compute device. |

## Outputs

Stem WAVs in `--out` (e.g. `vocals.wav`, `no_vocals.wav`, `drums.wav`, `bass.wav`, `other.wav` depending on model).

## Step-by-step tutorial

1. Check optional parts: `af.py doctor --list-optional --json` (the separation part carries its own "Do you want…?" wording — ask first).
2. Install only what you need: `af.py doctor --install <part>`.
3. Split: `af.py separate song.mp3 --out stems/ --two-stems vocals`.
4. Use the isolated drums/bass stems with `af.py analyze --stems stems/` for much more accurate groove measurement.

## Honesty

Stem separation on music is approximate. The optional model is downloaded only when you ask; nothing is downloaded silently.

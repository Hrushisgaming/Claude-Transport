# audio-forge — `sfx`

Synthesised sound effects (UI, transitions, impacts, game, ambience). Pure numpy, no downloads.

## Exact command

```
python3 af.py sfx --list
python3 af.py sfx --name whoosh_up --dur 0.9 --out whoosh.wav
python3 af.py sfx --all --dir sfx/     # render the whole library (44.1 kHz stereo WAV, -3 dBFS)
```

### Flags

| Flag | Meaning |
|---|---|
| `--list` | print every effect name. |
| `--name NAME` | which effect to render. |
| `--dur DUR` | duration in seconds. |
| `--out OUT` | output WAV path. |
| `--all --dir DIR` | render the whole library into a folder. |

## Outputs

`<out>.wav` — 44.1 kHz stereo, peaked at −3 dBFS.

## Step-by-step tutorial

1. List the library: `af.py sfx --list` (whooshes, impacts, hits, risers, glitch, UI, coin, laser, explosion, stingers, heartbeat, typing, …).
2. Render one effect: `af.py sfx --name impact --dur 0.6 --out impact.wav`.
3. Render the whole library: `af.py sfx --all --dir mygame/sfx/`.

## Honesty

Synthesised SFX are fine for games, beds and demos; they are not foley-quality field recordings. Nobody has listened to them.

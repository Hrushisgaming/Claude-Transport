# audio-forge — `at`

Print what the analyzer saw at a specific time `t` in a `deep.json` — the nearest events (drop, riser, hit, stop, section start …) around that moment.

## Exact command

```
python3 af.py at DEEP.json T [--bars N]
```

### Flags

| Flag | Meaning |
|---|---|
| `DEEP.json` | output of `af.py deep`. |
| `T` | time in seconds (e.g. `31.2`). |
| `--bars` | how many bars of context to show around `t`. |

## Outputs

Stdout: the analyzer events nearest to `t` with their times, types and strengths.

## Step-by-step tutorial

1. Run `af.py deep track.mp3 --out deep/track/`.
2. Ask what happened at a moment: `af.py at deep/track/deep.json 31.2`.
3. Use it to decide whether an AI's claimed timestamp matches a real analyzer event (see `aicheck`).

## Honesty

It reports nearest events within a tolerance; if nothing is near `t`, it says so. It does not interpret.

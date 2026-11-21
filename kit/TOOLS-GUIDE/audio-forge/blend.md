# audio-forge — `blend`

Turn **several** studied tracks into one style **family**: what they all share, what varies, and ranges to stay inside. One reference teaches one sound; several references teach a style — the shared habits are the style, the differences are your room to be original.

## Exact command

```
python3 af.py blend --name NAME [--out OUT] STYLE [STYLE ...]
```

Each input is a folder with `dna.json` (from `af.py study` / `copy.py study`).

## Outputs (in `--out`, default `styles/<NAME>/`)

| File | Contents |
|---|---|
| `dna.json` | the family as a normal dna: every number = the **median** of the members, plus `family{members, ranges, consensus, tempo_clusters, key_votes}` so `af.py compare cand.wav styles/NAME/dna.json` works unchanged and judges "inside the range" instead of "equal to one track" |
| `brief.md` | what all members do (copy this), what varies (free choice), ranges, then the usual measured brief |
| `genre.json` | draft genre from the median |

## Step-by-step tutorial

1. Study several references: `af.py study a.mp3 --name a`, `af.py study b.mp3 --name b`, …
2. Blend them: `af.py blend styles/a styles/b styles/c --name lms-family --out styles/lms-family`.
3. Read `styles/lms-family/brief.md` — the shared habits and the ranges.
4. Compose inside the ranges: `af.py compose --genre lms-family --out mytrack.wav`.
5. Judge with `af.py compare mytrack.wav styles/lms-family/dna.json` — "inside the range" passes, "equal to one track" is too strict.

## Honesty

Only measurements are blended; no notes, melodies or lyrics exist in the inputs. Medians and ranges summarize the family; they are not a target every track must hit.

# audio-forge — `aicheck`

Compare what an AI **said it heard** (Gemini, Qwen, …) with what the `deep` analyzer measured, and write the "check my numbers" prompt. A sanity check, not a judge.

## Exact command

```
python3 af.py aicheck DEEP.json ANSWER.txt [--tol 2.5]
python3 af.py aicheck DEEP.json --prompt
```

### Flags

| Flag | Meaning |
|---|---|
| `DEEP.json` | output of `af.py deep`. |
| `ANSWER` | the AI's listening answer (timestamps + words). |
| `--tol TOL` | seconds within which an analyzer event confirms a claim (default 2.5). |
| `--prompt` | print the "check my numbers" prompt for this track (same format as the listening-test-pack). |

## How scoring works

Every `mm:ss` (or `mm:ss-mm:ss`) in the answer becomes a claim; the nearest analyzer event within `--tol` seconds confirms it (event = drop, breakdown, build, riser, stop, end cut, hit, section start). The claim's words (drop, breakdown, riser, fill, cut, climax, impact) are checked for a sensible kind. AI timestamps are usually good to about ±2 s, and an AI can be wrong.

## Outputs

- A confirmation table (which claims the analyzer confirms, which it missed).
- With `--prompt`: the "check my numbers" prompt text.

## Step-by-step tutorial

1. Produce the analyzer's view: `af.py deep track.mp3 --out deep/track/`.
2. Have the AI listen and write an answer file (`answer.txt` with timestamps).
3. Score it: `af.py aicheck deep/track/deep.json answer.txt --tol 2.5`.
4. Save the result in `listening-test-pack/results/`. Fix any row the AI calls wrong by changing ONE knob per round.

## Honesty

AI timestamps are usually good to about ±2 s and an AI can be wrong. `aicheck` is a sanity check against measurements, not a verdict on the music.

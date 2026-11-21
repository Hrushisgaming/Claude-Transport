# audio-forge — `remake`

Turn an `analyze.py` profile into `compose.py` parameters plus a genre-spec override. This is style transfer: same tempo, key/mode, chord progression (as scale degrees), groove (kick/snare/hat pattern), swing, density, section structure and energy contour — rendered by the synth engine as an **original** piece. Melodies, samples and recordings from the reference are never copied.

## Exact command

```
python3 af.py remake PROFILE.json
```

`PROFILE.json` is the output of `af.py analyze ref.mp3 --out PROFILE.json`. `remake.py` reads it from `sys.argv[1]` (no `--out` flag — it prints compose-ready parameters to stdout).

## Outputs

Stdout: the derived parameters you can paste into `af.py compose`:
- genre / bpm / key / scale / intensity
- chord progression (as scale degrees)
- kick/snare/hat 16-step rhythm strings
- swing, density, section plan
- a JSON `--override` blob to deep-merge into the genre spec

Then run, e.g.:
```
af.py compose --genre <derived> --bpm <bpm> --key <key> --scale <scale> \
    --override '<override json>' --out remake.wav
```

## Step-by-step tutorial

1. Analyze the reference: `af.py analyze ref.mp3 --out ref.profile.json`.
2. Show the person the summary and the genre guess (it's a heuristic — say so) and confirm.
3. Remake: `af.py remake ref.profile.json`. Read the printed parameters.
4. Compose the remake with those parameters, try seed 1–3, and offer 2–3 variations:
   ```
   af.py compose --profile ref.profile.json --seed 3 --out remake.wav
   ```
5. Re-analyze the remake and report how close tempo/key/groove/energy arc are. Iterate with `--override`, `--intensity`, `--genre`, changing ONE knob per round.

## Honesty

Style transfer copies production style (tempo, key, groove, structure, energy contour), never the melody, hook or samples. `remake` builds a new chord progression and melody from the synth engine. Nobody has listened to the result.

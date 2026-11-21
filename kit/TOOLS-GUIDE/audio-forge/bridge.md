# audio-forge — `bridge`

Connect audio-forge to the NextPhase editor (editor-v1 today, newer versions through the same JSON). Everything speaks one small, versioned file: **`audio-forge/beatmap@1`**

```json
{ "schema", "bpm", "beats_per_bar", "beats[]", "downbeats[]",
  "sections[{name,start,end}]", "drops[]", "energy_per_beat[]?", "duration" }
```

`compose.py` writes one next to every song it makes; `bridge beatmap` makes one from any audio file or analyze profile.

## Exact command

```
python3 af.py bridge beatmap SRC [--out MAP.json]
python3 af.py bridge fit-tempo --shots WORK/shots.json
python3 af.py bridge snap --beatmap MAP.json --shots WORK/shots.json \
    [--song-at S] [--grid half] [--tol 0.12] [--fps 30]
python3 af.py bridge plan-bed --beatmap MAP.json --words WORK/tx/words.json \
    --drop-at-word "Claude" [--occurrence 1] --dur 46.4 \
    [--cut-words "first,last"] [--grid-offset O] [--song BED.wav]
python3 af.py bridge sfx-cues --beatmap MAP.json --song-at S --dur D \
    [--accent drops|sections|downbeats|beats] [--out FORGE-CUES.txt]
```

### Sub-commands

| Sub-command | What it does |
|---|---|
| `beatmap SRC` | build a beatmap from an audio file, `analyze.py` profile, or another beatmap |
| `fit-tempo --shots` | find the BPM (+offset) whose beat grid the existing cuts already line up with |
| `snap` | move cut times onto the nearest beat-grid point (writes `shots.snapped.json` + report) |
| `plan-bed` | the `--song-at` / `--ramp` values for editor-v1's `bed-mix.py` so the drop lands on a word |
| `sfx-cues` | synthesise whooshes/impacts/ticks and write an editor-v1 `sfx-cues.txt`-compatible cue sheet |

## Outputs

- `<MAP>.json` — a beatmap (`audio-forge/beatmap@1`).
- `shots.snapped.json` — beat-snapped cut times (a new file; the editor's own files are never edited silently).
- `FORGE-CUES.txt` — an editor-v1 sfx-cues.txt-compatible cue sheet.
- Stdout: `--song-at` / `--ramp` values and a ready `bed-mix.py` command.

## Step-by-step tutorial

1. Measure the footage: `python3 scripts/scenes.py video.mp4` → `work/shots.json` (average shot length, cuts/min).
2. Make a beatmap from your bed: `af.py bridge beatmap work/bed.wav --out work/beatmap.json`.
3. See which BPM the cuts already follow: `af.py bridge fit-tempo --shots work/shots.json`.
4. Snap cuts to the beat grid: `af.py bridge snap --beatmap work/beatmap.json --shots work/shots.json` → `shots.snapped.json`.
5. Plan the bed so the drop lands on a word:
   ```
   af.py bridge plan-bed --beatmap work/beatmap.json --words work/tx/words.json \
       --drop-at-word "Claude" --dur 46.4 --song work/bed.wav
   ```
   It prints the `--song-at` / `--ramp` values — show the plan and what you'll change, let the user approve.
6. Write sfx cues: `af.py bridge sfx-cues --beatmap work/beatmap.json --song-at 9.87 --dur 46.4 --accent drops`.

## Honesty

Nothing here edits the editor's own files; it prints values and writes new files for you to apply. Never edit editor-v1 files silently — show the plan and let the user approve (editor-v1 itself shows its plan before building).

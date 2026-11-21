# Working with NextPhase editor-v1 (and newer versions)

editor-v1 cuts a talking-head take to word onsets, uses `work/shots.json` (`[[t0, t1, name], ...]`), `work/tx/words.json` (`[{"w","s","e"}]`), a bed via `scripts/bed-mix.py`, and SFX through `sfx-cues.txt` (`<time> <sound-or-path> <gain>`). audio-forge speaks these formats and one more, `audio-forge/beatmap@1`:
`{schema, bpm, beats_per_bar, beats[], downbeats[], sections[{name,start,end}], drops[], energy_per_beat[], duration}` (song time, seconds). Any newer editor version can read the same file; keep the schema string stable and add fields rather than renaming them.

## Recipe A - make a bed that fits an existing edit
1. editor-v1 has planned the cuts (`work/shots.json` exists, plan approved by the user).
2. `af.py bridge fit-tempo --shots work/shots.json` -> best BPM + `offset_s` (e.g. 120 BPM, 0.1285 s). Alignment > 0.8 means the cuts really follow a grid; if it is < 0.5 the cuts are free-form, pick any BPM the user likes.
3. `af.py compose --genre <g> --bpm <bpm> --bars <enough> --out work/bed.wav` (length >= song-at + video duration; bed-mix never loops).
4. `af.py bridge plan-bed --beatmap work/bed.wav.beatmap.json --words work/tx/words.json --drop-at-word "<word>" --dur <video s> --song work/bed.wav --grid-offset <offset_s> [--cut-words "first,last"]`
   -> `song_at` (the drop lands on that word, nudged < half a beat so beats sit on the cut grid) and `--ramp` values that make the bed cut out on a punchline.
5. Show the user the printed `bed-mix.py` command and the plan. Run it only after they approve.

## Recipe B - snap an edit to an existing song
`af.py bridge beatmap song.mp3 --out map.json` (or use compose's beatmap), choose `--song-at`, then `af.py bridge snap --beatmap map.json --shots work/shots.json --song-at S --grid half --tol 0.12 --fps 30` -> `shots.snapped.json` + a report of every shift (ms). Cuts within `--tol` move to the nearest beat/half-beat, frame-quantised. Present the report; the user decides whether to adopt it.

## Recipe C - beat accents
`af.py bridge sfx-cues --beatmap map.json --song-at S --dur D --accent drops,sections,downbeats --out forge-cues.txt` synthesises whooshes/impacts/ticks into `forge-sfx/` and writes a cue sheet with absolute paths. After editor-v1 builds (it writes `sfx-cues.txt`), append: `cat forge-cues.txt >> sfx-cues.txt`, then run its `finish.sh`.

## Recipe D - voice from subtitles inside an edit
Voice track with `subs2speech.py` (confirm intent first), save as the edit's `vo.wav`, re-run word timing on it (`transcribe.py` in editor-v1) so captions and cuts key to the synthetic voice.

## Rules
Never rewrite editor-v1 scripts or the user's `build.py` unasked; print the exact change instead. The editor is free and never uploads; keep it that way. If editor-v1's own rights/FLAG table lists the bed, add the bed's source as "synthesised by audio-forge, original, no third-party rights".

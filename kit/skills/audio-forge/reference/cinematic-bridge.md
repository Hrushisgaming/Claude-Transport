# Working with cinematic-edit (and any video editor that writes a score brief)

cinematic-edit (the reference host) keeps ONE file, `plan.json`, as the edit. audio-forge never reads it directly; the host translates it
into a brief so that speed-ramp time stretching is already accounted for. Two small, versioned files cross the border.

## `audio-forge/scorebrief@1` (host -> audio-forge), all times in OUTPUT (video) seconds
```json
{"schema":"audio-forge/scorebrief@1","duration":42.3,"style":"hype-highlight",
 "acts":[{"name":"calm","t":0,"intensity":0.1},{"name":"finale","t":30,"intensity":1.0}],
 "events":[{"t":31.2,"strength":1.0,"kind":"impact"}], "cuts":[0,2.1,4.4], "speech":false}
```
`intensity` 0-1 per act (cinematic-edit derives it from `drone` and `heart_bpm`). `events` = the hits; the strongest one inside the peak act is the hero moment.
`cuts` are optional shot starts: if they follow a grid the bed adopts that tempo. Unknown keys are ignored.

## `audio-forge/score@1` (audio-forge -> host), written next to the bed as `<bed>.score.json`
`bed`, `beatmap`, `bpm`, `genre`, `key`, `scale`, `seed`, `sections[{name,start,end,act}]` (video time), `hero_s`, `drop_start_s`, `drop_error_ms`, `tempo_tuned`, `speech_forward`, `music_db_hint`, `sfx_density`, `notes[]`, optional `cues` (cue sheet, `<video s> <wav> <gain>`).

## What the host does with it (cinematic-edit's `audioforge.py score` automates this)
1. `music` = the bed, `music_start` = 0 (the bed already starts with the video), `audio_forge{bed,...,synthesised:true}` -> the rights gate treats it as original.
2. `sfx_cues` = the cue sheet when `--sfx` was used. `audio.mode: voice` when `speech_forward`.
3. Writes a patched COPY of the plan and shows the change; the person approves before the plan is touched.

## By hand
`python3 af.py score --brief brief.json --out bed.wav --style trailer` then set `"music": "bed.wav"` in plan.json. For music you supply: `python3 af.py bridge beatmap song.mp3 --out map.json`, `bridge snap --beatmap map.json --shots work/shots.json --song-at S` (shots.json comes from cinematic-edit's `scenes.py`; the same format editor-v1 writes).

## Rules
Free and local only. The person says yes before audio-forge is used. Subtitles to speech only after they confirm. Original music only. Say the bed has not been listened to.

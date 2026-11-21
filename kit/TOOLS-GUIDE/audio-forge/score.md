# audio-forge — `score`

One-shot soundtrack for a video: reads what the edit looks like, composes an **original** bed whose structure follows the video's acts and whose big drop lands on the video's biggest moment. The tempo is nudged by at most ±10% (never outside the genre's useful range) so a whole number of bars ends exactly on the hero moment.

## Exact command

```
python3 af.py score --brief BRIEF.json --out BED.wav
python3 af.py score --duration SECONDS --style STYLE --hero HERO --out BED.wav
python3 af.py score --plan PLAN.json --out BED.wav
python3 af.py score --list-styles
```

### Flags

| Flag | Meaning |
|---|---|
| `--brief BRIEF.json` | a video-editor brief (schema `audio-forge/scorebrief@1`, all times are **video seconds after speed ramps**). |
| `--plan PLAN.json` | a cinematic-edit `plan.json` (speed ramps are NOT accounted for). |
| `--duration SECONDS` | bed length when there is no brief. |
| `--hero SECONDS` | the moment the drop should land on (with `--duration`). |
| `--style STYLE` | one of 18 presets (see `--list-styles`); default comes from the brief. |
| `--genre GENRE` | overrides the style's genre. |
| `--seed SEED` | variation seed. |
| `--bpm BPM / --key KEY / --scale SCALE` | override the style-derived values. |
| `--intensity X` | 0–1 sparseness/density. |
| `--sfx` | also write a beat-accent cue sheet `<out>.cues.txt`. |
| `--no-tune` | do not nudge the tempo. |
| `--exact [--fade S]` | end exactly at the video length with a fade-out (never trim by hand). |
| `--tail S` | extra seconds of bed after the video ends (default 3). |
| `--out OUT` | output bed path. |

### Brief (schema `audio-forge/scorebrief@1`)

```json
{
  "schema": "audio-forge/scorebrief@1",
  "duration": 42.3,
  "style": "hype-highlight",
  "acts": [{"name": "calm", "t": 0, "intensity": 0.1},
           {"name": "finale", "t": 30, "intensity": 1.0}],
  "events": [{"t": 31.2, "strength": 1.0, "kind": "impact"}],
  "cuts": [0, 2.1, 4.4],
  "speech": false
}
```

## Outputs

- `<out>` — the bed (16-bit stereo 44.1 kHz WAV).
- `<out>.beatmap.json` — `audio-forge/beatmap@1` (beats, downbeats, sections, drops).
- `<out>.score.json` — `audio-forge/score@1`: `{bpm, sections in video time, where the drop landed, drop_error_ms, level hint, notes}`.
- `<out>.cues.txt` (only with `--sfx`).

Check `drop_error_ms` (should be near 0). If not, try `--seed`, `--bpm`, or tell the host to shift the bed with `music_start`.

## Step-by-step tutorial

1. Get the brief from the video editor (or write one: duration, acts with intensity, hit times, cut times, all in video seconds after speed ramps).
2. Pick the style: gameplay/sport → `hype-highlight`/`sport`; horror → `horror-chase`; a person talking → `vlog`/`talking-head`/`tutorial` (these set `speech_forward`); clips + a song → `music-video`/`anime-amv`/`travel`; product → `product-ad`.
3. Compose the bed:
   ```
   af.py score --brief brief.json --out work/bed.wav
   ```
4. Check `drop_error_ms` in `bed.score.json`. If it's not near 0, retry with a different `--seed` or `--bpm`, or ask the editor to shift the bed with `music_start`.
5. Speech-led styles set `speech_forward`: tell the host to keep the bed about −22 to −26 dB under the voice (use `audio_edit duck` or `stem_mix` sidechain).
6. Nobody has listened to the bed — hand it over and let the person decide.

## Honesty

The bed is synthesised, great for video beds but not a recorded band. Style presets are starting points chosen by reasoning. Report `drop_error_ms` and let the person's ears decide whether it fits.

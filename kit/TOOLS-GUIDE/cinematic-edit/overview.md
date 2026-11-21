# cinematic-edit — tools reference

Edit any video locally and free, in any aspect ratio (9:16, 16:9, 1:1, 4:5), with 18 style presets. Everything runs locally and free (ffmpeg + Python: numpy, opencv, pillow). Nothing is uploaded or posted.

Every step starts with `source skills/cinematic-edit/scripts/env.sh` (sets `$CE_PY`). First time: `bash skills/cinematic-edit/scripts/doctor.sh` until "All set".

## The core workflow

**Style first.** Ask which kind of video it is (or infer it and say so). `python3 scripts/styles.py list` prints the 18 presets; `reference/video-styles.md` is the guide.

| If the input is | then |
|---|---|
| One video (gameplay, sport, action, b-roll, screen recording) | **A. Moments edit** |
| Several clips + a track | **B. Beat montage**, then A on the result |
| A person talking (vlog, podcast, tutorial, comedy) | **D. Talking edit** (silence_cut first), then A with a speech style |
| Voice-over wanting found-footage look | **C. Documentary mode** (captions + devices + sourcing) |

Footage facts first: `python3 scripts/scenes.py video.mp4` reports average shot length and cuts/min and writes `work/shots.json`.

Ask for anything essential that is missing (the video, target format, optional music) in **one short question**, otherwise decide and state your assumptions.

## Tools

| Tool | Exact command | Outputs |
|---|---|---|
| `styles.py` | `python3 scripts/styles.py list` | 18 preset list |
| `analyze.py` | `python3 scripts/analyze.py VIDEO --out work --plan plan.json --style <id> [--format 9:16] [--music track.mp3] [--n 24]` | `work/shots.json`, `work/plan.json` (DRAFT; tune `--n` hits, `--gap` min seconds between) |
| `scenes.py` | `python3 scripts/scenes.py VIDEO` | `work/shots.json` |
| `silence_cut.py` | `python3 scripts/silence_cut.py VIDEO` | edited video with jump cuts |
| `render.py` | `python3 scripts/render.py PLAN.json --out OUT.mp4` | finished video |
| `mixdown.py` | `python3 scripts/mixdown.py VOICE.wav BED.wav` | mixed audio (voice ducks bed) |
| `follow.py` | `python3 scripts/follow.py VIDEO` | centre-of-motion tracking preview (for 16:9→9:16 reframing) |
| `hud_events.py` | `hud_events.py VIDEO --roi x,y,w,h --template ICON.png --label "survivor down" --merge plan.json --sfx impact` | events merged into plan |

Look at the footage before trusting the numbers: machines find LOUD, not MEANINGFUL. Grab frames at each moment (`ffmpeg -ss T -i VIDEO -frames:v 1 -vf scale=360:-2 f.png`) and re-rank by the story. In a chase: the first down, the hook, the last-survivor moment, the escape. Delete weak/duplicate events, change `strength`, add events by hand.

## Pairing with audio-forge

The cinematic-edit skill **offers, never assumes**, audio-forge:
- `af.py score --brief brief.json --out work/bed.wav` — a bed whose acts follow the video and whose drop lands on the biggest moment
- `af.py tts` / `af.py subs2speech` — speak subtitles
- `af.py sfx` — whooshes, impacts, risers
- `af.py bridge` — beatmap JSON to connect to editor-v1

Audio-forge is a separate skill; install it with `python3 install.py` if needed.

## Honesty

The analyzer finds loud/motion moments, not meaningful ones — re-rank by story. Nobody has listened to any generated audio or watched the rendered video. Style presets are starting points chosen by reasoning.

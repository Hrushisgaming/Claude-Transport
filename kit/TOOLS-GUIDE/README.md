# kit/TOOLS-GUIDE — every tool in the Video Studio Kit

This folder documents **every command in every skill** in the kit: what it does, its exact CLI (flags and arguments), the files and schemas it writes, and a step-by-step tutorial. It is the reference you keep open while working; each skill's own `SKILL.md` still covers philosophy, limits and the "do not" rules.

## How to run a tool

Each skill is a folder under `kit/skills/`. Its entry point is a small Python script you run with the kit's private Python (or `python3` if numpy/scipy are on your system Python).

| Skill | Entry point | Example |
|---|---|---|
| **audio-forge** | `python3 kit/skills/audio-forge/scripts/af.py <tool> ...` | `af.py compose --genre house --out song.wav` |
| **style-copy** | `python3 kit/skills/style-copy/scripts/copy.py <cmd> ...` | `copy.py study ref.mp3 --name my-style` |
| **roblox-ost** | (inside audio-forge) `af.py ost build|check ...` | `af.py ost build --out ost/ --strict` |
| **cinematic-edit** | `python3 kit/skills/cinematic-edit/scripts/<tool>.py ...` | `python3 scripts/analyze.py video.mp4 --out work` |
| **video-studio** | `python3 kit/skills/video-studio/scripts/studio.py ...` | front door that runs cinematic-edit then audio-forge in order |

Always run tools from the kit folder (`cd <kit folder>`) or use absolute paths. Never run inside the skill folder; write outputs next to your project (or `./audio-out/`), never into `kit/skills/`.

## What each skill contains

### audio-forge (`af.py <tool>`)

Generate, analyse and edit audio locally and free (numpy + scipy + ffmpeg). Nothing is uploaded unless you explicitly opt in to the optional NVIDIA API path in `hear`.

| Tool | What it does | Exact example | Main outputs |
|---|---|---|---|
| `compose` | Generate an original piece of music from code in any genre | `af.py compose --genre house --bars 32 --out song.wav` | `<out>.wav` (16-bit stereo 44.1 kHz), `<out>.beatmap.json`, optional `.mid` and stems |
| `analyze` | Measure a reference track: tempo, beats, key, chords, groove, structure, loudness, genre guess | `af.py analyze ref.mp3 --out profile.json` | `profile.json` (+ `--brief` summary line) |
| `remake` | Turn an `analyze` profile into `compose` parameters + a genre override (style transfer, original melody) | `af.py remake profile.json` | compose-ready parameters printed to stdout |
| `score` | One-shot video bed whose acts map to song sections and whose drop lands on a hero moment | `af.py score --duration 45 --style trailer --hero 31.2 --out bed.wav` | `bed.wav`, `bed.beatmap.json`, `bed.score.json` |
| `tts` | Text-to-speech (kokoro/piper/say/espeak/formant; formant is offline fallback) | `af.py tts --text "Hello" --out hello.wav` | `hello.wav` |
| `subs2speech` | Speak an .srt/.vtt/.ass as a timed voice track (dub or voice-over) | `subs2speech subs.srt --video in.mp4 --mode mix --out vo.mp4` | voice track / dubbed video + `<out>.fit.json` |
| `audio_edit` | Everyday edits: info, extract, trim, fade, norm, convert, concat, mix, duck, stretch, pitch, eq, loop, silence, mux, beatcut | `audio_edit loop bed.wav out.wav --dur 120 --xfade 1.0` | edited audio file |
| `bridge` | Connect audio-forge to the NextPhase editor-v1 via `audio-forge/beatmap@1` JSON | `bridge snap --beatmap map.json --shots work/shots.json` | `shots.snapped.json`, cue sheets, beatmap JSON |
| `sfx` | Synthesised sound effects (whoosh, impact, riser, UI, game) | `sfx --name whoosh_up --dur 0.9 --out whoosh.wav` | `<out>.wav` |
| `separate` | Split audio into stems (needs an optional model part) | `separate song.mp3 --out stems/` | `vocals.wav`, `no_vocals.wav`, … |
| `listen` | Transcribe speech to words + timestamps (`--srt`, `--words`) | `listen video.mp4 --srt out.srt` | `out.srt`, `words.json` |
| `selftest` | Run the full smoke test: compose, analyze, score, hear, deep, ost, adapt, audition, stem_mix, loop_doctor | `af.py selftest` | pass/fail lines, exit code |
| `hear` | Offline measurement telemetry (`--local`) plus optional NVIDIA model opinion | `hear song.wav --local --out feedback/` | `hear-local.json`, `hear-local.md` |
| `study` | Measure a reference's style into a Style DNA + brief + draft genre.json | `study ref.mp3 --name my-style --out styles/my-style` | `dna.json`, `brief.md`, `spectrogram.png`, `genre.json` |
| `compare` | Score a candidate against a reference DNA or audio; name the knob to turn | `compare cand.wav styles/my-style/dna.json` | per-measure table (OK/CLOSE/OFF) |
| `deep` | Hard points, sections, layers, loop-readiness, tone shifts, fills, chord cycle | `deep track.mp3 --out deep/track/` | `deep.json`, `timeline.md`, `labels.txt`, `hardpoints.csv`, `timeline.png` |
| `lyrics` | Lyric statistics vs bars/drops/sections (Whisper optional, asked first) | `lyrics track.mp3 --deep deep.json` | `lyrics/<name>/lyrics.json` |
| `blend` | Blend several studied tracks into one style family (median + ranges) | `blend styles/a styles/b --name lms-family --out styles/lms-family` | `dna.json`, `brief.md`, `genre.json` |
| `ost` | Build/check a Roblox game soundtrack set (lobby, tension, chase, lms, win, lose) | `ost build --out ost/ --format wav --strict --quick` | wav/ogg set, `roblox_manifest.md`, `MusicDirector.luau` |
| `survey` | Run `deep` over many tracks into one regression table | `survey DIR... --out survey.md` | `survey.md` table |
| `aicheck` | Score an AI's listening answer against what `deep` measured | `aicheck deep.json answer.txt --tol 2.5` | confirmation table + prompt |
| `at` | What the analyzer saw at a time `t` in a deep.json | `at deep.json 31.2` | nearest events at `t` |
| `adapt` | Compose → measure → compare → adjust, up to 5 rounds, towards a reference | `adapt --genre horror_chase --reference ref.wav --out adapted.wav` | `adapted.wav`, `adapt-log.json`, `adapt-log.md` |
| `audition` | Timestamped showcase of instruments + a mini-mix (V2 voices in context) | `audition --inst piano_m1,organ_rock --out audition/` | `showcase.wav/.md/.json`, `minimix.wav/.json` |
| `stem_mix` | Mix a folder of stems into one finished mix (EQ, mono bass, sidechain, width, loudness) | `stem_mix stems/ --out mix.wav --target-lufs -14` | `mix.wav` (+ processed stems) |
| `loop_doctor` | Diagnose and repair a music loop (seam, whole bars, DC, clipping, sub mono) | `loop_doctor loop.wav --bpm 178 --repair fixed.wav` | `fixed.wav` + diagnosis report |
| `doctor` | Check the machine, install core/optional parts, list capabilities | `doctor --capabilities` | status + optional-parts JSON |

See the individual page for each audio-forge tool: `audio-forge/compose.md`, `audio-forge/analyze.md`, … (one page per tool below).

### style-copy (`copy.py <cmd>`)

Measure a reference's style, then build an ORIGINAL piece in it and prove how close it got with numbers. Copies production style only — never notes, melody, lyrics, footage or characters.

| Command | What it does | Exact example | Outputs |
|---|---|---|---|
| `doctor` | which skills are installed and ready | `copy.py doctor` | status lines |
| `list` | prebuilt styles and your own installed styles | `copy.py list` | style list |
| `show` | print a style's brief | `copy.py show my-style` | `brief.md` contents |
| `study` | measure one reference into `dna.json` + brief | `study ref.mp3 --name my-style` | `styles/my-style/dna.json`, `brief.md`, `genre.json` |
| `blend` | blend several studied styles into a family | `blend s/a s/b --name lms-family` | family `dna.json`, `brief.md`, `genre.json` |
| `deep` | hard points, sections, loop-readiness, bar map | `deep ref.mp3` | `deep.json`, `timeline.md`, `labels.txt` |
| `lyrics` | lyric statistics against bars/drops | `lyrics ref.mp3 --deep deep.json` | `lyrics.json` |
| `plan` | turn a style into a bar-by-bar arrangement plan | `plan my-style` | plan JSON |
| `compare` | score a candidate against a reference DNA | `compare cand.wav ref.dna.json` | OK/CLOSE/OFF table |
| `adapt` | compose → compare → adjust towards a reference | `adapt REF --out CANDIDATE --genre G` | `CANDIDATE`, `adapt-log.*` |
| `audition` | instrument showcase + mini-mix | `audition --out DIR` | `showcase.*`, `minimix.*` |
| `stem-mix` | mix a stem folder into a finished mix | `stem-mix STEMS_DIR --out WAV` | `mix.wav` |
| `loop-doctor` | diagnose/repair a loop | `loop-doctor FILE [--repair OUT]` | report + `fixed.wav` |

See `style-copy/*.md` below.

### roblox-ost (`af.py ost build|check`)

One key and one BPM for every state so they crossfade on bar lines; loops are cut to whole bars with the decay tail folded onto the start.

| Command | What it does | Example | Outputs |
|---|---|---|---|
| `ost build` | lobby, tension, chase(+stems), lms_intro(+lms), win, lose | `ost build --out ost/ --format wav --strict --quick` | wav set, `roblox_manifest.md`, `MusicDirector.luau`, `chase_stems/` |
| `ost check` | Roblox upload limits + strict loop seam/headroom/mono-sub checks | `ost check loop.wav --bpm 178 --loop` | JSON report (`ready`, `issues`) |

See `roblox-ost/build.md` and `roblox-ost/check.md`.

### cinematic-edit (`scripts/<tool>.py`)

Edit any video locally and free, in any aspect ratio, with 18 style presets.

| Tool | What it does | Example | Outputs |
|---|---|---|---|
| `styles.py` | list/show the 18 style presets | `python3 scripts/styles.py list` | preset list |
| `analyze.py` | measure footage: shots, pace, motion, hits; write a draft plan | `python3 scripts/analyze.py video.mp4 --out work --plan plan.json` | `work/shots.json`, `work/plan.json` |
| `scenes.py` | shot detection → shots.json (average shot length, cuts/min) | `python3 scripts/scenes.py video.mp4` | `work/shots.json` |
| `silence_cut.py` | jump cuts: remove silent stretches | `python3 scripts/silence_cut.py video.mp4` | edited video |
| `render.py` | execute a `plan.json` into a finished video | `python3 scripts/render.py plan.json --out out.mp4` | `out.mp4` |
| `mixdown.py` | mix a voice track under a music bed with ducking | `python3 scripts/mixdown.py voice.wav bed.wav` | mixed audio |
| `follow.py` | preview centre-of-motion tracking for reframing | `python3 scripts/follow.py video` | tracking preview |
| `hud_events.py` | detect HUD/banner/kill-feed events from a template icon | `hud_events.py video.mp4 --roi x,y,w,h --template icon.png` | events merged into plan |
| `study_video.py` | measure a reference video's editing style | `study_video.py ref.mp4` | style DNA + brief |
| `synth.py` | impact / riser / whoosh sound design (used by render) | (internal) | sfx WAVs |
| `captions.py`, `devices.py`, `looks.py`, `matte.py`, `montage.py`, `export.py`, `plancheck.py`, `verify.py`, `transcribe.py`, `fetch_clip.py` | supporting devices: captions, documentary devices, colour looks, mattes, montages, export, plan verification, transcription, clip fetching | see `reference/` in the skill | per-tool outputs |

### video-studio (`scripts/studio.py`)

One front door that runs cinematic-edit then audio-forge in order, asks about audio once, shows the plan, waits for your go.

## Conventions used in this guide

- **Exact commands** are copy-pasteable. Replace the placeholder paths (`ref.mp3`, `song.wav`, `styles/…`) with your own files.
- **Schemas** are versioned (e.g. `audio-forge/hear-local@1`, `audio-dna@1`, `audio-forge/beatmap@1`, `audio-forge/scorebrief@1`) and shown on each tool's page.
- **Honesty:** every page says what the tool measures vs what only your ears can judge. None of these tools "listen" the way a person does — report the numbers and let the person decide.
- **Privacy:** nothing leaves your machine unless you explicitly pass `--yes` to `hear` API mode. `--local` needs no key and uploads nothing.

## Tutorial index

Each tool page below ends with a step-by-step tutorial. Start here if you are new:

1. [audio-forge: compose your first track](audio-forge/compose.md)
2. [audio-forge: analyze a reference and remake it](audio-forge/analyze.md)
3. [audio-forge: build a Roblox soundtrack set](roblox-ost/build.md)
4. [audio-forge: check a loop before shipping](roblox-ost/check.md)
5. [style-copy: study a style and compare a build](style-copy/study.md)
6. [cinematic-edit: analyze footage and make a plan](cinematic-edit/analyze.md)

Back to the kit: [`kit/README.md`](../README.md) · [`kit/CHANGES/CHANGES.md`](../CHANGES/CHANGES.md)


## Added in v3
`audio-forge/ostfight.md`, `hopefight.md`, `instrument_showcase.md`, `instrument_demo.md`.

`audio-forge/huntfight.md` (v3.1).

`HOW-TO-CREATE-MUSIC.md`, `HYDROGEN-PROMPT.md`, `audio-forge/feedback.md` (v3.2).

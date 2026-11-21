---
name: style-copy
description: Copy any STYLE from a reference file - a music genre or production sound, a video editing style, or a 2D animation style - into measurable instructions that ANY model can follow (GLM, Nemotron, any opencode model or API key model, even ones that cannot hear audio or watch video), then build an ORIGINAL new piece in that style and prove how close it is with numbers. Use whenever the person says "copy this style", "make it sound like this", "edit it like this video", "animate it like this", "same vibe/genre as this track", gives a reference mp3/wav/mp4/mov, or asks for a prebuilt style such as the Roblox guitar cover. Works with audio-forge (music), cinematic-edit (editing) and 2d-animation-long-form-aivxer (animation). Copies the style, never the content.
license: MIT
compatibility: opencode, Claude Code. Needs Python 3.9+ and ffmpeg. Audio styles need audio-forge, video/animation styles need cinematic-edit.
---

# style-copy: study a reference, build something NEW in its style, prove it with numbers

You are about to copy a STYLE, not a piece. You may not be able to hear or watch the reference, so this skill turns it into measurements (`dna.json`) and a step-by-step brief (`brief.md`) you can follow with a shell. Everything below is written so a small model can follow it literally.

## 0. The rules (read once, obey always)
1. **Style, never content.** Copy tempo, key and mode, brightness, distortion, rhythm density, arrangement shape, cut rhythm, camera motion, colour grade, frame cadence, line weight. Do NOT reproduce the reference's melody, riff, lyrics, audio, footage, characters, logos, on-screen text or jokes. The tools store only measurements. If asked to copy the content itself, say you can build something in the same style instead.
2. **You cannot hear or watch it unless a tool tells you.** Never write "it sounds like", "it feels like", "it looks the same". Write what the numbers say: "tempo 165.0 vs 165.2 (OK), brightness 6.8% off (OK), rolloff 34% lower (OFF)". Say plainly that you have not listened. The person's ears and eyes are the final judge.
3. **Local and private.** The reference stays on the person's computer. Do not upload it anywhere. `af.py hear` sends a clip to an API: ask first, every time. Never print or echo API keys.
4. **Ask before anything optional:** downloads, installs, credits, uploads. Free local steps need no asking.
5. **One change per round, at most 5 rounds**, then report. Do not polish forever.
6. **Work in the project folder only.** Studies go to `./styles/<name>/`. Do not touch the person's other files.

## 1. Pick the kind (ask one short question only if unclear)
| the reference is | kind | measured by | built with |
|---|---|---|---|
| a song / audio file (mp3, wav, m4a...) | **audio** | `af.py study` | audio-forge `compose` / `score` |
| a video about the cutting, colour, motion, effects, pacing | **edit** | `study_video.py` | cinematic-edit `analyze.py --style` |
| a drawn / animated video (ink lines, held frames, flat colour) | **animation** | `study_video.py --kind animation` | `2d-animation-long-form-aivxer` (original characters only) |
A video has BOTH: study it as video and also study its soundtrack as audio (the video study does this automatically when audio-forge is installed).

## 2. Library first
`python3 <skill>/scripts/copy.py list` shows prebuilt styles. If the person names one (for example "roblox guitar cover"), use it: `copy.py show roblox-guitar-cover`, then go to step 5. Shipped in the kit: audio genre `roblox_guitar_cover`, audio style and video style `roblox-edit`.

## 3. Study the reference
```
python3 <skill>/scripts/copy.py study /path/to/reference.mp3 --name my-style        # audio
python3 <skill>/scripts/copy.py study /path/to/reference.mp4 --name my-style         # edit (add --kind animation for drawn animation)
```
It writes `./styles/my-style/`: `dna.json` (numbers), `brief.md` (how to build, with the numbers filled in), plus `spectrogram.png` (audio) or `contact.jpg` (video, one frame per shot) and a draft `genre.json` / `preset.json`. Read `brief.md` completely. If you can SEE images, also open the picture. If the brief says the tempo is ambiguous (for example 165 or 82.6 BPM), ask the person which one feels right before building.

## 4. Build it (follow the brief, section "How to build it")
**Audio** (audio-forge, `AF=<audio-forge>/scripts/af.py`):
1. `python3 $AF` finds a private Python for you; no setup beyond `af.py doctor`.
2. `copy.py install my-style` copies the draft `genre.json` to `~/.config/audio-forge/genres/` (not needed for library styles).
3. `python3 $AF compose --genre <genre_name> --bpm <tempo> --key "<tonic>" --scale <mode> --bars <seconds*bpm/240> --seed 1 --out cand.wav`
4. Never copy the reference's chords or melody: write a NEW progression in the same mode (the brief says which chord types are used). Use `--seed 2,3...` for other takes.
**Edit** (cinematic-edit): `copy.py install my-style`, then `analyze.py your.mp4 --out work --plan plan.json --style my-style`; edit the plan by hand using the brief's cut rhythm, shot lengths and grade; render a preview. For a video that also needs matching music, build the audio half the same way.
**Animation** (`2d-animation-long-form-aivxer`): do not use `analyze.py`. Read its SKILL.md, then set its style parameters from `dna.json`: typical hold frames (2 = animate on twos), ink stroke px, palette hex values and their shares, median shot length, camera shift, flashes. Write ORIGINAL characters and scenes; copy the technique, not the drawings.

## 5. Compare and fix (the loop that replaces listening)
```
python3 <skill>/scripts/copy.py compare cand.wav styles/my-style/dna.json        # audio
python3 <skill>/scripts/copy.py compare preview.mp4 styles/my-style/dna.json     # video / animation
```
It prints every measure with reference, candidate, difference, a verdict (OK / CLOSE / OFF) and, for OFF, WHICH KNOB to change. Do this:
1. Pick the single OFF row with the biggest effect (order: tempo, key, loudness, brightness, balance, rhythm, arrangement).
2. Change that one knob (the compare output names it), rebuild, compare again.
3. Log each round in `./styles/my-style/log.md` (round, what you changed, closeness before and after). If a change made the closeness worse, undo it.
4. Stop at 5 rounds or when every row is OK or CLOSE.
The closeness number is a heuristic from the measurements. It is not proof that it sounds or looks the same.

## 6. Report (short, honest)
Give: the style name, the final numbers table (what matches, what is still OFF), which knobs you changed, the file paths, and: "I have not listened to / watched this; please check it by ear/eye." Offer the next take (`--seed`, another knob). Do not call it "identical" or "perfect".

## 7. Optional helpers
- `af.py hear file.wav --question "..."` (audio-forge): sends a short clip to NVIDIA's hosted audio model for a text description. Uploads audio: ask first. It is an opinion, not a measurement.
- `reference-check`: if the style involves a real person, brand or game, check facts and rights.
- `video-studio`: the front door that chains this with the editing and audio flows.

## 8. When something fails
- "audio-forge not found" / "cinematic-edit not found": the kit is not installed; tell the person to run `python3 install.py` from the kit and restart opencode.
- A tool prints a Python/ffmpeg error: run `af.py doctor` or `bash <cinematic-edit>/scripts/doctor.sh` and report its output; do not install packages by guessing.
- The numbers do not improve after 3 rounds: stop, report the three best OFF rows, and ask the person what they hear (their ear beats the metrics).

## Files
`scripts/copy.py` (entry point) · `reference/model-cheatsheet.md` (the 12-line version for small models) · `reference/dna-fields.md` (what each measurement means and which knob moves it) · `library/<name>/` (prebuilt styles: dna.json, brief.md, genre.json, README.md).


## 1.2 additions (several references, deeper analysis, plans)
- **Several references:** `copy.py study A.mp3 B.mp3 C.mp3 --name family` studies each, then BLENDS them: what they all share (the style), ranges (your room to be original), tempo clusters, key votes, drop anatomy statistics. `copy.py blend DIR DIR --name N` blends already-studied styles. Compare against a family with `copy.py compare cand.wav styles/family/dna.json`: inside the member range is fine.
- **`copy.py deep FILE`:** hard points, sections, layers, loop-readiness, bar map, Audacity labels. **`copy.py lyrics`:** lyric statistics (Whisper optional, asked first).
- **`copy.py plan NAME --bars 64 [--bpm B]`:** a bar-by-bar build plan from a studied style (sections scaled to your length, layers per section, hard points at the same % positions, the exact `compose --plan` command).
- **`copy.py adapt REF --out CANDIDATE [--genre G] [--rounds N]`:** compose → compare → adjust (up to 5 rounds) towards a reference (audio-forge).
- **`copy.py audition [--out DIR]`:** timestamped instrument showcase + mini-mix (audio-forge).
- **`copy.py stem-mix STEMS_DIR --out WAV`:** mix a folder of stems into a finished mix (audio-forge).
- **`copy.py loop-doctor FILE [--repair OUT]`:** diagnose and repair a music loop (audio-forge).
- Odd extensions (`.mpeg` holding mp3, `.mpga`, ...) are detected with ffprobe; `copy.py` also finds the kit's skills when run straight from an unzipped kit.
- Prebuilt: `roblox-lms-family` (ten measured Last Man Standing themes). For Roblox game music use the **roblox-ost** skill.

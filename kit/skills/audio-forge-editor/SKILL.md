---
name: audio-forge-editor
description: Make music and sound that locks to a video edit, in cinematic-edit, NextPhase editor-v1 or any editor - score a whole video (bed whose drop lands on the biggest moment), fit a bed to existing cuts, land the drop on a spoken word, snap cut times to the beat, add whoosh/impact/tick accents, clean up a voice, or dub subtitles into speech. Use when the user wants an edit "on the beat", music that fits a video, a beat-synced bed, music for a talking-head video, or audio for cinematic-edit / editor-v1. Needs the audio-forge skill.
license: MIT
compatibility: opencode, Claude Code
---

# Beat-synced audio for video edits (companion to audio-forge)

1. Load the `audio-forge` skill (hard rules apply: free/local, ask before downloads, original music, say you have not listened).
2. Which host?
   - **cinematic-edit**: use its `scripts/audioforge.py` (detect, state, score, sfx, cue, voice). It writes the brief, calls `af.py score`, and patches a COPY of plan.json. Read `audio-forge/reference/cinematic-bridge.md`.
   - **editor-v1 or another editor**: read `reference/editor-bridge.md` and follow Recipes A-D (fit-tempo -> compose -> plan-bed -> snap / sfx-cues).
   - **No editor, just a length**: `af.py score --duration S --style <id> --hero T --out bed.wav`.
3. Establish what exists: the approved plan, shots (`scenes.py` -> work/shots.json), words (work/tx/words.json), the video length. Do not build over an unapproved plan.
4. Ask only what is missing: style (see `reference/video-styles.md`), which moment the drop should hit, whether voice or music leads.
5. Show the result: genre, BPM, where the drop lands (`drop_error_ms`), the level hint. Apply only after the person approves; never edit their files silently; never upload anything.
6. Subtitle-to-speech: confirm intent first (audio-forge section 3.5); re-run word timing on the new voice before building captions.

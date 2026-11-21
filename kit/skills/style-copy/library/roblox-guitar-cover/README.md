# roblox-guitar-cover (prebuilt style)

**What it is:** the production style of a Roblox-edit guitar cover, measured on 2026-11-16 by `af.py study` from one reference (title "Fired LMS COVER", channel ROBLOXEDITS2025OFFICIAL, 97.9 s). **The audio is not included and nothing of its notes, melody or recording is used**: only measurements (tempo, key/mode, brightness, distortion, stereo width, loudness, arrangement shape).

**Measured:** 165 BPM (could also feel like 82.6), 4/4, G# minor, -14.5 LUFS, crest 14.5 dB, spectral centroid 2.67 kHz, flatness 0.61 (distorted guitar), side/mid -6.4 dB, about 1.7 attacks per beat, loud from bar 5 to the end with one short break near bar 57.

**Shipped as:** audio-forge genre `roblox_guitar_cover` (aliases `roblox-edit`, `guitar-cover`), audio style `roblox-edit`, and cinematic-edit video style `roblox-edit`.
- `genre.json` = the shipped genre (also built into audio-forge), `dna.json` + `brief.md` = the measurements and how to build from them. The video style `roblox-edit` is built into cinematic-edit (`styles.d/roblox-edit.json`).

**How close is the generated music (measured, not heard):** 61 out of 100 on 18 numbers. OK or close: tempo, key, loudness, spectral centroid, flatness, 5 of 6 frequency bands, stereo width, attacks per beat. Still off: crest factor (ours is more compressed), 85% rolloff (ours is darker), note sustain (ours is shorter), the 16-step rhythm fingerprint and the energy curve (ours has a shallower intro and break). Nobody has listened to it: judge by ear, then adjust with `af.py compare`.

**Video half is an assumption**, not a measurement: the reference was audio only. Run `style-copy` on a real Roblox edit video to replace `preset.json` with a measured one.

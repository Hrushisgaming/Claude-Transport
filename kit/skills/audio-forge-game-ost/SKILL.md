---
name: audio-forge-game-ost
description: Build a complete set of original video-game soundtrack tracks (lobby/menu, tension, chase, last-life climax, win/lose stingers, loops and adaptive stems) in survival-horror chase style like Forsaken-type Roblox games, or chiptune, metal, cinematic and ambient game styles. Use when the user wants game music, a chase theme, an OST, adaptive/layered game audio or looping tracks. Needs the audio-forge skill.
license: MIT
compatibility: opencode, Claude Code
---

> **Roblox games:** use the `roblox-ost` skill instead (it adds measured LMS references, hard-point analysis, loop checks, Roblox upload limits and a Luau director). This skill stays as the generic engine-agnostic game-OST guide.

# Game soundtrack sets (companion to audio-forge)

1. Load the `audio-forge` skill and follow its hard rules (free/local, ask before optional downloads, original compositions only; never copy a game's actual tracks).
2. Ask once (skip what is known): game feel (survival-horror chase / retro chiptune / cinematic / metal / ambient), how many states they need (lobby, tension, chase, climax, win, lose), target loop length, and whether the engine wants separate stems for adaptive layering.
3. Pick **one key and one BPM** for the whole set (chase games: 150-176 BPM, phrygian or harmonic minor).
4. Render with `compose` as in `audio-forge/reference/genres.md` section "Game soundtrack sets": ambient lobby, `horror_chase` at `--intensity 0.4` for tension and `0.9` for chase, `metal` for the climax, `sfx` stingers for win/lose, `--stems` for adaptive layers, `audio_edit loop` for seamless loops.
5. Verify each with `analyze --brief`, give the user a table (file, BPM, key, length, role), and say plainly you have not listened to them: they should audition and tell you which to push harder (`--seed`, `--intensity`, `--override`).

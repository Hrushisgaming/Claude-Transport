---
name: roblox-ost
description: Make music for a Roblox game (an OST) - lobby, tension, chase, Last Man Standing (LMS), win/lose stingers - by studying reference themes with measurements and building ORIGINAL looping tracks that fit the game's states, then checking loops, loudness and Roblox upload limits. Use whenever the person says Roblox music, Roblox soundtrack, OST, game music, chase theme, LMS / last man standing theme, round music, "make it like Forsaken" or similar, gives reference themes to learn from, or asks to analyse a track's drops, hard points, structure, loop points or lyrics. Includes the deep audio analyzer (hard points, layers, loop-readiness, bar map, lyrics statistics) and a Luau MusicDirector. Works in opencode and Claude Code with any model that has a shell, even one that cannot hear audio. Copies a style, never a track.
license: MIT
compatibility: opencode, Claude Code. Needs Python 3.9+ and ffmpeg. Uses the audio-forge and style-copy skills from the same kit (install with install.py). Lyrics from audio need Whisper (optional, asked first).
---

# roblox-ost: study a style, build original game music, prove it works in a loop

You make music for a game that plays it in STATES (lobby, round, chase, last-man-standing, win/lose). You may not be able to hear. So you work with measurements, build with `af.py`, and verify with numbers. Read `reference/roblox-ost-handbook.md` once when you start a Roblox music job (what each state needs, what the measured LMS references share, Roblox limits, loops, adaptive layering).

(`audio-forge-game-ost` is the older generic game-music skill; for Roblox use this one.)

## 0. Rules (obey always)
1. ORIGINAL music only. References are studied for style (tempo, key, structure, hard-point anatomy, layers, loudness). Never reproduce a reference's melody, riff, lyrics or audio, never sample it, never upload a ripped track. Say so if asked to "just remake it".
2. You cannot hear. Say "I have not listened; audition it" when you report. Labels such as drop, break or vocal are heuristics from energy.
3. Ask before anything that downloads (Whisper ~500 MB, Demucs ~1 GB, voice packs) or uploads. Nothing here uploads to Roblox for the person.
4. Lyrics: store statistics only. Transcripts are written only with `--keep-text` into a private `lyrics.local.json`; never paste lyrics of a real song into the chat or a file the person will share.
5. Half-time/double-time is a human call. When the tool says a tempo is ambiguous (e.g. 96 vs 193 BPM), ask which one they tap before building.

## 1. Pick the job
| The person wants | Do |
|---|---|
| to learn from reference themes | section 2 |
| one track in that style | sections 2 then 3 |
| a whole game set (lobby ... win/lose) | section 4 |
| to analyse a track (drops, hard points, loops, lyrics) | `copy.py deep` / `copy.py lyrics` (section 2) |
| to check a file before upload | `af.py ost check FILE --bpm B --loop` |

Prebuilt: `copy.py list` shows `roblox-lms-family` (measured from ten LMS themes). Use it when no references are given, or install it: `copy.py install roblox-lms-family`.

## 2. Study references (one or many)
`SC=<skills folder>/style-copy/scripts/copy.py` (the doctor shows where: `python3 $SC doctor`)
```bash
python3 $SC study ref1.mp3 ref2.mp3 ref3.mp3 --name my-family     # several files = studied one by one, then BLENDED
python3 $SC show my-family                                        # read brief.md fully: shared habits, ranges, numbers
python3 $SC deep ref1.mp3                                         # one track bar by bar: deep/ref1/timeline.md, labels.txt, hardpoints.csv, timeline.png
python3 $SC lyrics ref1.mp3 --deep deep/ref1/deep.json            # lyrics statistics (needs Whisper: the tool says so and exits 3; ask first)
python3 $SC lyrics --text lyrics.txt --deep deep/ref1/deep.json   # or lyrics the person typed: statistics only
```
Odd extensions such as `.mpeg` that hold mp3 are handled (ffprobe decides). One reference teaches one sound; several teach a STYLE: the shared habits are the style, the ranges are your room to be original.
Read in `timeline.md`: tempo feel, form, **hard points** (impacts, cuts, risers, drops WITH anatomy), layers entering/leaving at each section, the bar map, loop-readiness. Open `labels.txt` in Audacity (File > Import > Labels) so the person SEES the points on the waveform.

### Check your analysis against listeners (rev 2 tools)
`af.py survey DIR` (table over many tracks; run before/after any analyzer change), `af.py aicheck deep.json answer.txt` (score what a listening AI said against the measurements; `--prompt` writes the check-my-numbers prompt), `af.py at deep.json 36` (bar map around a time). See `NOTES-FOR-AGENTS.md` at the kit root.

## 3. Build one track
```bash
python3 $SC plan my-family --bars 64          # bar-by-bar plan + the compose command (hard points at the same % positions)
python3 af.py compose --genre horror_chase --key A --scale minor --bpm 178 --bars 64 --plan '<from plan.md>' --out cand.wav
python3 af.py deep cand.wav                   # YOUR hard points, form, loop check
python3 af.py compare cand.wav styles/my-family/dna.json   # numbers vs the family; a value INSIDE the member range is fine
```
(`af.py` lives in `<skills folder>/audio-forge/scripts/`.) Change ONE knob per round (the compare output names it), at most 5 rounds, log each round. Report what matches, what is still off, and that you have not listened.

## 4. Build a whole game set
```bash
python3 af.py ost build --out ost/ --family styles/my-family --key A --scale minor --bpm 178 [--format ogg] [--target-lufs -14] [--quick]
python3 af.py ost check ost/chase.ogg --bpm 178 --loop
```
Writes lobby, tension, chase (+stems), lms_intro (once) + lms (loop), win, lose; every loop is folded onto itself and cut to whole bars, loudness-matched; `roblox_manifest.md` says what plays when; `MusicDirector.luau` is the in-game state machine (crossfades on bar lines, intro then loop, stingers). One key and one BPM across the set so states crossfade and stems layer.
The person uploads at create.roblox.com (Creator Hub > Assets > Audio), puts the asset IDs into `TRACKS` in `MusicDirector.luau`, and tests in Studio. You have NOT run the Luau in Studio: say so.

## 5. Check before delivering
- `af.py ost check FILE --bpm B --loop`: format, length (<= 7 min), size (< 20 MB), sample rate (<= 48 kHz), peak headroom, whole bars, seam click, near-silent ends. Re-check Roblox's current audio rules at create.roblox.com/docs/audio/assets (they change; uploads need permission grants).
- Looping Sounds: prefer ogg/flac/wav over mp3 (encoder padding can add a tiny gap): verify in Studio.
- Loudness: the kit targets -14 LUFS for music beds so effects keep headroom. That is a choice, not a Roblox rule; the references measure -7.6 to -15 LUFS.

## 6. What to tell the person (always)
What was measured (3-5 numbers), what was built, which files loop, the check results, what is still OFF, and: "I have not listened. Audition the files; tell me what feels wrong and I will turn the matching knob." If a tool could not run (no Whisper, no Pillow), say what you skipped.

## Tools quick reference
| command | does |
|---|---|
| `copy.py study A B C --name N` | measure + blend references into a style family |
| `copy.py deep FILE` / `af.py deep FILE` | hard points, sections, layers, loop check, bar map, labels, picture |
| `copy.py lyrics ...` / `af.py lyrics ...` | lyric statistics vs bars and drops |
| `copy.py plan NAME --bars N` | bar-by-bar build plan from a style |
| `af.py compose ...` | render a track (genres: horror_chase, dark_ambient, metal, dnb, ...) |
| `af.py ost build / check` | whole Roblox set, loop making, loudness, upload checks, Luau director |
| `af.py compare CAND DNA.json` | numbers vs a reference or family |

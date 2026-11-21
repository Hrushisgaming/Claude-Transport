# Video Studio kit v3: cinematic-edit 3.0 + audio-forge 1.7 + style-copy + roblox-ost + video-studio

Edit any kind of video locally and for free, with picture and sound handled together. Nothing is uploaded.

## Install
```
python3 install.py              # opencode + Claude Code   (--claude / --opencode / --project to narrow)
bash ~/.claude/skills/cinematic-edit/scripts/doctor.sh         # until "All set"
python3 ~/.claude/skills/audio-forge/scripts/af.py doctor      # optional audio engine
```
Start a NEW session afterwards. Needs Python 3.9+ and ffmpeg. Existing copies are moved to `../video-studio-backups/`. editor-v1 can stay or go: cinematic-edit covers it (documentary mode).

## Say things like
- "Make `round.mp4` a hype-highlight edit, 9:16, show me the plan first" (the video-studio skill picks the flow)
- "Clean up `take.mov` for my vlog: remove the silences, captions, quiet music under it"
- "Trailer from these clips, drop on the big reveal at 31 s"
- "Cut these clips to my song, anime-AMV style"

## New in v3.3 (2026-11-20): round-2 listening fixes
- A random hunted render was heard as "tense / boss-fight action" (5/10). Now: no heroic lift by default, hollow (no-third) major chords, `bend_lead` (pitch-bent distorted saw), `string_tremolo` (cold clusters), `piano_dark`, accent-only low church bells, per-drop guitar riffs with tritone/minor-second hits, reese under the sub, chopped-Amen fills and reverse sweeps, evolving motifs, darker breakdown, optional low organ / dark brass. See `skills/roblox-ost/references/hunted-vs-heroic.md` (Round 2).
- `af.py feedback` now emits recipe changes; `huntfight.py --same-as x.recipe.json --apply overrides.json` re-renders the same piece with only those changes. Prompt updated (JSON first, code-as-data part). Tests: `tests/huntfight_smoke_test.py`.

## New in v3.2 (2026-11-20): variation by default, feedback loop, tutorial
- **Variation by default** (`forge/recipe.py`): `af.py huntfight` now picks a different recipe every run (key, tempo 168-180, chord cycles, drum style, palette, structure lengths, SFX, ending, procedural lead motifs) and avoids the last few. Pass `--lock key=D,bpm=176,...` only for what the user specified; `--seed N` or `--same-as x.recipe.json` reproduces a piece exactly. Each render writes `*.recipe.json`.
- **Mood knowledge in code**: `MOODS["hunted"]` holds what listening feedback taught (minor-only harmony, no brass/organ/glockenspiel/hero lift, dark bells, cold piano, Amen breaks, crawl SFX + shout, tape-stop/static-crash/hard-cut/dark-fade endings).
- **Feedback loop**: `TOOLS-GUIDE/HYDROGEN-PROMPT.md` (the exact prompt + JSON schema) and `af.py feedback` (turns the listener's reply into locks, mix changes, advice).
- **Tutorial**: `TOOLS-GUIDE/HOW-TO-CREATE-MUSIC.md` is how an AI should create music with this kit. Tests: `tests/recipe_test.py`.

## New in v3.1 (2026-11-20): the HUNTED rewrite
- **`af.py huntfight`**: the OST rewritten after the first one was heard as happy. Amen breakbeats, dark tubular bells, front-and-centre distorted guitars, cold piano, dark choir, minor-only harmony, crawling stereo SFX and a vocal "HA!" before the drop, a dry-tick clock section, a glitch interruption, a semitone lift, and a tape-stop + blunt-hit death ending. New `forge/horror_fx.py` (`crawl static shout_ha tape_stop blunt_hit`) and `skills/roblox-ost/references/hunted-vs-heroic.md` (what separates hunted from heroic). Tests: `tests/horror_fx_test.py`. `ostfight.py` stays as the heroic version.

## New in v3 (2026-11-19): merged real voices + weighted OST
- **19 new instruments** merged next to V2's (`piano_grand piano_bright ep_rhodes bell_church glock celesta organ_drawbar organ_church guitar_ks guitar_amp guitar_crunch guitar_heavy guitar_lead harp harpsichord chip_pluck string_ensemble brass_section bass_guitar`), written from a listening AI's description of your reference themes. V2's own names are untouched so you can A/B them: `af.py instrument_showcase --out showcase/` renders every voice at the same loudness (V2 left, real right) with an `index.html`.
- **`af.py ostfight`**: one original 64-bar OST built by priority: Eternal Hope Eternal Fight first (breakbeat drops, booms, hard cut), A Grave Soul second (the clock section: ticks, quarter-hour chimes, hour tolls, heartbeat), the other themes (not Fired/Showtime) as low-priority signatures. `af.py hopefight` is the Hope-only 52-bar piece. Both are hand-written, not random.
- Housekeeping: version file, hard-coded paths, TODO and changelog fixed. Test: `python3 skills/audio-forge/tests/instruments_test.py`. Style families added to the library: `roblox-lms-chase`, `roblox-lms-presenter`, `eternal-hope-ref`.
- **Honest:** nobody has listened to any of it. `compare.py` is slow on V2 (minutes per file).

## New in V2: Roblox music, deep audio analysis, Claude Code commands
- **roblox-ost** (new skill): study reference themes, build ORIGINAL game music for lobby / tension / chase / Last Man Standing / win / lose, check loops and Roblox upload limits, ship a Luau `MusicDirector`. Slash commands `/roblox-ost` and `/audio-deep` (plus `/copy-style`, `/studio`) are installed for **opencode and Claude Code** by `install.py`.
- **Deep analyzer** (`af.py deep`, `copy.py deep`): hard points (impacts, cuts, risers, drops with their anatomy), sections and form, layers entering/leaving, loop-readiness, tempo feel (half/double time), mid-range lead layer, bar-by-bar timeline, Audacity labels. **Lyrics** (`af.py lyrics`): statistics against the bars and drops (Whisper optional, asked first; text only when you ask).
- **style-copy**: several references blend into a style family (`copy.py study A B C --name N`), `copy.py plan` turns a style into a bar-by-bar plan, odd file extensions work, and the prebuilt **`roblox-lms-family`** holds the measurements of ten Last Man Standing themes.
- **Tested here:** selftest incl. a synthetic track with known hard points (found within 25 ms), the ten reference themes, a quick Roblox set build with seam and upload checks. **Not tested:** the Luau script in Roblox Studio, Whisper/Demucs (no model downloads in my sandbox), real opencode/Claude Code sessions, anything by ear.

**One kit, nothing separate:** `examples/lms-analysis/` holds the analysis of the ten LMS reference themes (per-track `timeline.md`, Audacity `labels.txt`, `hardpoints.csv`, `timeline.png`, `dna.json`), the blended family with its 64-bar plan, and a quick sample Roblox set (`sample-roblox-set/`: lobby, tension, chase + stems, lms_intro + lms, win, lose, `roblox_manifest.md`, `MusicDirector.luau`). The installer does not copy `examples/`; the same family is built in as `roblox-lms-family` (`copy.py list`).

## What changed (earlier version)
**cinematic-edit 3.0**: 18 style presets (`styles.py list`): hype-highlight, horror-chase, trailer, vlog, travel, sport, talking-head, tutorial, product-ad, music-video, documentary, comedy-meme, aesthetic-lofi, anime-amv, wedding-memory, news-explainer, real-estate, cyber-tech. Ten new colour looks. `silence_cut.py` (jump cuts), `scenes.py` (shot detection -> shots.json), `audioforge.py` (the bridge). Mixdown now takes a voice track (bed ducks under it), `music_start`, cue sheets, `audio.mode` voice/music/hybrid.
**audio-forge 1.1**: `score` tool (a bed whose structure follows the video's acts and whose drop lands on the biggest moment; tempo nudged by <= 10% so whole bars end on it), 4 video genres, 9 effects, `audio_edit voice`, capabilities list styles. **Fixed a bug**: `compose --plan` was ignored.
**video-studio**: one front door that runs both in order, asks about audio once, shows the plan, waits for your go.

**reference-check** (new skill): forces real search, real reference images, the agent's own checklist, compare-and-fix, and logged verified facts before it draws or shows anything real; `plancheck.py` blocks unverified on-screen facts. Free keyless fallback `refs.py wiki|commons|get` when the host has no web tools.

## Signature feature: style-copy ("Copying")
Give it a reference song or video (or name a prebuilt style) and ANY model, even one that cannot hear or watch, can build an ORIGINAL piece in that style and prove how close it got with numbers.
- `copy.py study REF` measures the style into `dna.json` (tempo, key/mode, brightness, distortion, stereo, loudness, rhythm density, arrangement shape; for video: cut rhythm, shot lengths, motion, flashes/shake, frame cadence, colour grade, palette, line weight) plus a step-by-step `brief.md`; `copy.py compare` scores your build against it and names the knob to turn. One change per round, max 5 rounds.
- Copies the style only: no notes, melody, lyrics, footage, characters or text are stored. The reference never leaves your computer.
- Prebuilt: **`roblox-edit`** (video style, assumed from the genre) and audio genre **`roblox_guitar_cover`** (measured from the reference you gave: 165 BPM, G# minor, bright distorted guitar, wide stereo, -14.5 LUFS). New in audio-forge: `study`, `compare`, guitar instruments, JSON custom genres (`~/.config/audio-forge/genres/`). New in cinematic-edit: `study_video.py`, personal styles (`~/.config/cinematic-edit/styles/`).
- opencode slash commands installed by `install.py`: `/copy-style <file or style>` and `/studio <task>` (restart opencode).
- **Honest numbers:** the shipped guitar genre scores 61/100 on 18 measurements against the reference (tempo, key, loudness, brightness, distortion, stereo and most frequency bands match; note sustain, rhythm feel, arrangement curve and crest factor do not). Nobody has listened to it. The video side of `roblox-edit` is an assumption; `study_video.py` was tested only on generated clips (it correctly found 3 shots and "drawn on twos"), not on real Roblox or anime footage.

## Also included (third-party, unchanged)
`canvas` and `editor-v3` (shared free by NextPhase) and `2d-animation-long-form-aivxer` (by aivxer), added as they were given, with their own SKILL.md, scripts and licence notes; `video-studio` routes to them and says how audio-forge and reference-check plug in. **Licence:** NextPhase asks that you do not resell or repackage their kits, and aivxer asks to keep the credit line when sharing, so keep this kit personal or share the original downloads instead. editor-v3 includes a song (`music/song.m4a`) whose licence its authors say is unconfirmed: use an audio-forge bed or your own track for monetised videos. editor-v3 spends Higgsfield credits (it asks first). Setup: `bash ~/.claude/skills/canvas/scripts/doctor.sh --install-speech` and `bash ~/.claude/skills/editor-v3/scripts/setup.sh --speech`. **Checked here:** their SKILL.md headers, Python and shell syntax, and a read of every network command (npm HyperFrames, GSAP from a CDN, pip into a private venv, optional PyTorch RobustVideoMatting through torch.hub with `trust_repo=True`, which runs code downloaded from GitHub, so say yes to it deliberately). **Not run:** their demos and setups (no internet or soundfile in my sandbox).

## Documentation (read this first)

`kit/TOOLS-GUIDE/README.md` documents **every tool in every skill** (audio-forge, style-copy, roblox-ost, cinematic-edit, video-studio): description, exact CLI, outputs/schemas, and a step-by-step tutorial per tool. One page per tool; linked from each skill's `SKILL.md`.

`kit/CHANGES/CHANGES.md` (+ `kit/CHANGES/*.md` module notes) documents every change in this V2 release, skill by skill and module by module.

## How they work together
cinematic-edit writes a *brief* (acts, hit times after speed ramps, cuts) -> `af.py score` composes the bed -> a patched COPY `plan.scored.json` comes back -> you approve -> render. Rights gate treats the synthesised bed as original. Contract: `skills/audio-forge/reference/cinematic-bridge.md`.

## Tested here (Python 3.15.2 + numpy/scipy venv, synthetic footage) and not
Passing: `af.py selftest` in full — compose (all genres incl. corporate/warm_piano/epic_trailer/soft_ambient), analyze, score (drop on the hero moment, `--plan` honoured), hear `--local`, study + compare (self = 100/100), deep detectors (hard points, drops, risers, tone shifts, fills, chord cycle, fade-out not loop-ready), lyrics, blend, ost build+check (all 7 loop states ready), all 41 instrument keys (legacy + 17 V2), breakbeats (amen/dnb/horror/metal), audition, adapt (compose→compare→adjust round log), stem_mix, loop_doctor.
**Not tested:** the NVIDIA API path in `hear` (no API key; `--local` needs none and uploads nothing), Roblox Studio (the Luau `MusicDirector` is written but not run in Studio), real gameplay/vlog footage, real opencode/Claude Code sessions, macOS/Windows beyond this host, Whisper/captions with the new styles, Kokoro voices. Nobody has listened to generated music: audition it (`af.py audition --seed N --genre G`). Style presets are starting points chosen by reasoning, not tuned on real edits.

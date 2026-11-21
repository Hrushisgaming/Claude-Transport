---
name: audio-forge
description: Generate, analyse and edit audio entirely on the user's machine for free. Composes original music from code in 16 genres (chiptune, synthwave, lo-fi, house, techno, dnb, trap, dubstep, metal, jazz, cinematic, dark ambient, survival-horror "chase" themes like Forsaken-style game OSTs), speaks text or video subtitles with text-to-speech, makes sound effects, edits and masters audio (trim, loop, duck, normalise, mux into video), analyses a reference track (tempo, beats, key, chords, groove, structure) and remakes an original piece in its style, scores a whole video (a bed whose structure follows the video's acts and whose drop lands on its biggest moment, for 18 video styles: highlights, trailers, vlogs, tutorials, podcasts, ads, travel, weddings...), and pairs with the cinematic-edit and NextPhase editor-v1 video skills to cut on the beat. Use for any request about music, soundtrack, beat, bed, jingle, voice-over, TTS, dubbing, subtitles-to-speech, SFX, remix, stems, or "make something that sounds like this".
license: MIT
compatibility: opencode, Claude Code. Needs Python 3.9+ and ffmpeg; everything else installs on demand.
metadata:
  audience: creators
  cost: free, local, no accounts
---

# audio-forge

Free, local audio toolkit. Everything the user hears is **synthesised from code or a free local model**: no samples, no paid APIs, no accounts, nothing uploaded.

## 0. Find the skill folder and run tools

`SKILL_DIR` is the folder holding this file (the skill tool usually names it). If unsure:

```bash
SKILL_DIR=$(for d in ./.opencode/skills ./.claude/skills ~/.config/opencode/skills ~/.claude/skills ~/.agents/skills; do [ -f "$d/audio-forge/SKILL.md" ] && echo "$d/audio-forge" && break; done)
AF="python3 $SKILL_DIR/scripts/af.py"        # Windows: python  or  py -3
```

Every tool is `$AF <tool> ...` and automatically uses the private environment if one exists. Tools: `doctor compose analyze remake tts subs2speech audio_edit bridge sfx separate listen selftest score hear study compare deep lyrics blend ost survey aicheck at adapt audition stem_mix loop_doctor`. `$AF <tool> --help` documents each one. New in V2: `adapt` (compose→compare→adjust towards a reference), `audition` (instrument showcase + mini-mix), `stem_mix` (stem-folder mixer), `loop_doctor` (diagnose/repair a loop), `hear --local` (offline telemetry), plus the V2 instruments and breakbeats in `forge/`.

## 1. Hard rules

1. **Free and local.** Never use a paid API, hosted TTS, credits or sign-ups. Never upload or publish anything.
2. **Ask before any optional download.** Only the core (numpy+scipy, ~60 MB) installs without asking. For everything else run `$AF doctor --list-optional --json` and ask the user using that part's `question` string, which has the form *"Do you want [PART]? It [does DESCRIPTION]. One-time download, about [SIZE]."* Ask only for parts the task needs; do not pitch the rest. Use your question tool if you have one (opencode `question`, Claude Code `AskUserQuestion`), else ask in chat and wait. Never type or request a password: if `doctor` prints a `sudo` command, show it to the user.
3. **Never reproduce copyrighted music.** "In the style of X" means tempo, key/mode, groove, instrumentation, structure and energy arc, rendered as an **original** composition. Do not transcribe or re-synthesise a reference's melody, hook or samples, and say so if asked to.
4. **Subtitles to speech: confirm first** (section 5). Never auto-dub because a subtitle file exists.
5. **Be honest about quality.** The `formant` voice is a timing placeholder, not speech to ship. Say which engine produced a voice. The synth engine makes convincing genre-appropriate demos and game/video beds, not studio-realistic orchestras or vocals.
6. **Report what you verified.** After generating, run `analyze` on the result (section 3.2) and state tempo/key/length; do not claim it "sounds good", you have not heard it. Hand the user the file and let them listen.
7. Write outputs next to the user's project (or `./audio-out/`), never inside the skill folder. Never delete user files.

## 2. First run

```bash
$AF doctor                      # python, ffmpeg, core, optional parts (installs nothing)
$AF doctor --install core       # only if core is missing; safe without asking
$AF selftest                    # ~15 s proof that synthesis + analysis + bridge work here
```
If ffmpeg is missing, doctor prints the install command (brew / winget / apt) for the user to run.

## 3. What the user can ask for

### 3.1 Compose music
Gather in **one** question at most (skip what they already said): genre/mood, length or use (loop, intro, full track, game level, video bed), tempo/key if they care. Then:
```bash
$AF compose --genre synthwave --bars 32 --out song.wav --midi --stems stems/
$AF compose --genre forsaken --bpm 168 --key F# --scale phrygian --bars 48 --seed 7 --out chase.wav
$AF compose --list              # all genres + aliases
```
Useful flags: `--seed N` (variations: change it to get a different take), `--intensity 0-1` (sparser/denser), `--dynamics 0-1.5` (flat vs dramatic energy arc), `--duration SECONDS`, `--plan '[["intro",.2],["drop",.8]]'`, `--override '{json}'` (edit any part of the genre spec, see `reference/genres.md`), `--midi` (also writes a .mid for any DAW), `--stems DIR` (one wav per instrument). Each render also writes `<out>.beatmap.json` (exact beats, bars, sections, drops).
Offer 2-3 seeds when the user is choosing. For loops, use `$AF audio_edit loop` (section 3.5).
Genres: chiptune synthwave lofi boombap house techno dnb trap edm dubstep horror_chase dark_ambient cinematic rock metal jazz, plus video-oriented `corporate` (bright, steady: product/tutorial), `warm_piano` (vlog/wedding/travel), `epic_trailer` (long build, huge hit), `soft_ambient` (stays under speech). More in `reference/genres.md`.

### 3.2 Check your own output (always)
```bash
$AF analyze song.wav --brief      # one line: bpm, meter, key, genre-like, LUFS, swing, kick pattern, sections, drops
```
Compare with what you asked for. Tell the user the result in plain words.

### 3.3 Reference audio: analyse, then remake in that style
```bash
$AF analyze ref.mp3 --out ref.profile.json            # full profile (tempo, beats, key, chords, groove, structure, spectrum, genre guess)
$AF remake ref.profile.json                           # preview the parameters that will be used
$AF compose --profile ref.profile.json --seed 3 --out remake.wav
```
Steps: (1) analyse; (2) **show the user the summary and the genre guess** (it is a heuristic, say so) and confirm; (3) if `tempo.ambiguous` is true ask which feels right ("87 or 174 BPM?") and re-run `analyze --bpm-range LO HI`; (4) remake; (5) re-analyse the remake and report how close tempo/key/groove/energy arc are; (6) iterate with `--override`, `--intensity`, `--genre`. Details and limits: `reference/analysis.md`.
Optional ask-first parts that improve this: **demucs** (stem splitter, ~1 GB: measures the real drum pattern/bassline), **librosa** (~250 MB: tempo cross-check). Offer demucs only if the user wants accuracy beyond the full-mix estimate.

### 3.4 Text to speech
```bash
$AF tts --list                                         # engines present, voices
$AF tts --text "Hello." --engine kokoro --voice af_heart --speed 1.0 --out hello.wav
$AF tts --file script.txt --voice-fx radio --out vo.wav     # fx: robot radio telephone cave deep demon chipmunk whisper
```
Engines: `kokoro` (natural, 54 voices, ~400 MB), `piper` (good, ~100 MB), `say` (macOS built-in), `espeak` (robotic, tiny), `formant` (placeholder). With no voice pack installed only `formant`/system voices exist: **tell the user, and ask-first offer the natural voice pack.** Voices and languages: `reference/tts.md`.

### 3.5 Subtitles to speech (dub / voice-over)
**Before running, ask (one question call, only what is unclear):**
1. "Do you want the subtitle text spoken aloud as a voice track, timed to each subtitle?" (when they only said "tts" and a video/subtitles exist)
2. "What should happen to the original audio: replace it (dub), keep it quietly underneath (voice-over), or just give me the voice track as a separate file?"
3. "Which voice/language?" (list what is installed)
Then:
```bash
$AF subs2speech subs.srt --engine kokoro --voice af_heart --duration 94.2 --out voice.wav
$AF subs2speech subs.srt --video in.mp4 --mode replace --out dubbed.mp4          # dub
$AF subs2speech subs.srt --video in.mp4 --mode mix --orig-db -16 --out vo.mp4    # voice-over
```
Cues too long for their slot are sped up (max x1.35, pitch kept); the rest are listed in `<out>.fit.json`. Tell the user a long subtitle file takes a while (Kokoro measured ~0.8x realtime on a modest CPU plus ~40 s model load on first use; each cue is cached). **Read the report to the user** and offer to shorten those lines, then re-run. No subtitle file? Ask-first offer **whisper** (`$AF listen video.mp4 --srt out.srt`, ~500 MB).

### 3.6 Edit and master audio
`$AF audio_edit <cmd>`: `info extract trim fade norm convert concat mix duck stretch pitch eq loop silence mux beatcut`. Loudness: `norm --lufs -14` (music/streaming), `-16` (speech), `-23` (broadcast). Looping a bed to length with crossfaded seams: `audio_edit loop bed.wav out.wav --dur 120 --xfade 1.0`. Music under voice: `audio_edit duck music.wav voice.wav out.wav`. Recipes: `reference/editing.md`.

### 3.7 Sound effects
`$AF sfx --list` then `$AF sfx --name whoosh_up --dur 0.9 --out whoosh.wav` or `--all --dir sfx/` (whooshes, impacts, hits, risers, glitch, UI, coin, laser, explosion, stingers, heartbeat, typing...).

### 3.8 Video-game soundtracks (e.g. Forsaken-style)
Survival-horror chase energy = `horror_chase` (aliases `forsaken`, `chase`, `roblox`, `horror`): 150-176 BPM, phrygian/harmonic minor, driving distorted pulse, guitars, brass stabs, industrial hits, risers, choir. Build a **set**, not one track:
- Lobby/calm: `dark_ambient --bars 32`; tension: `horror_chase --intensity 0.4`; chase: `horror_chase --intensity 0.9`; last-life/climax: `metal --bpm 176`; win/lose: `sfx stinger_bright` / `stinger_dark`.
- Use the **same `--key` and `--bpm`** across a set so layers crossfade cleanly; use `--stems` for adaptive layering; loop with `audio_edit loop`.
Full recipe: `reference/genres.md` (section "Game soundtrack sets").

### 3.10 Score a whole video (any style)
One command makes a bed that fits an edit. The host (e.g. cinematic-edit) writes a small *brief* (`audio-forge/scorebrief@1`: duration, acts with intensity, hit times, cut times, all in **video seconds after speed ramps**); you can also give just a length:
```bash
$AF score --list-styles                                   # 18 styles -> genre/intensity/tempo/speech-forward/sfx density
$AF score --brief work/af/brief.json --out work/af/bed.wav [--style trailer] [--genre G] [--seed 2] [--sfx]
$AF score --duration 45 --style vlog --hero 31.2 --exact --out bed.wav   # no brief: length + style (+ the moment the drop should hit); --exact = ends at 45.0 s with a fade, never trim by hand
```
Method: acts become song sections (quiet start = intro, the act before the peak = build, the most intense act = drop/climax, quiet end = outro); the tempo is nudged by at most 10 percent so a whole number of bars ends **exactly** on the hero moment; if the cuts already follow a grid (>= 0.55 alignment) that tempo is used. Output: the bed, `<out>.beatmap.json`, and `<out>.score.json` (`audio-forge/score@1`: bpm, genre, sections in video time, where the drop landed and the error in ms, level hint, notes). Check `drop_error_ms` (should be near 0); if it is not, try `--seed`, `--bpm`, or tell the host to shift the bed with `music_start`. Speech-led styles (`vlog talking-head tutorial documentary news-explainer comedy-meme`) set `speech_forward`: tell the host to keep the bed about -22 to -26 dB under the voice. Style recipes: `reference/video-styles.md`; the cinematic-edit contract: `reference/cinematic-bridge.md`. Speech clean-up for a recorded voice: `$AF audio_edit voice raw.wav clean.wav`. Extra effects for video: `camera_shutter record_scratch rewind notification bass_drop swipe logo_sting riser_long cash` (`$AF sfx --list`). Say you have not listened to the bed.

### 3.11 Hear a clip (optional, sends audio to NVIDIA)
`$AF hear bed.wav --question "..."` sends a short clip (max 60 s, mono 16 kHz) to NVIDIA's hosted Nemotron 3 Nano Omni and prints its description. **It uploads audio: ask the person first, every project, and never use it silently.** It needs the person's own NVIDIA key (`~/.config/audio-forge/nvidia.key`, chmod 600, or env `NVIDIA_API_KEY`); never print or echo the key. Many hosts (opencode included) do not pass audio files to the model, so this is how an agent gets any audio description at all. Report its answer as the model's opinion, not a measurement: timing and loudness come from `$AF analyze`, and whether music sounds good is the person's call. `--dry-run` checks the clip without sending anything. If it fails, tell the person once (check key and model name); do not retry in a loop.

### 3.9 Editor-v1 / video editing on the beat
Works with NextPhase **editor-v1** and any newer version through one small JSON (`audio-forge/beatmap@1`). Details and exact commands: `reference/editor-bridge.md`. Summary:
```bash
$AF bridge fit-tempo --shots work/shots.json                 # which BPM do the existing cuts already follow? (+ offset)
$AF compose --genre house --bpm 120 --bars 40 --out work/bed.wav
$AF bridge plan-bed --beatmap work/bed.wav.beatmap.json --words work/tx/words.json \
    --drop-at-word "Claude" --dur 46.4 --song work/bed.wav --grid-offset 0.1285 --cut-words "first,last"
$AF bridge snap --beatmap work/bed.wav.beatmap.json --shots work/shots.json --song-at 9.87   # beat-snapped cut times (a new file)
$AF bridge sfx-cues --beatmap work/bed.wav.beatmap.json --song-at 9.87 --dur 46.4 --accent drops,sections
```
`plan-bed` prints the `--song-at` / `--ramp` values and a ready `bed-mix.py` command. Never edit editor-v1 files silently: show the plan and what you will change, let the user approve (editor-v1 itself shows its plan before building). Building a different/bigger editor skill that should offer audio-forge to its users? See `reference/merging.md` (paste-in block, the "should I use audio-forge?" question, data contracts); a host can detect this skill with `$AF doctor --capabilities`.

## 4. Extending
Genres are data (`scripts/forge/genres.py`): copy a spec, change the rhythm strings, instruments and mix, or pass `--override`. New instruments go in `forge/instruments.py` (one function). See `reference/genres.md`.

## 5. Known limits (say these when relevant)
- Tempo was within 1 BPM on 12 of 13 synthetic test tracks (the miss was a half-time reading of a 174 BPM drum-and-bass track, which the tool flags as ambiguous): confirm half/double-time with the user. Key detection gave the true key, its relative, or the mode's parent key on 9 of 13 synthetic test tracks (weakest on power-chord-heavy rock/metal and modal tunes), so treat it as a hint and let the user confirm.
- Genre guess is a heuristic (right family most of the time, not always the exact genre).
- Full-mix groove detection is approximate; stems from demucs are much better.
- Output is synthesised: great for beds, game loops, demos, jingles and prototyping; it will not pass for a recorded band or a human singer.
- Non-English TTS voices were not exercised in testing; English voices were.


## 1.2 additions: deep analysis, lyrics, blending, Roblox sets
- `af.py deep FILE`: hard points (impacts, cuts, risers, drops with anatomy), sections/form, layers entering/leaving, chord cycle, loop-readiness, tempo feel (half/double time), mid-range lead layer, bar map, Audacity labels, picture. See `reference/deep-analysis.md`.
- `af.py lyrics FILE|--text T [--deep deep.json]`: lyric STATISTICS (density, repetition, rhyme, theme words, where words sit against bars/drops/hard points). Whisper is optional (asked first); the tool exits 3 with `needs: whisper` instead of downloading.
- `af.py blend STYLE_DIR... --name N`: several studied tracks -> one style family (shared habits, ranges, tempo clusters).
- `af.py ost build|check`: Roblox set (lobby, tension, chase+stems, lms_intro+lms, win, lose), seam-safe loops cut to whole bars, loudness match, Roblox upload checks, `MusicDirector.luau`. Use with the **roblox-ost** skill.
- `study` now stores hard points, form, layers and loop info in `dna.json -> deep` (schema audio-dna@2); `compare` scores them (first drop position, drops, hits and stops per minute, risers, chord cycle, lead share, section changes).

## New in V2

- **`adapt`** — compose → measure → compare → adjust (up to 5 rounds) towards a reference; writes `adapt.wav`, `adapt-log.json`, `adapt-log.md`. Closeness is a heuristic from measurements, not hearing.
- **`audition`** — timestamped instrument showcase WAV + `showcase.md`/`.json` + a genre mini-mix (`minimix.wav`/`.json`).
- **`stem_mix`** — mix a folder of stems into a finished mix (role detection, EQ carve, mono bass, kick sidechain, width, loudness match, limiter).
- **`loop_doctor`** — diagnose and repair a music loop (whole-bar snap, tail fold, micro-fade, DC clean, peak normalise).
- **`hear --local`** — offline measurement telemetry (bands, mud, harshness, sub, punch, stereo correlation, clipping/DC, archetypes, override suggestions); no API key, no upload.
- **17 new instruments** (`piano_m1`, `organ_rock`, `organ_pipe`, `bell_tubular`, `clock_bell`, `acid_303`, `chip_lead`, `pulsing_bass`, `y2k_bass`, `showtime_sax`, `marimba`, `rave_stab`, `orch_hit`, `rave_shout`, `heartbeat`, `siren_riser`, `clock_tick`) and breakbeats (`amen`, `dnb`, `horror`, `metal`).

All V2 details and per-tool tutorials: `kit/TOOLS-GUIDE/`. Every change: `kit/CHANGES/CHANGES.md` + `kit/CHANGES/*.md` module notes.

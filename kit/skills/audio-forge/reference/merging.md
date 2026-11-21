# Merging audio-forge into a video editor skill

For: the author of a full video-editor skill (opencode / Claude Code) who wants it to **offer** audio-forge for music, voice, sound effects and beat-synced cutting. Everything here is written so a human can follow it and an AI can follow it. Copy the paste-in block in section 5 and you have most of the integration.

Contents: 1 What audio-forge is · 2 Quick facts · 3 Three ways to merge · 4 Step-by-step (recommended way) · 5 Paste-in block for your SKILL.md · 6 The "should I use audio-forge?" question · 7 Where it plugs into an editing pipeline · 8 Data contracts · 9 Pitfalls · 10 Optional downloads · 11 Rules the AI must keep · 12 Test the merge · 13 Evolving it (v2 editor) · 14 Limits and what was tested · 15 File map

---

## 1. What audio-forge is

A free, local audio toolkit packaged as agent skills. No accounts, no paid APIs, nothing uploaded. It can:

| Capability | What the user gets |
|---|---|
| **Music** | Original tracks in 16 genres (chiptune, synthwave, lofi, boombap, house, techno, dnb, trap, edm, dubstep, horror_chase = Forsaken-style, dark_ambient, cinematic, rock, metal, jazz). Tempo, key, length, intensity controllable. Also MIDI and per-instrument stems. |
| **Text to speech** | Natural neural voices (Kokoro, 54 voices, optional ~400 MB), compact voices (Piper), system voices, plus voice effects (radio, robot, demon...). |
| **Subtitles to speech** | A subtitle file (.srt/.vtt/.ass) becomes a timed voice track, fitted to each cue, with a report of cues that do not fit. Can dub or voice-over onto a video. |
| **Reference analysis and remake** | Tempo, beats, bars, key, chords, groove, structure, loudness of any audio; an original piece rendered in that style. |
| **Sound effects** | 25 synthesised effects (whooshes, impacts, risers, UI, glitch, stingers...). |
| **Audio editing** | Trim, fade, loudness-normalise, loop, duck, mix, stretch, pitch, EQ, convert, mux into video. |
| **Beat sync for video** | Find the BPM your cuts already follow, place a bed so its drop lands on a spoken word, snap cut times to the beat, write SFX cue sheets. |

Synthesised music is great for beds, game loops, demos and prototyping. It is not a recorded band or a human singer, and the host skill should not promise that.

## 2. Quick facts

| | |
|---|---|
| Skill names | `audio-forge` (engine), `audio-forge-editor` (beat-sync companion), `audio-forge-game-ost` (game music companion) |
| Version | read `VERSION` in the skill folder (1.0.0) |
| Needs | Python 3.9+, ffmpeg. Core installs numpy + scipy (~60 MB) into a private venv at `~/.cache/audio-forge` |
| Single entry point | `python3 <skill_dir>/scripts/af.py <tool> [args]` (works on macOS, Linux, WSL and native Windows; no bash needed) |
| Tools | `doctor compose analyze remake tts subs2speech audio_edit bridge sfx separate listen selftest` |
| Detect it | `python3 <skill_dir>/scripts/af.py doctor --capabilities` prints JSON (version, ready, installed parts, genres, schemas) and exits 0 only when ready |
| Shared file formats | `audio-forge/beatmap@1`, `audio-forge/profile@1` (JSON, seconds) |
| Where it looks for configuration | environment variable `AUDIO_FORGE_HOME` (default `~/.cache/audio-forge`) |
| Cost | $0 |

## 3. Three ways to merge

**A. Side by side (recommended).** Install both skills as siblings. Your editor skill *offers* audio-forge, the agent loads it with the skill tool, and the two exchange JSON/WAV files. Nothing is copied, each skill updates independently, and users who do not want audio never see it. This is how audio-forge already works with editor-v1.

**B. Vendored.** Copy `audio-forge/scripts/` into your skill as `your-skill/audio/` and call `python3 <your-skill>/audio/af.py`. Use it when you must ship one folder. Costs: you carry updates yourself, and two skills named differently but containing the same `forge/` package can drift. Keep `VERSION` so `--capabilities` still reports it. Do not rename the `forge/` package or `af.py`.

**C. Detect-only.** Your skill never calls audio-forge directly; it just *tells the user* it exists when a request is audio-shaped. Smallest change, least automation.

Pick A unless you have a reason not to. The rest of this file assumes A.

## 4. Step by step (way A)

1. **Install audio-forge** (users run once):
   `python3 install.py` from the unzipped package. It copies the three skills into `~/.config/opencode/skills` and `~/.claude/skills` (`--project` for the current project only). Old copies are moved to `../audio-forge-backups/`, outside the skills folder, so they are never loaded twice.
2. **Keep your skill name unique.** The three audio-forge names above are taken. Skill names must be lowercase letters, digits and single hyphens, and match the folder name.
3. **Add the hook to your SKILL.md.** Paste the block in section 5 into your editor skill (a short "Audio" section near where your workflow reaches sound). Adjust the two or three marked lines to your own file names.
4. **Decide your insertion points** using the table in section 7: at planning (ask), before build (bed/voice), after build (SFX cues), at finish (loudness).
5. **Store the user's answer** in your project state (suggested: `work/audio-forge.json`) so you never ask twice.
6. **Test** with the checklist in section 12.

You do not need to read audio-forge's source. Everything the host needs is the `af.py` command line and the formats in section 8.

## 5. Paste-in block for your editor skill's SKILL.md

Copy from here to the end of the block. Lines marked `# ADAPT` are the only ones that depend on your skill.

````markdown
## Audio (optional: audio-forge)

audio-forge is a separate free, local skill that can make a music bed, read subtitles aloud as a voice track, add sound effects,
and line cuts up with the beat. Never assume it exists and never use it without the user's yes.

**Detect it** (silent, no install):
```bash
AF_DIR=$(for d in ./.opencode/skills ./.claude/skills ~/.config/opencode/skills ~/.claude/skills ~/.agents/skills; do [ -f "$d/audio-forge/SKILL.md" ] && echo "$d/audio-forge" && break; done)
[ -n "$AF_DIR" ] && python3 "$AF_DIR/scripts/af.py" doctor --capabilities   # JSON; "ready": true means core + ffmpeg are present
```
- Found and `ready` -> go to **Ask**.
- Found, not ready -> tell the user to run `python3 "$AF_DIR/scripts/af.py" doctor` (it installs a ~60 MB core, asks before anything bigger); continue without audio-forge meanwhile.
- Not found -> say once: "audio-forge is not installed; it is free and local (python3 install.py from its package). Want to continue without it?" Then continue without it.

**Ask once per project** (skip if `work/audio-forge.json` exists, if the user already said "use audio-forge" / "no music" / supplied their own audio and said to use it, or if you cannot ask the user, in which case do not use it):
Use your question tool (opencode `question`, Claude Code `AskUserQuestion`), else plain chat, and wait.
> "Do you want me to use audio-forge for this video's sound? It is a free tool that runs on your computer: it can write a music bed that fits your cuts, read your subtitles aloud as a voice track, add whoosh/impact effects on the beat, and snap cut times to the beat. Nothing is uploaded."
Options: **Yes, use it for what fits** / **Only some of it** (then ask which: music bed, voice from subtitles, sound effects, beat-snapped cuts) / **No, I'll bring my own audio** / **Not now**.
Save the answer to `work/audio-forge.json` as `{"use": "yes|partial|no", "parts": [...]}`.
If the user brings their own music, you may still offer (one line, one time) to detect its beat so the cuts can land on it. # ADAPT: your beat-sync step

**Then follow audio-forge's own rules**: load the `audio-forge` skill (and `audio-forge-editor` for the beat-sync recipes), ask before any optional download using the question strings from `af.py doctor --list-optional --json`, and for subtitle-to-speech confirm first whether to replace the original audio, keep it underneath, or just make a voice track.

**Where it plugs in** # ADAPT: map to your own stages
1. Plan stage: after the cut plan exists, show the audio plan (genre, BPM, drop word, SFX accents) with the rest of the plan and wait for approval.
2. Before build: `bridge fit-tempo` -> `compose` -> `bridge plan-bed` (bed), `subs2speech` (voice) if chosen.
3. After build: `bridge snap` (report only), `bridge sfx-cues` appended to your SFX cue sheet.
4. Finish: loudness normalise with `audio_edit norm` (-14 LUFS music-led, -16 speech-led) and re-check the voice is still clear.
Never edit the user's files from audio-forge output without showing the change first. Never upload or post anything.
````

## 6. The "should I use audio-forge?" question

This is the main user-facing behaviour of the merge, so it is worth getting right.

**When to ask**
- At the point the host knows there will be sound decisions (usually right after planning the cuts), once per project.
- Not when: the user already named audio-forge or said "no music"/"keep it silent"; the project state already has an answer; the session is non-interactive (then do not use it); the user supplied finished audio and said to use it (offer beat detection at most once, in one line).
- Ask the **big picture first**, then only the part-specific questions the chosen parts need. Do not bundle the optional-download questions into the first one; question fatigue makes people say no to everything.

**Question and options** (wording reusable as-is)

| Field | Text |
|---|---|
| Header | Sound |
| Question | Do you want me to use audio-forge for this video's sound? |
| Detail | A free tool on your computer: music bed that fits your cuts, subtitles read aloud, effects on the beat, cuts snapped to the beat. Nothing is uploaded. |
| Option 1 | Yes, use it for what fits (I'll show the audio plan before building) |
| Option 2 | Only some of it (music bed / voice from subtitles / sound effects / beat-snapped cuts) |
| Option 3 | No, I'll bring my own audio |
| Option 4 | Not now |

**Follow-ups by answer**
- *Yes*: show a one-screen audio plan (genre/mood, BPM, which word the drop lands on, voice yes/no, SFX accents) inside your normal plan and wait for approval.
- *Only some*: ask which parts (multi-select), then proceed with only those.
- *No*: record `no`; do not mention audio-forge again unless the user does.
- *Not now*: record `later`; offer again only when the user raises sound or at the finish step.

**Part-specific questions** come from audio-forge itself, verbatim, via `af.py doctor --list-optional --json` (each entry has a `question`, e.g. *"Do you want the natural voice pack (Kokoro)? It reads text or subtitles aloud in a natural human-sounding voice... One-time download, about 400 MB."*). Ask only for parts the chosen task needs.

**Subtitle-to-speech confirmation** (separate from the above, always asked): speak the subtitles aloud? replace the original audio / keep it underneath / separate voice file? which voice and language?

## 7. Where it plugs into an editing pipeline

| Editor stage | Call | Produces | Host does with it |
|---|---|---|---|
| Detect | `doctor --capabilities` | JSON | decide whether to offer |
| Plan | `bridge fit-tempo --shots shots.json` | BPM + offset + alignment score | choose a tempo for the bed; if alignment is below roughly 0.5 the cuts probably do not follow a grid |
| Plan | `analyze music.mp3 --brief` / `bridge beatmap music.mp3` | beat map of the user's own song | show where the drops are; choose where the song starts |
| Build | `compose --genre G --bpm B --bars N --out bed.wav` | bed.wav + `bed.wav.beatmap.json` (+ `.mid`, stems) | feed the bed to your mixer |
| Build | `bridge plan-bed --beatmap ... --words words.json --drop-at-word W --dur D` | `song_at`, `--ramp` values, a ready editor-v1 `bed-mix.py` command | use the numbers in your own mixer or run the command after approval |
| Build | `subs2speech subs.srt --duration D --out voice.wav` | voice.wav + `voice.wav.fit.json` | place on the voice track; show problem cues |
| Build | `bridge snap --beatmap ... --shots shots.json --song-at S` | `shots.snapped.json` + shift report | show the report; adopt only if approved |
| Post-build | `bridge sfx-cues --beatmap ... --song-at S --dur D` | cue sheet + `forge-sfx/*.wav` | append to your SFX cue sheet |
| Finish | `audio_edit norm in out --lufs -14` | normalised file | final loudness |
| Finish | `audio_edit mux video.mp4 audio.wav out.mp4 --mode replace\|mix` | muxed video (video stream copied) | optional, if you do not mux yourself |

## 8. Data contracts

All times are **seconds** (floats). Audio files written by audio-forge are 16-bit PCM WAV, 44.1 kHz stereo (voice tracks mono). If your mixer works at 48 kHz, resample on load (ffmpeg does it).

### `audio-forge/beatmap@1` (written next to every composed track as `<file>.beatmap.json`, or by `bridge beatmap`)
```json
{
  "schema": "audio-forge/beatmap@1",
  "source": "compose | analyze",
  "duration": 64.0,
  "bpm": 120.0,
  "beats_per_bar": 4,
  "swing": 0.0,
  "beats":     [0.0, 0.5, 1.0, "..."],
  "downbeats": [0.0, 2.0, 4.0, "..."],
  "sections":  [{"name": "intro", "start": 0.0, "end": 8.0, "bars": 4}, "..."],
  "drops":     [16.0, 40.0],
  "energy_per_beat": [0.21, 0.24, "..."]
}
```
`beats`/`downbeats` are song time. Section names you can see: intro build drop chase climax main verse break outro. `energy_per_beat` is present for analysed audio only (0-1).

### `audio-forge/profile@1` (from `analyze`)
Top-level keys: `tempo{bpm, candidates, steady, ambiguous, alt_octaves}`, `meter`, `key{best, relative, alternatives}`, `chords_per_bar`, `pattern{kick,snare,hat}`, `swing`, `loudness{lufs,lra,true_peak_db}`, `dynamics`, `stereo`, `bands_db`, `spectral`, `sections`, `drops`, `energy_per_beat`, `beats`, `downbeats`, `genre_guess`, `summary`.

### Files audio-forge reads from the host
| File | Shape | Used by |
|---|---|---|
| `shots.json` | `[[t0, t1, name], ...]` (also tolerates objects with `t0/t1` or `start/end`, or plain numbers) | `fit-tempo`, `snap` |
| `words.json` | `[{"w": "word", "s": 1.23, "e": 1.5}, ...]` (also `word/start/end`) | `plan-bed` |
| subtitles | `.srt`, `.vtt`, `.ass` | `subs2speech` |

### Files audio-forge writes for the host
| File | Shape |
|---|---|
| `*.beatmap.json` | above |
| `*.snapped.json` | same shape as `shots.json`, plus `*.report.json` with per-shot shifts in ms |
| `forge-cues.txt` | one cue per line: `<video_seconds> <absolute path to wav> <gain>`; lines starting with `#` are comments. This is editor-v1's `sfx-cues.txt` format |
| `voice.wav` + `voice.wav.fit.json` | per cue: `start end slot natural tempo played status text`, status `ok / overflows-slot / runs-into-next-cue` |
| `*.mid` | standard MIDI file, one track per instrument layer |
| stems dir | one WAV per instrument track |

### Versioning rules
`schema` strings are the contract. Changes are **additive**: new keys may appear, existing keys keep their meaning, a breaking change gets a new `@2`. A host should read what it needs and ignore unknown keys, and check `schema` starts with `audio-forge/beatmap@` before use.

## 9. Pitfalls

- **Time bases.** Beat maps are in *song* time. Your edit is in *video* time. `song_at` is the song time that plays at video time 0: `video_t = song_t - song_at`. editor-v1's `bed-mix.py` uses exactly this meaning (`--song-at`).
- **Bed length.** editor-v1's bed-mix never loops or stretches the song. `plan-bed` warns when the bed is too short; generate more bars or use `audio_edit loop`.
- **Tempo octaves.** Analysis can read half or double time. Confirm with the user when `tempo.ambiguous` is true, then re-run with `--bpm-range LO HI`. Tracks audio-forge composes carry their declared tempo, so analysing them is exact.
- **Name clashes.** audio-forge's speech-to-text tool is `listen.py`, deliberately not `transcribe.py`, so it cannot collide with an editor's own `transcribe.py`. Keep your scripts' names distinct from `af.py`, `compose.py`, `analyze.py`, `tts.py`, `bridge.py`, `sfx.py`.
- **Separate Python environments.** audio-forge uses its own venv (`~/.cache/audio-forge/venv`). Do not install your packages into it, and do not rely on it having yours.
- **ffmpeg** must be on PATH for audio-forge. If your editor already requires it, nothing new is asked.
- **Long renders.** A 2-minute track renders in about 5-10 seconds. Natural voices are slower: measured ~0.8x realtime on a modest CPU (a 5 s line took ~7 s) plus ~40 s to load the model on first use, so a few minutes of subtitles can take minutes. Demucs and Whisper (optional) take minutes too. Tell the user before starting any of these.
- **Do not edit the host's files silently.** `snap` and `plan-bed` only print or write new files; applying them is the host's job after the user approves.
- **Rights table.** If your editor lists third-party rights, audio-forge music, voices and effects are synthesised on the user's machine: "original, no third-party rights". Remakes are original compositions in a style and never copy a reference's melody or samples.
- **Paths with spaces** are fine; always quote them. On Windows use `py -3` or `python` instead of `python3`.

## 10. Optional downloads (always ask first)

| Part id | What it does | Size |
|---|---|---|
| core | numpy + scipy, required for everything except detection | ~60 MB (installs without asking) |
| kokoro | natural human-sounding voices (54, several languages) | ~400 MB |
| piper | compact good-quality voices | ~100 MB |
| espeak | tiny robotic voice, many languages (needs the system package manager) | ~5 MB |
| librosa | second opinion on tempo/beats when analysing audio | ~250 MB |
| demucs | splits a song into drums, bass, vocals, other; measures grooves accurately | ~1 GB |
| whisper | speech-to-text: subtitles and word timings from a video | ~500 MB (small model) |

Ask with the exact `question` strings from `af.py doctor --list-optional --json`. A host skill should not install any of these itself.

## 11. Rules the AI must keep (the host should repeat them)

1. Free and local only. No paid APIs, credits, accounts or sign-ups. Nothing is uploaded or published.
2. Ask before any optional download; never ask for or type a password (show `sudo` commands to the user instead).
3. Confirm intent before subtitle-to-speech; never dub just because subtitles exist.
4. Original music only: "in the style of" means tempo, key, groove, instrumentation and structure, never a copied melody or sample.
5. Be honest: name the voice engine used; the `formant` voice is a timing placeholder; say you have not listened to generated audio and let the user audition it.
6. Show the plan, wait for approval, then build. Do not modify the user's existing files unasked.

## 12. Test the merge

Run these in order after installing both skills and pasting the block.

```bash
AF="python3 $AF_DIR/scripts/af.py"
$AF doctor --capabilities                          # ready: true, version present
$AF selftest                                       # ALL PASSED
$AF compose --genre house --bpm 120 --bars 32 --out /tmp/bed.wav
$AF bridge fit-tempo --shots <your shots.json>     # prints a BPM and alignment
$AF bridge plan-bed --beatmap /tmp/bed.wav.beatmap.json --words <your words.json> --drop-at-word "<a word you say>" --dur <video seconds> --song /tmp/bed.wav
$AF bridge snap --beatmap /tmp/bed.wav.beatmap.json --shots <your shots.json> --song-at <from plan-bed>
```
Then in a fresh agent session, check the **behaviour**:

| Test | Expected |
|---|---|
| Ask the editor for "a video with music" | The agent asks the audio-forge question once, with the four options |
| Answer "No, I'll bring my own audio" | No further mention of audio-forge; `work/audio-forge.json` says `no` |
| Re-run the editor in the same project | It does not ask again |
| Answer "Yes", request subtitle voice | It asks replace / keep underneath / track only before generating |
| Pick a voice pack not installed | It asks with the size and what it does; "no" falls back to the placeholder voice and says so |
| Rename the audio-forge folder away | The editor says audio-forge is not installed and carries on |
| Say "use audio-forge" up front | No first question; goes straight to the plan |

## 13. Evolving it (a v2 editor)

- Keep reading `doctor --capabilities`. A v2 host can require `schemas.beatmap == "audio-forge/beatmap@1"` and fall back gracefully otherwise.
- Ask for features by adding fields to the beat map, not by changing existing ones. Likely useful additions: per-section `mood`, `loop_points`, `energy_per_bar`, `stem_files`.
- A v2 editor can write its own `shots.json` extension (extra keys per shot) without breaking `snap`, which only reads the first three entries.
- If you need a new audio capability, the place to add it is one tool file under `scripts/` plus an entry in `af.py`'s TOOLS list and `doctor.py`'s `tools` list; document it in `SKILL.md` section 3.

## 14. Limits and what was tested

Tested on Linux, Python 3.12: all 16 genres render; analysis round trips on 13 synthetic tracks (tempo within 1 BPM on 12/13, key right-or-relative on 9/13, genre top-1 on 8/13); real Kokoro neural TTS, voice effects and subtitle fitting; MIDI parsed by an independent library; the editor bridge on synthetic cuts and words; the installer and frontmatter rules; clean-machine venv bootstrap.

**Not tested:** loading inside real opencode / Claude Code sessions, macOS, native Windows, Piper, eSpeak, macOS `say`, Demucs, Whisper, librosa, non-English voices, feeding the bridge's output into editor-v1 itself. Nobody has listened to the generated music; the user should audition it.

## 15. File map

```
AudioForge/
  install.py            installs the three skills (opencode + Claude Code)
  SETUP-PROMPT.txt      paste into an agent to install and demo
  README.md             overview for users
  README-MERGING.md     this file
  skills/
    audio-forge/        engine + docs (SKILL.md, VERSION, reference/, scripts/)
      scripts/af.py     single entry point
      scripts/forge/    synthesis engine (dsp, instruments, drums, theory, genres, song)
      reference/        genres.md analysis.md tts.md editing.md editor-bridge.md merging.md
    audio-forge-editor/     beat-sync companion skill
    audio-forge-game-ost/   game-soundtrack companion skill
```

## 16. The reference host: cinematic-edit (1.1)

cinematic-edit 3.0 is a full host built the way sections 3-7 describe (way A, side by side). Its `scripts/audioforge.py` does the detect/ask/state/score steps, and its SKILL.md has an "Audio" section you can copy as a model. The contract it uses beyond sections 7-8:

| File | Direction | Purpose |
|---|---|---|
| `audio-forge/scorebrief@1` | host -> audio-forge | duration, acts + intensity, hit times, cut times (video seconds, after speed ramps) |
| `audio-forge/score@1` | audio-forge -> host | bed path, bpm, sections in video time, where the drop landed (`drop_error_ms`), level hint |

Call: `python3 af.py score --brief brief.json --out bed.wav`. Detect: `doctor --capabilities` now also lists `styles` and `provides: video_score`. Details: `reference/cinematic-bridge.md`.

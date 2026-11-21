---
name: video-studio
description: One front door for making any video with the cinematic-edit and audio-forge skills working together. Use when the user wants a finished video (highlight reel, vlog, trailer, tutorial, podcast clip, ad, travel film, music video, wedding film, meme...) with picture AND sound handled in one flow - "edit this and add music", "make me a trailer from these clips", "clean up my talking video and score it". It picks the style, runs the edit, offers audio-forge for music/voice/effects, and keeps both on one plan. Routes to cinematic-edit (general), canvas (minimal talking-head explainers), editor-v3 (silhouette long-form) and 2d-animation-long-form-aivxer (animated explainers). audio-forge and reference-check are optional helpers.
license: MIT
compatibility: opencode, Claude Code. Needs Python 3.9+ and ffmpeg.
---

# video-studio: picture + sound, one flow

You orchestrate two skills. Load `cinematic-edit` (the editor, owns `plan.json`) and, only if the person agrees, `audio-forge` (music, voice, effects). Their rules apply: free and local, nothing uploaded, ask before downloads, look at real frames, never claim you listened to generated audio.

## 0. Check the tools
`python3 <video-studio>/scripts/studio.py doctor` prints which skills are installed and ready (JSON, exit 0 = cinematic-edit ready). Missing cinematic-edit: stop and tell the person how to install the kit (`python3 install.py`). Missing audio-forge: carry on without it, say so once.

## 1. Intake (one short question at most; otherwise decide and state assumptions)
What footage, which kind of video, target format (default from the style), whether they have their own music or voice. Pick a style: `python3 <cinematic-edit>/scripts/styles.py list`.
| they say | style |
|---|---|
| gameplay / kill montage / highlights | `hype-highlight` (sport: `sport`; scary chase: `horror-chase`) |
| trailer, teaser, launch | `trailer` |
| me talking: vlog / podcast / how-to / jokes | `vlog` / `talking-head` / `tutorial` / `comedy-meme` |
| product, app, brand | `product-ad` (tech reveal: `cyber-tech`) |
| clips + a song | `music-video` / `anime-amv` / `aesthetic-lofi` |
| trip, nature, property, wedding | `travel` / `real-estate` / `wedding-memory` |
| found footage + narration | `documentary`; data story: `news-explainer` |
| "make it like THIS video / song" (any reference file or a named style such as the Roblox guitar cover) | **`style-copy`** skill (study, build original, compare by numbers); prebuilt: `roblox-edit` |
| me talking, wanting a premium minimal look (paintings, charts, captions, no effects on my face) | **`canvas`** skill (long 16:9 or short 9:16) |
| a long cinematic piece in a backlit silhouette look (needs a front take AND a side take; paid Higgsfield credits) | **`editor-v3`** skill |
| a topic or script turned into an animated 2D explainer / money or history story, no footage | **`2d-animation-long-form-aivxer`** skill |

Start the project: `python3 <video-studio>/scripts/studio.py new myvideo --style vlog --source take.mp4` (makes the folder, `work/studio.json` records style/source/answers so nothing is asked twice).

## 1b. Real things need reference-check
If the video names or shows a real game, character, controller, product, person, place or figure, load the `reference-check` skill BEFORE planning visuals or writing any on-screen text, and follow it in order (search, real references you look at, your own checklist, compare and fix, log verified facts). Its checked-facts table goes into PLAN.md.

## 2. The flow (each step hands files to the next)
1. **Prepare picture.** Talking footage: `silence_cut.py`, then `transcribe.py` (cinematic-edit mode D). Several clips + a song: `montage.py`. Always: `scenes.py` -> `work/shots.json`.
2. **Draft the edit.** `analyze.py <video> --out work --plan plan.json --style <id>`. Look at frames at the moments; re-rank by story; write the arc, overlays, captions.
3. **Ask about audio (once).** Follow cinematic-edit's "Audio" section: `audioforge.py detect`, then the question, then `audioforge.py state --set ...`. Skip if they brought their own track and said to use it.
4. **Plan the sound.** `audioforge.py score plan.json [--sfx]` -> `plan.scored.json` (bed whose drop lands on the hero moment; speech styles get a quiet bed). Voice from subtitles only after confirmation (`audioforge.py voice ... --yes-confirmed`). Noisy voice: `audioforge.py clean-voice`.
5. **Show the plan and wait for the go:** arc, the hits, the audio plan (genre, BPM, where the drop lands, level), sources and rights (`plancheck.py plan.json --md PLAN.md`).
6. **Preview, inspect, adjust.** `render.py plan.json out --preview` and stills (`--range a,b --png`); view them. Offer another bed take (`--seed 2`) rather than describing sound you cannot hear.
7. **Final and export.** `render.py` then `export.py --preset tiktok|reels|shorts|youtube|x|all`. Hand over, say what you would change next, publish nothing.

## 1c. Copying a style (the signature feature)
When the person gives a reference to imitate, or names a prebuilt style, load `style-copy` and follow it: `copy.py list`, `copy.py study REF`, build an ORIGINAL piece from the brief (audio-forge for music, cinematic-edit for the edit, the animation skill for animation), then `copy.py compare` and fix, one change per round. It copies the style only, never the melody, footage, characters or text, and it works with models that cannot hear or watch because everything is measured. In opencode: `/copy-style <reference file or style name>` and `/studio <task>` start these flows.

## 2b. The other skills in this kit (third-party; load their own SKILL.md and follow it, do not rewrite their rules)
| skill | what it makes | cost / needs | audio |
|---|---|---|---|
| `canvas` | minimal edit of a talking head: paintings, photos on paper, blue line, graphs, explainer graphics, word-by-word captions | $0. Node 22+, Chrome, ffmpeg, ~3 GB free while rendering. Always asks LONG or SHORT first | no music unless the creator gives one; `bed-mix.py` mixes it |
| `editor-v3` | long 16:9 cinematic edit, speaker as a coloured-backdrop silhouette | edits free; the silhouette clips are made in Higgsfield and spend the person's credits: show the cost, wait for a clear yes. Needs a front take and a side take | the kit song's licence is unconfirmed (see its LICENSE-NOTES.md) |
| `2d-animation-long-form-aivxer` | 20 s to 20 min animated ink-line explainer from a script, original characters | free tools (skia-python, sherpa-onnx, ffmpeg); slow renders (about 10-15 min per minute on 2 CPUs) | makes its own voice, music and effects |

Run each skill's own setup first (`bash ~/.claude/skills/canvas/scripts/doctor.sh --install-speech`; `bash ~/.claude/skills/editor-v3/scripts/setup.sh --speech` then `scripts/py scripts/demo.py`). They install private environments under `~/.cache`, never system-wide; for the animation skill, create a virtual environment instead of using `--break-system-packages`.

**How the helpers plug in (ask first, as always):**
- `reference-check`: Canvas paintings come from Wikimedia Commons (`refs.py commons "<query>"` prints each file's licence for PLAN.md); log every fact that appears on screen or in the script with `refs.py claim`; the animation skill says to "research or flag" facts, so verify them with a source or tell the person which were not checked.
- `audio-forge`: when the person wants an ORIGINAL bed with no rights worries (for editor-v3 this replaces the kit song of unconfirmed licence): `af.py score --duration D --style documentary|talking-head --hero T --exact --out bed.wav`. Canvas: `bed-mix.py --song bed.wav --song-at 0 --dur D --under 18.6`. Editor-v3: set `EDITOR_SONG=bed.wav`, `DROP_IN_SONG` = the bed's `drop_start_s` and `DROP_AT` = the hero time in `mix.py` (the two are equal when the bed starts at video time 0). These hand-offs are written from reading the scripts, not tested.
- `cinematic-edit`: use it for action/gameplay/general edits, and for `silence_cut.py`, `scenes.py` and exports on any finished render. The three skills above own their own looks; do not mix their effects.
- Credit: the animation skill is by aivxer ("keep this credit line when sharing or selling"); Canvas and Editor V3 are shared free by NextPhase ("don't resell or repackage as a paid product"). Never strip their credit or LICENSE-NOTES.

## 3. Rules of thumb
- Voice leads in speech styles: bed -22 to -26 dB, effects quiet (`audio.mode: voice`). Music leads in music styles.
- One hero moment per video: freeze or biggest hit, the bed's drop on it, silence a beat before it.
- Styles are starting points. Say which you chose and why; the person's taste wins.
- Keep one plan: never fork plan.json by hand outside `plan.scored.json`; `--apply` only after approval.

# NOTES FOR AGENTS (read first; written 2026-11-18)

You are picking up a job another Claude was doing when its chat was deleted. This file says what the job is, what is done, what is true, and what to do next. TODO.md has the checklist.

## The job (from the user)
The user makes Roblox game music (lobby / tension / chase / Last Man Standing "LMS"). This kit studies REFERENCE themes with measurements and builds ORIGINAL tracks. The analyzer cannot hear, so we test it against what listening AIs (Gemini in AI Studio, Qwen) hear. When they disagree, check the raw bar data (`af.py at`) and fix the analyzer. The user also wants the tools to analyze and copy styles better.

## What happened so far
1. A listening-test-pack was built (`listening-test-pack.zip`): audio of 4 reference tracks + a sketch, and prompts. Step 1 (A Grave Soul NOW RUN) was run in Gemini; see `listening-test-pack/results/a-grave-soul_gemini.txt`.
2. Gemini AGREED with the analyzer on: 164 BPM, minor key, no vocals, opening impact ~1 s, drop ~12 s, big drop ~48-49 s.
3. Gemini found things the OLD analyzer missed: a breakdown (it said 0:36-37), a snare roll / riser (0:44-49), a final cut at ~1:09 with a tail. It also called the 0:49 moment the climax while the old analyzer labeled that whole section "outro".
4. Checking the raw bar map showed the old analyzer HAD the data (bars 27-30 sit ~3 dB lower, bars 48-50 fall to silence) but (a) `detect_stops` only fires on >=14 dB cuts, (b) `label_sections` called the last section "outro" because its mean energy included the fade, (c) nothing looked for dips or ramps.
5. THIS session fixed that in `skills/audio-forge/scripts/deep.py` (rev 2, see CHANGELOG): `detect_tail`, `detect_dips` (breakdowns + builds), tail-aware `label_sections`, new rows in timeline.md / labels.txt / hardpoints.csv, and `hard_points.breakdowns/builds/tail` in deep.json. A Grave Soul now reads: build 1-8, drop 9-18, drop 19-26, break 27-30 (0:38), build 31-33 (0:44), drop 34-47 (0:48.3), outro 48-50, end cut 1:09.8.
6. New tools (in `skills/audio-forge/scripts/`, all via `af.py`): `survey` (table over many tracks = regression check), `aicheck` (scores an AI's pasted answer against deep.json, or prints the check-my-numbers prompt), `at` (bar-map slice around a time).
7. `study.py` / `plan.py`: style DNA and build plans now carry breakdowns, builds and the end cut.
8. Example analyses for 5 tracks were regenerated (`examples/lms-analysis/tracks/*`), and the 5 check-my-numbers prompts in the listening pack were rebuilt from the new analyzer. Baseline table: `examples/lms-analysis/survey-rev2.md`.

## Rules (keep these)
- Nobody here can hear. Never say a track "sounds like" anything. Report measurements and say "I have not listened; audition it".
- ORIGINAL music only. Study style, never copy a melody, riff, lyrics or audio. Never paste lyrics of a real song. Lyrics = statistics only.
- Ask before downloading models or uploading anything.
- Half/double tempo is the user's call: ask which tempo they tap.
- If a lyric file is for Suno, write every line out in full, no "(same)" or "..." (the user's saved preference).
- After ANY change to deep.py: run `python3 skills/audio-forge/scripts/af.py survey <folder of audio> --out new.md` and diff against `examples/lms-analysis/survey-rev2.md`. Do not ship a change that adds breakdowns to every track.

## Known limits of rev 2 (be honest about these)
- Bar-level resolution (~1.5 s at 164 BPM): section starts are bar-grid times; Gemini said breakdown 0:36-37, analyzer says 0:38.1 (data shows the dip starts at bar 27). Trust the bar data, not the AI's seconds (AIs are good to about +-2 s).
- The 0:24 "drum fill" Gemini heard is NOT confirmed by the data (only a faint bump). Unconfirmed, not disproven.
- "Build" is an energy / onset-density ramp (+0.4 onsets/beat, +0.2 dB/bar for A Grave Soul), not a detected bright sweep: the air band does not rise in that track. Whether it is a snare roll is for ears.
- The first drop is stamped at bar 9 = 0:11.74; the level jump in the audio is at ~12.5-13.0 s (bar-grid rounding). Use `af.py at` for exact feel.
- Quiet starts (first 3 bars) are never called breakdowns. Tracks under 3 s (win/lose stingers) are skipped.
- 5 of the 10 example tracks (necrobloxians, showtime, eternity-forsakened, eternity-v2, vigilante-shootdown) have no audio in the kit, so their deep.json / dna.json are still rev 1. The dna.json of the 5 refreshed tracks is also still rev 1 (run `af.py study` on the audio to refresh).
- `survey-rev2.md` does not include A Grave Soul (its audio lives in the listening pack); add it when you re-baseline.

## Where things are
- analyzer: `skills/audio-forge/scripts/deep.py` (detectors near the top; `label_sections`; outputs at the bottom)
- new tools: `survey.py`, `aicheck.py`, `at.py` (same folder). style copy: `skills/style-copy/scripts/plan.py`, `skills/audio-forge/scripts/study.py`
- Roblox workflow skill: `skills/roblox-ost/SKILL.md` + `reference/roblox-ost-handbook.md`
- listening pack (separate zip): `README`, `prompts/`, `audio/`, `results/`


## UPDATE 2026-11-20 (v3.2): READ THIS FIRST
- VARIATION IS THE DEFAULT. Never reuse a fixed seed/key/tempo/structure unless the user specified it; lock only what they said. Save the recipe.
- Read TOOLS-GUIDE/HOW-TO-CREATE-MUSIC.md before composing. Mood knowledge lives in forge/recipe.py MOODS and skills/roblox-ost/references/.
- Listening feedback: use TOOLS-GUIDE/HYDROGEN-PROMPT.md, then `af.py feedback`. Trust a listener's mood, not its numbers.

## UPDATE 2026-11-20 (v3.3)
- Round-2 listener notes are encoded (see hunted-vs-heroic.md Round 2). A listener's FACTS were right this time (tempo, key, timestamps) except the lift position; still verify.
- Open: wide stereo depth, a more convincing guitar timbre, heavier impacts. Everything still unheard.

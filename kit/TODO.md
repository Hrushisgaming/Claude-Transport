# TODO (update this file as you go; date every change)

## Done (2026-11-18)
- [x] deep.py rev 2: breakdown, build, end-cut detection; tail-aware outro labeling
- [x] tools: af.py survey / aicheck / at
- [x] study.py + plan.py carry breakdowns, builds, end cut
- [x] regenerated deep outputs for 5 tracks; rebuilt 5 check-my-numbers prompts; saved survey-rev2.md
- [x] Step 1 (A Grave Soul) run in Gemini and scored with aicheck (7/7 timestamps near analyzer events; 1 weak: the 0:24 fill)
- [x] deep.py rev 3: tone-shift (centroid / band balance) section detector; survey diff shows lmsy2k splitting and other tracks stable

## Progress (2026-11-18, latest)
- [x] Step 3 lmsy2k run in Gemini and scored: tempo, key, 0:05 drop, 1:07 break, end cut agree. Gemini's 0:10 / 0:29 / 0:47 are real tone changes with almost no loudness change; analyzer misses them (one 26-bar "verse"). 0:38 build and 0:45 riser not supported. Details: listening-test-pack/results/lmsy2k_manualcheck.md. Analysis files: examples/lms-analysis/tracks/lmsy2k/.
- [x] Eternal Hope hq re-scored with the real analyzer; old version dropped.
- [ ] deep.py: add a tone-shift (centroid / band balance) section detector; survey diff must show lmsy2k splitting and other tracks staying stable.

- [x] Step 2 onebounce run in Gemini and scored: mostly agrees; analyzer misses 1-bar fill dips and harmonic changes, drop stamped 1.6 s early. Details: listening-test-pack/results/onebounce_manualcheck.md.

## V2 upgrade — DONE (2026-11-19)
- [x] Part 1: forge/ overhauled (numpy+scipy only): SVF filters, KS strings, ping-pong delay, hall reverb, tube overdrive, guitar cab, 17 new instruments, breakbeats, theory, V2 mixdown/master; genres.py breakbeat + V2 voices; all 8 genres build
- [x] Part 2: hear.py --local offline telemetry; deep.py tone-shift/fill/harmonic detectors; study.py band-rhythm + archetypes + V2 genre drafts; compare.py breakdown/build/end-cut/tone-shift/fill/ending rows; ost.py strict build+check; cinematic-edit/synth.py impact/riser/whoosh + stereo depth
- [x] Part 3: adapt.py, audition.py, stem_mix.py, loop_doctor.py + audioutil.py; registered in af.py, doctor.py, copy.py
- [x] Part 5 verified: `af.py selftest` ALL PASSED (~4.5 min); audition / hear --local / adapt / stem_mix / loop_doctor / deep / compare / ost check --loop all green; `kit/examples/lms-analysis/sample-roblox-set/` rebuilt with `ost build --quick --format wav --strict`, every loop state `ready: true`
- [x] Part 4 docs: kit/TOOLS-GUIDE/ (README + one page per tool, all five skills, linked from kit/README.md); kit/CHANGES/CHANGES.md + module notes; SKILL.md (audio-forge, style-copy), CHANGELOG.md, TODO.md updated

## Remaining (packaging)
- [x] Clean temp artifacts (`<temp folder>/`, `__pycache__`, `*.pyc`)
- [ ] Build `Video-Studio-Kit-v3.zip` preserving structure + exec bits, excluding `__pycache__/`, `*.pyc`, `.DS_Store`, `.pytest_cache/`, test WAVs
- [ ] Verify `zipfile.ZipFile.testzip() == None`; confirm `kit/install.py`, `kit/CHANGES/CHANGES.md`, `kit/TOOLS-GUIDE/README.md`, all skills present
- [ ] Report exact filename/path/size MB; list created/modified files under kit/CHANGES/, kit/TOOLS-GUIDE/, kit/skills/

## Do not
- do not claim anything sounds like anything; do not upload to Roblox; do not paste real lyrics; do not delete the rev 1 notes in CHANGELOG; do not run NVIDIA API without a key; do not run Roblox Studio


## 2026-11-19 (v3)
- [x] merged real voices, ostfight, showcase, fixes
- [ ] user listens to the OST and the instrument A/B, says which voices to keep and what is off; ONE knob per round
- [ ] compare.py is slow (minutes per file): profile it
- [ ] decide: make the best real voices the default classic names (piano, bell, organ, guitar) after the A/B
- [ ] presenter-style composer for Showtime / Fired (long intro+build)


## 2026-11-20 (v3.1)
- [x] huntfight + horror_fx from Hydrogen's notes
- [ ] user listens to hunt_v3 and sends Hydrogen's next notes; ONE knob per round
- [ ] unknown: does the OST need the Hope-style first-drop impact stronger (measured jump is 3.8 dB)? Hope's reference jump is larger.
- [ ] ostfight.py is the heroic version: keep or retire


## 2026-11-20 (v3.2)
- [x] recipe/variation, feedback loop, tutorial
- [ ] user sends Hydrogen's reply to a random-recipe render; run af.py feedback; one knob per round
- [ ] only hunted has a composer: build presenter (Showtime/Fired) and heroic composers on the same recipe system
- [ ] expand feedback.py rules from real replies


## 2026-11-20 (v3.3)
- [ ] user listens to v21_fixed vs v21 (variation demo zip) and to seed 2; send Hydrogen's next reply (JSON first)
- [ ] stereo width, guitar timbre, heavier impacts
- [ ] chase-themes style (Chase_themes.zip not unzipped yet)

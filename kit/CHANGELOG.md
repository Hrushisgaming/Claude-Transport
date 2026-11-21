# Changelog
## Video Studio Kit v3.5 (2026-11-21): engines merged, selftest green
- FIX `forge/instruments.py`: V2 library (all legacy + V2 keys, `render()`) merged with the buzz-free v3 engine, now `forge/instruments_v3.py`. v3 voices are adapted to V2's signature and registered before the 1.4 real/voices merge, so those newer voices still win shared names. `strings` and `choir` stay V2's; quiet v3 pads are levelled up. 90 voices all render finite above 0.2 peak.
- FIX `hear.py`: string literals split across lines (script did not parse). `forge/instruments_v3.py`: `iirpeak` used with `sosfilt` (now `lfilter`), single-cutoff bandpass.
- CHANGE `selftest.py`: `hear` checks now cover the X-ray report and `--json` (the old `--dry-run` / `--local` modes no longer exist). Selftest: 43 passed.
- Verified by running the selftest and an `ost build` of the full set; NOT verified by ear.
## audio-forge 1.7.0 (2026-11-20): round-2 listening fixes
- NEW voices `bend_lead`, `string_tremolo`, `piano_dark` (forge/voices.py). `huntfight.py`: hollow major chords, riffs (syncopated/gallop/tritone/triplet) per drop, tritone and chromatic-run motifs that mutate, accent-only bells, reese layer, fills + reverse crash, darker breakdown, optional low organ / dark brass, glitch section never uses stiff DnB. `recipe.py`: new defaults (lift none 88%, DnB 6%, lead bend_lead, pads trem_strings, bells church accents, piano dark), new fields, `upgrade_recipe` for old recipes. `feedback.py`: recipe rules, 3 dB cap. Prompt: JSON first + code-as-data.
- Verified: same seed (21) re-rendered with the overrides keeps key/tempo/structure and changes exactly the listed things (bells 53 -> 15 events, no choir/square/bright piano, tubular bells 23 -> 0, reese added); 12-recipe smoke test builds; fresh random render (seed 2, brass+organ on, static-crash ending) clean. The analyzer's key LABEL flipped to "G# major" but the minor/major-third energy ratio is 1.3-1.5 (minor): label is a heuristic. NOT verified by ear.
## audio-forge 1.6.0 (2026-11-20): variation, recipes, feedback loop
- NEW `forge/recipe.py` (moods, `make_recipe`, locks, history, `parse_locks`), `huntfight.py` rewritten as recipe-driven (structure lengths, key 12 minors, tempo range, cycles, drums, palette, SFX, 4 endings, procedural motifs, clock on/off), `feedback.py`, `TOOLS-GUIDE/HYDROGEN-PROMPT.md`, `TOOLS-GUIDE/HOW-TO-CREATE-MUSIC.md`, `tests/recipe_test.py`, `skills/roblox-ost/references/listening-reports/`.
- Verified: 60 seeds -> 60 different recipes; locks honoured; same recipe reproduces the audio bit-for-bit; 3 random seeds + 2 locked renders finish, finite, no clipping. NOT verified by ear.
- Known limits: only the hunted mood has a composer; `feedback.py` mapping is rule-based and conservative; listener numbers are not trusted.
## audio-forge 1.5.0 (2026-11-20): hunted rewrite
- NEW `huntfight.py` (registered in af.py), `forge/horror_fx.py`, `tests/horror_fx_test.py`, `TOOLS-GUIDE/audio-forge/huntfight.md`, `skills/roblox-ost/references/hunted-vs-heroic.md`.
- Why: the first weighted OST sounded happy to the user. Hydrogen's comparison blamed major chords, warm pads, glockenspiel, brass fanfare + key lift, hero hook, pretty clock, peaceful fade. All removed in huntfight.
- Verified by analysis only: structure (clock breakdown 4 bars, build, riser, final breakdown, A minor), intro 3.8 dB quieter than the first drop, ending = tape-stop to a dark tail to one dry hit. NOT verified by ear.
## Video Studio Kit v3 / audio-forge 1.4.0 (2026-11-19)
- NEW `forge/real.py`, `forge/voices.py`: 19 physically-motivated voices (see README). Registered beside V2's voices in `instruments.py` without replacing any V2 key (`bell_tubular` and `organ_pipe` stay V2's; the new bell is `bell_church`, pipe organ `organ_church`). `song.py` sets (BASS/PAD/GUITAR) know the new names so auto-HPF and widening apply. Levels trimmed: brass_section, guitar_crunch, guitar_lead, guitar_heavy peak-normalised.
- NEW `ostfight.py` (weighted OST), `hopefight.py`, `instrument_showcase.py` (A/B page), `instrument_demo.py`; registered in `af.py`. NEW `tests/instruments_test.py`.
- NEW style-copy library entries: roblox-lms-chase (8 hunted themes), roblox-lms-presenter (Showtime + Fired), eternal-hope-ref.
- FIX: audio-forge VERSION said 1.1.0; hard-coded /Users/hrushi paths in docs; TODO packaging items.
- Verified: all 41 V2 + 19 new voices render finite; V2 `af.py selftest` passed 39+ checks (no failure) before I stopped it; ostfight deep analysis finds the intended structure (clock breakdown, two risers, end cut with tail, A minor). NOT verified: anything by ear.
## Video Studio Kit V2 (2026-11-19)
- Part 1: `forge/` overhauled to numpy + scipy only — resonant SVF filters (lp/bp/hp, 2× oversampled, scalar or per-sample cutoff), Karplus-Strong strings, ping-pong delay, vectorised hall reverb, asymmetric tube overdrive, guitar cab (~130 Hz HP + ~4 kHz LP), `hpf_stereo`, osc/supersaw with delayed vibrato and portamento, Nyquist clipping ≥ sr×0.44. 17 new instruments (`piano_m1`, `organ_rock`, `organ_pipe`, `bell_tubular`, `clock_bell`, `acid_303`, `chip_lead`, `pulsing_bass`, `y2k_bass`, `showtime_sax`, `marimba`, `rave_stab`, `orch_hit`, `rave_shout`, `heartbeat`, `siren_riser`, `clock_tick`); all 41 voices render. Guitars: KS → asymmetric tanh drive → 130 Hz HPF → 4 kHz cab; palm mute 0.968 vs open 0.996. Piano (inharmonic partials, unison detune, hall reverb), DX7 Rhodes (14:1 tine + chorus), organ (90s drawbars, key click, rotary, pipe + cathedral reverb), bells (Y2K FM, tubular, celesta, clock bell). Breakbeats (`amen`, `dnb`, `horror`, `metal`) via `forge/drums.py`. `forge/theory.py`: call-and-response, syncopation, octave leaps, phrasing, `arp()`. `forge/song.py`: auto HPF ~150 Hz non-bass, mono low-end 160 Hz, widening, kick sidechain, light master preserving crest. `forge/genres.py`: breakbeat integration + V2 voices; 8 genres build cleanly.
- Part 2: `hear.py --local` offline JSON+Markdown telemetry (bands, mud 200–500 Hz, harshness 3–8 kHz, sub weight, per-beat punch/crest, stereo correlation/phase risk, clipping/DC, archetypes, exact `compose --override` suggestions); API mode slices >60 s via `deep.py` sections, merges local+API, ask-first (`--yes`). `deep.py`: tone-shift, half-bar fill/snare-roll, harmonic-shift detectors (rev 3). `study.py`: band-rhythm grids, archetypes, bass-vs-mid rhythm separation, V2-aware genre drafts. `compare.py`: breakdown/build/end-cut/tone-shift/fill/ending rows. `ost.py`: strict loop/headroom/mono-sub/DC/clipping build+check (`--strict` gate). `cinematic-edit/synth.py`: impact/riser/whoosh punch + stereo depth (`stereo()` mid/side width, `low_mono()`).
- Part 3: new tools `adapt.py` (compose→compare→adjust ≤5 rounds, round log), `audition.py` (showcase + mini-mix), `stem_mix.py` (stem-folder mixer, EQ/mono-bass/sidechain/width/loudness), `loop_doctor.py` (diagnose/repair loops); shared helper `audioutil.py`; all registered in `af.py`, `doctor.py --capabilities`, `copy.py` (`adapt`, `audition`, `stem-mix`, `loop-doctor`).
- Part 4: `kit/TOOLS-GUIDE/` (one page per tool across all five skills, linked from `kit/README.md`); `kit/CHANGES/CHANGES.md` + module notes; `SKILL.md`, `TODO.md`, this `CHANGELOG.md` updated.
- Part 5: `af.py selftest` ALL PASSED; `audition`, `hear --local`, `adapt`, `stem_mix`, `loop_doctor`, `deep`, `compare`, `ost check --loop` all green; `kit/examples/lms-analysis/sample-roblox-set/` rebuilt with `ost build --quick --format wav --strict`, every loop state `ready: true` under `ost check --loop`.
- Not run: NVIDIA API path in `hear` (no key; `--local` needs none, uploads nothing), Roblox Studio (`MusicDirector.luau` written, not executed in Studio). Never claimed audio "sounds good"; all listening left to the user.
## deep.py rev 3 (2026-11-18)
- NEW detectors:
  - `detect_tone_shifts`: spectral texture shifts (centroid jumps or band balance changes) under flat loudness (solves lmsy2k 26-bar verse bug)
  - `detect_fill_dips`: 1-2 bar short dips before impacts with rapid recovery and onset bursts (onebounce 0:19)
  - `detect_chroma_changes`: harmonic content shifts via mean-centered chroma distance under flat loudness (onebounce 0:40, 1:00)
- Section segmentation: tone shifts inject section boundaries into `bounds` so texture changes become distinct sections even when loudness is steady
- deep.json: `hard_points.tone_shifts`, `.fill_dips`, `.chroma_changes` (`rev: 3`); timeline.md / labels.txt / hardpoints.csv gain TONE SHIFT, FILL, HARMONIC SHIFT
- study.py & plan.py carry tone shifts, fill dips, and harmonic shifts into style DNA and build plans
## deep.py rev 2 (2026-11-18)
- NEW detectors: `detect_tail` (end cut / fade), `detect_dips` (breakdowns and builds, bar level); sections now start at them
- FIX: last section was labeled "outro" whenever its mean energy was low, even when it held the climax; the fade-out bars no longer count toward a section's energy
- deep.json: `hard_points.breakdowns`, `.builds`, `.tail` (schema name unchanged, `rev: 2`); timeline.md / labels.txt / hardpoints.csv gain BREAKDOWN, BUILD, END CUT rows
- NEW tools: af.py `survey`, `aicheck`, `at`
- study.py / plan.py carry breakdowns, builds, end cut into style DNA and build plans
- see NOTES-FOR-AGENTS.md and TODO.md
## cinematic-edit 3.0 / audio-forge 1.1 / video-studio 1.0
- styles.py + `analyze.py --style` (18 presets); looks vivid clean film pastel golden sport cyber sepia matte
- silence_cut.py, scenes.py, audioforge.py; mixdown: voice, voice ducking, music_start, sfx_cues, audio.mode; plancheck: synthesised bed row
- audio-forge: score.py + forge/styles.py, genres corporate warm_piano epic_trailer soft_ambient, 9 effects, `audio_edit voice`, capabilities styles/schemas
- FIX: genres.build ignored its `plan` argument (compose --plan did nothing)
- added third-party skills unchanged: canvas, editor-v3 (NextPhase), 2d-animation-long-form-aivxer (aivxer); video-studio routes to them
- audio-forge: `hear` (optional audio description via NVIDIA, asks first), `score --exact`
- reference-check skill, `reftest.py duel`
- style-copy skill (signature): study/compare/install, library with roblox-guitar-cover; audio-forge `study`, `compare`, `guitar_pluck`/`guitar_elec`, JSON custom genres, genre `lufs`/`dynamics`, genre `roblox_guitar_cover`, style `roblox-edit`; cinematic-edit `study_video.py`, JSON user styles, style `roblox-edit`; opencode commands /copy-style and /studio

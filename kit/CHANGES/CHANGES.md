# kit/CHANGES — Video Studio Kit V2 (change log)

This directory documents **every change** in the V2 upgrade of `kit/`, skill by skill and module by module. Module notes live next to this file (`audio-forge.md`, `style-copy.md`, `cinematic-edit.md`, `roblox-ost.md`, `video-studio.md`).

## Summary of V2

| Part | What | Where |
|---|---|---|
| Part 1 | `forge/` overhauled to numpy + scipy only: resonant SVF filters, Karplus-Strong strings, ping-pong delay, vectorised hall reverb, tube overdrive, guitar cab, delayed vibrato, portamento, 17 new instruments, breakbeats, call-and-response theory, V2 mixdown/master | `skills/audio-forge/scripts/forge/` |
| Part 2 | `hear.py --local` offline telemetry; `deep.py` tone-shift/fill/harmonic detectors; `study.py` band-rhythm grids + archetypes + V2-aware genre drafts; `compare.py` breakdown/build/end-cut/tone-shift/fill/ending rows; `ost.py` strict build+check; `cinematic-edit/synth.py` impact/riser/whoosh + stereo depth | `skills/audio-forge/scripts/*.py`, `skills/cinematic-edit/scripts/synth.py` |
| Part 3 | New tools: `adapt.py`, `audition.py`, `stem_mix.py`, `loop_doctor.py`; shared helper `audioutil.py`; all registered in `af.py`, `doctor.py`, `copy.py` | `skills/audio-forge/scripts/*.py`, `skills/style-copy/scripts/copy.py` |
| Part 4 | `kit/TOOLS-GUIDE/` (one page per tool across all five skills, linked from `kit/README.md`); updated `SKILL.md`, `TODO.md`, `CHANGELOG.md`; this `kit/CHANGES/` directory | `kit/TOOLS-GUIDE/`, `kit/CHANGES/` |
| Part 5 | End-to-end verification: `af.py selftest` ALL PASSED; `audition`, `hear --local`, `adapt`, `stem_mix`, `loop_doctor`, `deep`, `compare`, `ost check --loop` all green; `kit/examples/lms-analysis/sample-roblox-set/` rebuilt with `ost build --quick --format wav --strict`; every loop state `ready: true` | verified by running |

## Verified test results (truthful)

`af.py selftest` (run with `<your python>`, numpy 2.5.5, scipy 1.18.1, Python 3.15.2): **ALL PASSED** in ~4.5 min, including:
- compose all genres; analyze tempo/key/beats; score drop on hero; hear --local; study+compare self=100/100; deep detectors; ost loop seam check; all 41 instrument keys render; breakbeats amen/dnb/horror/metal; audition showcase+mini-mix; adapt round log; stem_mix to −14 LUFS; loop_doctor diagnose+repair; ost check bars/headroom/sub.

`ost build --quick --format wav --strict` rebuilt `kit/examples/lms-analysis/sample-roblox-set/` (lobby/tension/chase/lms_intro/lms/win/lose + chase_stems, A minor, 178 BPM): **every loop state `ready: true`** under `ost check --loop` (bars whole, peak ≤ −1.5 dBFS headroom, sub ≤ 140 Hz mono corr ≥ 0.85, no DC, no clipping).

**Never claimed audio "sounds good":** none of these tools listens the way a person does. All listening-dependent judgements are left to the user. The NVIDIA API path in `hear` was not run (no key; `--local` is offline and needs none). Roblox Studio was not run (the Luau `MusicDirector.luau` is written but not executed in Studio).

## What was NOT changed / not run

- Third-party skills `canvas`, `editor-v3`, `2d-animation-long-form-aivxer` are unchanged (NextPhase / aivxer, keep their credit lines and licences).
- `install.py` unchanged (still installs the kit into opencode/Claude Code).
- NVIDIA API (`hear` without `--local`) not run: no API key available; `--local` requires no key and uploads nothing.
- Roblox Studio not run: `MusicDirector.luau` is generated, not executed in Studio.

See the module notes below for per-skill and per-module detail.

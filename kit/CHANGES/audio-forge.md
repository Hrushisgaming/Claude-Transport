# CHANGES module notes — audio-forge

## Part 1: `forge/` overhauled (numpy + scipy only)

### `forge/dsp.py`
- `svf_lp` / `svf_bp` / `svf_hp`: 2×-oversampled resonant state-variable filters, scalar or per-sample cutoff
- `ks_string`: Karplus-Strong string with damp factor
- `ping_pong_delay`: stereo ping-pong delay
- `hall_reverb`: fast vectorised multi-tap hall reverb
- `asym_drive`: asymmetric tube overdrive (`np.tanh(x*drive + 0.15)` shape)
- guitar cab: ~130 Hz high-pass + ~4 kHz low-pass
- `hpf_stereo`: stereo high-pass
- `osc` / `supersaw`: delayed vibrato, portamento, Nyquist clipping at ≥ sr×0.44
- `mono_below` rewritten to FFT-based mono collapse (flat-1 below 0.9×cutoff, cosine taper to 1.1×cutoff) because the old IIR high/low split leaked side energy

### `forge/instruments.py`
- 41 voices total: every legacy key kept working and upgraded, plus 17 new:
  `piano_m1`, `organ_rock`, `organ_pipe`, `bell_tubular`, `clock_bell`, `acid_303`, `chip_lead`,
  `pulsing_bass`, `y2k_bass`, `showtime_sax`, `marimba`, `rave_stab`, `orch_hit`, `rave_shout`,
  `heartbeat`, `siren_riser`, `clock_tick`
- Guitars: KS root/5th/oct → asymmetric `np.tanh(x*drive + 0.15)` → 130 Hz HPF → 4 kHz cab; palm mute damp 0.968 vs open 0.996 (`guitar_mute` voice; muting is expressed with `m` rhythm characters, not `kw.mute`)
- Piano: inharmonic partials k=1..8, unison detune, fast high-partial decay, 10 ms hammer, hall reverb
- DX7 Rhodes: 14:1 tine + chorus
- Organ: 90s drawbars `[0.5,1,1.5,2,3,4,6,8]` + 20 ms key click + stereo shimmer; rock B3 + 6 Hz rotary; pipe 35 ms breath + cathedral reverb
- Bells: Y2K 3.5:1 FM + ping-pong + reverb; tubular `[1,2.76,4.07,5.43]`; cold celesta; deep clock bell with octave-down hum + felt/metal strike

### `forge/drums.py`
- Punchy kicks/snares/hats plus `breakbeat()` generator for `amen`, `dnb`, `horror`, `metal` (feeds `dnb`, `horror_chase`, `metal`, `roblox_lms_family`, `roblox_guitar_cover`); static drum patterns still supply non-break colour

### `forge/theory.py`
- Call-and-response, syncopation, octave leaps, expressive phrasing, `arp()`

### `forge/song.py`
- Auto high-pass (~150 Hz) on non-bass tracks; mono low-end below 140 Hz (now 160 Hz in `song.mixdown`); stereo widening on guitars/pads/supersaws; kick sidechain duck; soft saturation + light limiter master chain (`compress(-16,1.55...)`, ceiling/normalize −1.5 dBFS) to preserve crest

### `forge/genres.py`
- Breakbeat integration + V2 voices; all 8 genres build cleanly; `resolve`/`deep_merge` helpers

## Part 2

### `hear.py` (rewritten)
- `--local` offline JSON + Markdown telemetry: band balance (sub/bass/low-mid/mid/high-mid/air, calibrated to RMS), mud/clash 200–500 Hz, harshness 3–8 kHz, sub weight, per-beat punch/crest, stereo band correlation/phase risk, clipping/DC, archetype guesses, exact `af.py compose --override` suggestions
- API mode slices tracks >60 s using `deep.py` sections, merges local+API, ask-first (`--yes` required non-interactively); `--local` needs no key and uploads nothing

### `deep.py`
- Tone-shift boundary detector; half-bar fill / snare-roll detector; `hard_points` gains `tone_shifts`, `fill_dips`, `chroma_changes` (rev 3); timeline.md/labels.txt/hardpoints.csv gain TONE SHIFT, FILL, HARMONIC SHIFT rows

### `study.py`
- `band_rhythm` low/mid grids; archetype detection (guitar/bell/303/chip/piano/breakbeat); bass-vs-mid rhythm separation; V2-aware `draft_genre`

### `compare.py`
- Rows for breakdowns, builds, end cut, tone shift, fill, snare rolls, ending; `compare.rows` expects DNA key shape `key.tonic`/`key.mode`

### `ost.py`
- V2 flow via `compose`; strict loop / headroom / mono-sub / DC / clipping checks; `--strict` gate exits non-zero on any loop failure
- `ost check` also reports DC, clipped samples, true-peak headroom (>−1.0 dBFS fails), LUFS sanity (−9/−26 bounds), low-band correlation at 110 Hz / 6th order (threshold 0.85)
- Loop states use steady-state plans (`lobby`→`[["main",1.0]]`, `tension`/`chase`→`[["chase",1.0]]`, `lms`→family plan or `[["chase",1.0]]`) to stop quiet outro tails

### `cinematic-edit/scripts/synth.py`
- New `stereo()` mid/side width, `low_mono()`; punchier `impact` (30–80 Hz pitch-drop sub + 180 Hz body + 2–9 kHz crack + stereo tail); `riser` (rising saw stack + upward noise sweep, opening width); `whoosh` (band sweep with L→R pan, independent noise channels); all 12 kit sounds render finite with sane peaks

## Part 3: new tools (all registered in `af.py`, `doctor.py --capabilities`, `copy.py`)

### `audioutil.py` (new, shared helper — not a command)
- `import audioutil as U` (the name must be exact — a typo `audiotil` was made and fixed twice)
- Used by `loop_doctor.py`, `stem_mix.py`, `audition.py`, `adapt.py`: read/write WAV (+ ffmpeg fallback), resample, mono/stereo helpers, rms/peak/DC/lufs/low_corr measurements, `measure()`, `bpm_of()`, `ffprobe()`, `temp_wav()`

### `adapt.py` (new)
- Compose → measure → compare → adjust loop, ≤5 rounds, one grouped knob change per row type, keeps best-scoring round, stops after 2 non-improving rounds, logs every round to `adapt-log.json` / `.md`
- Tempo selection uses absolute distance to the genre BPM window; guitar muting via `m` rhythm chars

### `audition.py` (new)
- Timestamped instrument showcase WAV + `showcase.md`/`.json` + 175 BPM mini-mix + `minimix.json`

### `stem_mix.py` (new)
- Role detection, EQ carve (DC removed before EQ), mono bass, kick sidechain, widening, per-stem safety limiter at −1 dBFS, glue/saturation/limiter master, LUFS match, `--processed-out`, JSON report; processed stems normalised to −1.5 dBFS

### `loop_doctor.py` (new)
- Diagnose + repair: whole-bar snap, tail fold, micro-fade, DC clean, peak normalise; seam/head/tail/DC/clipping/sub-mono checks

### Registrations
- `af.py` TOOLS now: `compose analyze remake tts subs2speech audio_edit bridge sfx separate listen selftest score hear study compare deep lyrics blend ost survey aicheck at adapt audition stem_mix loop_doctor doctor`
- `doctor.py --capabilities` tools list and `provides` extended (adds offline_feedback, adaptive_composition, instrument_audition, stem_mixing, loop_repair)
- `copy.py` gained `adapt`, `audition`, `stem-mix`, `loop-doctor` commands delegating to `af.py`

### `selftest.py`
- Extended with V2 checks: all legacy+V2 instrument keys render, breakbeat generators, `hear --local` schema, audition outputs, adapt round log, stem_mix, loop_doctor, ost check — **ALL PASSED**

## Files changed (audio-forge)

`scripts/af.py`, `scripts/doctor.py`, `scripts/selftest.py`, `scripts/hear.py`, `scripts/deep.py`, `scripts/study.py`, `scripts/compare.py`, `scripts/ost.py`, `scripts/adapt.py` (new), `scripts/audition.py` (new), `scripts/stem_mix.py` (new), `scripts/loop_doctor.py` (new), `scripts/audioutil.py` (new), `scripts/forge/dsp.py`, `scripts/forge/instruments.py`, `scripts/forge/drums.py`, `scripts/forge/theory.py`, `scripts/forge/song.py`, `scripts/forge/genres.py`; `skills/cinematic-edit/scripts/synth.py`

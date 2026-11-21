# Audio-Forge Toolset Upgrade Notes

## What Was Upgraded

1. **High-Resolution Audio X-Ray (`skills/audio-forge/scripts/hear.py`)**
   - Gives text-only AIs (like Claude) deep, timestamped visibility into any `.wav`, `.mp3`, `.ogg`, or `.m4a` file.
   - Automatically detects **Electronic Buzz / Aliasing (0-10)** in `5-11 kHz`, **Excessive Vibrato / Wobble (0-10)** in `4.5-8.5 Hz`, **Tuning Offset (cents from A4=440 Hz)**, **Silence Drop-Outs (ms)**, **1.0s Clock Ticks**, **5.0s Clock Bells**, **16-Step Drum Grooves**, **Dissonance (minor 2nds & tritones)**, **Dry vs. Wet Contrast**, and a **Second-by-Second Audio X-Ray Table** + full JSON output.
   - Usage:
     `python3 skills/audio-forge/scripts/hear.py track.mp3 --step 2.0`
     `python3 skills/audio-forge/scripts/hear.py track.mp3 --json -o xray.json`

2. **Buzz-Free Physical & LMS Instrument Engine (`skills/audio-forge/scripts/forge/instruments.py`)**
   - **Zero Electronic Buzz**: Uses PolyBLEP anti-aliased oscillators, dynamic high-frequency decay filtering, and multi-stage resonant body/cabinet modeling.
   - **Zero Seasick Vibrato**: Replaces heavy pitch wobble with subtle, realistic ensemble drift (`<= 2 cents`).
   - **Upgraded & New Instruments**:
     - `guitar` / `guitars` / `power_guitar` / `palm_guitar`: Karplus-Strong physical plucked-string synthesis + asymmetrical tube amp + 4x12 guitar cabinet IR.
     - `strings` / `trem_strings`: 8-voice bowed ensemble with wood-body formants (`290 Hz`, `620 Hz`).
     - `piano_dark` / `ice_piano` / `music_box`: Stiff-string inharmonicity + hammer-felt transient + dual unison shimmer (modeled after *Eternal Hope, Eternal Fight*).
     - `harpsichord`: Baroque plucked-quill synthesis (modeled after *Showtime* & *ETERNITY V2*).
     - `pipe_organ` / `organ_low`: 5-rank stops (`16'`, `8'`, `4'`, `2-2/3'`, `2'`) with breathy air-pipe chiff.
     - `church_bells` / `clock_bell` / `clock_tick`: Risset inharmonic bronze bells + 2-stage mechanical escapement tick-tock.
     - `choir_pad` / `ha_laugh`: Vowel-formant choir pad and a two-syllable `"HA-HA!"` maniacal laugh.
     - `y2k_fm_bass` / `y2k_acid_lead` / `y2k_arp`: 2008 Roblox / Y2K electronic suite (modeled after *OneBounce* & *LMSY2K*).

3. **Hunted & Dread FX Toolkit (`skills/audio-forge/scripts/forge/horror_fx.py`)**
   - Exposes `apply_dread_fx(audio, sr, config)` so `song.py` / `recipe.py` can directly execute the `dread_fx` block from `unarchived_lms.recipe.json`.

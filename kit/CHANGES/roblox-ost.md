# CHANGES module notes — roblox-ost (`ost.py` in audio-forge)

## `skills/audio-forge/scripts/ost.py`
- V2 build flow via `forge`/`compose` with V2 instruments and breakbeats
- `ost build --strict`: exits non-zero if any loop state fails the seam/headroom/mono-sub checks; `--quick` halves bars for fast iteration; `--format wav|ogg|mp3|flac`
- Every loop seam-safe: render tail folded onto the start, cut to a whole number of bars, loudness-matched (linear gain + peak limit, no fades)
- One key + one BPM across all states (lobby, tension, chase+stems, lms_intro once + lms loop, win, lose stinger) so they crossfade on bar lines
- Loop states use steady-state plans (`lobby`→`[["main",1.0]]`, `tension`/`chase`→`[["chase",1.0]]`, `lms`→family plan or `[["chase",1.0]]`) to stop quiet outro tails
- `ost check` now also reports DC, clipped samples, true-peak headroom (>−1.0 dBFS fails), LUFS sanity (−9/−26 LUFS), low-band correlation at 110 Hz / 6th order (threshold 0.85); `--loop` adds seam, head/tail silence, whole-bars checks
- Writes `roblox_manifest.md` and `MusicDirector.luau` (Luau script not run in Roblox Studio here)
- Roblox upload limits documented: mp3/ogg/wav/flac, single track, <20 MB, ≤7 min, ≤48 kHz

# DNA fields and the knob that moves each one

## Audio DNA (style-copy/audio-dna@1), made by `af.py study`
| field | meaning | knob (audio-forge) |
|---|---|---|
| tempo.bpm / alt_octaves | tempo and its half/double readings | `compose --bpm` (ask which octave) |
| key.tonic / mode | key and major/minor/other | `--key`, `--scale` |
| mix.lufs / crest_db / lra | loudness, peak-to-average, range | genre `lufs`, `--dynamics`, `mix.*.gain_db` |
| timbre.centroid_hz / rolloff85_hz | brightness | instrument kw `bright`, `drive`, cutoff |
| timbre.flatness / hf_ratio_db | distortion / noise amount | guitar kw `drive`; fewer hats/noise |
| timbre.bands_db | level in sub/bass/low-mid/mid/high-mid/air | the layer's `mix.<layer>.gain_db`; bass octave and cutoff |
| mix.side_to_mid_db / band_correlation | stereo width (low should stay near mono) | `mix.<layer>.widen` |
| rhythm.onsets_per_beat / step16_density | attack density, 16-step feel (a style fingerprint, not a riff) | the layer `rhythm` strings, kick/snare/hat patterns |
| rhythm.sustain_ms | how long notes ring | kw `mute` (more = shorter) |
| structure.energy_per_bar_db / sections | arrangement shape | genre `plan`, layers per section, `--dynamics` |
| harmony.* | chord vocabulary and change rate (reduced on purpose) | `kind`, `chord_len`; write a NEW progression |

## Video DNA (style-copy/video-dna@1), made by `study_video.py`
| field | meaning | knob (cinematic-edit) |
|---|---|---|
| cutting.cuts_per_min / shot_len_* | cut rhythm | `events.per_min`, `events.gap`, montage `--every` |
| motion.subject_motion / camera_shift | how much moves | speed ramps, punch, follow reframe |
| motion.shake_spikes_per_min / flashes_per_min | shake and flash effects | fx lists (`shake`, `flash`, `chroma`, `glitch`) |
| cadence.typical_hold_frames | 1 = every frame drawn, 2 = on twos | animation skill: draw on that hold |
| grade.* and palette | saturation, brightness, contrast, warmth, vignette, letterbox, main colours | `acts[].look`, `look.vignette`, `look.letterbox` |
| line.edge_density / ink_stroke_px | amount of line art / stroke weight | animation skill ink width |
| audio.* | the soundtrack's own audio DNA | the audio loop above |
UNKNOWN by design: on-screen text, subject, jokes, melody.

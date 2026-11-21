# Deep analysis (af.py deep) - what it measures and how far to trust it

`python3 af.py deep track.mp3 [--out DIR] [--bpm-range LO HI]` (or `copy.py deep`) writes `deep.json` (audio-forge/deep@1), `timeline.md`, `labels.txt` (Audacity), `hardpoints.csv`, `timeline.png`. numpy+scipy only (librosa not needed). Inside `copy.py study` the compact result lives in `dna.json -> deep`.

| field | meaning | how it is found | trust |
|---|---|---|---|
| grid | bpm, bar length, first downbeat, bars; bar 1 = first detected downbeat | `analyze.py` beats/downbeats | bar COUNT good; `downbeat_phase_confidence` low means "beat 1" may be beat 2-4 |
| tempo_feel | the octave the track behaves like (e.g. 96 BPM that feels like 193) | attacks per beat, about 2 per beat is "normal" | medium: ASK the person which tempo they tap |
| hard_points.hits | sudden jumps: >= 6 dB in ~120 ms on a strong onset AND >= 4 dB above the typical jump within +-4 s (plain kicks do not count); type full impact / sub-kick / crash-high / accent; one-shot vs "level stays up" (entrance); offset from the 16th grid in ms | STFT flux + level jump, onset time corrected for window lag | good on a known test track (found 16.0 s impact at 15.98 s) |
| hard_points.stops | the music drops >= 14 dB for >= 80 ms and returns (the silence cut) | 3 s running median | good |
| hard_points.risers | high bands rise >= 8 dB in a straight ramp, faster than the overall level (a plain fade-in is NOT a riser), >= 0.5 s | band energy regression | good on synthetic sweeps; real risers with noise may merge |
| hard_points.drops | bar-level energy and bass jump + credit for the anatomy (cut before, riser before, impact on the downbeat); anatomy string says which | bar grid | good; a drop with no jump is missed |
| sections, form | novelty segmentation on bar features; drops are forced boundaries; labels intro/build/drop/break/outro/verse are energy heuristics; form letters A B A' by similarity | self-similarity | medium: the person's ears decide names |
| layer_moves | bands entering (+) or leaving (-) at each section start, in dB | band energy 2 bars before/after | good |
| phrase.chord_loop_bars | shortest repeating chord cycle (2/4/8/16 bars), None if none | mean-centred bar chroma periodicity | medium; None means long sections / slow harmony |
| loop | loop-ready? fade-out s, lead-in s, level jump at the seam, whole bars | ends and grid | good; a finished track is rarely loop-ready |
| tempo_map | local tempo every 6 s, drift, changes | autocorrelation near the global tempo | medium |
| lead_layer | when a pitched MID-RANGE layer (vocal, lead synth, guitar) stands out, relative to this track | harmonic/percussive split, 300-3400 Hz | cannot say which instrument. A syllable-rate vocal detector was tried and rejected (the beat itself sits in that band at 170+ BPM) |
| role_guess | lobby / tension / chase guess | tempo feel, density, mode | heuristic |

Lyrics: `af.py lyrics` (Whisper optional) or `--text`; statistics only unless `--keep-text`. Real vocals need Whisper/Demucs.
Known-truth regression: `tests/make_known_track.py` builds a synthetic track with a riser, a 0.3 s cut, an impact, a drop and a lead layer at known times; `selftest.py` checks the analyzer finds them.

# CHANGES module notes — cinematic-edit

## `skills/cinematic-edit/scripts/synth.py` (V2 polish)
- New `stereo()` mid/side width helper and `low_mono()`
- `impact`: punchier — 30–80 Hz pitch-drop sub + 180 Hz body + 2–9 kHz crack + stereo tail
- `riser`: rising saw stack + upward noise sweep, opening width
- `whoosh`: band sweep with L→R pan, independent noise channels
- All 12 kit sounds render finite with sane peaks

## Interface
- All other cinematic-edit tools (`styles.py`, `analyze.py`, `scenes.py`, `silence_cut.py`, `render.py`, `mixdown.py`, `follow.py`, `hud_events.py`, `study_video.py`, `plancheck.py`, `export.py`, …) keep their existing interfaces; backward compatible.

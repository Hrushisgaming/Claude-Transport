# CHANGES module notes — video-studio

## `skills/video-studio/scripts/studio.py`
- Interface unchanged: `studio.py doctor` (JSON readiness report) and `studio.py new NAME --style STYLE [--source VIDEO]`
- Documents how audio-forge plugs in (ask first): original bed via `af.py score --duration D --style ... --hero T --exact --out bed.wav`; Canvas `bed-mix.py` hand-off; Editor-v3 `EDITOR_SONG`/`DROP_IN_SONG`/`DROP_AT` hand-off
- Orchestrates cinematic-edit + audio-forge (optional, person's yes); third-party skills (canvas, editor-v3, 2d-animation-long-form-aivxer) unchanged

# CHANGES module notes — style-copy

## `skills/style-copy/scripts/copy.py`
- Gained `adapt`, `audition`, `stem-mix`, `loop-doctor` commands, each delegating to `af.py <same>` (audio-forge)
- `--help` lists the new commands; `copy.py doctor --capabilities` (via audio-forge) reflects the extended tool set
- Argument parser `cmd` choices extended: `doctor list show study install compare blend deep lyrics plan adapt audition stem-mix loop-doctor`
- Only style measurements are stored; references never leave the machine; no notes/melody/lyrics/footage/characters/text copied

## Behavior unchanged
`doctor`, `list`, `show`, `study`, `install`, `compare`, `blend`, `deep`, `lyrics`, `plan` keep their existing interfaces (backward compatible).

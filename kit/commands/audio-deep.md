---
description: Deep-analyse a track - hard points (impacts, cuts, risers, drops), sections, layers, loop-readiness, bar map, lyrics statistics
---
Use the roblox-ost skill (or style-copy). Analyse this audio file in depth: $ARGUMENTS

Run `copy.py deep FILE` and read `deep/<name>/timeline.md` fully; tell me in plain words: the tempo and whether it feels half/double time, the form, every hard point with its time and bar, the anatomy of each drop (what happens before and on it), which layers enter where, whether the file is loop-ready and why not, and when a mid-range lead layer is prominent. Point me to `labels.txt` (Audacity labels) and `timeline.png`. If I also want lyrics: `copy.py lyrics FILE --deep deep/<name>/deep.json` (Whisper is optional: ask before installing it; or use `--text` for lyrics I paste, statistics only). You cannot hear: say these are measurements and the drop/break labels are heuristics.

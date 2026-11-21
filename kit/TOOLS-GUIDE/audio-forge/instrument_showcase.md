# audio-forge — `instrument_showcase`

Render every voice (V2 left, real right) at the same loudness; writes mp3 clips, index.json and a standalone index.html. Nobody has listened to the output: audition it.

## Exact command

```
af.py instrument_showcase --out showcase/ [--only key1,key2]
```

## Tutorial
1. Run the command from the kit folder (needs numpy, scipy, ffmpeg).
2. Open the output and listen. Say what is wrong (instrument sound, notes, or pacing).
3. Change ONE knob per round (mix gains are the `S.track(..., gain_db=...)` lines in the script).

# audio-forge — `instrument_demo`

One short A-minor phrase per real voice, back to back. Nobody has listened to the output: audition it.

## Exact command

```
af.py instrument_demo --out demo.wav
```

## Tutorial
1. Run the command from the kit folder (needs numpy, scipy, ffmpeg).
2. Open the output and listen. Say what is wrong (instrument sound, notes, or pacing).
3. Change ONE knob per round (mix gains are the `S.track(..., gain_db=...)` lines in the script).

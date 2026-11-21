# audio-forge — `ostfight`

One original 64-bar OST by priority: Eternal Hope first (breakbeat, booms, hard cut), A Grave Soul second (clock section: ticks, chimes, tolls, heartbeat), other themes as low-priority signatures. Nobody has listened to the output: audition it.

## Exact command

```
af.py ostfight --out ost.wav [--seed 7] [--bpm 174] [--stems DIR] [--midi] [--dynamics 0.5] [--lufs -14]
```

## Tutorial
1. Run the command from the kit folder (needs numpy, scipy, ffmpeg).
2. Open the output and listen. Say what is wrong (instrument sound, notes, or pacing).
3. Change ONE knob per round (mix gains are the `S.track(..., gain_db=...)` lines in the script).

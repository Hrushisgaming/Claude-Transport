# audio-forge — `huntfight`

The HUNTED version of the weighted OST ("hunted to death, last one standing"). Eternal Hope first (relentless Amen breakbeat, booms, hard cut), A Grave Soul second (crawl SFX + vocal shout before the drop, dry-tick CLOCK section with low tolls and minor chimes, tape-stop + blunt-hit ending), LMSY2K / ONEBOUNCE / Vigilante / Necrobloxians as low-priority signatures. Only minor harmony (i, bII, VI, iv, V). No brass, organ, glockenspiel or major-key lift. Nobody has listened to the output: audition it.

## Exact command

```
af.py huntfight --out hunt.wav [--seed 7] [--bpm 174] [--stems DIR] [--midi] [--dynamics 0.5] [--lufs -14]
```

## Tutorial
1. Run it from the kit folder (needs numpy, scipy, ffmpeg). It renders 63 bars, then applies a tape-stop to the finished mix and appends a dark tail and one dry hit.
2. Listen. Say what is wrong in one of three words: sound, notes, pacing. Change ONE knob per round (mix gains are the `S.track(..., gain_db=...)` lines).
3. `forge/horror_fx.py` has the reusable ear candy: `crawl`, `static`, `shout_ha`, `tape_stop`, `blunt_hit`. Test: `python3 skills/audio-forge/tests/horror_fx_test.py`.

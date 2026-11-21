# audio-forge — `feedback`

Turns a listener's notes (JSON block from the prompt in `TOOLS-GUIDE/HYDROGEN-PROMPT.md`, or plain prose) into `overrides.json`: recipe changes (e.g. lift=none, lead=bend_lead), locks, mix changes in dB (capped at 3 dB per track per round), a BPM delta, advice, and a list of things it could not map. Conservative: changes nothing the listener did not ask for, and never trusts a listener's numbers over the analyzer. Nobody has listened to the output of the composers; this is how the listener's ears reach the kit.

## Exact command

```
af.py feedback reply.txt --out overrides.json
af.py huntfight --out v2.wav --seed 12 --apply overrides.json
```

## Tutorial
See `TOOLS-GUIDE/HOW-TO-CREATE-MUSIC.md` (step 6) and `TOOLS-GUIDE/HYDROGEN-PROMPT.md`.

`--same-as piece.wav.recipe.json --apply overrides.json` re-renders the same piece with only those changes.

# audio-forge — `selftest`

Run the full smoke test: compose (all genres), analyze, score, hear dry-run, study+compare, deep detectors, ost loop seam check, all legacy + V2 instruments, breakbeats, `hear --local`, `audition`, `adapt`, `stem_mix`, `loop_doctor`, `ost check`.

## Exact command

```
python3 af.py selftest
```

## Outputs

Pass/fail lines for every check, then `ALL PASSED` or `SOME FAILED`, plus an exit code (0 = all passed, 1 = any fail). It takes about 4–5 minutes and writes nothing to your project (uses temp files only).

## What it verifies

- Every genre renders finite audio with a sane peak (house, chiptune, horror_chase, lofi, corporate, warm_piano, epic_trailer, soft_ambient)
- `compose --plan` is honoured (the old bug where `plan` was ignored is fixed)
- Analyze: tempo within tolerance, key, beats
- `score`: the drop lands on the hero moment (error near 0 ms)
- `hear` dry run: local telemetry written, nothing sent
- `study` + `compare`: a track vs its own DNA = 100/100
- `deep`: tempo, hard stops, impacts, drops with anatomy, risers, kicks, lead layer, chord cycle, fade-out not loop-ready
- `lyrics`: repetition/hook counted
- `blend`: family has members, ranges, consensus
- `ost` loop cut to whole bars and passes the seam check
- All 41 instrument keys (legacy + 17 V2) render finite audio above 0.2 peak
- Breakbeats: amen / dnb / horror / metal generate events
- `hear --local`: offline telemetry with bands, mud, harshness, punch, stereo
- `audition`: showcase + timestamp guide + mini-mix
- `adapt`: compose → compare → adjust loop with a round log
- `stem_mix`: stems mixed to the loudness target
- `loop_doctor`: diagnoses and repairs a loop
- `ost check`: strict loop report with bars, headroom, sub checks

## Step-by-step tutorial

Run it after any change to the audio-forge engine:
```
python3 af.py selftest
```
If anything fails, read the `FAIL` line and the error under it, fix, and re-run until `ALL PASSED`.

## Honesty

Selftest proves the pipeline runs and numbers are produced; it is not a listening test. Nobody has listened to any of the generated audio.

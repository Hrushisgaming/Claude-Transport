# audio-forge — `deep`

The deep analyzer: hard points, structure, layers, loop-readiness, tempo feel and the mid-range lead layer — bar by bar. All from measurements; nobody listens.

## Exact command

```
python3 af.py deep AUDIO [--out DIR] [--name NAME]
    [--bpm-range LO HI] [--no-png] [--json]
```

`DIR` defaults to `./deep/<name>/`.

## Outputs (in `DIR/`)

| File | Contents |
|---|---|
| `deep.json` | `audio-forge/deep@1` — everything below, machine readable |
| `timeline.md` | the whole track as text: hard points, sections, bar map (readable by a model that cannot hear) |
| `labels.txt` | Audacity label track (File > Import > Labels); also readable by most DAWs as markers |
| `hardpoints.csv` | hard points as CSV |
| `timeline.png` | energy / bands / markers picture (if Pillow exists) |

## What it finds

- **hits** — impacts and accents where energy jumps inside ~120 ms: type (sub/kick, crash/high, full), strength, tail length, position in bar
- **stops** — hard stops/cuts: music drops ≥14 dB for ≥80 ms and comes back (the "silence before the drop" trick)
- **risers** — rising brightness/high-band ramps (≥1 beat): sweeps, snare rolls, build-ups
- **drops** — big entrances (bar-level energy jump) with their **anatomy**: cut before, riser before, impact on it, bass entry, brightness change
- **breakdowns** — runs of ≥2 bars sitting ≥2 dB under surroundings; **builds** ramping into drops
- **tone shifts** (rev 3) — spectral texture shifts (centroid jumps or band balance changes) under flat loudness
- **fill dips** (rev 3) — 1–2 bar level dips with fast recovery and onset bursts before impacts
- **harmonics** (rev 3) — harmonic content shifts via mean-centered chroma distance under flat loudness
- **sections** — novelty segmentation on bars; labels intro/build/drop/break/outro are heuristics; form string (A B A' C)
- **layers** — which frequency layers enter or leave at each section boundary
- **phrase/loop** — chord-loop length in bars; whether the FILE is loop-ready (fade/silence at the ends, level jump, bar-grid length)
- **tempo** — local tempo map (drift), and the "feel" octave (e.g. 96 BPM that behaves like 193)
- **lead layer** — when a pitched mid-range layer (vocal, lead synth, guitar) is prominent, relative to the track itself (it cannot say which). For real vocals/lyrics use `af.py lyrics` (Whisper, asked first).

Only measurements and positions are stored: no notes, melodies or lyrics.

## Step-by-step tutorial

1. Analyze a reference track:
   ```
   af.py deep ref.mp3 --out deep/ref/
   ```
2. Read `deep/ref/timeline.md` — it's the whole track as text, usable by a model that cannot hear.
3. Import `deep/ref/labels.txt` into Audacity (File > Import > Labels) to see the hard points as markers.
4. Check `loop-ready`: if the file fades out or has a level jump at the ends, it is not loop-ready — use `af.py loop_doctor` or `af.py ost build` to make a seamless loop.
5. Feed `deep.json` into `af.py compare` to score a candidate, or into `af.py adapt` to compose toward it.

## Honesty

Section labels (intro/build/drop/break/outro) are heuristics. The lead-layer detector cannot tell you which instrument is prominent. Tone shifts are real spectral changes but may or may not be musically meaningful. Report positions and measurements, not interpretation.

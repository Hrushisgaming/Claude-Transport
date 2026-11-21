# Hear (local): bed.wav

28.67 s analysed, BPM 102.85, key B minor, loudness -9.2 LUFS, peak -1.36 dBFS, clipped samples 0, DC [2e-05, 0.00019].

All numbers below are measured offline; nothing was uploaded. Archetypes are heuristic guesses.

## Band balance (dBFS, and dB vs a rough target)
| band | overall | target | delta |
|---|---|---|---|
| sub | -17.5 | -24.0 | 6.5 |
| bass | -19.8 | -19.0 | -0.8 |
| low_mid | -24.8 | -23.0 | -1.8 |
| mid | -26.0 | -21.0 | -5.0 |
| high_mid | -40.2 | -25.0 | -15.2 |
| air | -55.2 | -28.0 | -27.2 |

## Sections
| section | time | mud | harsh | sub weight | punch crest | low/mid/high corr | phase risk | archetype guesses |
|---|---|---|---|---|---|---|---|---|
| intro | 2.31-6.97 s | 0 | 100 | -3.6 dB | 9.1 dB | -0.01/0.17/-0.14 | high | piano / keys (harmonic, wideband) 0.52; guitar (distorted / power chords) 0.45 |
| drop | 6.97-27.98 s | 34 | 57 | 2.3 dB | 8.8 dB | 0.98/0.1/0.04 | high | guitar (distorted / power chords) 0.57; piano / keys (harmonic, wideband) 0.45 |

## Issues found
- intro 2.31-6.97 s: a band is close to mono-incompatible (corr {'low_corr': -0.01, 'mid_corr': 0.17, 'high_corr': -0.14, 'phase_risk': 'high'})
- drop 6.97-27.98 s: a band is close to mono-incompatible (corr {'low_corr': 0.98, 'mid_corr': 0.1, 'high_corr': 0.04, 'phase_risk': 'high'})

## Exact knob suggestions (`af.py compose --override`)
```json
{
 "mix": {
  "hat": {
   "gain_db": -14
  }
 },
 "lead": {
  "kw": {
   "bright": 0.45
  }
 },
 "dynamics": 0.7,
 "lufs": -9.2
}
```
- `mix.hat.gain_db / lead.kw.bright` -> {'hat_gain_db': -14, 'lead_bright': 0.45}: 3-8 kHz harshness 59/100; tame hats and lead brightness
- `dynamics` -> 0.7: median beat crest is only 8.8 dB: the master is squashed
- `lufs` -> -9.2: match the reference's integrated loudness (compose already accepts lufs in a genre spec)

```
af.py compose --genre <base> --override '{"mix":{"hat":{"gain_db":-14}},"lead":{"kw":{"bright":0.45}},"dynamics":0.7,"lufs":-9.2}' --out adapted.wav
```

## Per-beat punch (first 64 beats)
`9.4, 8.8, 7.9, 9.1, 8.5, 9.2, 8.8, 8.9, 9.9, 11.0, 9.1, 9.5, 8.7, 9.6, 8.8, 8.6, 8.0, 8.2, 8.6, 8.4, 8.8, 8.9, 9.3, 9.2, 8.4, 9.2, 8.3, 7.9, 8.3, 9.9, 7.8, 8.8, 9.0, 7.8, 8.8, 9.3, 8.3, 9.4, 9.4, 8.6, 8.2, 9.0, 8.8, 8.3, 11.0, 10.2, 9.4`

Reminder: nobody listened here. The person's ears decide whether it sounds good.

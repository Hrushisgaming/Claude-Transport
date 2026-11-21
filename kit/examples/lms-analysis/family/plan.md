# Build plan from style `roblox-lms-family`

64 bars at 176.0 BPM = 87 s, key A minor. Positions are the reference's PROPORTIONS; section labels are energy heuristics. Structure comes from the most typical family member `a-grave-soul-now-run`; the shared habits and ranges are in brief.md.

| bars | section | energy | layers entering/leaving |
|---|---|---|---|
| 1-10 | build (build) | -3.5 dB | - |
| 11-23 | drop (drop) | -1.5 dB | +sub 4dB, +air 7dB |
| 24-42 | drop (drop) | -2.5 dB | - |
| 43-64 | outro (outro) | -3.7 dB | +mid 4dB, +air 3dB |

## Hard points to place (bar numbers in YOUR track)
- bar 11: **DROP**: bass/sub entry about +3 dB
- bar 43: **DROP**: bass/sub entry about +2 dB
- about 2 other hard accents/hits across the track (the reference had 1.5 per minute); put them on bar lines or the 16th grid (100% of the reference's did)

## Compose it
`python3 af.py compose --genre roblox_lms_family --bars 64 --bpm 176 --plan '[["build", 0.156], ["drop", 0.203], ["drop", 0.297], ["outro", 0.344]]' --out cand.wav`

Then: `af.py deep cand.wav` to see YOUR hard points and loop check, and `af.py compare cand.wav <style dir>/dna.json` to compare with the reference numbers. Say plainly that nobody has listened.

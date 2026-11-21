# Build plan from style `lms-chase`

64 bars at 175.0 BPM = 88 s, key A minor. Positions are the reference's PROPORTIONS; section labels are energy heuristics. Structure comes from the most typical family member `agravesoul`; the shared habits and ranges are in brief.md.

| bars | section | energy | layers entering/leaving |
|---|---|---|---|
| 1-10 | build (build) | -3.5 dB | - |
| 11-23 | drop (drop) | -1.5 dB | +sub 4dB, +air 7dB |
| 24-33 | drop (drop) | -1.8 dB | - |
| 34-38 | break (break_) | -3.5 dB | -lowmid 4dB, -highmid 4dB, -air 4dB |
| 39-42 | build (build) | -3.1 dB | - |
| 43-60 | drop (drop) | -0.9 dB | +mid 4dB, +air 3dB |
| 61-64 | outro (outro) | -16.4 dB | -sub 8dB, -bass 7dB, -lowmid 9dB, -mid 10dB, -highmid 8dB, -air 7dB |

## Hard points to place (bar numbers in YOUR track)
- bar 11: **DROP**: bass/sub entry about +3 dB
- bar 34: **breakdown**: strip back for about 4 bars: energy about 2 dB under the sections around it, bass about 2 dB down; it leads into a drop
- bar 39: **build**: 3-bar build before the drop: denser drum hits (about +0.4 per beat) and a slowly rising level
- bar 43: **DROP**: bass/sub entry about +2 dB
- bar 62: **end**: hard cut then decay: last full-level music, then about 2.92 s of tail. For a LOOP, do not copy this ending; make the last bar lead back into bar 1.
- about 2 other hard accents/hits across the track (the reference had 1.5 per minute); put them on bar lines or the 16th grid (100% of the reference's did)

## Compose it
`python3 af.py compose --genre lms_chase --bars 64 --bpm 175 --plan '[["build", 0.156], ["drop", 0.203], ["drop", 0.156], ["break_", 0.078], ["build", 0.062], ["drop", 0.281], ["outro", 0.062]]' --out cand.wav`

Then: `af.py deep cand.wav` to see YOUR hard points and loop check, and `af.py compare cand.wav <style dir>/dna.json` to compare with the reference numbers. Say plainly that nobody has listened.

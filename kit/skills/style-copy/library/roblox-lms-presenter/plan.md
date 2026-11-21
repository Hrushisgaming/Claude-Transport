# Build plan from style `lms-presenter`

64 bars at 171.1 BPM = 90 s, key G minor. Positions are the reference's PROPORTIONS; section labels are energy heuristics. Structure comes from the most typical family member `showtime`; the shared habits and ranges are in brief.md.

| bars | section | energy | layers entering/leaving |
|---|---|---|---|
| 1-7 | intro (intro) | -10.0 dB | - |
| 8-37 | build (build) | -3.0 dB | +sub 9dB, +bass 4dB, +mid 4dB, +highmid 3dB, +air 8dB |
| 38-45 | drop (drop) | -1.6 dB | - |
| 46-52 | drop (drop) | -1.2 dB | - |
| 53-54 | build (build) | -8.2 dB | -sub 11dB, -bass 5dB, -lowmid 15dB, -mid 13dB, -highmid 7dB |
| 55-61 | drop (drop) | -0.9 dB | +sub 8dB, +bass 5dB, +lowmid 15dB, +mid 13dB, +highmid 8dB, +air 3dB |
| 62-64 | outro (outro) | -18.3 dB | -sub 13dB, -bass 5dB, -lowmid 8dB, -mid 8dB, -highmid 5dB, -air 7dB |

## Hard points to place (bar numbers in YOUR track)
- bar 4: **riser**: high-band sweep about 6.62 s, +46 dB
- bar 8: **DROP**: riser over bars 6-7 (high bands up about +46 dB); full impact ON the downbeat of bar 8; bass/sub entry about +6 dB
- bar 16: **stop**: cut of 0.1 s, then full impact
- bar 38: **DROP**: full impact ON the downbeat of bar 38; bass/sub entry about +2 dB
- bar 53: **breakdown**: strip back for about 2 bars: energy about 7 dB under the sections around it, bass about 7 dB down; it leads into a drop
- bar 54: **DROP**: bass/sub entry about +6 dB
- bar 62: **end**: hard cut then decay: last full-level music, then about 2.285 s of tail. For a LOOP, do not copy this ending; make the last bar lead back into bar 1.
- about 2 other hard accents/hits across the track (the reference had 1.6 per minute); put them on bar lines or the 16th grid (100% of the reference's did)

## Compose it
`python3 af.py compose --genre lms_presenter --bars 64 --bpm 171 --plan '[["intro", 0.109], ["build", 0.469], ["drop", 0.125], ["drop", 0.109], ["build", 0.031], ["drop", 0.109], ["outro", 0.047]]' --out cand.wav`

Then: `af.py deep cand.wav` to see YOUR hard points and loop check, and `af.py compare cand.wav <style dir>/dna.json` to compare with the reference numbers. Say plainly that nobody has listened.

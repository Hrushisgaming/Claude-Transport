# Genres, instruments and the spec format

`python3 af.py compose --list` prints the live list. Every genre is a dict in `scripts/forge/genres.py`.

| genre | BPM | typical scales | character / main voices |
|---|---|---|---|
| chiptune (8bit, chip) | 128-158 | major, pent_major | square/triangle, noise drums, arps, bit-crush |
| synthwave (retro, outrun) | 96-118 | minor, dorian | pad, plucked arp, saw bass, gated snare, chorus lead |
| lofi (lo-fi) | 70-88 | dorian, minor | swung, FM electric piano, soft kit, vinyl crackle |
| boombap (hiphop) | 82-96 | minor, dorian, phrygian | swung acoustic kit, sub bass, music-box lead |
| house | 120-126 | minor, dorian | four-on-floor, stabs, sidechain pump, offbeat hats |
| techno (tech, industrial) | 128-140 | minor, phrygian | industrial kit, rolling bass, drones, stabs |
| dnb (drum_and_bass) | 170-176 | minor, phrygian | two-step breaks, reese bass, strings |
| trap | 136-150 | minor, phrygian | rolling hats, 808 sub, bells |
| edm (pop, future_bass) | 126-150 | minor, major | supersaw chords/leads, big drops, risers |
| dubstep (wobble) | 138-146 | minor, phrygian | half-time, LFO wobble bass |
| horror_chase (forsaken, chase, roblox, horror) | 150-176 | phrygian, harmonic_minor | industrial kit, distorted pulse bass + guitar, brass stabs, risers, choir, tom fills |
| dark_ambient (ambient, drone) | 56-76 | phrygian, locrian | drones, sus pads, choir, sparse bells, long reverb |
| cinematic (orchestral, epic, trailer) | 72-100 | minor, harmonic_minor | strings, brass, toms, choir, impacts, big build |
| rock (punk) | 110-148 | minor, pent_minor | power chords, acoustic kit, lead guitar |
| metal (heavy) | 150-190 | phrygian, harmonic_minor | double-kick, palm-muted high-gain guitar |
| jazz (swing) | 96-150 | dorian, mixolydian | 8th-note swing, ride, walking bass, 7th chords |

## Spec format (all optional except bpm/scales)
```python
"mygenre": dict(
  bpm=(120, 130), scales=["minor"], kit="808|acoustic|chip|industrial", swing=0.0, swing_grid=1,   # swing: 0 straight .33 triplet .5 heavy
  chord_len=1,                     # bars per chord
  drums=dict(kick="x...x...x...x...", snare="....X.......X...", hat="x.x.x.x.x.x.x.x."),  # 16 chars = one bar of 16ths
  bass=dict(inst="saw_bass", oct=2, rhythm="x.x.o.x.xxx.o.f.", kw=dict(cutoff=700, drive=1.8)),
  chords=dict(inst="pad", oct=3, rhythm="x---------------", kind="triad|seventh|ninth|sus2|sus4|power"),
  arp=dict(inst="pluck", oct=4, rate=1, pattern="up|down|updown|random", kind="seventh"),
  lead=dict(inst="lead_saw", oct=5, density=0.5, contour="arch|rise|fall|flat", leap=0.2, rest=0.25),
  layers=dict(intro=[...], build=[...], drop=[...], break_=[...], outro=[...]),   # which layers play per section
  plan=[("intro",.1),("build",.1),("drop",.3),("break_",.1),("drop",.3),("outro",.1)],   # fractions of the song
  impact=True, fills=True, vinyl=False,
  mix=dict(bass=dict(sidechain=0.5, lp=2500, gain_db=-3), lead=dict(reverb=0.3, delay=0.25, chorus=0.4), reverb_rt60=2.0),
)
```
Rhythm chars: `X` accent `x` normal `o` ghost `.` rest `-` sustain. Bass: `x` root `o` octave up `e` octave down `f` fifth `t` third `b` flat-7 `w` walking `m` palm-muted root.
Layers: kick snare clap hat ohat perc ride tom metal bass chords arp lead guitar strings choir stab drone vinyl snare_roll riser impact.
Section names: intro build drop/chase/climax/main/verse break_ outro (drop-like names get impacts and fills).
Mix keys per track: gain_db hp lp reverb(send) delay(send) chorus drive crush sidechain(depth) widen comp.

## Override examples (no code editing)
```bash
python3 af.py compose --genre house --override '{"drums":{"hat":"xxxxxxxxxxxxxxxx"},"bass":{"inst":"reese"}}'
python3 af.py compose --genre horror_chase --override '{"progression":[0,1,0,6],"mix":{"guitar":{"drive":2.5}}}'
python3 af.py compose --genre synthwave --plan '[["intro",0.15],["drop",0.7],["outro",0.15]]'
```

## Instruments
`sine_sub saw_bass reese wobble sub_drop pluck lead_saw lead_square chip_tri pad strings brass ep bell piano organ choir guitar guitar_mute stab drone music_box`. Add one by writing `def name(f, dur, sr, **kw)` returning a mono array in `forge/instruments.py` and registering it in `INSTRUMENTS`.
Drum hits (`forge/drums.py`): kick snare clap hat ohat ride crash tom tom_hi tom_lo rim perc metal impact, in four kits.

## Game soundtrack sets (Forsaken-style and similar)
Keep **one key and one BPM** across the set so tracks layer and crossfade:
```bash
K="--key F# --bpm 168"
python3 af.py compose --genre dark_ambient $K --bars 32 --out lobby.wav
python3 af.py compose --genre horror_chase $K --scale phrygian --intensity 0.4 --bars 32 --out tension.wav
python3 af.py compose --genre horror_chase $K --scale phrygian --intensity 0.9 --bars 48 --stems chase_stems/ --out chase.wav
python3 af.py compose --genre metal $K --bars 32 --out lastlife.wav
python3 af.py sfx --name stinger_dark --out lose.wav ; python3 af.py sfx --name stinger_bright --out win.wav
python3 af.py audio_edit loop chase.wav chase_loop.wav --dur 180 --xfade 1.5
```
Adaptive audio: import `chase_stems/*.wav` (kick, bass, guitar, stab, lead, choir...) into the game engine and fade layers with danger level. These are original compositions in a genre feel; they are not copies of any game's actual tracks.

## Video-oriented genres (1.1)
Derived from the base genres (same instruments and patterns), tuned for video beds: `corporate` (98-122 BPM, major/mixolydian, piano + plucks, soft drums; product films, tutorials, real estate), `warm_piano` (66-90 BPM, piano and music box, light kick; vlogs, weddings, travel), `epic_trailer` (80-110 BPM, long build, toms, one huge climax; trailers, hype reels), `soft_ambient` (60-80 BPM, pads and drone only; podcasts, interviews, documentaries). Aliases: product, tutorial, explainer, vlog, wedding, travel, memories, hype, podcast, interview, documentary. `compose --plan` now works (it was ignored before 1.1).

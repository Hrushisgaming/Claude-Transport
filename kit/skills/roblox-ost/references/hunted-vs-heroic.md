# Hunted vs heroic (a listening AI's verdict on two renders, 2026-11-20)
The first weighted OST (`ostfight.py`) was heard as HAPPY / heroic. A listening AI (Hydrogen) compared it with A Grave Soul and LMSY2K. It named these causes. Treat as one listener's opinion; nobody here can hear.

| Heroic (avoid for a hunted theme) | Hunted (what the real themes do) |
|---|---|
| major chords (F, C, G, E major), major-7th/9th pads | stay minor; i, bII, VI, iv, leading-tone V; restless, never resolving warmly |
| warm drawbar organ, Rhodes, legato strings, harp | cold digital piano, dark choir, minor string swells, a low drone |
| glockenspiel / celesta sparkle | heavy tubular bells on key beats (doom, ticking death sentence) |
| brass fanfare, key lift up by a whole step, rising hook | no brass; semitone lift only for tension; frantic minor square-wave cells with chromatic neighbours |
| bouncy groove, smooth snare-roll transitions | chopped Amen breakbeats, ghost snares, stutter edits, glitch interruptions |
| calm clock + pretty intro | creeping stereo-panning crawl/scratch SFX, a vocal "HA!" jump-scare right before the drop |
| resolved chord and an 8 s bell fade | tape-stop pitch collapse, dark tail, one dry blunt hit that cuts dead; or a static/PC-crash cutoff (LMSY2K) |
| guitars tucked behind pads | distorted guitars front and centre (LMSY2K), tight and un-washed |

Check measured facts before trusting a listener: for the first render the analyzer said 174 BPM and a hard cut with a 4.2 s tail, while the listener heard ~120-126 BPM and an 8 s peaceful fade. Its mood verdict matched ours; its numbers did not.


## Round 2 (2026-11-20): a RANDOM hunted render (C# minor, 176 BPM) was heard as "tense", mood 5/10 ("energetic boss-fight action")
The listener's facts matched the recipe exactly (key, tempo, drum styles, clock section 0:38-0:49, breakdown ~1:11, end ~1:16), except the key lift it placed at 0:49 (the render lifted about 1:00). Its mood verdicts were consistent with round 1.

| Heard as bright/heroic | Change now in the kit |
|---|---|
| +1 semitone key lift | lift defaults to none (88%); optional |
| major-chord turns (F, E, Bb triads) | those chords are played hollow (root, fifth, octave: no third) in piano/pads |
| retro arcade square lead, repeated stab cells | `bend_lead`: pitch-bent distorted saw; new tritone / chromatic-run motifs; motifs mutate every other 4 bars; drop C has its own motifs |
| warm choir pad | `string_tremolo`: cold tremolo strings with a rubbing minor second |
| bright piano / music-box intro | `piano_dark`: low-passed, softer, low octave, sparse; the intro piano sits an octave lower |
| bright bells on every downbeat | low church bell on accents only (section starts and the bar before a boom) |
| boxy fuzz block guitars | per-drop riffs (syncopated / gallop / tritone / triplet), power-chord hits on the tritone and minor second, guitar high-pass raised |
| buried bass | reese layer on the sub, bass and sub up ~3 dB, guitars down 1 dB |
| stiff DnB loop in drop C | DnB is rare (6%) and never used for the glitch section; chopped Amen with a different fill at every 4th bar |
| no fills / risers | bar-end fills (roll, stutter, tom roll, hat burst, kick stutter) and reverse-cymbal swells into every section |
| calm bittersweet piano pause before the end | breakdown uses dark low piano with a minor-second rub, tremolo strings and (optionally) low organ |
| (suggested) low organ / dark brass stabs | optional, 25% each: A Grave Soul itself had neither, so they are never warm and never a fanfare |

Still open: wide stereo depth, a more convincing guitar timbre (the guitars are synthesised and still called "fake"), heavier impacts.

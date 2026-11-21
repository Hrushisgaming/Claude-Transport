# Roblox OST handbook

How game music works in a round-based Roblox game, what ten measured Last Man Standing (LMS) themes have in common, and how to build and ship loops. Facts are marked **measured** (from the kit's analyzer on the references the person supplied), **documented** (Roblox docs, re-check them) or **practice** (common craft, a choice not a rule). Nobody has listened to anything the kit generates.

## 1. A game score is a set of STATES, not a song
| state | job | feel | loops? |
|---|---|---|---|
| lobby / intermission | waiting, chat, shop | calm, sparse, low energy, low risk of annoying on repeat | yes, long (16-32 bars) |
| round / tension | the round is running, no threat on you yet | unease, pulse, restraint | yes |
| chase | a killer is after you | driving pulse, high energy, danger layers | yes, often with stems |
| LMS (last man standing) | one survivor, one killer; plays until the round ends | the most intense theme; escalation then a decision | intro once, then loop |
| win / escape | the round ended and the survivor is free | release, relief, brightness, no loop | no (sting) |
| lose / caught | you died | short dark sting | no |
**LMS definition (from the person):** only one player is left in the round and one player is hunting them; when the round ends the survivor is free and no longer has to survive. So the music must (a) announce the moment survivors == 1, (b) hold maximum tension without wearing out, (c) hand over cleanly to the release.

## 2. What ten measured LMS themes share (the person's references)
Measured by `copy.py study` on ten themes: Eternity (two versions), Escape The Necrobloxians, Showtime, Vigilante Shootdown, LMSY2K, ONEBOUNCE, Eternal Hope Eternal Fight (an old version and a better-quality version) and A Grave Soul NOW RUN (in-game). Ten tracks is a small sample: a pattern, not a law. Section labels are energy heuristics. Note: the two Eternal Hope files are different arrangements, not one file twice (old = about 140 BPM in B minor, better quality = about 174 BPM in A minor; their loudness envelopes correlate at only 0.17), and the two Eternity versions are near-twins, so that song counts a little extra.
- **Tempo:** feel-tempo clusters at about 176 BPM (6 tracks, 164-180), about 196 (2 tracks, probably double-time readings of ~96-100), 140 (1) and 120 (1). Ask which a track "feels like" before copying it.
- **Key:** minor modes only (A minor 4, B minor 4, G minor 1, F# minor 1).
- **Entrance:** all ten have a clear drop; the first lands at a median of about 10% into the track (range 5-49%; the old Eternal Hope is the late one). 52% of drops have an **impact on the downbeat**; **none** used a hard silence cut before it and only 5% a riser. The LMS entrance is a hit, not a pause.
- **Layers at drops:** sub enters (7 drops), air (6), bass (5), high-mid (4). The full-range arrival is the cue.
- **Shape:** typical share of a track (median over the tracks that have it): build about 13% (6 tracks), drop sections about 56% in total (9 tracks), break about 18% (3 tracks), outro about 27% (5 tracks).
- **Harmony:** chord cycles of 4 bars (5 tracks), 8 (1) or 16 (2); the rest change slowly with no repeating cycle.
- **Hard points:** 0-5.6 hard hits per minute (median 1.5); when present about all sit on the 16th grid. Hard stops are rare.
- **Loudness:** -15.5 to -7.6 LUFS (median about -12); dense mixes (about 2.4 attacks per beat, up to 4.3 for the double-time readers).
- **Loop-ready:** none of the ten finished tracks (they fade out or end). A game loop must be built to loop.

## 3. Building blocks
**Hard-point anatomy** (what a drop is made of): [riser] -> [cut] -> impact on the downbeat -> sub/bass entry -> brightness change. LMS references favour impact + bass entry. Use `copy.py deep` to read the anatomy of any track; reproduce the anatomy and the proportions, not the notes.
**Layers:** a section change is mostly layers entering or leaving (sub, bass, low-mid, mid, high-mid, air). Plan which layer enters on which bar; it is how tension is built without changing the tune.
**Loops (practice):** loop length is a whole number of bars; the reverb/delay tail is folded onto the start; no fade in/out; the last bar must lead into the first (same harmony or a dominant turnaround). Keep the energy even across the loop; put the build in a separate intro that plays once.
**Escalation without tempo change (practice):** same key and BPM across states; raise intensity by adding layers, density and register. That lets the game crossfade on bar lines.
**Release (practice):** the win sting is brighter, major-ish or open (fifth/octave), resolves, rings out and stops; the lose sting is short, low and dark.

## 4. Roblox technical facts
**Documented** (Creator Hub, create.roblox.com/docs/audio/assets, retrieved when this kit was built; re-check): formats mp3, ogg, wav, flac; one track per file; under 20 MB; at most 7 minutes; at most 48 kHz; mono, stereo or multichannel accepted; new audio is private by default and must be granted to the experience; upload counts are limited per period and rise with identity verification. Audio moderation can reject files.
**Practice:** prefer ogg (or flac) for loops: mp3 encoder padding can leave a tiny gap at the loop point (verify in Studio). Keep music around -14 LUFS so effects and voice have headroom; Roblox has no official music loudness spec and the references range -7.6 to -15 LUFS. Leave -1.5 dB peak headroom for the re-encode.
**In Studio (practice, not run by the kit):** `Sound.Looped = true`; fade with `TweenService` on `Volume`; for layers use several Sounds of identical length started together (set `TimePosition` to match) inside one `SoundGroup`; quantize switches by waiting until the next bar line (`barLen - (TimePosition % barLen)`); preload with `ContentProvider:PreloadAsync`; play stingers as non-looped Sounds and duck the bed. `MusicDirector.luau` does all of this.

## 5. Workflow with the kit
1. Study references: `copy.py study A B C --name family`, read `brief.md` (what they all share vs what varies), `copy.py deep A` for one track's hard points and loop info.
2. Decide tempo/key (ask on ambiguity). One key and BPM for the whole set.
3. Plan: `copy.py plan family --bars 64`.
4. Build: `af.py compose ...` for a track or `af.py ost build --family ...` for the set.
5. Verify: `af.py deep cand.wav`, `af.py compare`, `af.py ost check --loop`.
6. Audition by ear (the person), turn one knob, repeat (max 5 rounds).
7. Upload, paste asset IDs into `MusicDirector.luau`, test in Studio.

## 6. Honest limits
- The analyzer measures; it does not hear. Downbeat phase is often uncertain (`downbeat_phase_confidence`): bar COUNT is reliable, "beat 1" may be beat 2-4.
- Vocals/lyrics: the deep analyzer shows a "mid-range lead layer" (vocal, lead synth or guitar; cannot say which). Real lyrics need Whisper (optional, ~500 MB); Whisper on music is approximate, a Demucs vocal stem (optional, ~1 GB) improves it. Lyrics are analysed as statistics only.
- The kit's engine makes a genre feel, not a produced track: on the first LMS test its output was darker and sparser than the references (sub +5 dB, fewer attacks per beat). Use it for sketches, structure and stems; the person's DAW work (e.g. the LMMS/FL project) is where it becomes a finished OST.
- Copyright: a reference is a lesson, not material. Do not upload other people's tracks or close copies; Roblox and rights holders act on that.

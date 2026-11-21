# Roblox soundtrack set

One key (A minor) and one BPM (178) for every state, so they crossfade on bar lines and stems layer cleanly. Loudness target -14.0 LUFS (music bed; leaves headroom for SFX; NOT a Roblox rule). Nobody has listened: audition every file.

| state | file | plays when | loops | bars | LUFS | checks |
|---|---|---|---|---|---|---|
| lobby | lobby.wav | lobby / intermission: calm, sparse, loops quietly under chat | yes | 16 | -14.0 | OK |
| tension | tension.wav | round running, nobody chased yet: unease, pulse without the full attack | yes | 16 | -14.0 | OK |
| chase | chase.wav | a killer is chasing you: driving pulse, stems for danger layering | yes | 24 | -14.0 | OK |
| lms_intro | lms_intro.wav | LAST MAN STANDING entrance: plays ONCE when the last survivor remains, then hands over to `lms` | no | 8 | -14.0 | OK |
| lms | lms.wav | LAST MAN STANDING loop: one survivor, one killer; loops until the round ends (full-energy part of the family shape if --family) | yes | 24 | -14.0 | OK |
| win | win.wav | round over, you survived / the survivor escaped: relief, no loop | no | - | -14.4 | OK |
| lose | lose.wav | you were caught: short dark sting, no loop | no | - | -15.6 | OK |

Upload each file at create.roblox.com (Creator Hub > Assets > Audio) and put the returned asset IDs into the `TRACKS` table in `MusicDirector.luau`. New uploads are private to you until you grant them to your experience; verify limits on the Creator Hub audio page before relying on them.

Stems for adaptive layers: `chase_stems/`. All stems are the same length and start together; play them as synchronized Sounds and fade layers with danger level.

These are original compositions in a genre feel; they are not copies of any game's tracks.

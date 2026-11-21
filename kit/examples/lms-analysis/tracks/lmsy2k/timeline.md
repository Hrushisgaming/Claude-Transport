# Deep analysis: lmsy2k

78.52 s, grid 100.0 BPM (4/4, steady), first downbeat 0.099 s, 33 bars. bar 1 = first detected downbeat; with low phase confidence the bar COUNT is right but 'beat 1' may really be beat 2-4.
Tempo feel: analyzer 100.0 -> feels like **200.0 BPM** (high confidence; other readings [100.0]). Ask the person which tempo they tap.
Key F# minor, -11.3 LUFS. Form: **A B C D**. Chord cycle: 4 bars. Role guess (heuristic): chase / last-man-standing (fast, driving).

Nobody has listened to this. Labels like drop/break are heuristics from energy; the person's ears decide.

## Hard points (in time order)
| time | bar:beat | % | kind | detail |
|---|---|---|---|---|
| 0:04.90 | 3:1.0 | 6.2 | **DROP** | +16.9 dB: full impact (+10.0 dB, level stays up) -> bass +29.8 dB, brightness -1544 Hz |
| 0:04.90 | 3:1.0 | 6.2 | hit | full impact +10.0 dB (low +23.7, high +11.2), level stays up (entrance), +1.6 ms off the 16th grid |
| 1:07.30 | 29:1.0 | 85.7 | BREAKDOWN | 3 bars (to bar 31, 1:14.50), 5.2 dB under its surroundings, bass +7.2 dB |
| 1:15.81 | 32:3.19 | 96.5 | FADE | fade-out: music last at normal level, then 2.71 s of tail (4.1 dB down within 1 s) |

Hits per minute 0.8, stops per minute 0.0, hits on the 16th grid 1.0, hits on beat 1 1.0, types {'full impact': 1, 'sub/kick impact': 0, 'crash/high burst': 0, 'accent': 0}.

## Sections
| bar | time | len | label | form | energy | key | layers entering / leaving |
|---|---|---|---|---|---|---|---|
| 1 | 0:00.10 | 2 bars | intro | A | -17.1 dB | F# minor | - |
| 3 | 0:04.90 | 26 bars | verse | B | -3.4 dB | F# minor | +sub 43dB, +bass 30dB, +lowmid 10dB, +mid 6dB, +highmid 8dB, +air 8dB |
| 29 | 1:07.30 | 3 bars | break | C | -9.5 dB | F# minor | -sub 13dB, -bass 7dB, -lowmid 4dB, -highmid 9dB, -air 4dB |
| 32 | 1:14.50 | 2 bars | outro | D | -14.4 dB | A# minor | -sub 6dB, -bass 9dB, -lowmid 6dB, -mid 8dB, +highmid 5dB, -air 11dB |

## Loop-readiness: NOT ready
- ends with 1.8 s of fade/silence: a looping Sound would play that gap every cycle
- starts with 4.9 s of quiet before the music
- level jump at the seam: last 0.25 s -90 dB vs first 0.25 s -34 dB
- length is 32.68 bars from the first downbeat (-775 ms from a whole bar): a loop would drift off the grid
- a rip of a finished track is rarely loop-ready; your own render should pass this before you upload it

## Mid-range lead layer (vocal, lead synth or guitar; relative to this track): prominent in 18% of bars
bars 1-2 (0:00.10-0:04.90), bars 29-32 (1:07.30-1:16.90)

Tempo drift max 0.2%, no tempo change found.

## Bar map (energy relative to the loudest bar; marks = events inside the bar)
   1  0:00.10   -16.6 dB  #############                 
   2  0:02.50   -17.7 dB  ###########                   
   3  0:04.90     0.0 dB  ############################  **DROP** hit
   4  0:07.30    -0.4 dB  ############################  
   5  0:09.70    -4.0 dB  ########################      
   6  0:12.10    -4.1 dB  ########################      
   7  0:14.50    -3.9 dB  ########################      
   8  0:16.90    -4.1 dB  ########################      
   9  0:19.30    -3.9 dB  ########################      
  10  0:21.70    -4.0 dB  ########################      
  11  0:24.10    -3.9 dB  ########################      
  12  0:26.50    -4.0 dB  ########################      
  13  0:28.90    -2.7 dB  #########################     
  14  0:31.30    -2.6 dB  ##########################    
  15  0:33.70    -2.7 dB  #########################     
  16  0:36.10    -2.7 dB  #########################     
  17  0:38.50    -2.7 dB  #########################     
  18  0:40.90    -2.8 dB  #########################     
  19  0:43.30    -2.8 dB  #########################     
  20  0:45.70    -3.4 dB  #########################     
  21  0:48.10    -4.1 dB  ########################      
  22  0:50.50    -4.2 dB  ########################      
  23  0:52.90    -4.0 dB  ########################      
  24  0:55.30    -4.2 dB  ########################      
  25  0:57.70    -4.5 dB  ########################      
  26  1:00.10    -4.5 dB  ########################      
  27  1:02.50    -4.5 dB  ########################      
  28  1:04.90    -4.4 dB  ########################      
  29  1:07.30    -8.9 dB  ####################          BREAKDOWN
  30  1:09.70   -10.8 dB  ##################            
  31  1:12.10    -8.9 dB  ####################          
  32  1:14.50    -9.4 dB  ###################           FADE
  33  1:16.90   -19.4 dB  ##########                    

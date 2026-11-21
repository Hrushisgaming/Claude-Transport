# Deep analysis: a-grave-soul-now-run

73.25 s, grid 164.0 BPM (4/4, steady), first downbeat 0.029 s, 50 bars. bar 1 = first detected downbeat; with low phase confidence the bar COUNT is right but 'beat 1' may really be beat 2-4.
Tempo feel: analyzer 164.0 -> feels like **164.0 BPM** (high confidence; other readings [82.0]). Ask the person which tempo they tap.
Key B minor, -12.6 LUFS. Form: **A B C C' C' D E**. Chord cycle: 8 bars. Role guess (heuristic): chase / last-man-standing (fast, driving).

Nobody has listened to this. Labels like drop/break are heuristics from energy; the person's ears decide.

## Hard points (in time order)
| time | bar:beat | % | kind | detail |
|---|---|---|---|---|
| 0:01.49 | 1:4.99 | 2.0 | hit | full impact +7.4 dB (low +7.3, high +8.7), one-shot, level back in 1.88 s, -5.2 ms off the 16th grid |
| 0:11.74 | 9:1.0 | 16.0 | **DROP** | +2.3 dB: bass +2.6 dB, brightness +655 Hz |
| 0:38.08 | 27:1.0 | 52.0 | BREAKDOWN | 4 bars (to bar 30, 0:43.93), 2.3 dB under its surroundings, bass +2.0 dB, leads into a drop |
| 0:43.93 | 31:1.0 | 60.0 | BUILD | 3 bars (to bar 33, 0:48.32), onset density +0.4/beat, level +0.23 dB/bar |
| 0:48.32 | 34:1.0 | 66.0 | **DROP** | +2.2 dB: bass +2.3 dB, brightness -27 Hz |
| 1:09.85 | 48:3.83 | 95.4 | END CUT | hard cut then decay: music last at normal level, then 3.4 s of tail (7.4 dB down within 1 s) |

Hits per minute 0.8, stops per minute 0.0, hits on the 16th grid 1.0, hits on beat 1 1.0, types {'full impact': 1, 'sub/kick impact': 0, 'crash/high burst': 0, 'accent': 0}.

## Sections
| bar | time | len | label | form | energy | key | layers entering / leaving |
|---|---|---|---|---|---|---|---|
| 1 | 0:00.03 | 8 bars | build | A | -3.5 dB | B minor | - |
| 9 | 0:11.74 | 10 bars | drop | B | -1.5 dB | B minor | +sub 4dB, +air 7dB |
| 19 | 0:26.37 | 8 bars | drop | C | -1.8 dB | B minor | - |
| 27 | 0:38.08 | 4 bars | break | C' | -3.5 dB | B minor | -lowmid 4dB, -highmid 4dB, -air 4dB |
| 31 | 0:43.93 | 3 bars | build | C' | -3.1 dB | B minor | - |
| 34 | 0:48.32 | 14 bars | drop | D | -0.9 dB | B minor | +mid 4dB, +air 3dB |
| 48 | 1:08.81 | 3 bars | outro | E | -16.4 dB | B minor | -sub 8dB, -bass 7dB, -lowmid 9dB, -mid 10dB, -highmid 8dB, -air 7dB |

## Loop-readiness: NOT ready
- ends with 3.3 s of fade/silence: a looping Sound would play that gap every cycle
- level jump at the seam: last 0.25 s -60 dB vs first 0.25 s -19 dB
- a rip of a finished track is rarely loop-ready; your own render should pass this before you upload it

## Mid-range lead layer (vocal, lead synth or guitar; relative to this track): prominent in 22% of bars
bars 15-16 (0:20.52-0:23.44), bars 37-39 (0:52.71-0:57.10), bars 45-46 (1:04.42-1:07.35)

Tempo drift max 0.1%, no tempo change found.

## Bar map (energy relative to the loudest bar; marks = events inside the bar)
   1  0:00.03    -6.2 dB  ######################        hit
   2  0:01.49    -2.4 dB  ##########################    
   3  0:02.96    -3.6 dB  #########################     
   4  0:04.42    -3.1 dB  #########################     
   5  0:05.88    -3.3 dB  #########################     
   6  0:07.35    -2.1 dB  ##########################    
   7  0:08.81    -3.6 dB  #########################     
   8  0:10.27    -3.4 dB  #########################     
   9  0:11.74    -2.0 dB  ##########################    **DROP**
  10  0:13.20    -0.6 dB  ###########################   
  11  0:14.66    -1.9 dB  ##########################    
  12  0:16.13    -1.7 dB  ##########################    
  13  0:17.59    -1.4 dB  ###########################   
  14  0:19.05    -0.8 dB  ###########################   
  15  0:20.52    -1.9 dB  ##########################    
  16  0:21.98    -2.0 dB  ##########################    
  17  0:23.44    -1.5 dB  ###########################   
  18  0:24.91    -1.2 dB  ###########################   
  19  0:26.37    -2.9 dB  #########################     
  20  0:27.83    -2.7 dB  #########################     
  21  0:29.30    -2.3 dB  ##########################    
  22  0:30.76    -0.6 dB  ###########################   
  23  0:32.22    -1.7 dB  ##########################    
  24  0:33.69    -1.3 dB  ###########################   
  25  0:35.15    -0.8 dB  ###########################   
  26  0:36.61    -1.8 dB  ##########################    
  27  0:38.08    -4.1 dB  ########################      BREAKDOWN
  28  0:39.54    -4.4 dB  ########################      
  29  0:41.01    -4.0 dB  ########################      
  30  0:42.47    -1.7 dB  ##########################    
  31  0:43.93    -3.4 dB  #########################     BUILD
  32  0:45.40    -3.1 dB  #########################     
  33  0:46.86    -2.9 dB  #########################     
  34  0:48.32    -0.7 dB  ###########################   **DROP**
  35  0:49.78    -0.9 dB  ###########################   
  36  0:51.25    -0.3 dB  ############################  
  37  0:52.71    -1.1 dB  ###########################   
  38  0:54.17    -1.5 dB  ###########################   
  39  0:55.64    -1.0 dB  ###########################   
  40  0:57.10     0.0 dB  ############################  
  41  0:58.57    -1.4 dB  ###########################   
  42  1:00.03    -1.3 dB  ###########################   
  43  1:01.49    -1.1 dB  ###########################   
  44  1:02.96    -0.5 dB  ############################  
  45  1:04.42    -1.2 dB  ###########################   
  46  1:05.88    -1.0 dB  ###########################   
  47  1:07.35    -1.0 dB  ###########################   
  48  1:08.81    -4.2 dB  ########################      END CUT
  49  1:10.27   -13.4 dB  ###############               
  50  1:11.74   -31.6 dB                                

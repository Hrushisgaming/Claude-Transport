# Deep analysis: hope-ref

73.42 s, grid 173.97 BPM (4/4, steady), first downbeat 0.834 s, 53 bars. bar 1 = first detected downbeat; with low phase confidence the bar COUNT is right but 'beat 1' may really be beat 2-4.
Tempo feel: analyzer 174.0 -> feels like **174.0 BPM** (medium confidence; other readings [87.0]). Ask the person which tempo they tap.
Key A minor, -14.6 LUFS. Form: **A B C D D'**. Chord cycle: 4 bars. Role guess (heuristic): chase / last-man-standing (fast, driving).

Nobody has listened to this. Labels like drop/break are heuristics from energy; the person's ears decide.

## Hard points (in time order)
| time | bar:beat | % | kind | detail |
|---|---|---|---|---|
| 0:00.49 | 0:4.0 | 0.7 | hit | full impact +23.4 dB (low +26.2, high +20.8), level stays up (entrance), -0.4 ms off the 16th grid |
| 0:11.70 | 8:4.52 | 15.9 | hit | full impact +9.4 dB (low +11.1, high +10.2), one-shot, level back in 1.88 s, +6.0 ms off the 16th grid |
| 0:11.87 | 9:1.0 | 16.2 | **DROP** | +2.2 dB: full impact (+9.4 dB, one-shot 1.88 s) -> bass +2.1 dB, brightness +518 Hz |
| 0:38.08 | 27:5.0 | 51.9 | hit | sub/kick impact +7.9 dB (low +12.6, high +1.8), one-shot, level back in 0.22 s, -0.0 ms off the 16th grid |
| 0:51.88 | 37:4.99 | 70.7 | hit | sub/kick impact +8.1 dB (low +14.2, high +2.7), one-shot, level back in 0.23 s, -2.8 ms off the 16th grid |
| 1:05.67 | 47:4.98 | 89.4 | hit | sub/kick impact +9.0 dB (low +14.1, high +2.0), one-shot, level back in 0.22 s, -5.7 ms off the 16th grid |
| 1:08.43 | 50:1.0 | 93.2 | BREAKDOWN | 2 bars (to bar 51, 1:11.19), 6.6 dB under its surroundings, bass +6.3 dB |
| 1:11.88 | 52:2.99 | 97.9 | END CUT | hard cut then decay: music last at normal level, then 1.55 s of tail (69.4 dB down within 1 s) |

Hits per minute 4.1, stops per minute 0.0, hits on the 16th grid 1.0, hits on beat 1 0.6, types {'full impact': 2, 'sub/kick impact': 3, 'crash/high burst': 0, 'accent': 0}.

## Sections
| bar | time | len | label | form | energy | key | layers entering / leaving |
|---|---|---|---|---|---|---|---|
| 1 | 0:00.83 | 8 bars | drop | A | -2.8 dB | C minor | - |
| 9 | 0:11.87 | 25 bars | drop | B | -1.3 dB | G# minor | +air 4dB |
| 34 | 0:46.36 | 16 bars | drop | C | -2.0 dB | A minor | - |
| 50 | 1:08.43 | 2 bars | break | D | -8.7 dB | A minor | -bass 8dB, -lowmid 6dB, -mid 7dB, -highmid 9dB, -air 13dB |
| 52 | 1:11.19 | 2 bars | outro | D' | -37.8 dB | C minor | -sub 45dB, -bass 34dB, -lowmid 25dB, -mid 27dB, -highmid 32dB, -air 26dB |

## Loop-readiness: NOT ready
- ends with 1.5 s of fade/silence: a looping Sound would play that gap every cycle
- level jump at the seam: last 0.25 s -90 dB vs first 0.25 s -28 dB
- length is 52.62 bars from the first downbeat (-527 ms from a whole bar): a loop would drift off the grid
- a rip of a finished track is rarely loop-ready; your own render should pass this before you upload it

## Mid-range lead layer (vocal, lead synth or guitar; relative to this track): prominent in 21% of bars
bars 35-40 (0:47.74-0:56.02)

Tempo drift max 0.2%, no tempo change found.

## Bar map (energy relative to the loudest bar; marks = events inside the bar)
   1  0:00.83    -1.0 dB  ###########################   
   2  0:02.21    -3.5 dB  #########################     
   3  0:03.59    -1.6 dB  ###########################   
   4  0:04.97    -3.3 dB  #########################     
   5  0:06.35    -2.1 dB  ##########################    
   6  0:07.73    -4.2 dB  ########################      
   7  0:09.11    -2.7 dB  #########################     
   8  0:10.49    -4.3 dB  ########################      hit
   9  0:11.87    -1.3 dB  ###########################   **DROP**
  10  0:13.25    -1.2 dB  ###########################   
  11  0:14.63    -1.4 dB  ###########################   
  12  0:16.01    -1.2 dB  ###########################   
  13  0:17.39    -1.7 dB  ##########################    
  14  0:18.77    -1.7 dB  ##########################    
  15  0:20.15    -1.8 dB  ##########################    
  16  0:21.53    -1.5 dB  ###########################   
  17  0:22.91     0.0 dB  ############################  
  18  0:24.29    -0.2 dB  ############################  
  19  0:25.67    -0.8 dB  ###########################   
  20  0:27.05    -0.3 dB  ############################  
  21  0:28.43    -0.7 dB  ###########################   
  22  0:29.80    -0.4 dB  ############################  
  23  0:31.18    -0.9 dB  ###########################   
  24  0:32.56    -0.4 dB  ############################  
  25  0:33.94    -1.1 dB  ###########################   
  26  0:35.32    -1.6 dB  ###########################   
  27  0:36.70    -2.0 dB  ##########################    hit
  28  0:38.08    -1.8 dB  ##########################    
  29  0:39.46    -2.2 dB  ##########################    
  30  0:40.84    -2.1 dB  ##########################    
  31  0:42.22    -2.4 dB  ##########################    
  32  0:43.60    -2.1 dB  ##########################    
  33  0:44.98    -2.2 dB  ##########################    
  34  0:46.36    -1.4 dB  ###########################   
  35  0:47.74    -1.8 dB  ##########################    
  36  0:49.12    -1.7 dB  ##########################    
  37  0:50.50    -2.1 dB  ##########################    hit
  38  0:51.88    -1.8 dB  ##########################    
  39  0:53.26    -2.3 dB  ##########################    
  40  0:54.64    -1.9 dB  ##########################    
  41  0:56.02    -1.6 dB  ###########################   
  42  0:57.40    -1.9 dB  ##########################    
  43  0:58.77    -2.4 dB  ##########################    
  44  1:00.16    -2.1 dB  ##########################    
  45  1:01.53    -2.3 dB  ##########################    
  46  1:02.91    -2.0 dB  ##########################    
  47  1:04.29    -2.3 dB  ##########################    hit
  48  1:05.67    -2.0 dB  ##########################    
  49  1:07.05    -2.4 dB  ##########################    
  50  1:08.43    -7.9 dB  #####################         BREAKDOWN
  51  1:09.81    -9.4 dB  ###################           
  52  1:11.19    -4.8 dB  ########################      END CUT
  53  1:12.57   -70.8 dB                                

# Deep analysis: eternal-hope-old

73.84 s, grid 139.98 BPM (4/4, steady), first downbeat 0.07 s, 43 bars. bar 1 = first detected downbeat; with low phase confidence the bar COUNT is right but 'beat 1' may really be beat 2-4.
Tempo feel: analyzer 140.0 -> feels like **140.0 BPM** (high confidence; other readings [70.0]). Ask the person which tempo they tap.
Key B minor, -15.5 LUFS. Form: **A B C D**. Chord cycle: 4 bars. Role guess (heuristic): tension / mid-intensity round music.

Nobody has listened to this. Labels like drop/break are heuristics from energy; the person's ears decide.

## Hard points (in time order)
| time | bar:beat | % | kind | detail |
|---|---|---|---|---|
| 0:01.79 | 2:1.01 | 2.4 | hit | full impact +10.2 dB (low +11.0, high +7.6), one-shot, level back in 1.17 s, +4.7 ms off the 16th grid |
| 0:36.08 | 22:1.0 | 48.9 | **DROP** | +2.3 dB: bass +2.3 dB, brightness -328 Hz |
| 0:44.65 | 27:1.0 | 60.5 | BREAKDOWN | 3 bars (to bar 29, 0:49.79), 2.5 dB under its surroundings, bass +1.4 dB, leads into a drop |
| 1:11.54 | 42:3.74 | 96.9 | END CUT | hard cut then decay: music last at normal level, then 2.3 s of tail (20.6 dB down within 1 s) |

Hits per minute 0.8, stops per minute 0.0, hits on the 16th grid 1.0, hits on beat 1 1.0, types {'full impact': 1, 'sub/kick impact': 0, 'crash/high burst': 0, 'accent': 0}.

## Sections
| bar | time | len | label | form | energy | key | layers entering / leaving |
|---|---|---|---|---|---|---|---|
| 1 | 0:00.07 | 21 bars | drop | A | -1.8 dB | B minor | - |
| 22 | 0:36.08 | 5 bars | drop | B | -0.7 dB | B minor | +sub 4dB, +lowmid 4dB |
| 27 | 0:44.65 | 15 bars | break | C | -1.7 dB | B minor | -bass 3dB, -lowmid 4dB, -highmid 3dB |
| 42 | 1:10.37 | 2 bars | outro | D | -14.4 dB | B minor | -sub 10dB, -bass 13dB, -lowmid 14dB, -mid 16dB, -highmid 18dB, -air 17dB |

## Loop-readiness: NOT ready
- ends with 2.2 s of fade/silence: a looping Sound would play that gap every cycle
- level jump at the seam: last 0.25 s -79 dB vs first 0.25 s -22 dB
- a rip of a finished track is rarely loop-ready; your own render should pass this before you upload it

## Mid-range lead layer (vocal, lead synth or guitar; relative to this track): prominent in 33% of bars
bars 16-17 (0:25.79-0:29.22), bars 23-25 (0:37.79-0:42.93), bars 35-37 (0:58.36-1:03.51), bars 40-42 (1:06.94-1:12.08)

Tempo drift max 0.0%, no tempo change found.

## Bar map (energy relative to the loudest bar; marks = events inside the bar)
   1  0:00.07    -5.7 dB  #######################       
   2  0:01.78    -0.9 dB  ###########################   hit
   3  0:03.50    -2.6 dB  ##########################    
   4  0:05.21    -1.7 dB  ##########################    
   5  0:06.93    -1.9 dB  ##########################    
   6  0:08.64    -1.0 dB  ###########################   
   7  0:10.36    -2.6 dB  ##########################    
   8  0:12.07    -1.9 dB  ##########################    
   9  0:13.79    -1.3 dB  ###########################   
  10  0:15.50     0.0 dB  ############################  
  11  0:17.21    -1.3 dB  ###########################   
  12  0:18.93    -1.2 dB  ###########################   
  13  0:20.64    -1.1 dB  ###########################   
  14  0:22.36    -0.3 dB  ############################  
  15  0:24.07    -1.3 dB  ###########################   
  16  0:25.79    -1.4 dB  ###########################   
  17  0:27.50    -1.4 dB  ###########################   
  18  0:29.22    -1.3 dB  ###########################   
  19  0:30.93    -2.7 dB  #########################     
  20  0:32.65    -3.0 dB  #########################     
  21  0:34.36    -2.6 dB  ##########################    
  22  0:36.08    -0.0 dB  ############################  **DROP**
  23  0:37.79    -0.9 dB  ###########################   
  24  0:39.50    -1.1 dB  ###########################   
  25  0:41.22    -0.7 dB  ###########################   
  26  0:42.93    -1.0 dB  ###########################   
  27  0:44.65    -3.7 dB  #########################     BREAKDOWN
  28  0:46.36    -3.4 dB  #########################     
  29  0:48.08    -3.3 dB  #########################     
  30  0:49.79    -0.8 dB  ###########################   
  31  0:51.51    -2.4 dB  ##########################    
  32  0:53.22    -2.2 dB  ##########################    
  33  0:54.94    -2.6 dB  ##########################    
  34  0:56.65    -0.1 dB  ############################  
  35  0:58.36    -1.1 dB  ###########################   
  36  1:00.08    -1.2 dB  ###########################   
  37  1:01.79    -1.0 dB  ###########################   
  38  1:03.51    -0.4 dB  ############################  
  39  1:05.22    -1.2 dB  ###########################   
  40  1:06.94    -1.1 dB  ###########################   
  41  1:08.65    -0.9 dB  ###########################   
  42  1:10.37    -4.4 dB  ########################      END CUT
  43  1:12.08   -24.3 dB  #####                         

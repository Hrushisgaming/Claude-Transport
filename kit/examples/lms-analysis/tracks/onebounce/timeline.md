# Deep analysis: onebounce

77.18 s, grid 96.5 BPM (4/4, steady), first downbeat 0.945 s, 31 bars. bar 1 = first detected downbeat; with low phase confidence the bar COUNT is right but 'beat 1' may really be beat 2-4.
Tempo feel: analyzer 96.5 -> feels like **193.0 BPM** (high confidence; other readings [96.5]). Ask the person which tempo they tap.
Key B minor, -7.6 LUFS. Form: **A B A'**. Chord cycle: 4 bars. Role guess (heuristic): chase / last-man-standing (fast, driving).

Nobody has listened to this. Labels like drop/break are heuristics from energy; the person's ears decide.

## Hard points (in time order)
| time | bar:beat | % | kind | detail |
|---|---|---|---|---|
| 0:08.41 | 4:1.0 | 10.9 | **DROP** | +3.2 dB: bass +4.2 dB, brightness -131 Hz |
| 1:15.85 | 31:1.47 | 98.3 | END CUT | hard cut then decay: music last at normal level, then 1.34 s of tail (45.0 dB down within 1 s) |

Hits per minute 0.0, stops per minute 0.0, hits on the 16th grid None, hits on beat 1 None, types {'full impact': 0, 'sub/kick impact': 0, 'crash/high burst': 0, 'accent': 0}.

## Sections
| bar | time | len | label | form | energy | key | layers entering / leaving |
|---|---|---|---|---|---|---|---|
| 1 | 0:00.94 | 3 bars | build | A | -5.1 dB | B minor | - |
| 4 | 0:08.41 | 27 bars | drop | B | -0.9 dB | B minor | +bass 5dB |
| 31 | 1:15.56 | 1 bars | outro | A' | -7.5 dB | B minor | -sub 8dB, -bass 6dB, -lowmid 4dB, -mid 4dB, -highmid 7dB, -air 12dB |

## Loop-readiness: NOT ready
- ends with 1.3 s of fade/silence: a looping Sound would play that gap every cycle
- level jump at the seam: last 0.25 s -63 dB vs first 0.25 s -15 dB
- length is 30.65 bars from the first downbeat (-861 ms from a whole bar): a loop would drift off the grid
- a rip of a finished track is rarely loop-ready; your own render should pass this before you upload it

## Mid-range lead layer (vocal, lead synth or guitar; relative to this track): prominent in 10% of bars
bars 30-31 (1:13.07-1:18.04)

Tempo drift max 0.1%, no tempo change found.

## Bar map (energy relative to the loudest bar; marks = events inside the bar)
   1  0:00.94    -5.1 dB  #######################       
   2  0:03.43    -5.1 dB  #######################       
   3  0:05.92    -5.0 dB  #######################       
   4  0:08.41    -3.1 dB  #########################     **DROP**
   5  0:10.89    -0.9 dB  ###########################   
   6  0:13.38    -1.0 dB  ###########################   
   7  0:15.87    -0.9 dB  ###########################   
   8  0:18.36    -2.0 dB  ##########################    
   9  0:20.84    -0.4 dB  ############################  
  10  0:23.33    -0.5 dB  ############################  
  11  0:25.82    -0.3 dB  ############################  
  12  0:28.30    -0.3 dB  ############################  
  13  0:30.79    -0.2 dB  ############################  
  14  0:33.28    -0.6 dB  ###########################   
  15  0:35.76    -0.3 dB  ############################  
  16  0:38.25    -0.8 dB  ###########################   
  17  0:40.74    -1.4 dB  ###########################   
  18  0:43.23    -1.2 dB  ###########################   
  19  0:45.71    -1.1 dB  ###########################   
  20  0:48.20    -1.0 dB  ###########################   
  21  0:50.69    -1.0 dB  ###########################   
  22  0:53.17    -0.9 dB  ###########################   
  23  0:55.66    -1.0 dB  ###########################   
  24  0:58.15    -0.2 dB  ############################  
  25  1:00.63     0.0 dB  ############################  
  26  1:03.12    -0.0 dB  ############################  
  27  1:05.61    -0.1 dB  ############################  
  28  1:08.10    -0.5 dB  ############################  
  29  1:10.58    -1.7 dB  ##########################    
  30  1:13.07    -2.5 dB  ##########################    
  31  1:15.56    -7.5 dB  #####################         END CUT

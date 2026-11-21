# Deep analysis: necrobloxians

76.18 s, grid 175.02 BPM (4/4, steady), first downbeat 0.748 s, 55 bars. bar 1 = first detected downbeat; with low phase confidence the bar COUNT is right but 'beat 1' may really be beat 2-4.
Tempo feel: analyzer 175.0 -> feels like **175.0 BPM** (high confidence; other readings [87.5]). Ask the person which tempo they tap.
Key A minor, -11.5 LUFS. Form: **A B C D**. Chord cycle: no clear repeating cycle. Role guess (heuristic): chase / last-man-standing (fast, driving).

Nobody has listened to this. Labels like drop/break are heuristics from energy; the person's ears decide.

## Hard points (in time order)
| time | bar:beat | % | kind | detail |
|---|---|---|---|---|
| 0:03.49 | 3:1.0 | 4.6 | **DROP** | +2.1 dB: bass +3.5 dB, brightness +558 Hz |
| 0:19.95 | 15:1.0 | 26.2 | **DROP** | +5.9 dB: full impact (+8.9 dB, one-shot 0.84 s) -> bass +6.2 dB, brightness -331 Hz |
| 0:19.95 | 15:1.0 | 26.2 | hit | full impact +8.9 dB (low +9.4, high +8.2), one-shot, level back in 0.84 s, +0.9 ms off the 16th grid |
| 0:41.89 | 31:1.01 | 55.0 | hit | full impact +9.8 dB (low +18.0, high +4.7), one-shot, level back in 0.16 s, +3.4 ms off the 16th grid |
| 1:01.08 | 45:1.0 | 80.2 | **DROP** | +1.2 dB: full impact (+12.5 dB, level stays up) -> bass +0.9 dB, brightness -119 Hz |
| 1:01.09 | 45:1.02 | 80.2 | hit | full impact +12.5 dB (low +15.7, high +10.3), level stays up (entrance), +8.5 ms off the 16th grid |

Hits per minute 2.4, stops per minute 0.0, hits on the 16th grid 1.0, hits on beat 1 1.0, types {'full impact': 3, 'sub/kick impact': 0, 'crash/high burst': 0, 'accent': 0}.

## Sections
| bar | time | len | label | form | energy | key | layers entering / leaving |
|---|---|---|---|---|---|---|---|
| 1 | 0:00.75 | 4 bars | build | A | -3.8 dB | E minor | - |
| 5 | 0:06.23 | 10 bars | build | B | -3.4 dB | A minor | - |
| 15 | 0:19.95 | 30 bars | drop | C | -0.8 dB | A minor | +sub 14dB, +bass 6dB, +lowmid 10dB, +mid 6dB, +highmid 4dB, +air 4dB |
| 45 | 1:01.08 | 11 bars | outro | D | -4.8 dB | A minor | +lowmid 4dB |

## Loop-readiness: NOT ready
- ends with 1.8 s of fade/silence: a looping Sound would play that gap every cycle
- level jump at the seam: last 0.25 s -78 dB vs first 0.25 s -15 dB
- a rip of a finished track is rarely loop-ready; your own render should pass this before you upload it

## Mid-range lead layer (vocal, lead synth or guitar; relative to this track): prominent in 24% of bars
bars 1-2 (0:00.75-0:03.49), bars 8-11 (0:10.35-0:15.83), bars 39-40 (0:52.86-0:55.60), bars 48-49 (1:05.20-1:07.94)

Tempo drift max 0.2%, no tempo change found.

## Bar map (energy relative to the loudest bar; marks = events inside the bar)
   1  0:00.75    -5.0 dB  #######################       
   2  0:02.12    -4.7 dB  ########################      
   3  0:03.49    -2.7 dB  #########################     **DROP**
   4  0:04.86    -2.8 dB  #########################     
   5  0:06.23    -2.7 dB  #########################     
   6  0:07.61    -3.4 dB  #########################     
   7  0:08.98    -3.6 dB  #########################     
   8  0:10.35    -2.2 dB  ##########################    
   9  0:11.72    -1.7 dB  ##########################    
  10  0:13.09    -1.7 dB  ##########################    
  11  0:14.46    -2.4 dB  ##########################    
  12  0:15.83    -2.8 dB  #########################     
  13  0:17.20    -4.8 dB  ########################      
  14  0:18.57    -8.7 dB  ####################          
  15  0:19.95    -0.5 dB  ############################  **DROP** hit
  16  0:21.32    -0.4 dB  ############################  
  17  0:22.69    -0.8 dB  ###########################   
  18  0:24.06    -0.4 dB  ############################  
  19  0:25.43    -0.3 dB  ############################  
  20  0:26.80     0.0 dB  ############################  
  21  0:28.17    -0.4 dB  ############################  
  22  0:29.55    -0.8 dB  ###########################   
  23  0:30.92    -0.4 dB  ############################  
  24  0:32.29    -0.5 dB  ############################  
  25  0:33.66    -0.4 dB  ############################  
  26  0:35.03    -0.1 dB  ############################  
  27  0:36.40    -0.1 dB  ############################  
  28  0:37.77    -0.2 dB  ############################  
  29  0:39.14    -0.1 dB  ############################  
  30  0:40.52    -0.7 dB  ###########################   
  31  0:41.89    -0.7 dB  ###########################   hit
  32  0:43.26    -1.2 dB  ###########################   
  33  0:44.63    -1.3 dB  ###########################   
  34  0:46.00    -1.5 dB  ###########################   
  35  0:47.37    -0.3 dB  ############################  
  36  0:48.74    -0.7 dB  ###########################   
  37  0:50.11    -0.6 dB  ###########################   
  38  0:51.48    -0.6 dB  ###########################   
  39  0:52.86    -1.9 dB  ##########################    
  40  0:54.23    -2.4 dB  ##########################    
  41  0:55.60    -1.4 dB  ###########################   
  42  0:56.97    -1.5 dB  ###########################   
  43  0:58.34    -1.5 dB  ###########################   
  44  0:59.71    -3.4 dB  #########################     
  45  1:01.08    -1.1 dB  ###########################   **DROP** hit
  46  1:02.46    -1.2 dB  ###########################   
  47  1:03.83    -1.0 dB  ###########################   
  48  1:05.20    -1.5 dB  ###########################   
  49  1:06.57    -0.8 dB  ###########################   
  50  1:07.94    -0.6 dB  ###########################   
  51  1:09.31    -0.5 dB  ############################  
  52  1:10.68    -0.8 dB  ###########################   
  53  1:12.06    -2.6 dB  ##########################    
  54  1:13.43   -10.5 dB  ##################            
  55  1:14.80   -31.8 dB                                

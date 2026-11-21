# Deep analysis: eternity-v2

80.34 s, grid 179.98 BPM (4/4, steady), first downbeat 0.333 s, 60 bars. bar 1 = first detected downbeat; with low phase confidence the bar COUNT is right but 'beat 1' may really be beat 2-4.
Tempo feel: analyzer 180.0 -> feels like **180.0 BPM** (medium confidence; other readings [90.0]). Ask the person which tempo they tap.
Key A minor, -15.0 LUFS. Form: **A A' B C D B E**. Chord cycle: 16 bars. Role guess (heuristic): chase / last-man-standing (fast, driving).

Nobody has listened to this. Labels like drop/break are heuristics from energy; the person's ears decide.

## Hard points (in time order)
| time | bar:beat | % | kind | detail |
|---|---|---|---|---|
| 0:05.67 | 5:1.0 | 7.1 | **DROP** | +2.3 dB: bass +5.1 dB, brightness -296 Hz |
| 0:09.57 | 7:4.7 | 11.9 | riser | +13.1 dB over 1.51 s (linearity 0.93) |
| 0:38.67 | 29:4.01 | 48.1 | hit | sub/kick impact +8.3 dB (low +12.5, high +3.3), one-shot, level back in 0.13 s, +3.0 ms off the 16th grid |
| 0:41.67 | 32:1.0 | 51.9 | **DROP** | +2.8 dB: bass +2.5 dB, brightness +150 Hz |
| 0:45.67 | 35:1.01 | 56.9 | hit | full impact +11.7 dB (low +14.5, high +5.4), one-shot, level back in 0.37 s, +3.0 ms off the 16th grid |
| 0:53.01 | 40:3.02 | 66.0 | hit | full impact +8.4 dB (low +9.3, high +7.7), level stays up (entrance), +6.4 ms off the 16th grid |

Hits per minute 2.2, stops per minute 0.0, hits on the 16th grid 1.0, hits on beat 1 0.33, types {'full impact': 2, 'sub/kick impact': 1, 'crash/high burst': 0, 'accent': 0}.

## Sections
| bar | time | len | label | form | energy | key | layers entering / leaving |
|---|---|---|---|---|---|---|---|
| 1 | 0:00.33 | 4 bars | build | A | -4.4 dB | A minor | - |
| 5 | 0:05.67 | 15 bars | drop | A' | -1.8 dB | A minor | +sub 7dB, +bass 4dB |
| 20 | 0:25.67 | 9 bars | break | B | -3.5 dB | A minor | - |
| 29 | 0:37.67 | 3 bars | break | C | -5.7 dB | E minor | - |
| 32 | 0:41.67 | 4 bars | break | D | -4.7 dB | A minor | +bass 4dB, +lowmid 5dB, +highmid 4dB, +air 6dB |
| 36 | 0:47.01 | 9 bars | break | B | -3.4 dB | A minor | - |
| 45 | 0:59.01 | 16 bars | outro | E | -11.8 dB | A minor | - |

## Loop-readiness: NOT ready
- ends with 5.8 s of fade/silence: a looping Sound would play that gap every cycle
- starts with 0.4 s of quiet before the music
- level jump at the seam: last 0.25 s -82 dB vs first 0.25 s -36 dB
- a rip of a finished track is rarely loop-ready; your own render should pass this before you upload it

## Mid-range lead layer (vocal, lead synth or guitar; relative to this track): prominent in 25% of bars
bars 2-4 (0:01.67-0:05.67), bars 50-52 (1:05.67-1:09.67), bars 54-56 (1:11.01-1:15.01)

Tempo drift max 0.3%, no tempo change found.

## Bar map (energy relative to the loudest bar; marks = events inside the bar)
   1  0:00.33    -4.4 dB  ########################      
   2  0:01.67    -4.3 dB  ########################      
   3  0:03.00    -4.3 dB  ########################      
   4  0:04.33    -4.7 dB  ########################      
   5  0:05.67    -1.3 dB  ###########################   **DROP**
   6  0:07.00    -3.2 dB  #########################     
   7  0:08.33    -2.0 dB  ##########################    riser
   8  0:09.67    -2.3 dB  ##########################    
   9  0:11.00    -1.1 dB  ###########################   
  10  0:12.34    -1.9 dB  ##########################    
  11  0:13.67    -1.9 dB  ##########################    
  12  0:15.00    -2.3 dB  ##########################    
  13  0:16.34    -2.2 dB  ##########################    
  14  0:17.67    -2.4 dB  ##########################    
  15  0:19.00    -0.9 dB  ###########################   
  16  0:20.34    -0.2 dB  ############################  
  17  0:21.67    -0.8 dB  ###########################   
  18  0:23.00    -2.1 dB  ##########################    
  19  0:24.34    -1.8 dB  ##########################    
  20  0:25.67    -2.0 dB  ##########################    
  21  0:27.00    -2.0 dB  ##########################    
  22  0:28.34    -2.2 dB  ##########################    
  23  0:29.67    -0.6 dB  ###########################   
  24  0:31.00    -0.3 dB  ############################  
  25  0:32.34    -2.7 dB  #########################     
  26  0:33.67   -10.5 dB  ##################            
  27  0:35.00    -3.7 dB  #########################     
  28  0:36.34    -7.4 dB  #####################         
  29  0:37.67    -2.7 dB  #########################     hit
  30  0:39.00   -10.6 dB  ##################            
  31  0:40.34    -3.9 dB  ########################      
  32  0:41.67    -5.2 dB  #######################       **DROP**
  33  0:43.01    -1.9 dB  ##########################    
  34  0:44.34    -8.9 dB  ####################          
  35  0:45.67    -2.8 dB  #########################     hit
  36  0:47.01    -7.0 dB  #####################         
  37  0:48.34    -1.7 dB  ##########################    
  38  0:49.67    -8.0 dB  #####################         
  39  0:51.01    -2.3 dB  ##########################    
  40  0:52.34    -4.5 dB  ########################      hit
  41  0:53.67    -1.1 dB  ###########################   
  42  0:55.01    -2.0 dB  ##########################    
  43  0:56.34    -2.2 dB  ##########################    
  44  0:57.67    -2.1 dB  ##########################    
  45  0:59.01    -1.8 dB  ##########################    
  46  1:00.34    -2.3 dB  ##########################    
  47  1:01.67    -0.7 dB  ###########################   
  48  1:03.01     0.0 dB  ############################  
  49  1:04.34    -4.8 dB  ########################      
  50  1:05.67    -7.3 dB  #####################         
  51  1:07.01    -7.7 dB  #####################         
  52  1:08.34    -8.7 dB  ####################          
  53  1:09.67    -6.2 dB  ######################        
  54  1:11.01    -8.7 dB  ####################          
  55  1:12.34    -6.5 dB  ######################        
  56  1:13.67   -10.0 dB  ###################           
  57  1:15.01   -16.5 dB  #############                 
  58  1:16.34   -27.3 dB  ###                           
  59  1:17.67   -35.2 dB                                
  60  1:19.01   -45.6 dB                                

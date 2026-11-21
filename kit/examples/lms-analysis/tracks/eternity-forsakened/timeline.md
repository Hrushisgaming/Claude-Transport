# Deep analysis: eternity-forsakened

75.01 s, grid 179.98 BPM (4/4, steady), first downbeat 1.308 s, 55 bars. bar 1 = first detected downbeat; with low phase confidence the bar COUNT is right but 'beat 1' may really be beat 2-4.
Tempo feel: analyzer 180.0 -> feels like **180.0 BPM** (high confidence; other readings [90.0]). Ask the person which tempo they tap.
Key A minor, -12.9 LUFS. Form: **A A' B C C' D D' D' C'**. Chord cycle: 16 bars. Role guess (heuristic): chase / last-man-standing (fast, driving).

Nobody has listened to this. Labels like drop/break are heuristics from energy; the person's ears decide.

## Hard points (in time order)
| time | bar:beat | % | kind | detail |
|---|---|---|---|---|
| 0:03.98 | 3:1.0 | 5.3 | **DROP** | +0.9 dB: full impact (+8.2 dB, one-shot 0.14 s) -> bass +0.8 dB, brightness +595 Hz |
| 0:03.98 | 3:1.03 | 5.3 | hit | full impact +8.2 dB (low +9.0, high +4.8), one-shot, level back in 0.14 s, +8.6 ms off the 16th grid |
| 0:10.64 | 8:1.0 | 14.2 | **DROP** | +3.1 dB: bass +4.0 dB, brightness -613 Hz |
| 0:21.31 | 16:1.0 | 28.4 | **DROP** | +2.4 dB: full impact (+10.7 dB, level stays up) -> bass +1.8 dB, brightness +201 Hz |
| 0:21.32 | 16:1.02 | 28.4 | hit | full impact +10.7 dB (low +24.0, high +5.1), level stays up (entrance), +7.0 ms off the 16th grid |
| 0:47.97 | 35:4.98 | 64.0 | hit | full impact +11.4 dB (low +14.4, high +11.2), one-shot, level back in 0.46 s, -6.1 ms off the 16th grid |
| 0:47.98 | 36:1.0 | 64.0 | **DROP** | +1.9 dB: full impact (+11.4 dB, one-shot 0.46 s) -> bass +1.5 dB, brightness +218 Hz |
| 0:53.31 | 40:1.0 | 71.1 | **DROP** | +1.9 dB: full impact (+12.7 dB, one-shot 1.78 s) -> bass +1.1 dB, brightness +304 Hz |
| 0:53.31 | 40:1.0 | 71.1 | hit | full impact +12.7 dB (low +14.7, high +16.1), one-shot, level back in 1.78 s, +0.6 ms off the 16th grid |
| 0:58.64 | 43:4.99 | 78.2 | hit | full impact +8.7 dB (low +12.5, high +4.8), one-shot, level back in 0.42 s, -4.4 ms off the 16th grid |
| 1:01.31 | 45:5.0 | 81.7 | hit | full impact +10.0 dB (low +15.9, high +4.5), one-shot, level back in 0.41 s, -1.0 ms off the 16th grid |
| 1:03.97 | 47:4.97 | 85.3 | hit | full impact +15.9 dB (low +20.4, high +13.6), level stays up (entrance), -9.3 ms off the 16th grid |
| 1:03.98 | 48:1.0 | 85.3 | **DROP** | +4.8 dB: full impact (+15.9 dB, level stays up) -> bass +4.2 dB, brightness +463 Hz |

Hits per minute 5.6, stops per minute 0.0, hits on the 16th grid 1.0, hits on beat 1 1.0, types {'full impact': 7, 'sub/kick impact': 0, 'crash/high burst': 0, 'accent': 0}.

## Sections
| bar | time | len | label | form | energy | key | layers entering / leaving |
|---|---|---|---|---|---|---|---|
| 1 | 0:01.31 | 2 bars | build | A | -6.8 dB | E major | - |
| 3 | 0:03.98 | 5 bars | build | A' | -6.1 dB | A minor | +sub 3dB |
| 8 | 0:10.64 | 6 bars | build | B | -3.2 dB | A minor | +sub 7dB, +bass 4dB |
| 14 | 0:18.64 | 10 bars | drop | C | -1.6 dB | A minor | +highmid 4dB |
| 24 | 0:31.98 | 8 bars | drop | C' | -0.6 dB | A minor | - |
| 32 | 0:42.65 | 4 bars | break | D | -10.4 dB | A minor | -sub 8dB, -bass 10dB, -lowmid 5dB, -mid 9dB, -highmid 9dB, -air 3dB |
| 36 | 0:47.98 | 4 bars | break | D' | -9.9 dB | A minor | +mid 4dB, +highmid 3dB |
| 40 | 0:53.31 | 8 bars | build | D' | -7.5 dB | A minor | +bass 3dB, +mid 5dB, +highmid 5dB, +air 5dB |
| 48 | 1:03.98 | 8 bars | drop | C' | -2.3 dB | A minor | +sub 13dB, +bass 6dB, +lowmid 4dB, +mid 7dB, +highmid 8dB, +air 8dB |

## Loop-readiness: NOT ready
- level jump at the seam: last 0.25 s -45 dB vs first 0.25 s -19 dB
- length is 55.27 bars from the first downbeat (+364 ms from a whole bar): a loop would drift off the grid
- a rip of a finished track is rarely loop-ready; your own render should pass this before you upload it

## Mid-range lead layer (vocal, lead synth or guitar; relative to this track): prominent in 24% of bars
none stands out

Tempo drift max 0.2%, no tempo change found.

## Bar map (energy relative to the loudest bar; marks = events inside the bar)
   1  0:01.31    -7.2 dB  #####################         
   2  0:02.64    -6.5 dB  ######################        
   3  0:03.98    -4.9 dB  #######################       **DROP** hit
   4  0:05.31    -7.5 dB  #####################         
   5  0:06.64    -5.5 dB  #######################       
   6  0:07.97    -6.7 dB  ######################        
   7  0:09.31    -5.7 dB  #######################       
   8  0:10.64    -3.5 dB  #########################     **DROP**
   9  0:11.98    -2.6 dB  ##########################    
  10  0:13.31    -2.2 dB  ##########################    
  11  0:14.64    -4.0 dB  ########################      
  12  0:15.98    -3.4 dB  #########################     
  13  0:17.31    -3.3 dB  #########################     
  14  0:18.64    -2.1 dB  ##########################    
  15  0:19.98    -5.4 dB  #######################       
  16  0:21.31    -1.1 dB  ###########################   **DROP** hit
  17  0:22.64    -0.9 dB  ###########################   
  18  0:23.98    -0.4 dB  ############################  
  19  0:25.31    -1.9 dB  ##########################    
  20  0:26.64    -1.6 dB  ###########################   
  21  0:27.98    -0.8 dB  ###########################   
  22  0:29.31    -0.5 dB  ############################  
  23  0:30.64    -1.6 dB  ###########################   
  24  0:31.98    -1.1 dB  ###########################   
  25  0:33.31    -0.3 dB  ############################  
  26  0:34.65     0.0 dB  ############################  
  27  0:35.98    -1.1 dB  ###########################   
  28  0:37.31    -0.8 dB  ###########################   
  29  0:38.65    -0.4 dB  ############################  
  30  0:39.98    -0.1 dB  ############################  
  31  0:41.31    -1.1 dB  ###########################   
  32  0:42.65    -6.0 dB  ######################        
  33  0:43.98   -13.1 dB  ################              
  34  0:45.31    -7.4 dB  #####################         
  35  0:46.65   -15.0 dB  ##############                hit
  36  0:47.98    -5.4 dB  #######################       **DROP**
  37  0:49.31   -13.4 dB  ###############               
  38  0:50.65    -6.3 dB  ######################        
  39  0:51.98   -14.4 dB  ###############               
  40  0:53.31    -5.1 dB  #######################       **DROP** hit
  41  0:54.65    -9.5 dB  ###################           
  42  0:55.98    -5.8 dB  #######################       
  43  0:57.31    -9.5 dB  ###################           hit
  44  0:58.65    -5.3 dB  #######################       
  45  0:59.98    -9.9 dB  ###################           hit
  46  1:01.31    -3.8 dB  ########################      
  47  1:02.65   -11.5 dB  #################             hit
  48  1:03.98    -1.5 dB  ###########################   **DROP**
  49  1:05.31    -1.2 dB  ###########################   
  50  1:06.65    -0.7 dB  ###########################   
  51  1:07.98    -2.4 dB  ##########################    
  52  1:09.31    -1.4 dB  ###########################   
  53  1:10.65    -1.0 dB  ###########################   
  54  1:11.98    -1.3 dB  ###########################   
  55  1:13.32    -8.7 dB  ####################          

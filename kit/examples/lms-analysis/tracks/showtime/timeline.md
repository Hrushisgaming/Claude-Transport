# Deep analysis: showtime

93.88 s, grid 176.98 BPM (4/4, steady), first downbeat 1.024 s, 68 bars. bar 1 = first detected downbeat; with low phase confidence the bar COUNT is right but 'beat 1' may really be beat 2-4.
Tempo feel: analyzer 177.0 -> feels like **177.0 BPM** (medium confidence; other readings [88.5]). Ask the person which tempo they tap.
Key G minor, -10.4 LUFS. Form: **A B C D B' E**. Chord cycle: no clear repeating cycle. Role guess (heuristic): chase / last-man-standing (fast, driving).

Nobody has listened to this. Labels like drop/break are heuristics from energy; the person's ears decide.

## Hard points (in time order)
| time | bar:beat | % | kind | detail |
|---|---|---|---|---|
| 0:04.39 | 3:2.93 | 4.7 | riser | +45.9 dB over 6.62 s (linearity 0.83) |
| 0:10.52 | 8:1.0 | 11.2 | **DROP** | +4.8 dB: riser +46 dB over 6.62 s -> full impact (+9.7 dB, one-shot 1.59 s) -> bass +5.5 dB, brightness +1344 Hz |
| 0:10.86 | 8:2.0 | 11.6 | hit | full impact +9.7 dB (low +13.4, high +11.0), one-shot, level back in 1.59 s, +1.2 ms off the 16th grid |
| 0:21.62 | 16:1.75 | 23.0 | STOP | cut 0.1 s, -17.5 dB, then full impact |
| 0:21.71 | 16:2.02 | 23.1 | hit | full impact +10.7 dB (low +12.9, high +13.0), level stays up (entrance), +7.8 ms off the 16th grid |
| 0:53.91 | 40:1.0 | 57.4 | **DROP** | +1.1 dB: full impact (+8.0 dB, one-shot 0.23 s) -> bass +2.2 dB, brightness -226 Hz |
| 0:54.26 | 40:2.01 | 57.8 | hit | full impact +8.0 dB (low +9.2, high +8.8), one-shot, level back in 0.23 s, +4.6 ms off the 16th grid |
| 1:17.30 | 57:1.99 | 82.3 | hit | full impact +19.8 dB (low +35.0, high +11.7), level stays up (entrance), -3.1 ms off the 16th grid |
| 1:18.32 | 58:1.0 | 83.4 | **DROP** | +6.3 dB: bass +5.8 dB, brightness -2129 Hz |

Hits per minute 2.6, stops per minute 0.6, hits on the 16th grid 1.0, hits on beat 1 0.0, types {'full impact': 4, 'sub/kick impact': 0, 'crash/high burst': 0, 'accent': 0}.

## Sections
| bar | time | len | label | form | energy | key | layers entering / leaving |
|---|---|---|---|---|---|---|---|
| 1 | 0:01.02 | 7 bars | intro | A | -10.0 dB | G major | - |
| 8 | 0:10.52 | 20 bars | drop | B | -2.9 dB | G minor | +sub 9dB, +bass 4dB, +mid 4dB, +highmid 3dB, +air 8dB |
| 28 | 0:37.64 | 12 bars | break | C | -3.3 dB | G minor | - |
| 40 | 0:53.91 | 9 bars | drop | D | -1.6 dB | B minor | - |
| 49 | 1:06.12 | 9 bars | drop | B' | -2.8 dB | G minor | - |
| 58 | 1:18.32 | 11 bars | outro | E | -5.7 dB | G minor | +sub 8dB, +bass 5dB, +lowmid 15dB, +mid 13dB, +highmid 8dB, +air 3dB |

## Loop-readiness: NOT ready
- ends with 2.8 s of fade/silence: a looping Sound would play that gap every cycle
- level jump at the seam: last 0.25 s -64 dB vs first 0.25 s -20 dB
- length is 68.47 bars from the first downbeat (+641 ms from a whole bar): a loop would drift off the grid
- a rip of a finished track is rarely loop-ready; your own render should pass this before you upload it

## Mid-range lead layer (vocal, lead synth or guitar; relative to this track): prominent in 26% of bars
bars 1-4 (0:01.02-0:06.45), bars 31-35 (0:41.71-0:48.49), bars 37-38 (0:49.84-0:52.56), bars 64-66 (1:26.46-1:30.53)

Tempo drift max 0.4%, no tempo change found.

## Bar map (energy relative to the loudest bar; marks = events inside the bar)
   1  0:01.02   -12.5 dB  ################              
   2  0:02.38   -10.8 dB  ##################            
   3  0:03.74   -11.4 dB  #################             riser
   4  0:05.09    -9.2 dB  ###################           
   5  0:06.45    -9.6 dB  ###################           
   6  0:07.80    -8.4 dB  ####################          
   7  0:09.16    -8.4 dB  ####################          
   8  0:10.52    -4.2 dB  ########################      **DROP** hit
   9  0:11.87    -3.1 dB  #########################     
  10  0:13.23    -3.1 dB  #########################     
  11  0:14.59    -2.5 dB  ##########################    
  12  0:15.94    -3.1 dB  #########################     
  13  0:17.30    -3.0 dB  #########################     
  14  0:18.65    -2.7 dB  #########################     
  15  0:20.01    -2.1 dB  ##########################    
  16  0:21.36    -3.7 dB  #########################     STOP hit
  17  0:22.72    -2.4 dB  ##########################    
  18  0:24.08    -2.5 dB  ##########################    
  19  0:25.43    -1.9 dB  ##########################    
  20  0:26.79    -2.1 dB  ##########################    
  21  0:28.14    -2.3 dB  ##########################    
  22  0:29.50    -2.0 dB  ##########################    
  23  0:30.86    -1.8 dB  ##########################    
  24  0:32.21    -3.1 dB  #########################     
  25  0:33.57    -4.8 dB  ########################      
  26  0:34.93    -3.4 dB  #########################     
  27  0:36.28    -4.0 dB  ########################      
  28  0:37.64    -3.1 dB  #########################     
  29  0:38.99    -3.9 dB  ########################      
  30  0:40.35    -3.0 dB  #########################     
  31  0:41.71    -3.2 dB  #########################     
  32  0:43.06    -1.9 dB  ##########################    
  33  0:44.42    -4.1 dB  ########################      
  34  0:45.77    -3.1 dB  #########################     
  35  0:47.13    -3.5 dB  #########################     
  36  0:48.49    -2.7 dB  #########################     
  37  0:49.84    -4.0 dB  ########################      
  38  0:51.20    -3.6 dB  #########################     
  39  0:52.55    -3.4 dB  #########################     
  40  0:53.91    -3.1 dB  #########################     **DROP** hit
  41  0:55.27    -1.7 dB  ##########################    
  42  0:56.62    -1.7 dB  ##########################    
  43  0:57.98    -1.3 dB  ###########################   
  44  0:59.34    -1.5 dB  ###########################   
  45  1:00.69    -1.6 dB  ###########################   
  46  1:02.05    -1.4 dB  ###########################   
  47  1:03.40    -1.0 dB  ###########################   
  48  1:04.76    -1.5 dB  ###########################   
  49  1:06.12    -1.1 dB  ###########################   
  50  1:07.47    -1.4 dB  ###########################   
  51  1:08.83    -0.7 dB  ###########################   
  52  1:10.18    -1.4 dB  ###########################   
  53  1:11.54    -1.6 dB  ###########################   
  54  1:12.90    -1.2 dB  ###########################   
  55  1:14.25    -1.0 dB  ###########################   
  56  1:15.61    -5.6 dB  #######################       
  57  1:16.96   -10.9 dB  ##################            hit
  58  1:18.32    -1.8 dB  ##########################    **DROP**
  59  1:19.68    -0.5 dB  ############################  
  60  1:21.03    -0.8 dB  ###########################   
  61  1:22.39    -0.5 dB  ############################  
  62  1:23.75    -1.6 dB  ###########################   
  63  1:25.10    -1.3 dB  ###########################   
  64  1:26.46    -1.0 dB  ###########################   
  65  1:27.81     0.0 dB  ############################  
  66  1:29.17    -1.7 dB  ##########################    
  67  1:30.53   -12.8 dB  ################              
  68  1:31.88   -40.3 dB                                

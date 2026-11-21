# Deep analysis: vigilante-shootdown

78.52 s, grid 120.02 BPM (4/4, steady), first downbeat 0.86 s, 39 bars. bar 1 = first detected downbeat; with low phase confidence the bar COUNT is right but 'beat 1' may really be beat 2-4.
Tempo feel: analyzer 120.0 -> feels like **120.0 BPM** (high confidence; other readings [60.0]). Ask the person which tempo they tap.
Key B minor, -9.5 LUFS. Form: **A B**. Chord cycle: 4 bars. Role guess (heuristic): tension / mid-intensity round music.

Nobody has listened to this. Labels like drop/break are heuristics from energy; the person's ears decide.

## Hard points (in time order)
| time | bar:beat | % | kind | detail |
|---|---|---|---|---|
| 0:06.86 | 4:1.0 | 8.7 | **DROP** | +2.8 dB: bass +3.3 dB, brightness +558 Hz |
| 1:13.03 | 37:1.36 | 93.0 | riser | +12.5 dB over 0.96 s (linearity 0.79) |

Hits per minute 0.0, stops per minute 0.0, hits on the 16th grid None, hits on beat 1 None, types {'full impact': 0, 'sub/kick impact': 0, 'crash/high burst': 0, 'accent': 0}.

## Sections
| bar | time | len | label | form | energy | key | layers entering / leaving |
|---|---|---|---|---|---|---|---|
| 1 | 0:00.86 | 3 bars | build | A | -6.1 dB | B minor | - |
| 4 | 0:06.86 | 36 bars | drop | B | -3.0 dB | B minor | +sub 18dB, +air 9dB |

## Loop-readiness: NOT ready
- ends with 3.4 s of fade/silence: a looping Sound would play that gap every cycle
- level jump at the seam: last 0.25 s -90 dB vs first 0.25 s -24 dB
- length is 38.84 bars from the first downbeat (-323 ms from a whole bar): a loop would drift off the grid
- a rip of a finished track is rarely loop-ready; your own render should pass this before you upload it

## Mid-range lead layer (vocal, lead synth or guitar; relative to this track): prominent in 38% of bars
bars 17-18 (0:32.85-0:36.85), bars 20-25 (0:38.85-0:50.85), bars 33-36 (1:04.85-1:12.85), bars 38-39 (1:14.85-1:18.85)

Tempo drift max 0.1%, no tempo change found.

## Bar map (energy relative to the loudest bar; marks = events inside the bar)
   1  0:00.86    -6.0 dB  ######################        
   2  0:02.86    -6.7 dB  ######################        
   3  0:04.86    -5.5 dB  #######################       
   4  0:06.86    -4.0 dB  ########################      **DROP**
   5  0:08.86    -2.6 dB  ##########################    
   6  0:10.86    -2.8 dB  #########################     
   7  0:12.86    -2.5 dB  ##########################    
   8  0:14.86    -2.2 dB  ##########################    
   9  0:16.86    -0.7 dB  ###########################   
  10  0:18.86    -0.6 dB  ###########################   
  11  0:20.86    -0.9 dB  ###########################   
  12  0:22.86    -0.8 dB  ###########################   
  13  0:24.86    -0.6 dB  ###########################   
  14  0:26.86    -0.6 dB  ###########################   
  15  0:28.86    -0.9 dB  ###########################   
  16  0:30.86    -0.6 dB  ###########################   
  17  0:32.85    -0.8 dB  ###########################   
  18  0:34.85    -0.8 dB  ###########################   
  19  0:36.85    -1.1 dB  ###########################   
  20  0:38.85    -0.6 dB  ###########################   
  21  0:40.85    -0.7 dB  ###########################   
  22  0:42.85    -0.5 dB  ############################  
  23  0:44.85    -0.8 dB  ###########################   
  24  0:46.85    -0.9 dB  ###########################   
  25  0:48.85    -0.5 dB  ############################  
  26  0:50.85     0.0 dB  ############################  
  27  0:52.85    -0.2 dB  ############################  
  28  0:54.85    -0.5 dB  ############################  
  29  0:56.85    -0.1 dB  ############################  
  30  0:58.85    -0.9 dB  ###########################   
  31  1:00.85    -1.0 dB  ###########################   
  32  1:02.85    -1.1 dB  ###########################   
  33  1:04.85    -1.8 dB  ##########################    
  34  1:06.85    -4.3 dB  ########################      
  35  1:08.85    -4.9 dB  #######################       
  36  1:10.85    -4.4 dB  ########################      
  37  1:12.85    -1.5 dB  ###########################   riser
  38  1:14.85   -13.9 dB  ###############               
  39  1:16.85   -46.4 dB                                

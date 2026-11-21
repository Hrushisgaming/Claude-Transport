"""make_known_track.py OUT.wav - a synthetic 120 BPM track with KNOWN hard points, used by selftest to prove the deep analyzer finds them (riser 12.0-15.7 s, cut 15.7-16.0, impact+drop 16.0, lead layer 24-32 s)."""
import numpy as np, wave, sys
sr=44100; bpm=120; beat=60/bpm; bar=4*beat; dur=34.0; n=int(dur*sr); rng=np.random.default_rng(1)
x=np.zeros(n)
def put(sig,t0,gain=1.0):
    i=int(t0*sr); j=min(n,i+len(sig)); x[i:j]+=gain*sig[:j-i]
def env_decay(L,tau): t=np.arange(int(L*sr))/sr; return np.exp(-t/tau)
def kick(): t=np.arange(int(.25*sr))/sr; f=50+110*np.exp(-t*30); return np.sin(2*np.pi*np.cumsum(f)/sr)*np.exp(-t/.07)
def hat(): s=rng.standard_normal(int(.05*sr)); s=np.diff(s,prepend=0); return s*env_decay(.05,.012)*0.5
def pad(freqs,L): t=np.arange(int(L*sr))/sr; return sum(np.sin(2*np.pi*f*t) for f in freqs)/len(freqs)
chords=[[110,164.8,220],[98,146.8,196],[87.3,130.8,174.6],[98,146.8,196]]       # 4-bar cycle
# quiet intro bars 1-4 (0-8 s): pad + hats
for b in range(0,4): put(pad(chords[b%4],bar)*np.hanning(int(bar*sr))**.3,b*bar,0.10)
for k in range(0,int(8/(beat/2))): put(hat(),k*beat/2,0.25)
# bars 5-8 (8-16 s): + kicks on beats, pad louder
for b in range(4,8): put(pad(chords[b%4],bar)*np.hanning(int(bar*sr))**.3,b*bar,0.16)
for k in range(0,int(8/(beat/2))): put(hat(),(8+k*beat/2)-0.0 if False else k*beat/2,0.0)
for k in range(int(8/beat),int(16/beat)): put(kick(),k*beat,0.5)
for k in range(int(8/(beat/2)),int(16/(beat/2))): put(hat(),k*beat/2,0.25)
# riser 12.0-15.7: filtered noise sweeping up, rising level  (HF rises faster than total)
L=3.7; t=np.arange(int(L*sr))/sr; noise=rng.standard_normal(len(t)); from scipy.signal import butter, sosfilt
out=np.zeros(len(t)); 
for seg in range(37):
    a=int(seg*0.1*sr); b=int((seg+1)*0.1*sr); fc=500+7000*(seg/36)**1.5; sos=butter(2,[fc*0.7/(sr/2),min(0.99,fc*1.3/(sr/2))],'band',output='sos'); out[a:b]=sosfilt(sos,noise[a:b])
out*=np.linspace(0.05,0.7,len(t))**1.2; put(out,12.0,0.9)
# hard STOP 15.7-16.0: silence (cut everything)
x[int(15.7*sr):int(16.0*sr)]=0
# IMPACT + DROP at 16.0 (bar 9): boom + noise, then full groove loud
t=np.arange(int(1.6*sr))/sr; boom=np.sin(2*np.pi*(40+60*np.exp(-t*6))*t)*np.exp(-t/.5); nz=rng.standard_normal(len(t))*np.exp(-t/.35)*0.5; put(boom+nz,16.0,0.9)
for b in range(8,16): put(pad(chords[b%4],bar)*np.hanning(int(bar*sr))**.3,b*bar,0.22)
for k in range(int(16/beat),int(32/beat)): put(kick(),k*beat,0.8)
for k in range(int(16/(beat/2)),int(32/(beat/2))): put(hat(),k*beat/2,0.3)
for k in range(int(16/beat),int(32/beat)):                           # saw bass on offbeats
    tt=np.arange(int(.2*sr))/sr; put(np.sign(np.sin(2*np.pi*55*tt))*np.exp(-tt/.12)*0.25,k*beat+beat/2)
# mid-range LEAD layer enters bar 13 (24 s) to 32 s: vibrato tone 440-880 Hz with harmonics
t=np.arange(int(8*sr))/sr; f0=523*(1+0.01*np.sin(2*np.pi*5.5*t)); lead=sum(np.sin(2*np.pi*np.cumsum(f0*h)/sr)/h for h in (1,2,3,4))*0.25; put(lead,24.0,0.5)
# outro 32-34 s fade
x[int(32*sr):]*=np.linspace(1,0,n-int(32*sr))
x=x/np.max(np.abs(x))*0.9
st=np.stack([x,x],1); pcm=(st*32767).astype('<i2')
with wave.open(sys.argv[1],'wb') as w: w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes(pcm.tobytes())
print("TRUTH: drop+impact at 16.0 s (bar 9 if bar1 at 0), stop 15.7-16.0, riser 12.0-15.7, lead layer 24-32 s, chord cycle 4 bars, section change at 8 s and 16 s, fade-out 32-34 s, 120 BPM")

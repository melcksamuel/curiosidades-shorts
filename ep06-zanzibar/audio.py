import numpy as np, json, subprocess, sys
from scipy.io import wavfile
from scipy.signal import lfilter
sys.path.insert(0,'.')
SR=44100
D=json.load(open('aud/durs.json')); W=[json.load(open(f'aud/n{i}.json')) for i in range(len(D))]
starts=np.concatenate([[0],np.cumsum(D)[:-1]]); TOT=sum(D); N=int(TOT*SR)+SR
def wt(i,w,n=0):
    k=0
    for a,b,x in W[i]:
        if x.lower().strip('.,!?…:')==w:
            if k==n: return starts[i]+a
            k+=1
    return starts[i]
rng=np.random.default_rng(1)
# voz
voice=np.zeros(N)
for i in range(len(D)):
    raw=subprocess.check_output(['ffmpeg','-v','error','-i',f'aud/n{i}.mp3','-f','s16le','-ac','1','-ar',str(SR),'-'])
    v=np.frombuffer(raw,np.int16)/32768.0; s=int(starts[i]*SR); voice[s:s+len(v)]+=v[:N-s]
def add(buf,sig,t,g=1.0):
    s=int(t*SR); e=min(N,s+len(sig)); 
    if s<N: buf[s:e]+=sig[:e-s]*g
def env(n,a=0.005,d=0.3):
    t=np.arange(n)/SR; return np.minimum(1,t/a)*np.exp(-t/d)
def kick(): n=int(.4*SR); t=np.arange(n)/SR; f=45+90*np.exp(-t*30); return np.sin(2*np.pi*np.cumsum(f)/SR)*env(n,.002,.18)
def snare(g=1): n=int(.25*SR); t=np.arange(n)/SR; return (rng.standard_normal(n)*0.7+np.sin(2*np.pi*190*t)*0.4)*env(n,.001,.07)*g
def pluck(f,dur=.6):
    n=int(dur*SR); p=int(SR/f); buf=rng.uniform(-1,1,p); out=np.zeros(n)
    for k in range(n):
        out[k]=buf[k%p]; buf[k%p]=0.5*(buf[k%p]+buf[(k+1)%p])*0.996
    return out*env(n,.002,dur*0.6)
def boom():
    n=int(1.4*SR); t=np.arange(n)/SR; f=38+60*np.exp(-t*8)
    return (np.sin(2*np.pi*np.cumsum(f)/SR)*0.9+lfilter([0.05],[1,-0.95],rng.standard_normal(n))*0.6)*env(n,.003,.45)
def whoosh(): n=int(.45*SR); t=np.arange(n)/SR; x=lfilter([0.08],[1,-0.92],rng.standard_normal(n)); return x*np.sin(np.pi*t/.45)**2*1.5
def popf(): n=int(.12*SR); t=np.arange(n)/SR; return np.sin(2*np.pi*(900-3000*t)*t)*env(n,.001,.03)
def tick(): n=int(.05*SR); return rng.standard_normal(n)*env(n,.0005,.006)*0.8
def splash(): n=int(1.2*SR); x=lfilter([0.2],[1,-0.6],rng.standard_normal(n)); t=np.arange(n)/SR; return x*env(n,.01,.35)*(1+0.5*np.sin(2*np.pi*6*t))
def crash(): n=int(1.5*SR); x=rng.standard_normal(n); return lfilter([0.3],[1,-0.3],x)*env(n,.002,.4)+boom()[:n]*0.6 if False else lfilter([0.3],[1,-0.3],x)*env(n,.002,.4)+np.pad(boom(),(0,n))[:n]*0.6
# música: marcha tensa em ré menor, 112 bpm
bpm=112; beat=60/bpm; music=np.zeros(N)
notes={'D':146.8,'F':174.6,'A':220.0,'C':261.6,'Bb':233.1,'G':196.0,'E':164.8}
prog=[['D','F','A','F'],['Bb','D','F','D'],['C','E','G','E'],['A','C','E','C']]
sec=lambda t: 'calm' if starts[7]<=t<starts[8] else ('war' if starts[5]<=t<starts[7] else 'full')
nb=int(TOT/beat)+1
pl_cache={}
for b in range(nb):
    t=b*beat; s=sec(t); bar=b//4; ch=prog[bar%4]
    if s!='calm':
        if b%2==0: add(music,kick(),t,0.9 if s=='war' else 0.7)
        add(music,snare(),t+beat*0.5,0.25)
        if b%4==3: 
            for r in range(4): add(music,snare(),t+beat*0.5+r*beat/8,0.15+0.05*r)
        if s=='war': add(music,snare(),t,0.3); add(music,boom()[:int(.6*SR)],t,0.25) if b%4==0 else None
    else:
        if b%4==0: add(music,kick(),t,0.5)
    for k in range(2):
        nm=ch[(b*2+k)%4]; f=notes[nm]*(2 if s!='calm' else 1)
        if f not in pl_cache: pl_cache[f]=pluck(f,.5)
        add(music,pl_cache[f],t+k*beat/2,0.35 if s!='calm' else 0.25)
    if b%4==0:
        f0=notes[ch[0]]/2; n=int(beat*4*SR); tt=np.arange(n)/SR
        dr=(np.sin(2*np.pi*f0*tt)+0.4*np.sin(2*np.pi*f0*1.5*tt))*np.minimum(1,tt/.3)*np.minimum(1,(beat*4-tt)/.3)
        add(music,dr,t,0.22)
# sfx
sfx=np.zeros(N)
add(sfx,boom(),starts[0]+0.25,1.0)
for i in range(1,len(D)): add(sfx,whoosh(),starts[i]-0.05,0.8)
for t in [0.05,wt(0,'durou'),starts[1]+0.05,wt(2,'declara'),wt(2,'khalid'),wt(3,'ultimato')-0.1,wt(3,'nove'),wt(4,'quase'),wt(4,'canhões'),wt(4,'iate'),
          wt(5,'ninguém'),wt(7,'quarenta'),wt(7,'quinhentos'),wt(7,'britânico')-0.6,wt(8,'fugiu'),wt(8,'absurdo'),wt(8,'conta'),wt(9,'você'),wt(9,'comenta')]:
    add(sfx,popf(),t,0.7)
add(sfx,boom(),wt(1,'sultão'),0.7)
for k in range(16): add(sfx,tick(),starts[5]+0.05+k*0.25,0.6)
tf=wt(5,'fogo')
t=tf
while t<starts[6]:
    add(sfx,boom(),t,0.9); add(sfx,boom(),t+0.35,0.7); t+=0.8
add(sfx,splash(),wt(6,'afunda'),1.0); add(sfx,crash(),wt(6,'chamas'),1.0); add(sfx,boom(),wt(6,'desaba'),0.8)
for k in range(12): add(sfx,tick(),starts[0]+0.3+k*0.33,0.4)
# ducking
venv=lfilter([0.002],[1,-0.998],np.abs(voice)); venv=venv/ (venv.max()+1e-9)
duck=1-0.55*np.clip(venv*3,0,1)
mix=voice*1.0+music*0.2*duck+sfx*0.35
mix=np.tanh(mix*1.1)
mix=mix/np.abs(mix).max()*10**(-3/20)
fade=int(0.6*SR); mix[int(TOT*SR)-fade:int(TOT*SR)]*=np.linspace(1,0.3,fade)
mix=mix[:int(TOT*SR)]
wavfile.write('aud/mix.wav',SR,(mix*32767).astype(np.int16))
print('ok',TOT)

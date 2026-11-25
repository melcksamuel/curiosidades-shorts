import numpy as np, json, subprocess
from scipy.io import wavfile
from scipy.signal import lfilter
SR=44100
D=json.load(open('aud/durs.json')); W=[json.load(open(f'aud/n{i}.json')) for i in range(len(D))]
starts=np.concatenate([[0],np.cumsum(D)[:-1]]); TOT=sum(D); N=int(TOT*SR)+SR
def wt(i,w,n=0):
    k=0
    for a,b,x in W[i]:
        if x.lower().strip('.,!?…:')==w:
            if k==n: return starts[i]+a
            k+=1
    print('MISSING',i,w); return starts[i]
rng=np.random.default_rng(7)
voice=np.zeros(N)
for i in range(len(D)):
    raw=subprocess.check_output(['ffmpeg','-v','error','-i',f'aud/n{i}.mp3','-f','s16le','-ac','1','-ar',str(SR),'-'])
    v=np.frombuffer(raw,np.int16)/32768.0; s=int(starts[i]*SR); voice[s:s+len(v)]+=v[:N-s]
def add(buf,sig,t,g=1.0):
    s=int(t*SR); e=min(N,s+len(sig))
    if 0<=s<N: buf[s:e]+=sig[:e-s]*g
def env(n,a=0.005,d=0.3):
    t=np.arange(n)/SR; return np.minimum(1,t/a)*np.exp(-t/d)
def kick(): n=int(.35*SR); t=np.arange(n)/SR; f=50+80*np.exp(-t*35); return np.sin(2*np.pi*np.cumsum(f)/SR)*env(n,.002,.14)
def snap(): n=int(.12*SR); return lfilter([1,-1],[1],rng.standard_normal(n))*env(n,.0005,.02)*0.5
def marimba(f,dur=.45):
    n=int(dur*SR); t=np.arange(n)/SR
    return (np.sin(2*np.pi*f*t)+0.35*np.sin(2*np.pi*f*4*t)*np.exp(-t*30))*env(n,.002,.18)
def boom():
    n=int(1.3*SR); t=np.arange(n)/SR; f=38+60*np.exp(-t*8)
    return (np.sin(2*np.pi*np.cumsum(f)/SR)*0.9+lfilter([0.05],[1,-0.95],rng.standard_normal(n))*0.5)*env(n,.003,.4)
def whoosh(): n=int(.4*SR); t=np.arange(n)/SR; x=lfilter([0.08],[1,-0.92],rng.standard_normal(n)); return x*np.sin(np.pi*t/.4)**2*1.4
def popf(): n=int(.12*SR); t=np.arange(n)/SR; return np.sin(2*np.pi*(900-3000*t)*t)*env(n,.001,.03)
def squeak(): # caneta no quadro
    n=int(.35*SR); t=np.arange(n)/SR; f=2200+400*np.sin(2*np.pi*7*t)
    x=np.sin(2*np.pi*np.cumsum(f)/SR)*0.15+lfilter([0.3],[1,-0.5],rng.standard_normal(n))*0.25
    return x*np.sin(np.pi*t/.35)
def gulp():
    out=np.zeros(int(1.0*SR))
    for k in range(3):
        n=int(.18*SR); t=np.arange(n)/SR; f=300-200*t/.18
        s=np.sin(2*np.pi*np.cumsum(f)/SR)*env(n,.005,.06)
        o=int(k*.3*SR); out[o:o+n]+=s
    return out
def bleh():
    n=int(.7*SR); t=np.arange(n)/SR; f=110+30*np.sin(2*np.pi*9*t)
    return (np.sign(np.sin(2*np.pi*np.cumsum(f)/SR))*0.3)*np.sin(np.pi*t/.7)
def ding():
    n=int(1.6*SR); t=np.arange(n)/SR
    return sum(np.sin(2*np.pi*f*t)*a for f,a in [(1046,1),(1568,.5),(2093,.3)])*env(n,.002,.5)*0.6
bpm=104; beat=60/bpm; music=np.zeros(N)
majC=[261.6,293.7,329.6,392.0,440.0,523.3]
minA=[220.0,261.6,293.7,329.6,392.0,440.0]
pat=[0,2,4,2,3,1,5,3]
nb=int(TOT/beat)+1
for b in range(nb):
    t=b*beat
    tense = starts[5]<=t<starts[8]
    sc=minA if tense else majC
    if b%2==0: add(music,kick(),t,0.6 if not tense else 0.8)
    if not tense: add(music,snap(),t+beat,0.6) if b%2==0 else None
    for k in range(2):
        idx=pat[(b*2+k)%8]; f=sc[idx]*(1 if tense else 2)
        add(music,marimba(f),t+k*beat/2,0.4 if not tense else 0.3)
    if b%4==0:
        f0=sc[0]/2; n=int(beat*4*SR); tt=np.arange(n)/SR
        pad=(np.sin(2*np.pi*f0*tt)+0.5*np.sin(2*np.pi*f0*1.5*tt))*np.minimum(1,tt/.3)*np.minimum(1,(beat*4-tt)/.3)
        add(music,pad,t,0.18 if not tense else 0.28)
sfx=np.zeros(N)
add(sfx,boom(),starts[0]+0.15,1.0)
for i in range(1,len(D)): add(sfx,whoosh(),starts[i]-0.05,0.7); add(sfx,squeak(),starts[i]+0.3,0.5)
add(sfx,gulp(),wt(0,'bebeu'),0.8); add(sfx,boom(),wt(0,'nobel'),0.7); add(sfx,ding(),wt(0,'nobel'),0.6)
for t in [wt(1,'1984'),wt(1,'estresse'),wt(1,'ácido'),wt(2,'nenhuma'),wt(3,'barry'),wt(3,'robin'),wt(3,'espiral'),wt(4,'ninguém'),wt(4,'porquinhos'),
          wt(5,'1984'),wt(5,'esposa'),wt(6,'dias'),wt(7,'oitavo'),wt(7,'inflamado'),wt(8,'helicobacter'),wt(8,'antibiótico'),wt(9,'2005'),wt(9,'você'),wt(9,'siga')]:
    add(sfx,popf(),t,0.7)
add(sfx,boom(),wt(4,'falhou'),0.6)
add(sfx,gulp(),wt(5,'bebeu'),1.0)
add(sfx,bleh(),wt(6,'vômito'),0.5)
add(sfx,boom(),wt(7,'cheio'),0.7)
add(sfx,ding(),wt(9,'nobel'),0.8); add(sfx,boom(),wt(9,'nobel'),0.6)
venv=lfilter([0.002],[1,-0.998],np.abs(voice)); venv=venv/(venv.max()+1e-9)
duck=1-0.55*np.clip(venv*3,0,1)
mix=voice*1.0+music*0.2*duck+sfx*0.35
mix=np.tanh(mix*1.1); mix=mix/np.abs(mix).max()*10**(-3/20)
fade=int(0.6*SR); mix[int(TOT*SR)-fade:int(TOT*SR)]*=np.linspace(1,0.3,fade)
mix=mix[:int(TOT*SR)]
wavfile.write('aud/mix.wav',SR,(mix*32767).astype(np.int16))
print('ok',TOT)

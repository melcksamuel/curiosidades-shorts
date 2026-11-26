# Trilha procedural bem baixa (pulso suave) + SFX de caneta/pop/impacto. Voz em primeiro plano.
import numpy as np, json, subprocess
from scipy.io import wavfile
from scipy.signal import lfilter
SR=44100
D=json.load(open('aud/durs.json'))
def load_words(i):
    out=[]
    for a,b,x in json.load(open(f'aud/n{i}.json')):
        ps=x.split(); st=(b-a)/len(ps); out+=[[a+k*st,a+(k+1)*st,p] for k,p in enumerate(ps)]
    return out
W=[load_words(i) for i in range(len(D))]
starts=np.concatenate([[0],np.cumsum(D)[:-1]]); TOT=sum(D); N=int(TOT*SR)+SR
def wt(i,w,n=0):
    k=0
    for a,b,x in W[i]:
        if x.lower().strip('.,!?…:;')==w:
            if k==n: return starts[i]+a
            k+=1
    print('MISSING',i,w); return starts[i]
rng=np.random.default_rng(11)
voice=np.zeros(N)
for i in range(len(D)):
    raw=subprocess.check_output(['ffmpeg','-v','error','-i',f'aud/n{i}.mp3','-f','s16le','-ac','1','-ar',str(SR),'-'])
    v=np.frombuffer(raw,np.int16)/32768.0; s=int(starts[i]*SR); voice[s:s+len(v)]+=v[:N-s]
def add(buf,sig,t,g=1.0):
    s=int(t*SR); e=min(N,s+len(sig))
    if 0<=s<N: buf[s:e]+=sig[:e-s]*g
def env(n,a=0.003,d=0.2):
    t=np.arange(n)/SR; return np.minimum(1,t/a)*np.exp(-t/d)
def pop(): n=int(.1*SR); t=np.arange(n)/SR; return np.sin(2*np.pi*(700-2500*t)*t)*env(n,.001,.03)
def tick(): n=int(.05*SR); return lfilter([1,-1],[1],rng.standard_normal(n))*env(n,.0005,.01)*0.5
def pen(): n=int(.22*SR); t=np.arange(n)/SR; x=lfilter([0.5],[1,-0.7],rng.standard_normal(n)); return x*np.sin(np.pi*t/.22)**2*0.5
def thud(): n=int(.5*SR); t=np.arange(n)/SR; f=60+80*np.exp(-t*25); return np.sin(2*np.pi*np.cumsum(f)/SR)*env(n,.002,.12)
def brrr(dur=0.9):
    out=np.zeros(int(dur*SR)); k=0
    while k*0.055<dur:
        n=int(.03*SR); b=rng.standard_normal(n)*env(n,.0005,.008); o=int(k*0.055*SR); out[o:o+n]+=b[:len(out)-o]; k+=1
    return out*0.8
def clack(): n=int(.15*SR); return (rng.standard_normal(n)*env(n,.0005,.012)+np.sin(2*np.pi*180*np.arange(n)/SR)*env(n,.001,.05))*0.8
def ding(): n=int(1.2*SR); t=np.arange(n)/SR; return (np.sin(2*np.pi*1318*t)+0.4*np.sin(2*np.pi*2636*t))*env(n,.002,.4)*0.5
def haha():
    out=np.zeros(int(.9*SR))
    for k in range(4):
        n=int(.12*SR); t=np.arange(n)/SR; f=320+60*np.sin(2*np.pi*8*t)+20*k
        out[int(k*.2*SR):int(k*.2*SR)+n]+=np.sign(np.sin(2*np.pi*np.cumsum(f)/SR))*0.25*np.sin(np.pi*t/.12)
    return out
def tickt(): n=int(.04*SR); return np.sin(2*np.pi*1500*np.arange(n)/SR)*env(n,.0005,.01)*0.6
# música: pulso suave em Ré menor, 84 bpm, bem discreta
bpm=84; bt=60/bpm; music=np.zeros(N)
roots=[146.8,116.5,130.8,110.0]
for b in range(int(TOT/bt)+1):
    t=b*bt; r=roots[(b//4)%4]
    n=int(bt*SR); tt=np.arange(n)/SR
    add(music,(np.sin(2*np.pi*r*tt)+0.3*np.sin(2*np.pi*r*2*tt))*np.minimum(1,tt/.02)*np.exp(-tt/.35)*0.5,t,1.0)
    if b%2==1: add(music,tick(),t,0.35)
    if b%4==0:
        pad=(np.sin(2*np.pi*r*2*tt[:int(4*bt*SR)] if False else 0)) if False else None
sfx=np.zeros(N)
# calendários: tick + pop
for (i,w) in [(1,'dia'),(3,'dia'),(4,'dia'),(6,'dia'),(7,'dia')]: add(sfx,tickt(),wt(i,w),0.9); add(sfx,pop(),wt(i,w)+0.05,0.6)
for (i,w,n) in [(0,'1932',0),(0,'austrália',0),(0,'guerra',0),(1,'vinte',0),(2,'três',0),(2,'duas',0),(2,'dez',0),(7,'986',0),(7,'contestado',0),(8,'saldo',0),(8,'nenhum',0),(8,'orgulho',0),(9,'cercas',0),(9,'siga',0)]:
    add(sfx,pop(),wt(i,w,n),0.7); add(sfx,pen(),wt(i,w,n)-0.05,0.5)
add(sfx,thud(),wt(0,'guerra'),0.8); add(sfx,thud(),wt(0,'perdeu'),1.0)
add(sfx,brrr(0.7),wt(2,'balas')-0.1,0.45)
add(sfx,brrr(0.5),wt(3,'acertar')-0.2,0.4)
add(sfx,brrr(0.5),wt(4,'metralhadora')+0.1,0.45); add(sfx,clack(),wt(4,'travou'),0.9); add(sfx,thud(),wt(4,'travou'),0.6)
add(sfx,haha(),wt(5,'riram')-0.1,0.6)
add(sfx,ding(),wt(5,'medalhas'),0.5)
add(sfx,thud(),wt(7,'fim'),0.9)
add(sfx,thud(),wt(9,'afinal'),0.4)
venv=lfilter([0.002],[1,-0.998],np.abs(voice)); venv=venv/(venv.max()+1e-9)
duck=1-0.6*np.clip(venv*3,0,1)
mix=voice*1.0+music*0.10*duck+sfx*0.28
mix=np.tanh(mix*1.8); mix=mix/np.abs(mix).max()*10**(-3/20)
fade=int(0.5*SR); mix[int(TOT*SR)-fade:int(TOT*SR)]*=np.linspace(1,0.3,fade)
mix=mix[:int(TOT*SR)]
wavfile.write('aud/mix.wav',SR,(mix*32767).astype(np.int16)); print('ok',TOT)

# Trilha procedural bem baixa (pulso suave) + SFX de caneta/pop/impacto. Voz em primeiro plano.
import numpy as np, json, subprocess, sys
sys.path.insert(0,'.')
from shots import whips
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
roots=[110.0,87.3,98.0,82.4]
for b in range(int(TOT/bt)+1):
    t=b*bt; r=roots[(b//4)%4]
    n=int(bt*SR); tt=np.arange(n)/SR
    add(music,(np.sin(2*np.pi*r*tt)+0.3*np.sin(2*np.pi*r*2*tt))*np.minimum(1,tt/.02)*np.exp(-tt/.35)*0.5,t,1.0)
    if b%2==1: add(music,tick(),t,0.35)
    if b%4==0:
        pad=(np.sin(2*np.pi*r*2*tt[:int(4*bt*SR)] if False else 0)) if False else None
sfx=np.zeros(N)
def slosh(dur=1.2):
    n=int(dur*SR); t=np.arange(n)/SR
    x=lfilter([0.02],[1,-0.98],rng.standard_normal(n))
    return x*np.sin(np.pi*t/dur)*(1+0.5*np.sin(2*np.pi*3*t))*6
def drip(): n=int(.12*SR); t=np.arange(n)/SR; return np.sin(2*np.pi*(400+1600*t/.12)*t)*env(n,.001,.04)*0.6
def tok(): return tickt()
def hiss(dur=1.0):
    n=int(dur*SR); t=np.arange(n)/SR
    x=lfilter([1,-1],[1],rng.standard_normal(n))*0.25
    return x*np.minimum(1,t/0.05)*np.minimum(1,(dur-t)/0.2)
def bubbles(dur=1.5):
    out=np.zeros(int(dur*SR))
    for k in range(int(dur*14)):
        n=int(.04*SR); tt=np.arange(n)/SR; f=600+900*rng.random()
        b=np.sin(2*np.pi*(f+f*3*tt/.04)*tt)*env(n,.001,.012); o=int(rng.random()*(dur-.05)*SR); out[o:o+n]+=b
    return out*0.5
def beat(): n=int(.35*SR); t=np.arange(n)/SR; return (np.sin(2*np.pi*55*t)*env(n,.003,.07)+0.6*np.sin(2*np.pi*50*(t-.16))*env(n,.003,.07)*(t>.16))
def flat(dur=1.4): n=int(dur*SR); t=np.arange(n)/SR; return np.sin(2*np.pi*1000*t)*np.minimum(1,t/.01)*np.minimum(1,(dur-t)/.1)*0.25
def bleep(): n=int(.08*SR); t=np.arange(n)/SR; return np.sin(2*np.pi*1000*t)*env(n,.002,.04)*0.4
for (i,w,n) in [(0,'1386',0),(0,'porco',0),(0,'preso',0),(1,'crime',0),(1,'bebê',0),(1,'tribunal',0),(2,'relatos',0),(2,'vestido',0),(2,'multidão',0),
                (3,'carrasco',0),(3,'luvas',0),(4,'piada',0),(4,'200',0),(5,'século',0),(5,'ratos',0),(5,'advogado',0),(6,'defesa',0),(6,'gatos',0),
                (7,'1587',0),(7,'besouros',0),(7,'insetos',0),(8,'vila',0),(8,'terreno',0),(8,'terra',0),(9,'veredito',0),(9,'você',0),(9,'siga',0)]:
    add(sfx,pop(),wt(i,w,n),0.6); add(sfx,pen(),wt(i,w,n)-0.05,0.45)
add(sfx,thud(),wt(0,'1386'),0.9)
add(sfx,clack(),wt(0,'preso'),0.9)
add(sfx,thud(),starts[0]+3.9,1.0); add(sfx,clack(),starts[0]+3.9,0.8)
add(sfx,thud(),wt(0,'condenado'),1.0)
add(sfx,thud(),wt(1,'assassinato'),1.0)
for k in range(10): add(sfx,tickt(),wt(2,'multidão')+k*0.09,0.3)
add(sfx,ding(),wt(3,'luvas'),0.4)
for k in range(8): add(sfx,tickt(),starts[4]+1.5+k*0.14,0.5)
add(sfx,thud(),wt(4,'animais'),0.6)
for k in range(10): add(sfx,tickt(),wt(5,'comeram')+k*0.11,0.35)
add(sfx,thud(),wt(5,'advogado'),0.9)
add(sfx,hiss(0.8),wt(6,'tinham'),0.5); add(sfx,thud(),wt(6,'gatos'),0.7)
for k in range(10): add(sfx,tickt(),wt(7,'atacaram')+k*0.12,0.35)
add(sfx,thud(),wt(7,'advogado'),0.9)
add(sfx,thud(),wt(8,'recusou'),1.0); add(sfx,thud(),wt(8,'demais'),0.8)
add(sfx,thud(),wt(9,'sumiu'),0.9)
add(sfx,haha(),wt(9,'porco'),0.4)
add(sfx,ding(),wt(9,'siga'),0.4)
def whoosh():
    n=int(.28*SR); t=np.arange(n)/SR
    x=lfilter([0.15],[1,-0.85],rng.standard_normal(n)); return x*np.sin(np.pi*t/.28)**2*2.2
# sem efeito sonoro nas transições/deslizes de câmera (pedido do Melck)
venv=lfilter([0.002],[1,-0.998],np.abs(voice)); venv=venv/(venv.max()+1e-9)
duck=1-0.6*np.clip(venv*3,0,1)
mix=voice*1.0+music*0.10*duck+sfx*0.12
mix=np.tanh(mix*1.8); mix=mix/np.abs(mix).max()*10**(-3/20)
fade=int(0.5*SR); mix[int(TOT*SR)-fade:int(TOT*SR)]*=np.linspace(1,0.3,fade)
mix=mix[:int(TOT*SR)]
wavfile.write('aud/mix.wav',SR,(mix*32767).astype(np.int16)); print('ok',TOT)

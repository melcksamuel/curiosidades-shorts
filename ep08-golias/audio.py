# Trilha chiptune procedural + SFX 8-bit
import numpy as np, json, subprocess
from scipy.io import wavfile
from scipy.signal import lfilter
SR=44100
D=json.load(open('aud/durs.json')); W=[json.load(open(f'aud/n{i}.json')) for i in range(len(D))]
for i in range(len(W)):
    o=[]
    for a,b,x in W[i]:
        ps=x.split()
        if len(ps)>1:
            st=(b-a)/len(ps); o+=[[a+k*st,a+(k+1)*st,p] for k,p in enumerate(ps)]
        else: o.append([a,b,x])
    W[i]=o
starts=np.concatenate([[0],np.cumsum(D)[:-1]]); TOT=sum(D); N=int(TOT*SR)+SR
def wt(i,w,n=0):
    k=0
    for a,b,x in W[i]:
        if x.lower().strip('.,!?…:')==w:
            if k==n: return starts[i]+a
            k+=1
    print('MISSING',i,w); return starts[i]
rng=np.random.default_rng(8)
voice=np.zeros(N)
for i in range(len(D)):
    raw=subprocess.check_output(['ffmpeg','-v','error','-i',f'aud/n{i}.mp3','-f','s16le','-ac','1','-ar',str(SR),'-'])
    v=np.frombuffer(raw,np.int16)/32768.0; s=int(starts[i]*SR); voice[s:s+len(v)]+=v[:N-s]
def add(buf,sig,t,g=1.0):
    s=int(t*SR); e=min(N,s+len(sig))
    if 0<=s<N: buf[s:e]+=sig[:e-s]*g
def env(n,a=0.003,d=0.2):
    t=np.arange(n)/SR; return np.minimum(1,t/a)*np.exp(-t/d)
def sq(f,dur,duty=0.5,d=0.15):
    n=int(dur*SR); t=np.arange(n)/SR; ph=(f*t)%1
    return np.where(ph<duty,1.0,-1.0)*env(n,.002,d)*0.5
def tri(f,dur):
    n=int(dur*SR); t=np.arange(n)/SR; ph=(f*t)%1
    return (4*np.abs(ph-0.5)-1)*np.minimum(1,(dur-t)/0.01)*0.7
def noise(dur,d=0.05,lp=None):
    n=int(dur*SR); x=rng.standard_normal(n)
    # ruído "8-bit": sample & hold
    x=np.repeat(x[::8],8)[:n]
    return x*env(n,.001,d)*0.5
def kick(): n=int(.2*SR); t=np.arange(n)/SR; f=40+180*np.exp(-t*40); ph=np.cumsum(f)/SR; return np.where(ph%1<.5,1,-1)*env(n,.001,.07)*0.8
def sweep(f0,f1,dur,duty=.5):
    n=int(dur*SR); f=np.linspace(f0,f1,n); ph=np.cumsum(f)/SR
    return np.where(ph%1<duty,1.0,-1.0)*np.minimum(1,(dur-np.arange(n)/SR)/.02)*0.4
def coin(): return np.concatenate([sq(988,.06,.5,1),sq(1319,.22,.5,.12)])
def blip(): return sq(1760,.05,.25,.03)
def boom():
    n=int(.9*SR); x=np.repeat(rng.standard_normal(n//16+1),16)[:n]
    return x*env(n,.001,.25)*0.9+kick()[:n].tolist().__len__()*0 if False else x*env(n,.001,.25)*0.9
def powerdown(): return sweep(880,110,1.2,.25)
def powerup(): return sweep(220,1320,.5,.5)
def jump(): return sweep(300,900,.18,.5)
def hit(): 
    n=int(.5*SR); x=np.repeat(rng.standard_normal(n//24+1),24)[:n]; return x*env(n,.001,.12)
def whoosh(): n=int(.3*SR); x=np.repeat(rng.standard_normal(n//4+1),4)[:n]; t=np.arange(n)/SR; return x*np.sin(np.pi*t/.3)**2*0.35
def fanfare():
    out=[]
    for f,d in [(523,.1),(659,.1),(784,.1),(1047,.45)]: out.append(sq(f,d,.5,.3))
    return np.concatenate(out)
# --- música: Lá menor "épico 8-bit", 132 bpm
bpm=132; bt=60/bpm; music=np.zeros(N)
prog=[(220.0,[440,523.3,659.3]),(174.6,[349.2,440,523.3]),(196.0,[392,493.9,587.3]),(164.8,[329.6,415.3,493.9])]
nb=int(TOT/bt)+1
calm=(starts[6],starts[8])  # arqueologia: mais esparso
for b in range(nb):
    t=b*bt; bar=(b//4)%4; root,ch=prog[bar]
    sparse = calm[0]<=t<calm[1]
    climax = starts[8]<=t<starts[9]
    if b%2==0 or climax: add(music,kick(),t,0.7)
    if not sparse:
        if b%2==1: add(music,noise(.12,.04),t,0.5)
        add(music,noise(.05,.012),t+bt/2,0.25)
    # baixo triangular em colcheias
    for k in range(2):
        add(music,tri(root/ (2 if k else 1),bt/2*0.9),t+k*bt/2,0.5 if not sparse else 0.35)
    # arpejo de pulso 12.5% em semicolcheias
    if not sparse or b%2==0:
        for k in range(4):
            f=ch[(b*4+k)%3]*(1 if not climax else 2)
            add(music,sq(f,bt/4*0.9,.125,.06),t+k*bt/4,0.22)
# melodia simples nas cenas 0,1,9
mel=[659.3,0,587.3,523.3,493.9,0,523.3,440]
for b in range(nb):
    t=b*bt
    if t<starts[2] or t>=starts[9]:
        f=mel[b%8]
        if f: add(music,sq(f,bt*0.8,.5,.25),t,0.18)
sfx=np.zeros(N)
add(sfx,boom(),0.05,0.9); add(sfx,fanfare(),0.1,0.25)
for i in range(1,len(D)): add(sfx,whoosh(),starts[i]-0.05,0.7)
for it in [(0,'metros'),(1,'samuel'),(1,'seis'),(2,'manuscritos'),(2,'antes'),(3,'quatro'),(4,'septuaginta'),(4,'josefo'),
              (5,'gigante'),(5,'couraça'),(6,'gate'),(6,'2005'),(6,'nomes'),(7,'três'),(9,'comenta'),(9,'siga'),(9,'metros',1)]:
    add(sfx,blip(),wt(*it),0.8)
add(sfx,hit(),wt(0,'não'),0.8)
add(sfx,coin(),wt(1,'quase'),0.6)
add(sfx,powerup(),wt(2,'rolo'),0.5)
add(sfx,powerdown(),wt(3,'quatro'),0.55)
add(sfx,coin(),wt(3,'dois'),0.6)
add(sfx,coin(),wt(4,'concordam'),0.6); add(sfx,hit(),wt(4,'dois'),0.6)
add(sfx,hit(),wt(5,'quilos'),0.7)
add(sfx,powerup(),wt(6,'caco'),0.5)
add(sfx,coin(),wt(7,'três'),0.6)
for k in range(6): add(sfx,sweep(400,600,.08,.25),wt(8,'davi')+k*0.12,0.3)
add(sfx,jump(),wt(8,'venceu'),0.7)
hitt=wt(8,'venceu')+0.45
add(sfx,boom(),hitt,1.0); add(sfx,hit(),hitt,0.9); add(sfx,fanfare(),hitt+0.5,0.5)
venv=lfilter([0.002],[1,-0.998],np.abs(voice)); venv=venv/(venv.max()+1e-9)
duck=1-0.55*np.clip(venv*3,0,1)
mix=voice*1.0+music*0.2*duck+sfx*0.3
mix=np.tanh(mix*2.0); mix=mix/np.abs(mix).max()*10**(-3/20)
fade=int(0.6*SR); mix[int(TOT*SR)-fade:int(TOT*SR)]*=np.linspace(1,0.3,fade)
mix=mix[:int(TOT*SR)]
wavfile.write('aud/mix.wav',SR,(mix*32767).astype(np.int16))
print('ok',TOT)

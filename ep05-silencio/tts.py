import os, certifi, json, asyncio, subprocess
certifi.where = lambda: os.path.expanduser("~/.ccr/ca-bundle.crt")
import edge_tts
from script import SCENES, VOICE
os.makedirs("aud",exist_ok=True)
async def one(name, spk, txt):
    v,r,p = VOICE[spk]
    c = edge_tts.Communicate(txt, v, rate=r, pitch=p, boundary="WordBoundary")
    words=[]
    with open(f"aud/{name}.mp3","wb") as f:
        async for ch in c.stream():
            if ch["type"]=="audio": f.write(ch["data"])
            elif ch["type"]=="WordBoundary":
                words.append([ch["offset"]/1e7,(ch["offset"]+ch["duration"])/1e7,ch["text"]])
    subprocess.run(["ffmpeg","-y","-loglevel","error","-i",f"aud/{name}.mp3","-ar","48000","-ac","1",f"aud/{name}.wav"],check=True)
    d=float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",f"aud/{name}.wav"]))
    return dict(name=name,spk=spk,text=txt,words=words,dur=d)
async def main():
    out=[]
    for i,sc in enumerate(SCENES):
        lines=[]
        for j,(s,t) in enumerate(sc):
            lines.append(await one(f"s{i}_{j}",s,t))
        out.append(lines)
    json.dump(out,open("aud/lines.json","w"),ensure_ascii=False,indent=1)
    tot=0
    for i,sc in enumerate(out):
        d=sum(l["dur"] for l in sc)+0.35*(len(sc)-1)
        print(i,round(d,2),[l["dur"] for l in sc]); tot+=d+0.25
    print("total",tot)
asyncio.run(main())

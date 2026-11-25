import os, certifi, json, asyncio, subprocess, sys
certifi.where = lambda: os.path.expanduser("~/.ccr/ca-bundle.crt")
import edge_tts
sys.path.insert(0,'.')
from script import LINES
async def one(i, txt):
    c = edge_tts.Communicate(txt, "pt-BR-FranciscaNeural", rate="+10%", boundary="WordBoundary")
    words=[]
    with open(f"aud/n{i}.mp3","wb") as f:
        async for ch in c.stream():
            if ch["type"]=="audio": f.write(ch["data"])
            elif ch["type"]=="WordBoundary":
                words.append([ch["offset"]/1e7,(ch["offset"]+ch["duration"])/1e7,ch["text"]])
    json.dump(words, open(f"aud/n{i}.json","w"), ensure_ascii=False)
async def main():
    await asyncio.gather(*[one(i,t) for i,t in enumerate(LINES)])
asyncio.run(main())
durs=[]
for i in range(len(LINES)):
    d=float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",f"aud/n{i}.mp3"]))
    durs.append(d+0.12 + (0.9 if i==len(LINES)-1 else 0))
json.dump(durs,open("aud/durs.json","w"))
print([round(d,2) for d in durs], round(sum(durs),2))

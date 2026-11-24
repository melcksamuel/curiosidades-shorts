import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
L = json.load(open(os.path.join(HERE, "aud/lines.json")))
GAP, TAIL, END = 0.3, 0.45, 1.3

SCENE_START, SCENE_DUR, LINES, WORDS = [], [], [], []
t = 0.0
for i, sc in enumerate(L):
    off = 0.0
    for j, l in enumerate(sc):
        ld = l["words"][-1][1] + 0.15
        toks = l["text"].split()
        ws = l["words"]
        if len(toks) != len(ws):
            toks = [w[2] for w in ws]
        words = [dict(a=t + off + w[0], b=t + off + w[1], txt=tok, spk=l["spk"], scene=i, line=len(LINES))
                 for w, tok in zip(ws, toks)]
        LINES.append(dict(scene=i, spk=l["spk"], start=t + off, end=t + off + ld, wav=os.path.join(HERE, "aud", l["name"] + ".wav"), words=words))
        WORDS.extend(words)
        off += ld + GAP
    d = off - GAP + TAIL + (END if i == len(L) - 1 else 0)
    SCENE_START.append(t); SCENE_DUR.append(d); t += d
TOTAL = t


def scene_at(T):
    for i in range(len(SCENE_START) - 1, -1, -1):
        if T >= SCENE_START[i]:
            return i
    return 0


def norm(s):
    import unicodedata
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in s if c.isalnum())


def wt(scene, word, nth=1):
    """absolute start time of the nth occurrence of word in a scene"""
    k = 0
    for w in WORDS:
        if w["scene"] == scene and norm(w["txt"]) == norm(word):
            k += 1
            if k == nth:
                return w["a"]
    raise KeyError((scene, word))


if __name__ == "__main__":
    for i in range(len(SCENE_START)):
        print(i, round(SCENE_START[i], 2), round(SCENE_DUR[i], 2))
    print("TOTAL", TOTAL)

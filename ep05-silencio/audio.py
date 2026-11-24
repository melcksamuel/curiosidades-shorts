"""Trilha ambiente + SFX procedurais + mix com ducking -> mix.wav"""
import numpy as np, math
from scipy.io import wavfile
from scipy.signal import lfilter, butter
from timeline import SCENE_START, SCENE_DUR, LINES, TOTAL, wt

SR = 48000
N = int((TOTAL + 0.5) * SR)
rng = np.random.default_rng(5)
t_all = np.arange(N) / SR


def S(i): return SCENE_START[i]


def lp(x, fc, order=2):
    b, a = butter(order, fc / (SR / 2), "low"); return lfilter(b, a, x)


def hp(x, fc, order=2):
    b, a = butter(order, fc / (SR / 2), "high"); return lfilter(b, a, x)


def add(buf, sig, t0, g=1.0):
    i = int(t0 * SR)
    if i < 0: sig = sig[-i:]; i = 0
    j = min(len(buf), i + len(sig))
    if j > i: buf[i:j] += sig[:j - i] * g


def mtof(m): return 440 * 2 ** ((m - 69) / 12)


# ---------- music ----------
music = np.zeros(N)
# energy curve per scene (pad level, keys density)
LEVEL = [0.55, 0.6, 0.75, 1.0, 0.55, 0.18, 0.85, 1.0, 1.0, 1.0]
KEYS = [0.3, 0.4, 0.6, 0.5, 0.0, 0.0, 0.8, 0.5, 1.0, 1.0]
lvl = np.zeros(N); kd = np.zeros(N)
for i in range(len(SCENE_START)):
    a, b = int(S(i) * SR), int((S(i) + SCENE_DUR[i]) * SR)
    lvl[a:b] = LEVEL[i]; kd[a:b] = KEYS[i]
lvl[int(SCENE_START[-1] * SR + SCENE_DUR[-1] * SR):] = 1
sm = np.exp(-1 / (0.5 * SR))
lvl = lfilter([1 - sm], [1, -sm], lvl)

# chords D maj7, B m7, G maj7, A sus2 (4s each)
CH = [[50, 57, 61, 64, 66], [47, 54, 57, 62, 66], [43, 50, 54, 59, 62], [45, 52, 57, 59, 64]]
CHLEN = 4.0
pad = np.zeros(N)
for c in range(int(TOTAL / CHLEN) + 2):
    t0 = c * CHLEN
    seg = int((CHLEN + 1.5) * SR)
    tt = np.arange(seg) / SR
    env = np.minimum(1, tt / 1.2) * np.clip((CHLEN + 1.5 - tt) / 1.5, 0, 1)
    sig = np.zeros(seg)
    for m in CH[c % 4]:
        f = mtof(m)
        for det in (-0.12, 0.12):
            ph = rng.uniform(0, 6.28)
            sig += np.sin(2 * np.pi * f * (1 + det / 100) * tt + ph) + 0.25 * np.sin(4 * np.pi * f * tt + ph)
    add(pad, sig * env, t0)
pad = lp(pad, 1800) / 12
# sub drone
drone = 0.35 * np.sin(2 * np.pi * mtof(38) * t_all) * (0.7 + 0.3 * np.sin(2 * np.pi * 0.1 * t_all))
music += (pad + drone * 0.5) * lvl

# soft keys (bell) arpeggio from chord tones
keys = np.zeros(N)
step = 0.5
for k in range(int(TOTAL / step)):
    t0 = k * step
    i = int(t0 * SR)
    if i >= N: break
    if rng.random() > kd[i] * 0.75: continue
    ch = CH[int(t0 / CHLEN) % 4]
    m = rng.choice(ch) + 12 * rng.choice([1, 2], p=[0.6, 0.4])
    f = mtof(m)
    dur = 2.2; tt = np.arange(int(dur * SR)) / SR
    env = np.exp(-tt * 2.4) * np.minimum(1, tt / 0.004)
    sig = (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * 2.01 * f * tt) * np.exp(-tt * 4) + 0.12 * np.sin(2 * np.pi * 3.0 * f * tt) * np.exp(-tt * 7)) * env
    add(keys, sig, t0, 0.16)
# simple reverb-ish echo
for d, g in ((0.23, 0.35), (0.41, 0.22), (0.67, 0.12)):
    keys[int(d * SR):] += keys[:-int(d * SR)] * g
music += keys
music /= np.max(np.abs(music)) + 1e-9

# ---------- sfx ----------
sfx = np.zeros(N)


def whoosh(d=0.6, f0=300, f1=3000):
    n = int(d * SR); tt = np.arange(n) / SR
    x = rng.standard_normal(n)
    env = np.sin(np.pi * tt / d) ** 2
    y = np.zeros(n); cut = np.linspace(f0, f1, n)
    # time-varying 1-pole lp
    yv = 0
    for k in range(0, n, 64):
        a = math.exp(-2 * math.pi * cut[k] / SR)
        seg = x[k:k + 64]
        out = lfilter([1 - a], [1, -a], seg, zi=[yv * a])[0]
        y[k:k + 64] = out; yv = out[-1]
    return y * env * 0.6


def chime(f=1568, d=2.0, g=1.0):
    tt = np.arange(int(d * SR)) / SR
    s = sum(np.sin(2 * np.pi * f * r * tt) * np.exp(-tt * (2 + 2 * q)) / (q + 1) for q, r in enumerate((1, 2.76, 5.4)))
    return s * g * 0.5


def shimmer(d=1.4):
    tt = np.arange(int(d * SR)) / SR
    x = hp(rng.standard_normal(len(tt)), 4000) * np.minimum(1, tt / d * 2) * np.exp(-np.maximum(0, tt - d / 2) * 4) * 0.25
    for k, f in enumerate((1175, 1480, 1760, 2349)):
        x[int(k * 0.07 * SR):] += chime(f, d)[:len(tt) - int(k * 0.07 * SR)] * 0.35
    return x


def rumble(d=1.2):
    tt = np.arange(int(d * SR)) / SR
    x = lp(rng.standard_normal(len(tt)), 120, 4) * 6
    return x * np.exp(-tt * 2.5) * np.minimum(1, tt / 0.02) + 0.6 * np.sin(2 * np.pi * 45 * tt) * np.exp(-tt * 3)


def wind(d=1.6):
    tt = np.arange(int(d * SR)) / SR
    x = rng.standard_normal(len(tt))
    y = lp(hp(x, 400), 1400) * (0.6 + 0.4 * np.sin(2 * np.pi * 1.3 * tt)) * np.sin(np.pi * tt / d)
    return y * 1.2


def crackle(d=1.2):
    n = int(d * SR); x = np.zeros(n)
    for _ in range(70):
        i = rng.integers(0, n - 200)
        x[i:i + 120] += rng.standard_normal(120) * np.exp(-np.arange(120) / 25) * rng.uniform(0.2, 1)
    tt = np.arange(n) / SR
    x += lp(rng.standard_normal(n), 600) * 0.6
    return hp(x, 300) * np.sin(np.pi * tt / d) * 0.8


def pop():
    tt = np.arange(int(0.12 * SR)) / SR
    return np.sin(2 * np.pi * (900 - 3000 * tt) * tt) * np.exp(-tt * 40) * 0.6


def soft_boom():
    tt = np.arange(int(1.6 * SR)) / SR
    return np.sin(2 * np.pi * (60 - 15 * tt) * tt) * np.exp(-tt * 2.2) * 0.9


add(sfx, soft_boom(), 0.0, 0.7)
add(sfx, chime(1175, 2.5), 0.05, 0.35)
for i in range(1, len(SCENE_START)):
    add(sfx, whoosh(0.55, 250, 2600), S(i) - 0.3, 0.55)
add(sfx, chime(1568), S(1) + 0.15, 0.5)
add(sfx, pop(), S(2) + 0.3, 0.5)
add(sfx, chime(1760, 2.0), wt(2, "Davi"), 0.35)
add(sfx, shimmer(), S(3) - 0.1, 0.7)
add(sfx, shimmer(), S(7) - 0.1, 0.7)
add(sfx, wind(), wt(4, "vento") - 0.05, 0.55)
add(sfx, rumble(), wt(4, "terremoto") - 0.02, 0.8)
add(sfx, crackle(), wt(4, "fogo") - 0.02, 0.6)
for q in range(3):
    add(sfx, chime(587, 3.0), wt(5, "voz") + q * 1.1, 0.25 / (q + 1))
add(sfx, chime(2093, 1.5), wt(6, "ainda") + 0.6, 0.3)
add(sfx, chime(2349, 2.0), wt(8, "sozinho") - 0.1, 0.4)
add(sfx, pop(), wt(9, "siga"), 0.6)
add(sfx, chime(1568, 2.5), wt(9, "siga") + 0.05, 0.3)
for k, w in enumerate(["ora", "novo", "outro"]):
    add(sfx, chime(1319 + k * 200, 1.2), wt(0, w), 0.12)

# ---------- voice ----------
voice = np.zeros(N)
for ln in LINES:
    sr, x = wavfile.read(ln["wav"])
    x = x.astype(np.float64) / 32768
    if ln["spk"] == "R":  # leitura com leve reverb
        y = x.copy()
        for d, g in ((0.05, 0.25), (0.11, 0.15), (0.19, 0.08)):
            y[int(d * SR):] += x[:-int(d * SR)] * g
        x = y
    add(voice, x, ln["start"])
voice /= np.max(np.abs(voice)) + 1e-9

env = lfilter([1 - math.exp(-1 / (0.08 * SR))], [1, -math.exp(-1 / (0.08 * SR))], np.abs(voice))
env = np.clip(env / (np.percentile(env[env > 1e-4], 90) + 1e-9), 0, 1)
duck = 1 - 0.55 * env

fade = np.clip((TOTAL + 0.4 - t_all) / 1.2, 0, 1)
mix = (voice * 1.0 + music * 0.22 * duck + sfx * 0.35 * (0.6 + 0.4 * duck)) * fade
mix = np.tanh(mix * 1.1)
mix *= 10 ** (-3 / 20) / np.max(np.abs(mix))
wavfile.write("mix.wav", SR, (mix * 32767).astype(np.int16))
print("ok", len(mix) / SR)

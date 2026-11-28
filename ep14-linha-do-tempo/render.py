# Ep14 — A linha do tempo que engana (Cleópatra x Lua x pirâmides, mamutes, Oxford x astecas, guilhotina x Voyager) — estilo STICKMAN SKETCH (traço de marcador, fundo branco, toques de cor chapada)
# Legendas: uma palavra por vez, Montserrat Bold branca em caixa preta arredondada, corte seco.
import cairo, math, json, sys, os, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
D = json.load(open('aud/durs.json'))
STARTS = np.concatenate([[0], np.cumsum(D)[:-1]])
sys.path.insert(0, '.')
from script import LINES
from shots import SHOTS

# ---------- palavras ----------
def load_words(i):
    out = []
    for a, b, x in json.load(open(f'aud/n{i}.json')):
        ps = x.split()
        wts = [len(p) * (4 if p.isdigit() else 1) for p in ps]; tot = sum(wts); acc = 0
        for k, p in enumerate(ps):
            out.append([a + (b - a) * acc / tot, a + (b - a) * (acc + wts[k]) / tot, p]); acc += wts[k]
    return out
WR = [load_words(i) for i in range(len(D))]
DISP = []
for i in range(len(D)):
    sw = LINES[i].split()
    DISP.append(sw if len(sw) == len(WR[i]) else [w[2] for w in WR[i]])
    if len(sw) != len(WR[i]): print('ALINHAMENTO diferente na cena', i, len(sw), len(WR[i]), file=sys.stderr)

def norm(x): return x.lower().strip('.,!?…:;')
def wt(i, w, n=0):
    k = 0
    for a, b, x in WR[i]:
        if norm(x) == w:
            if k == n: return a
            k += 1
    print('MISSING', i, w, file=sys.stderr); return 0.0

# ---------- cores ----------
def rgb(h): h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
INK = (0.067, 0.067, 0.067); WHITE = (1, 1, 1)
BLUE = rgb('3A9BF5'); LBLUE = rgb('B8E3FF'); BROWN = rgb('9C6B3E'); LBROWN = rgb('C99763')
SKIN = rgb('F7C4A5'); RED = rgb('E85D54'); YEL = rgb('F9B316'); GREEN = rgb('69A332')
DGRAY = (0.33, 0.34, 0.37); LGRAY = (0.82, 0.83, 0.85)
def c255(c): return tuple(int(v * 255) for v in c)

JS = 0
TPG = 0.0
ZL = 1.0
def nz(a, b=0.0):
    v = math.sin(a * 12.9898 + b * 78.233 + JS * 37.719) * 43758.5453
    return (v - math.floor(v)) * 2 - 1

# ---------- primitivas (traço de marcador com tremida) ----------
def stroke(c, pts, w=8, col=INK, closed=False, fill=None, amp=2.0, seed=0):
    P = [(x + nz(i + seed, 1.3) * amp, y + nz(i + seed, 2.7) * amp) for i, (x, y) in enumerate(pts)]
    c.move_to(*P[0])
    for p in P[1:]: c.line_to(*p)
    if closed: c.close_path()
    if fill is not None:
        c.set_source_rgb(*fill); c.fill_preserve()
    c.set_source_rgb(*col); c.set_line_width(w / ZL); c.set_line_cap(cairo.LINE_CAP_ROUND); c.set_line_join(cairo.LINE_JOIN_ROUND)
    c.stroke()

def ell_pts(cx, cy, rx, ry, rot=0.0, n=28, a0=0.0, a1=2 * math.pi):
    pts = []
    for k in range(n + 1 if a1 - a0 < 2 * math.pi - 1e-6 else n):
        a = a0 + (a1 - a0) * k / n
        x, y = rx * math.cos(a), ry * math.sin(a)
        pts.append((cx + x * math.cos(rot) - y * math.sin(rot), cy + x * math.sin(rot) + y * math.cos(rot)))
    return pts

def ellipse(c, cx, cy, rx, ry, w=8, fill=WHITE, col=INK, rot=0.0, seed=0, amp=1.6):
    stroke(c, ell_pts(cx, cy, rx, ry, rot), w, col, True, fill, amp, seed)

def arc(c, cx, cy, rx, ry, a0, a1, w=8, col=INK, seed=0, fill=None):
    stroke(c, ell_pts(cx, cy, rx, ry, 0, 18, math.radians(a0), math.radians(a1)), w, col, fill is not None, fill, 1.2, seed)

def rect(c, x0, y0, x1, y1, w=8, fill=WHITE, col=INK, seed=0, amp=2.0):
    stroke(c, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], w, col, True, fill, amp, seed)

TXT = []
def txt(s, size, cx, cy, col=INK, rot=0, weight='Black'): TXT.append((s, size, cx, cy, c255(col), rot, weight))

# ---------- personagens ----------
def man(c, x, y, s=1.0, f=1, arm=(-15, 15), leg=(8, -8), expr='n', hat=None, prop=None, w=8):
    d = lambda a, L, ox, oy: (ox + f * L * math.sin(math.radians(a)) * s, oy + L * math.cos(math.radians(a)) * s)
    ph = TPG * 6 + x * 0.013
    y = y - (abs(math.sin(ph * 1.5)) * 18 * s if expr == 'shock' else 0)
    bob = (0.5 + 0.5 * math.sin(ph)) * 7 * s
    sway = 15 if expr == 'shock' else 8
    hip0 = y - 115 * s
    hipy, shy, hy = hip0 - bob * 0.5, y - 190 * s - bob, y - 252 * s - bob * 1.4 + 3 * math.sin(ph * 0.5) * s
    for a in leg: stroke(c, [(x, hipy), d(a, 115, x, hip0)], w)
    stroke(c, [(x, shy), (x, hipy)], w)
    hands = []
    for k, a in enumerate(arm):
        a = a + sway * math.sin(ph * 1.7 + k * 2.3)
        e = d(a, 95, x, shy + 8 * s); stroke(c, [(x, shy + 8 * s), e], w); hands.append(e)
    if prop == 'tie': stroke(c, [(x, shy + 4 * s), (x - 16 * s, shy + 56 * s), (x + 16 * s, shy + 56 * s)], 5, INK, True, RED, 1)
    if prop == 'medal':
        ellipse(c, x, shy + 40 * s, 13 * s, 13 * s, 5, YEL); stroke(c, [(x, shy + 6 * s), (x, shy + 28 * s)], 4, RED)
    ellipse(c, x, hy, 46 * s, 46 * s, w, WHITE, seed=3)
    ex = 15 * s; ey = hy - 6 * s; my = hy + 20 * s
    if expr in ('n', 'sad', 'smile', 'angry'):
        blink = (int(TPG * 15) + int(x)) % 40 == 0
        for sg in (-1, 1):
            if blink: stroke(c, [(x + sg * ex - 7 * s, ey), (x + sg * ex + 7 * s, ey)], 4)
            else: ellipse(c, x + sg * ex, ey, 4.5 * s, 4.5 * s, 3, INK)
    if expr == 'n': stroke(c, [(x - 12 * s, my), (x + 12 * s, my)], 6)
    elif expr == 'sad': arc(c, x, my + 14 * s, 15 * s, 12 * s, 200, 340, 6)
    elif expr == 'smile': arc(c, x, my - 8 * s, 18 * s, 14 * s, 20, 160, 6)
    elif expr == 'angry':
        stroke(c, [(x - ex - 10 * s, ey - 14 * s), (x - ex + 8 * s, ey - 6 * s)], 6)
        stroke(c, [(x + ex + 10 * s, ey - 14 * s), (x + ex - 8 * s, ey - 6 * s)], 6)
        stroke(c, [(x - 14 * s, my + 2 * s), (x + 14 * s, my - 2 * s)], 6)
    elif expr == 'shock':
        for sg in (-1, 1):
            ellipse(c, x + sg * ex, ey, 11 * s, 11 * s, 4, WHITE); ellipse(c, x + sg * ex, ey, 3.5 * s, 3.5 * s, 2, INK)
        ellipse(c, x, my + 4 * s, 9 * s, 13 * s, 5, INK)
    elif expr == 'x':
        for sg in (-1, 1):
            stroke(c, [(x + sg * ex - 9 * s, ey - 9 * s), (x + sg * ex + 9 * s, ey + 9 * s)], 5)
            stroke(c, [(x + sg * ex - 9 * s, ey + 9 * s), (x + sg * ex + 9 * s, ey - 9 * s)], 5)
        arc(c, x, my + 14 * s, 15 * s, 10 * s, 200, 340, 6)
    elif expr == 'laugh':
        for sg in (-1, 1): arc(c, x + sg * ex, ey + 4 * s, 9 * s, 8 * s, 200, 340, 5)
        ellipse(c, x, my, 17 * s, 14 * s, 5, INK); ellipse(c, x, my + 8 * s, 9 * s, 6 * s, 0.1, RED, RED)
    elif expr == 'smug':
        for sg in (-1, 1):
            ellipse(c, x + sg * ex, ey, 9 * s, 9 * s, 3, WHITE); rect(c, x + sg * ex - 11 * s, ey - 12 * s, x + sg * ex + 11 * s, ey - 1 * s, 0.1, WHITE, WHITE, 0, 0)
            ellipse(c, x + sg * ex + f * 3 * s, ey + 2 * s, 3 * s, 3 * s, 2, INK)
            stroke(c, [(x + sg * ex - 10 * s, ey - 2 * s), (x + sg * ex + 10 * s, ey - 2 * s)], 4)
        stroke(c, [(x - 12 * s, my), (x + 6 * s, my + 2 * s), (x + 16 * s, my - 6 * s)], 5)
    if hat == 'nemes':
        stroke(c, [(x - 50 * s, hy - 10 * s), (x - 66 * s, hy + 70 * s), (x - 40 * s, hy + 70 * s), (x - 36 * s, hy + 20 * s)], 6, INK, True, YEL, 1.2, 11)
        stroke(c, [(x + 50 * s, hy - 10 * s), (x + 66 * s, hy + 70 * s), (x + 40 * s, hy + 70 * s), (x + 36 * s, hy + 20 * s)], 6, INK, True, YEL, 1.2, 12)
        for sg in (-1, 1):
            for k in range(3): stroke(c, [(x + sg * (44 + k * 2) * s, hy + (10 + k * 20) * s), (x + sg * (60 + k * 2) * s, hy + (14 + k * 20) * s)], 4, BLUE)
        stroke(c, ell_pts(x, hy - 10 * s, 54 * s, 50 * s, 0, 16, math.pi, 2 * math.pi), 7, INK, True, YEL, 1.2, 13)
        for k in range(4): arc(c, x, hy - 10 * s, (18 + k * 10) * s, (16 + k * 9) * s, 200, 340, 4, BLUE, k)
        ellipse(c, x, hy - 56 * s, 9 * s, 12 * s, 4, GREEN, seed=14)
    elif hat == 'astro':
        ellipse(c, x, hy, 66 * s, 66 * s, 7, None, seed=15)
        arc(c, x + 22 * s, hy - 22 * s, 30 * s, 30 * s, 220, 300, 5, LBLUE, 2)
        rect(c, x - 38 * s, shy + 20 * s, x + 38 * s, shy + 70 * s, 6, LGRAY, seed=16)
    elif hat == 'grad':
        stroke(c, [(x - 70 * s, hy - 46 * s), (x, hy - 72 * s), (x + 70 * s, hy - 46 * s), (x, hy - 22 * s)], 7, INK, True, INK, 1.0, 17)
        stroke(c, [(x, hy - 47 * s), (x + 50 * s, hy - 38 * s), (x + 54 * s, hy + 6 * s)], 4, YEL)
    elif hat == 'helmet':
        stroke(c, ell_pts(x, hy - 6 * s, 54 * s, 50 * s, 0, 16, math.pi, 2 * math.pi), 7, INK, True, LBROWN, 1.5)
        stroke(c, [(x - 62 * s, hy - 6 * s), (x + 62 * s, hy - 6 * s)], 8)
    elif hat == 'cap':
        stroke(c, [(x - 52 * s, hy - 18 * s), (x - 40 * s, hy - 58 * s), (x + 40 * s, hy - 58 * s), (x + 52 * s, hy - 18 * s)], 7, INK, True, LBROWN, 1.5)
        stroke(c, [(x - 56 * s, hy - 16 * s), (x + 56 * s, hy - 16 * s)], 8)
        ellipse(c, x, hy - 38 * s, 7 * s, 7 * s, 3, YEL)
    elif hat == 'bowler':
        stroke(c, ell_pts(x, hy - 22 * s, 38 * s, 34 * s, 0, 14, math.pi, 2 * math.pi), 7, INK, True, DGRAY, 1.5)
        stroke(c, [(x - 56 * s, hy - 22 * s), (x + 56 * s, hy - 22 * s)], 9)
    return hands

def rifle(c, x, y, s=1.0, f=1):
    stroke(c, [(x - f * 40 * s, y - 120 * s), (x + f * 120 * s, y - 175 * s)], 9, INK)
    stroke(c, [(x - f * 40 * s, y - 120 * s), (x - f * 70 * s, y - 100 * s), (x - f * 56 * s, y - 128 * s)], 6, INK, True, BROWN, 1)

def soldier(c, x, y, s=1.0, f=1, expr='n', aim=True, leg=(8, -8)):
    man(c, x, y, s, f, arm=(f * 78 * f, f * 85 * f) if aim else (-15, 15), leg=leg, expr=expr, hat='helmet')
    if aim: rifle(c, x, y, s, f)

def emu(c, x, y, s=1.0, f=1, run=None, expr='n', medal=False, w=7):
    ph = run if run is not None else 0.0
    amp = 30 if run is not None else 5
    hipy = y - 150 * s
    for k in (0, 1):
        a = math.sin(ph + k * math.pi) * amp
        hx0 = x + f * (k * 26 - 8) * s
        foot = (hx0 + f * math.sin(math.radians(a)) * 150 * s, hipy + math.cos(math.radians(a)) * 150 * s)
        stroke(c, [(hx0, hipy), foot], w, INK); stroke(c, [foot, (foot[0] + f * 30 * s, foot[1])], 6, INK)
    # penas da cauda
    stroke(c, [(x - f * 70 * s, y - 215 * s), (x - f * 130 * s, y - 250 * s), (x - f * 108 * s, y - 205 * s), (x - f * 138 * s, y - 185 * s), (x - f * 80 * s, y - 170 * s)], 6, INK, True, LBROWN, 1.5, 5)
    ellipse(c, x, y - 190 * s, 92 * s, 62 * s, w, BROWN, seed=2)
    for k in range(4):
        yy = y - (205 - k * 14) * s
        stroke(c, [(x - f * 40 * s, yy), (x + f * 4 * s, yy + 7 * s), (x + f * 44 * s, yy)], 4, LGRAY, False, None, 1, k)
    # pescoço + cabeça
    nx0, ny0 = x + f * 58 * s, y - 220 * s; nx1, ny1 = x + f * 92 * s, y - 345 * s
    stroke(c, [(nx0 - 16 * s, ny0 + 24 * s), (nx1 - 14 * s, ny1), (nx1 + 14 * s, ny1), (nx0 + 18 * s, ny0 + 28 * s)], 7, INK, True, LBROWN, 1.6, 9)
    ellipse(c, nx1 + f * 6 * s, ny1 - 8 * s, 32 * s, 23 * s, 7, LBROWN, seed=4)
    bx = nx1 + f * 38 * s
    stroke(c, [(bx, ny1 - 22 * s), (bx + f * 46 * s, ny1 - 6 * s), (bx, ny1 + 6 * s)], 6, INK, True, YEL, 1)
    ex, ey = nx1 + f * 10 * s, ny1 - 14 * s
    if expr == 'smug':
        ellipse(c, ex, ey, 8 * s, 8 * s, 3, WHITE); rect(c, ex - 10 * s, ey - 11 * s, ex + 10 * s, ey - 1 * s, 0.1, LBROWN, LBROWN, 0, 0)
        stroke(c, [(ex - 9 * s, ey - 1 * s), (ex + 9 * s, ey - 1 * s)], 4)
    elif expr == 'shock':
        ellipse(c, ex, ey, 10 * s, 10 * s, 4, WHITE); ellipse(c, ex, ey, 3 * s, 3 * s, 2, INK)
    else:
        ellipse(c, ex, ey, 5 * s, 5 * s, 3, INK)
    if medal:
        stroke(c, [(nx0 - 4 * s, ny0 + 10 * s), (nx0 + f * 14 * s, ny0 + 60 * s)], 5, BLUE)
        ellipse(c, nx0 + f * 14 * s, ny0 + 72 * s, 15 * s, 15 * s, 5, YEL)

def lewis(c, x, y, s=1.0, f=1, jam=False):
    for a in (-1, 1): stroke(c, [(x + f * 30 * s, y - 70 * s), (x + f * (30 + a * 45) * s, y)], 7)
    stroke(c, [(x - f * 70 * s, y - 80 * s), (x - f * 70 * s, y - 112 * s), (x - f * 20 * s, y - 112 * s), (x - f * 20 * s, y - 80 * s)], 7, INK, True, BROWN, 1.5)
    rect(c, x - f * 24 * s if f > 0 else x - 10 * s, y - 118 * s, x + f * 120 * s if f > 0 else x + 24 * s, y - 78 * s, 8, DGRAY)
    stroke(c, [(x + f * 120 * s, y - 106 * s), (x + f * 210 * s, y - 100 * s)], 9)
    ellipse(c, x + f * 20 * s, y - 150 * s, 40 * s, 40 * s, 7, LGRAY); ellipse(c, x + f * 20 * s, y - 150 * s, 10 * s, 10 * s, 5, INK)
    if jam:
        stroke(c, [(x + f * 20 * s, y - 80 * s), (x + f * 20 * s, y - 40 * s)], 0.1)

def bullet(c, x, y, s=1.0, rot=0.0):
    ca, sa = math.cos(rot), math.sin(rot)
    q = lambda px, py: (x + (px * ca - py * sa) * s, y + (px * sa + py * ca) * s)
    stroke(c, [q(-22, -9), q(10, -9), q(10, 9), q(-22, 9)], 5, INK, True, YEL, 0.8)
    stroke(c, [q(10, -9), q(30, 0), q(10, 9)], 5, INK, True, LBROWN, 0.8)

def building(c, x, y, s=1.0):
    stroke(c, [(x - 230 * s, y - 250 * s), (x, y - 360 * s), (x + 230 * s, y - 250 * s)], 8, INK, True, LBROWN, 1.5)
    rect(c, x - 220 * s, y - 250 * s, x + 220 * s, y - 225 * s, 8, WHITE)
    for k in range(5): rect(c, x - 190 * s + k * 95 * s, y - 225 * s, x - 160 * s + k * 95 * s, y - 40 * s, 7, WHITE, seed=k)
    rect(c, x - 235 * s, y - 40 * s, x + 235 * s, y, 8, WHITE)

def calendar(c, cx, cy, day, month, tp=0.0):
    rect(c, cx - 190, cy - 150, cx + 190, cy + 150, 9, WHITE, seed=1)
    rect(c, cx - 190, cy - 150, cx + 190, cy - 80, 9, RED, seed=2)
    for sg in (-1, 1): rect(c, cx + sg * 110 - 8, cy - 175, cx + sg * 110 + 8, cy - 125, 6, LGRAY, seed=3)
    txt(month, 62, cx, cy - 113, WHITE, 0, 'ExtraBold')
    txt(day, 170 if len(day) < 3 else 120, cx, cy + 36, INK)

def wheat(c, x0, x1, gy, n, tp=0.0, eaten=0.0, seed=1):
    for k in range(n):
        x = x0 + (x1 - x0) * k / max(1, n - 1)
        h = 120 + 30 * nz(k + seed, 5)
        if nz(k + seed, 9) > 1 - 2 * eaten: h *= 0.35
        lean = 10 * math.sin(tp * 2 + k)
        stroke(c, [(x, gy), (x + lean, gy - h)], 5, INK, False, None, 1.2, k)
        ellipse(c, x + lean, gy - h - 14, 8, 20, 4, YEL, rot=0.15 * math.sin(k), seed=k)

def ground(c, x0=-800, x1=1880, y=1090):
    stroke(c, [(x0, y), ((x0 + x1) / 2, y + 3), (x1, y - 2)], 7, INK, False, None, 2.5, 40)
    for k in range(-6, 20):
        gx = 130 + k * 135 + nz(k, 3) * 25
        stroke(c, [(gx - 12, y + 26), (gx, y + 14), (gx + 12, y + 26)], 4, INK, False, None, 1, k)

def dust(c, x, y, f, tp):
    for k in range(3):
        L = 50 + 25 * ((tp * 6 + k) % 3)
        stroke(c, [(x - f * 20, y - 20 - k * 22), (x - f * (20 + L), y - 20 - k * 22)], 5, LGRAY, False, None, 1, k)

def smoke(c, x, y, tp, n=4):
    for k in range(n):
        r = 22 + 10 * k; yy = y - 40 * k - ((tp * 60) % 30)
        ellipse(c, x + 12 * k * math.sin(tp * 4 + k), yy, r, r, 5, LGRAY, LGRAY)

def star(c, x, y, r, fill=YEL):
    pts = []
    for k in range(10):
        a = -math.pi / 2 + k * math.pi / 5; rr = r if k % 2 == 0 else r * 0.45
        pts.append((x + rr * math.cos(a), y + rr * math.sin(a)))
    stroke(c, pts, 6, INK, True, fill, 1.2, int(x) % 7)

def heart(c, x, y, s=1.0, fill=RED):
    pts = []
    for k in range(41):
        a = 2 * math.pi * k / 40
        px = 16 * math.sin(a) ** 3
        py = -(13 * math.cos(a) - 5 * math.cos(2 * a) - 2 * math.cos(3 * a) - math.cos(4 * a))
        pts.append((x + px * 5 * s, y + py * 5 * s))
    stroke(c, pts, 7, INK, True, fill, 1.2, 3)

def qmark(c, x, y, s=1.0): txt('?', int(120 * s), x, y, RED)
def smoothstep(x): x = min(max(x, 0), 1); return x * x * (3 - 2 * x)

GY = 1090
SHAKE = [0, 0]


def clock(c, cx, cy, r, hh, mm):
    ellipse(c, cx, cy, r, r, 10, WHITE, seed=2)
    for k in range(12):
        a = k * math.pi / 6
        stroke(c, [(cx + 0.82 * r * math.sin(a), cy - 0.82 * r * math.cos(a)), (cx + 0.92 * r * math.sin(a), cy - 0.92 * r * math.cos(a))], 6)
    ah = (hh % 12 + mm / 60) * math.pi / 6; am = mm * math.pi / 30
    stroke(c, [(cx, cy), (cx + 0.5 * r * math.sin(ah), cy - 0.5 * r * math.cos(ah))], 12)
    stroke(c, [(cx, cy), (cx + 0.78 * r * math.sin(am), cy - 0.78 * r * math.cos(am))], 8, RED)
    ellipse(c, cx, cy, 10, 10, 4, INK, INK)

def stopwatch(c, cx, cy, r, label, frac):
    rect(c, cx - 22, cy - r - 50, cx + 22, cy - r - 10, 7, LGRAY)
    ellipse(c, cx, cy, r, r, 10, WHITE, seed=6)
    pts = [(cx, cy)] + ell_pts(cx, cy, r * 0.8, r * 0.8, -math.pi / 2, 24, 0, 2 * math.pi * max(0.01, frac))
    if frac > 0.02: stroke(c, pts, 5, INK, True, YEL, 0.8)
    txt(label, int(r * 0.75), cx, cy + 8, INK)

def speedo(c, cx, cy, r, val, vmax=80):
    stroke(c, ell_pts(cx, cy, r, r, 0, 24, math.pi, 2 * math.pi), 10, INK, False, None, 1.2, 2)
    stroke(c, [(cx - r, cy), (cx + r, cy)], 10)
    for k in range(9):
        a = math.pi + k * math.pi / 8
        stroke(c, [(cx + 0.8 * r * math.cos(a), cy + 0.8 * r * math.sin(a)), (cx + 0.93 * r * math.cos(a), cy + 0.93 * r * math.sin(a))], 6)
    a = math.pi + math.pi * min(1, val / vmax)
    stroke(c, [(cx, cy), (cx + 0.75 * r * math.cos(a), cy + 0.75 * r * math.sin(a))], 10, RED)
    ellipse(c, cx, cy, 14, 14, 5, INK, INK)

def thermo(c, cx, cy, lvl):
    rect(c, cx - 30, cy - 260, cx + 30, cy + 40, 9, WHITE, seed=1)
    c.set_source_rgb(*BLUE); c.rectangle(cx - 16, cy + 30 - 290 * lvl, 32, 290 * lvl); c.fill()
    ellipse(c, cx, cy + 70, 55, 55, 9, BLUE, seed=2)
    for k in range(6): stroke(c, [(cx + 30, cy - 230 + k * 50), (cx + 58, cy - 230 + k * 50)], 5)

def flake(c, x, y, r):
    for k in range(3):
        a = k * math.pi / 3
        stroke(c, [(x - r * math.cos(a), y - r * math.sin(a)), (x + r * math.cos(a), y + r * math.sin(a))], 7, BLUE, False, None, 1, k)

def fly(c, x, y, s=1.0, stuck=True):
    for sg in (-1, 1): ellipse(c, x + sg * 34 * s, y - 34 * s, 30 * s, 18 * s, 5, LBLUE, rot=sg * 0.6, seed=sg + 2)
    ellipse(c, x, y, 26 * s, 34 * s, 6, DGRAY, seed=1)
    ellipse(c, x, y - 40 * s, 16 * s, 16 * s, 5, DGRAY, seed=2)
    for sg in (-1, 1): ellipse(c, x + sg * 9 * s, y - 44 * s, 6 * s, 6 * s, 3, WHITE)

def ruler(c, x, y0, y1, label):
    rect(c, x - 26, y1, x + 26, y0, 8, YEL, seed=3)
    n = 9
    for k in range(n + 1):
        yy = y0 + (y1 - y0) * k / n
        stroke(c, [(x - 26, yy), (x - 4 if k % 3 else x + 10, yy)], 5)
    txt(label, 90, x, y1 - 70, INK)

def gavel(c, cx, cy, ang=0.0):
    c.save(); c.translate(cx, cy); c.rotate(ang)
    stroke(c, [(0, 0), (0, 230)], 16, INK); stroke(c, [(0, 0), (0, 230)], 8, LBROWN)
    rect(c, -95, -45, 95, 45, 9, BROWN, seed=2)
    for sg in (-1, 1): rect(c, sg * 95 - 12, -55, sg * 95 + 12, 55, 7, LBROWN, seed=3)
    c.restore()

def bubble(c, x0, y0, x1, y1, tailx, taily):
    stroke(c, [(x0, y0), (x1, y0), (x1, y1), ((x0 + x1) / 2 + 40, y1), (tailx, taily), ((x0 + x1) / 2 - 20, y1), (x0, y1)], 8, INK, True, WHITE, 1.5, 4)

def burst(c, x, y, r, n=12, fill=YEL):
    pts = []
    for k in range(2 * n):
        a = k * math.pi / n; rr = r if k % 2 == 0 else r * 0.62
        pts.append((x + rr * math.cos(a), y + rr * math.sin(a)))
    stroke(c, pts, 8, INK, True, fill, 1.5, 7)

def splat_rays(c, x, y, te, n=10, col=INK):
    # traços radiais que expandem e somem em ~5 frames
    if te < 0 or te > 0.18: return
    u = te / 0.18
    for k in range(n):
        a = k * 2 * math.pi / n + 0.2
        r0 = 60 + 160 * u; r1 = r0 + 60 * (1 - u)
        stroke(c, [(x + r0 * math.cos(a), y + r0 * math.sin(a)), (x + r1 * math.cos(a), y + r1 * math.sin(a))], 8, col)

def impact(t, t0):
    if 0 <= t - t0 < 0.25: SHAKE[0] = 9 * math.sin((t - t0) * 90)
def bar(c, x0, y0, x1, y1, frac, col):
    rect(c, x0, y0, x1, y1, 8, WHITE, seed=3)
    if frac > 0.01:
        c.set_source_rgb(*col); c.rectangle(x0 + 6, y0 + 6, (x1 - x0 - 12) * frac, y1 - y0 - 12); c.fill()
    rect(c, x0, y0, x1, y1, 8, None, seed=3)

def heatwaves(c, x, y, tp, col=RED, n=4, spread=150, hgt=220):
    for k in range(n):
        xx = x - spread + 2 * spread * k / max(1, n - 1)
        off = (tp * 90 + k * 40) % 60
        pts = [(xx + 16 * math.sin(j * 0.9 + tp * 6 + k), y - off - j * hgt / 8) for j in range(9)]
        stroke(c, pts, 6, col, False, None, 0.8, k)

def stamp(s, cx, cy, col=RED, rot=-6, size=130): txt(s, size, cx, cy, col, rot)

# ---------- objetos do episódio (linha do tempo que engana) ----------
SAND = rgb('E9C27A'); DSAND = rgb('C99763')
def counter(v0, v1, t, a, b):
    u = smoothstep((t - a) / max(0.01, b - a)); return v0 + (v1 - v0) * u
def fmt(v): return f'{int(v):,}'.replace(',', '.')

def pyramid(c, x, gy, s=1.0, frac=1.0):
    bw, hh = 300 * s, 330 * s
    rows = 7; shown = max(1, int(round(rows * frac)))
    top = gy - hh * shown / rows
    half = bw * (1 - shown / rows)
    if shown >= rows:
        stroke(c, [(x - bw, gy), (x, gy - hh), (x + bw, gy)], 8, INK, True, SAND, 1.5, 2)
    else:
        stroke(c, [(x - bw, gy), (x - half, top), (x + half, top), (x + bw, gy)], 8, INK, True, SAND, 1.5, 2)
    for k in range(1, shown):
        yy = gy - hh * k / rows; hw = bw * (1 - k / rows)
        stroke(c, [(x - hw, yy), (x + hw, yy)], 4, DSAND, False, None, 1.0, k)
        for j in range(-3, 4):
            bx = x + j * hw / 3.5 + (k % 2) * hw / 7
            if abs(bx - x) < hw - 10: stroke(c, [(bx, yy), (bx, yy + hh / rows)], 3, DSAND, False, None, 0.8, j + k)
    # lado em sombra (hachura)
    if shown >= rows:
        for k in range(5):
            u = (k + 1) / 6
            stroke(c, [(x + 10 * s, gy - hh * (1 - u) - 6), (x + bw * u * 0.85, gy - 8)], 3, DSAND, False, None, 1.0, k + 20)

def block(c, x, y, s=1.0):
    rect(c, x - 70 * s, y - 80 * s, x + 70 * s, y, 8, SAND, seed=5)
    stroke(c, [(x - 100 * s, y + 4), (x + 100 * s, y + 4)], 8, BROWN)

def moon(c, x, y, r, craters=True):
    ellipse(c, x, y, r, r, 9, LGRAY, seed=4)
    if not craters:
        for k in range(5): ellipse(c, x - 300 + k * 150, y - r + 60 + 20 * (k % 2), 30, 12, 5, DGRAY, seed=k)
        return
    for k, (dx, dy, rr) in enumerate([(-0.35, -0.2, 0.22), (0.3, 0.25, 0.16), (0.1, -0.45, 0.12), (-0.15, 0.45, 0.1)]):
        ellipse(c, x + dx * r, y + dy * r, rr * r, rr * r, 5, DGRAY if k % 2 else WHITE, seed=k)

def flag(c, x, y, s=1.0, tp=0.0):
    stroke(c, [(x, y), (x, y - 170 * s)], 7)
    wv = 6 * math.sin(tp * 6)
    stroke(c, [(x, y - 170 * s), (x + 90 * s, y - 165 * s + wv), (x + 92 * s, y - 115 * s + wv), (x, y - 120 * s)], 6, INK, True, WHITE, 1.0, 3)

def mammoth(c, x, y, s=1.0, f=1, tp=0.0, walk=False):
    ph = tp * 8 + x * 0.01
    for k, dx in enumerate((-80, -40, 50, 90)):
        a = (14 * math.sin(ph + k * math.pi) if walk else 0)
        lx = x + f * dx * s
        stroke(c, [(lx - 18 * s, y - 120 * s), (lx - 18 * s + f * a * s * 0.5, y), (lx + 18 * s + f * a * s * 0.5, y), (lx + 18 * s, y - 120 * s)], 7, INK, True, BROWN, 1.0, k)
    stroke(c, [(x - f * 150 * s, y - 190 * s), (x - f * 175 * s, y - 120 * s)], 6)
    ellipse(c, x, y - 190 * s, 160 * s, 105 * s, 8, BROWN, seed=2)
    for k in range(7):  # pelos
        hx = x - 120 * s + k * 38 * s
        stroke(c, [(hx, y - 120 * s), (hx + 6 * s, y - 92 * s)], 4, INK, False, None, 1, k)
    hx, hy = x + f * 150 * s, y - 230 * s
    ellipse(c, hx, hy, 80 * s, 75 * s, 8, BROWN, seed=3)
    ellipse(c, hx - f * 30 * s, hy - 5 * s, 34 * s, 46 * s, 6, LBROWN, seed=6)
    # tromba
    sw = 10 * math.sin(tp * 4)
    stroke(c, [(hx + f * 50 * s, hy + 20 * s), (hx + f * 70 * s, hy + 110 * s), (hx + f * (60 + sw) * s, hy + 180 * s), (hx + f * (85 + sw) * s, hy + 195 * s)], 22 * s if s > 0.3 else 8, INK)
    stroke(c, [(hx + f * 50 * s, hy + 20 * s), (hx + f * 70 * s, hy + 110 * s), (hx + f * (60 + sw) * s, hy + 180 * s), (hx + f * (85 + sw) * s, hy + 195 * s)], max(2, 10 * s), BROWN)
    # presas
    stroke(c, [(hx + f * 30 * s, hy + 50 * s), (hx + f * 70 * s, hy + 120 * s), (hx + f * 140 * s, hy + 110 * s), (hx + f * 160 * s, hy + 70 * s)], 6, INK, False, None, 1, 8)
    stroke(c, [(hx + f * 30 * s, hy + 50 * s), (hx + f * 70 * s, hy + 120 * s), (hx + f * 140 * s, hy + 110 * s), (hx + f * 160 * s, hy + 70 * s)], 3, WHITE, False, None, 0.5, 8)
    ellipse(c, hx + f * 22 * s, hy - 20 * s, 7 * s, 7 * s, 3, INK, INK)

def island(c, cx, cy, tp=0.0):
    pts = []
    for k in range(18):
        a = 2 * math.pi * k / 18
        r = 1 + 0.18 * math.sin(3 * a + 1) + 0.1 * math.sin(5 * a)
        pts.append((cx + 330 * r * math.cos(a), cy + 170 * r * math.sin(a)))
    for j in range(3):
        yy = cy + 230 + j * 45
        stroke(c, [(cx - 420 + q * 70, yy + 10 * math.sin(q * 1.3 + tp * 4 + j)) for q in range(13)], 5, BLUE, False, None, 0.8, j)
    stroke(c, pts, 9, INK, True, WHITE, 1.5, 3)
    for k in range(5):
        stroke(c, [(cx - 240 + k * 110, cy - 30 + 30 * (k % 2)), (cx - 200 + k * 110, cy - 10 + 30 * (k % 2))], 4, LBLUE, False, None, 1, k)

def snow(c, tp, n=14, x0=60, x1=1020, y0=500, y1=1100):
    for k in range(n):
        x = x0 + (x1 - x0) * ((k * 0.618) % 1)
        y = y0 + ((tp * 220 + k * 97) % (y1 - y0))
        flake(c, x + 10 * math.sin(tp * 3 + k), y, 14)

def step_pyramid(c, x, gy, s=1.0):
    for k in range(4):
        hw = (300 - k * 60) * s; y1 = gy - k * 70 * s
        rect(c, x - hw, y1 - 70 * s, x + hw, y1, 8, LBROWN if k % 2 == 0 else SAND, seed=k)
    rect(c, x - 40 * s, gy - 280 * s, x + 40 * s, gy, 6, DSAND, seed=9)
    for k in range(8): stroke(c, [(x - 40 * s, gy - k * 35 * s), (x + 40 * s, gy - k * 35 * s)], 4)
    rect(c, x - 80 * s, gy - 380 * s, x + 80 * s, gy - 280 * s, 8, RED, seed=6)
    rect(c, x - 25 * s, gy - 340 * s, x + 25 * s, gy - 280 * s, 6, INK, seed=7)

def waves(c, x0, x1, y, tp, n=3, col=BLUE):
    for j in range(n):
        yy = y + j * 40
        stroke(c, [(x0 + q * 60, yy + 9 * math.sin(q * 1.2 + tp * 5 + j * 2)) for q in range(int((x1 - x0) / 60) + 1)], 5, col, False, None, 0.6, j)

def guillotine(c, x, gy, s=1.0, drop=0.0):
    stroke(c, [(x - 200 * s, gy), (x + 200 * s, gy)], 10)
    for sg in (-1, 1): rect(c, x + sg * 110 * s - 16 * s, gy - 620 * s, x + sg * 110 * s + 16 * s, gy, 8, BROWN, seed=2 + sg)
    rect(c, x - 140 * s, gy - 650 * s, x + 140 * s, gy - 620 * s, 8, BROWN, seed=5)
    by = gy - 600 * s + drop * 330 * s
    stroke(c, [(x - 94 * s, by), (x + 94 * s, by), (x + 94 * s, by + 70 * s), (x - 94 * s, by + 120 * s)], 7, INK, True, LGRAY, 1.0, 6)
    rect(c, x - 94 * s, by - 40 * s, x + 94 * s, by, 6, DGRAY, seed=7)
    rect(c, x - 94 * s, gy - 220 * s, x + 94 * s, gy - 150 * s, 7, LBROWN, seed=8)
    arc(c, x, gy - 185 * s, 34 * s, 34 * s, 180, 360, 6, INK, 3)

def rocket(c, x, y, s=1.0, tp=0.0, fire=True):
    if fire:
        fl = 1 + 0.25 * math.sin(tp * 40)
        stroke(c, [(x - 40 * s, y), (x, y + 170 * s * fl), (x + 40 * s, y)], 6, INK, True, YEL, 1.0, 4)
        stroke(c, [(x - 20 * s, y), (x, y + 90 * s * fl), (x + 20 * s, y)], 4, RED, True, RED, 0.6, 5)
        for k in range(4):
            r = (30 + 14 * k) * s; yy = y + (190 + 40 * k) * s
            ellipse(c, x + (k - 1.5) * 50 * s, yy, r, r, 5, LGRAY, LGRAY, seed=k)
    for sg in (-1, 1): stroke(c, [(x + sg * 45 * s, y - 120 * s), (x + sg * 95 * s, y + 10 * s), (x + sg * 45 * s, y)], 7, INK, True, RED, 1.0, sg + 3)
    rect(c, x - 45 * s, y - 380 * s, x + 45 * s, y, 8, WHITE, seed=2)
    stroke(c, [(x - 45 * s, y - 380 * s), (x, y - 480 * s), (x + 45 * s, y - 380 * s)], 8, INK, True, RED, 1.0, 6)
    for k in range(2): stroke(c, [(x - 45 * s, y - (120 + k * 130) * s), (x + 45 * s, y - (120 + k * 130) * s)], 5)

def probe(c, x, y, s=1.0, rot=0.0):
    c.save(); c.translate(x, y); c.rotate(rot)
    stroke(c, [(-150 * s, 0), (170 * s, 40 * s)], 5); stroke(c, [(0, 0), (-60 * s, 160 * s)], 5)
    ellipse(c, 170 * s, 40 * s, 14 * s, 14 * s, 4, LGRAY)
    rect(c, -36 * s, -30 * s, 36 * s, 30 * s, 6, YEL, seed=3)
    stroke(c, ell_pts(0, -50 * s, 110 * s, 40 * s, 0, 18, math.pi, 2 * math.pi), 7, INK, True, WHITE, 1.0, 2)
    stroke(c, [(-110 * s, -50 * s), (110 * s, -50 * s)], 7)
    stroke(c, [(0, -50 * s), (0, -100 * s)], 5)
    c.restore()

def arrowh(c, x0, y, x1, w=8, col=INK):
    stroke(c, [(x0, y), (x1, y)], w, col, False, None, 1.5, 1)
    sg = 1 if x1 > x0 else -1
    stroke(c, [(x1 - sg * 30, y - 22), (x1, y), (x1 - sg * 30, y + 22)], w, col, False, None, 1.0, 2)

def brace(c, x0, x1, y, label, col=INK, size=64):
    stroke(c, [(x0, y + 24), (x0, y), (x1, y), (x1, y + 24)], 6, col, False, None, 1.2, int(x0) % 5)
    txt(label, size, (x0 + x1) / 2, y - 45, col, 0, 'Black')

def cleo(c, x, y, s=1.0, f=1, arm=(-15, 15), expr='smug'):
    return man(c, x, y, s, f, arm, (8, -8), expr, hat='nemes')

def astro(c, x, y, s=1.0, f=1, arm=(-15, 15), expr='smile'):
    return man(c, x, y, s, f, arm, (8, -8), expr, hat='astro')

def board(c, x0, y0, x1, y1):
    rect(c, x0, y0, x1, y1, 9, rgb('2F4A3A'), seed=3)
    for k in range(3): stroke(c, [(x0 + 40, y0 + 60 + k * 60), (x1 - 60 - 50 * (k % 2), y0 + 64 + k * 60)], 5, WHITE, False, None, 2, k)

def campus(c, x, gy, s=1.0):
    building(c, x, gy, s)
    rect(c, x - 30 * s, gy - 520 * s, x + 30 * s, gy - 360 * s, 7, LBROWN, seed=8)
    stroke(c, [(x - 40 * s, gy - 520 * s), (x, gy - 600 * s), (x + 40 * s, gy - 520 * s)], 7, INK, True, DGRAY, 1, 9)

def big_tl(c, t, tp, ty=640, show_p=True, show_m=True):
    # pirâmide ---- Cleópatra ---- Lua (proporcional: 2491 x 2038 anos)
    xp, xc, xm = 150, 595, 960
    ground(c)
    if show_p: pyramid(c, xp, GY, 0.42)
    cleo(c, xc, GY, 1.0, 1 if show_m else -1, (-20, 20), 'shock' if show_p and show_m else 'smug')
    if show_m:
        moon(c, xm, 860, 85); astro(c, xm - 10, 790, 0.28, -1, (-120, 15), 'smile'); flag(c, xm + 30, 785, 0.4, tp)
    if show_p: brace(c, xp, xc - 40, ty, '2.491 anos', INK, 58)
    if show_m: brace(c, xc + 40, xm, ty, '2.038 anos', RED, 58)

# ---------- cenas ----------
def s0(c, t, tp):
    if t < 1.46:
        ground(c)
        cleo(c, 595, GY, 1.1, 1, (-20, 20), 'smug')
        txt('CLEÓPATRA', 130, 540, 300, INK, -3)
    elif t < 2.92:
        big_tl(c, t, tp, show_p=False)
        txt('MAIS PERTO DA LUA...', 80, 540, 300, INK, -3)
        if t < 1.7: splat_rays(c, 960, 860, t - 1.46, 10, YEL)
    else:
        big_tl(c, t, tp)
        stamp('DO QUE DAS', 540, 270, RED, -4, 96); stamp('PIRÂMIDES?!', 540, 390, RED, -4, 96)
        if t > 3.43: splat_rays(c, 150, 1000, t - 3.43, 10); impact(t, 3.43)
        qmark(c, 700, 800)

def s1(c, t, tp):
    if t < 1.01:
        ground(c)
        pyramid(c, 540, GY, 1.3)
        txt('A GRANDE PIRÂMIDE', 96, 540, 300, INK, -3)
    elif t < 2.18:
        ground(c)
        pyramid(c, 760, GY, 0.85, smoothstep((t - 1.0) / 1.0) * 0.8 + 0.2)
        bx = 330 + 60 * smoothstep((t - 1.0) / 1.2)
        block(c, bx, GY - 6, 1.0)
        for k, mx in enumerate((bx - 140, bx - 230)):
            man(c, mx, GY, 0.85, 1, (75, 85), (25, -15), 'angry' if k == 0 else 'n')
        stroke(c, [(bx - 70, GY - 50), (bx - 130, GY - 170)], 4, BROWN)
        txt('FICOU PRONTA...', 96, 540, 300, INK, -3)
        dust(c, bx - 120, GY, 1, tp)
    else:
        calendar(c, 540, 700, '2560', 'ANO')
        ground(c)
        pyramid(c, 860, GY, 0.35)
        txt('a.C.', 90, 540, 960, RED)
        if t < 3.83: stamp('~2560 a.C.', 540, 300, RED, -4, 110)

def s2(c, t, tp):
    if t < 1.05:
        ground(c)
        cleo(c, 540, GY, 1.2, 1, (-20, -150), 'smile')
        txt('CLEÓPATRA', 120, 540, 300, INK, -3)
        star(c, 760, 640, 40); star(c, 320, 700, 30)
    elif t < 3.37:
        calendar(c, 540, 700, '69', 'NASCEU')
        ground(c)
        txt('a.C.', 90, 540, 960, RED)
        cleo(c, 860, GY, 0.55, -1, (-20, 20), 'smile')
    else:
        ground(c)
        pyramid(c, 170, GY, 0.42)
        cleo(c, 900, GY, 0.95, -1, (-20, 20), 'shock')
        v = counter(0, 2491, t, 3.37, 4.9)
        stroke(c, [(330, 900), (330 + (430) * min(1, v / 2491), 900)], 14, RED)
        arrowh(c, 330, 900, 330 + max(40, 430 * min(1, v / 2491)), 8, RED)
        txt(fmt(v), 170, 540, 300, RED, -3)
        txt('ANOS DEPOIS', 76, 540, 440, INK, 0, 'Black')

def s3(c, t, tp):
    if t < 1.43:
        moon(c, 540, 760, 230)
        qmark(c, 860, 520)
        txt('E A LUA?', 130, 540, 300, INK, -3)
    elif t < 3.07:
        moon(c, 540, 1500, 700, False)
        astro(c, 420, 870, 1.0, 1, (-20, 70), 'smile')
        flag(c, 560, 870, 1.2, tp)
        stamp('1969', 540, 300, RED, -4, 190)
    else:
        v = counter(0, 2038, t, 3.2, 4.3)
        bar(c, 120, 640, 800, 740, 1.0, SAND)
        txt('PIRÂMIDE → CLEÓPATRA', 46, 540, 600, INK, 0, 'Black')
        txt('2.491', 60, 920, 690, INK)
        bar(c, 120, 880, 800, 980, 0.82 * v / 2038, RED)
        txt('CLEÓPATRA → LUA', 46, 540, 840, INK, 0, 'Black')
        txt(fmt(v), 60, 920, 930, RED)
        txt('SÓ ~2.000 ANOS', 100, 540, 300, RED, -3)

def s4(c, t, tp):
    if t < 0.78:
        ground(c)
        man(c, 540, GY, 1.2, 1, (-20, 165), (8, -8), 'smug')
        txt('TEM MAIS', 140, 540, 300, RED, -4)
    elif t < 2.29:
        ground(c)
        pyramid(c, 540, GY, 1.1, 0.3 + 0.6 * smoothstep((t - 0.8) / 1.4))
        for k in range(3): man(c, 200 + k * 340, GY, 0.6, 1 if k % 2 else -1, (70, 80), (20, -15), 'n', w=7)
        txt('AS PIRÂMIDES SUBIAM', 84, 540, 300, INK, -3)
    else:
        ground(c)
        pyramid(c, 800, GY, 0.75)
        mammoth(c, 330 + 50 * (t - 2.29), GY, 0.9, 1, tp, True)
        stamp('MAMUTES!', 540, 300, RED, -5, 150)
        if t > 2.93: splat_rays(c, 450, 850, t - 2.93, 10); impact(t, 2.93)

def s5(c, t, tp):
    if t < 1.75:
        island(c, 540, 820, tp)
        mammoth(c, 470, 860, 0.45, 1, tp, True); mammoth(c, 680, 820, 0.35, -1, tp)
        snow(c, tp, 10, 120, 960, 520, 1080)
        txt('ILHA DE WRANGEL', 54, 540, 1100, DGRAY, 0, 'Black')
        txt('RÚSSIA', 120, 540, 300, INK, -3)
    else:
        ground(c)
        mammoth(c, 380, GY, 0.9, 1, tp)
        man(c, 840, GY, 1.0, -1, (-150, 150), (8, -8), 'shock')
        snow(c, tp, 12, 60, 1020, 540, 1100)
        v = counter(0, 4000, t, 1.75, 2.9)
        txt(f'~{fmt(v)}', 170, 540, 300, RED, -3)
        txt('ANOS ATRÁS', 76, 540, 440, INK, 0, 'Black')

def s6(c, t, tp):
    if t < 1.32:
        calendar(c, 540, 700, '1096', 'ANO')
        ground(c)
    elif t < 2.18:
        ground(c)
        board(c, 120, 600, 620, 900)
        man(c, 780, GY, 1.1, -1, (-20, 75), (8, -8), 'smug', hat='grad')
        txt('JÁ TINHA AULA', 110, 540, 300, INK, -3)
    else:
        ground(c)
        campus(c, 540, GY, 0.85)
        for k, x in enumerate((140, 940)): man(c, x, GY, 0.6, 1 if k == 0 else -1, (-20, 20), (8, -8), 'n', hat='grad', w=7)
        txt('OXFORD', 150, 540, 300, INK, -3)
        if t > 3.84: txt('INGLATERRA', 64, 540, 440, DGRAY, 0, 'Black')

def s7(c, t, tp):
    if t < 1.67:
        waves(c, -300, 1400, GY + 10, tp)
        step_pyramid(c, 540, GY, 0.9)
        txt('ASTECAS', 140, 540, 300, INK, -3)
    elif t < 3.05:
        waves(c, -300, 1400, GY + 10, tp)
        step_pyramid(c, 260, GY, 0.55); step_pyramid(c, 920, GY, 0.4)
        for k in range(3): rect(c, 460 + k * 100, GY - 110, 530 + k * 100, GY, 6, WHITE, seed=k)
        txt('TENOCHTITLÁN', 104, 540, 300, INK, -3)
        txt('(capital)', 56, 540, 420, DGRAY, 0, 'Bold')
    else:
        ground(c)
        campus(c, 230, GY, 0.45); step_pyramid(c, 850, GY, 0.4)
        txt('1096', 80, 230, 760 - 20, INK)
        txt('1325', 80, 850, 760 - 20, RED)
        v = counter(0, 229, t, 3.1, 4.6)
        arrowh(c, 340, 980, 340 + 380 * min(1, v / 229) + 30, 8, RED)
        txt(f'+{int(v)} ANOS', 66, 540, 900, RED, 0, 'Black')
        stamp('FUNDADA EM 1325', 540, 300, RED, -4, 96)

def s8(c, t, tp):
    if t < 1.89:
        ground(c)
        guillotine(c, 540, GY, 1.0, 0.0)
        txt('A ÚLTIMA GUILHOTINA', 76, 540, 300, INK, -3)
    elif t < 3.73:
        ground(c)
        calendar(c, 540, 700, '1977', 'FRANÇA')
        guillotine(c, 900, GY, 0.35, 0.0)
        txt('10 de setembro', 66, 540, 960, RED, 0, 'Black')
    else:
        ground(c)
        lift = min(140.0, max(0.0, (t - 4.8) * 200))
        rocket(c, 330, GY - 40 - lift, 0.9, tp, t > 4.8)
        probe(c, 780, 700, 0.9, 0.2 * math.sin(tp))
        txt('VOYAGER 1', 60, 780, 900, INK, 0, 'Black')
        txt('5 de setembro', 56, 780, 980, DGRAY, 0, 'Bold')
        if t < 4.34: txt('5 DIAS ANTES...', 110, 540, 300, INK, -3)
        else: stamp('MESMO ANO!', 540, 300, RED, -5, 140)
        if t > 4.8 and t < 5.0: impact(t, 4.8)

def s9(c, t, tp):
    if t < 1.09:
        ground(c)
        man(c, 540, GY, 1.2, 1, (-20, 75), (8, -8), 'smug')
        txt('OLHA DE NOVO', 120, 540, 300, INK, -3)
    elif t < 3.34:
        big_tl(c, t, tp, show_p=True, show_m=t > 2.0)
        if t < 2.18: txt('CLEÓPATRA', 100, 540, 300, INK, -3)
    elif t < 4.83:
        ground(c)
        man(c, 540, GY, 1.2, 1, (-150, 150), (8, -8), 'shock')
        qmark(c, 340, 720); qmark(c, 760, 680)
        txt('QUAL TE PEGOU?', 110, 540, 300, INK, -3)
    else:
        ground(c)
        cleo(c, 300, GY, 1.0, 1, (-20, -150), 'smile')
        astro(c, 780, GY, 1.0, -1, (-20, -150), 'smile')
        txt('SIGA', 200, 540, 330, RED, -4)
        heart(c, 540 + 10 * math.sin(tp * 5), 620, 0.7)
SCENES = [s0, s1, s2, s3, s4, s5, s6, s7, s8, s9]

# ---------- legendas: uma palavra por vez ----------
FP = '/usr/share/fonts/truetype/google-fonts/ofl/montserrat/Montserrat[wght].ttf'
_fc = {}
def font(size, weight='Bold'):
    k = (size, weight)
    if k not in _fc:
        f = ImageFont.truetype(FP, size)
        try: f.set_variation_by_name(weight)
        except Exception as e: print('var', e, file=sys.stderr)
        _fc[k] = f
    return _fc[k]

def caption(draw, i, t):
    ws = WR[i]; cur = None
    for k, (a, b, w) in enumerate(ws):
        nxt = ws[k + 1][0] if k + 1 < len(ws) else D[i]
        end = nxt if nxt - b < 0.28 else b + 0.06
        if a - 0.02 <= t < end: cur = k; break
    if cur is None: return
    s = DISP[i][cur]
    f = font(66, 'Bold')
    tw = draw.textlength(s, font=f)
    bh = 118; pad = int(bh * 0.19) + 12
    cx, cy = 540, 1290
    x0, x1 = cx - tw / 2 - pad, cx + tw / 2 + pad
    draw.rounded_rectangle((x0, cy - bh / 2, x1, cy + bh / 2), radius=6, fill=(0, 0, 0))
    draw.text((cx, cy + 2), s, font=f, fill=(255, 255, 255), anchor='mm')

def camera(i, t):
    sh = SHOTS.get(i) or [(0, 1, 1, (540, 640), (540, 640), False, 0)]
    cur = 0
    for k, s_ in enumerate(sh):
        if t >= s_[0]: cur = k
    t0, z0, z1, f0, f1, fix, wh = sh[cur]
    t1 = sh[cur + 1][0] if cur + 1 < len(sh) else D[i]
    lin = min(1, max(0, (t - t0) / max(0.01, t1 - t0)))
    u = 0.5 * lin + 0.5 * smoothstep(lin)
    Z = z0 + (z1 - z0) * u
    fx = f0[0] + (f1[0] - f0[0]) * u; fy = f0[1] + (f1[1] - f0[1]) * u
    wx = 0.0; whip = 0.0
    if wh and t - t0 < 0.2:
        v = (t - t0) / 0.2; wx = wh * 700 * (1 - v) ** 2; whip = 1 - v
    return Z, fx, fy, wx, fix, whip

def render_frame(i, k):
    global JS, TPG, ZL
    t = k / FPS
    P = int(t * 15)
    tp = P / 15.0
    TPG = tp
    JS = P % 3
    SHAKE[0] = 0; SHAKE[1] = 0
    TXT.clear()
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    c = cairo.Context(surf)
    c.set_source_rgb(1, 1, 1); c.paint()
    # a tremida de impacto é aplicada depois de desenhar (translação do contexto precisa vir antes)
    Z, fx, fy, wx, fixtxt, whip = camera(i, t)
    ZL = Z
    c.save()
    c.translate(540 + wx, 640); c.scale(Z, Z); c.translate(-fx, -fy)
    SCENES[i](c, t, tp)
    c.restore()
    buf = np.frombuffer(surf.get_data(), np.uint8).reshape(H, W, 4)
    img = Image.fromarray(buf[..., [2, 1, 0]].copy(), 'RGB')
    if SHAKE[0]:
        dx = int(SHAKE[0]); img = Image.fromarray(np.roll(np.array(img), dx, 1))
    dr = ImageDraw.Draw(img)
    for s, size, cx, cy, col, rot, wgt in TXT:
        if not s: continue
        if not fixtxt:
            cx = (cx - fx) * Z + 540 + wx; cy = (cy - fy) * Z + 640; size = max(8, int(size * Z))
        f = font(size, wgt)
        if rot:
            tw = int(dr.textlength(s, font=f)) + 40; th = int(size * 1.5)
            lay = Image.new('RGBA', (tw, th), (0, 0, 0, 0)); ImageDraw.Draw(lay).text((tw / 2, th / 2), s, font=f, fill=col + (255,), anchor='mm')
            lay = lay.rotate(rot, resample=Image.BICUBIC, expand=True)
            img.paste(lay, (int(cx - lay.width / 2), int(cy - lay.height / 2)), lay)
        else:
            dr.text((cx, cy), s, font=f, fill=col, anchor='mm')
    if whip > 0.05:  # riscos de velocidade no deslize de câmera
        for q in range(7):
            yy = int(200 + (nz(q, 4.1) * 0.5 + 0.5) * 1100); ln = int(300 + 600 * whip)
            x0 = int((nz(q, 8.3) * 0.5 + 0.5) * 700)
            dr.line((x0, yy, x0 + ln, yy), fill=(17, 17, 17), width=5)
    caption(dr, i, t)
    return img

def to_bgra(img):
    a = np.array(img)
    out = np.empty((H, W, 4), np.uint8)
    out[..., 0] = a[..., 2]; out[..., 1] = a[..., 1]; out[..., 2] = a[..., 0]; out[..., 3] = 255
    return out.tobytes()

if __name__ == '__main__':
    if sys.argv[1] == '--still':
        os.makedirs('stills', exist_ok=True)
        for arg in sys.argv[2:]:
            T = float(arg); i = int(np.searchsorted(STARTS, T, side='right') - 1)
            render_frame(i, int(round((T - STARTS[i]) * FPS))).save(f'stills/s_{T:05.2f}.png')
    else:
        i = int(sys.argv[1]); n = int(round(D[i] * FPS))
        os.makedirs('out', exist_ok=True)
        p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgra', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                              '-c:v', 'libx264', '-crf', '19', '-preset', 'veryfast', '-pix_fmt', 'yuv420p', f'out/s{i}.tmp.mp4'], stdin=subprocess.PIPE)
        last = None; lastkey = None
        for k in range(n):
            p.stdin.write(to_bgra(render_frame(i, k)))
        p.stdin.close(); rc = p.wait()
        if rc == 0: os.replace(f'out/s{i}.tmp.mp4', f'out/s{i}.mp4')
        print('scene', i, 'rc', rc)

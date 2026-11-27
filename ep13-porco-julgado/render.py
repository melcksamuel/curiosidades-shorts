# Ep13 — Animais no tribunal (porco julgado em 1386) — estilo STICKMAN SKETCH (traço de marcador, fundo branco, toques de cor chapada)
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
        st = (b - a) / len(ps)
        for k, p in enumerate(ps): out.append([a + k * st, a + (k + 1) * st, p])
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
    if hat == 'helmet':
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

# ---------- objetos do episódio (animais no tribunal) ----------
PINK = SKIN
def counter(v0, v1, t, a, b):
    u = smoothstep((t - a) / max(0.01, b - a)); return v0 + (v1 - v0) * u
PURP = (0.55, 0.36, 0.62)

def pig(c, x, y, s=1.0, f=1, expr='n', tp=0.0, dress=False, bars=False, walk=False):
    ph = tp * 6 + x * 0.01
    bob = (0.5 + 0.5 * math.sin(ph)) * 6 * s
    by = y - 120 * s - bob
    for k, dx in enumerate((-60, -25, 35, 70)):
        a = (20 * math.sin(tp * 14 + k * math.pi) if walk else 0)
        fx = x + f * dx * s; fy = by + 40 * s
        stroke(c, [(fx, fy), (fx + f * a * s * 0.8, y)], 9, INK, False, None, 1.0, k)
    stroke(c, [(x - f * 105 * s, by - 20 * s), (x - f * 130 * s, by - 40 * s), (x - f * 120 * s, by - 60 * s), (x - f * 140 * s, by - 55 * s)], 5, INK, False, None, 1, 9)
    ellipse(c, x, by, 115 * s, 72 * s, 8, PINK, seed=2)
    if dress:
        stroke(c, [(x - f * 40 * s, by - 68 * s), (x + f * 60 * s, by - 60 * s), (x + f * 70 * s, by + 50 * s), (x - f * 50 * s, by + 64 * s)], 7, INK, True, RED, 1.5, 4)
        for k in range(3): ellipse(c, x + f * 12 * s, by - 30 * s + k * 30 * s, 6 * s, 6 * s, 3, YEL, seed=k)
        rect(c, x - f * 95 * s if f > 0 else x + 35 * s, by + 20 * s, x - 35 * s if f > 0 else x + 95 * s, by + 60 * s, 6, BLUE, seed=5)
    hx, hy = x + f * 110 * s, by - 40 * s
    for sg in (-1, 1):
        ex0 = hx + sg * 30 * s
        stroke(c, [(ex0 - 18 * s, hy - 45 * s), (ex0 + sg * 6 * s, hy - 92 * s), (ex0 + 22 * s, hy - 40 * s)], 6, INK, True, PINK, 1.2, 6 + sg)
    ellipse(c, hx, hy, 62 * s, 58 * s, 8, PINK, seed=3)
    sx = hx + f * 50 * s
    ellipse(c, sx, hy + 12 * s, 26 * s, 22 * s, 7, PINK, seed=4)
    for sg in (-1, 1): ellipse(c, sx + sg * 8 * s, hy + 12 * s, 4 * s, 6 * s, 2, INK, INK)
    ex, ey = hx + f * 8 * s, hy - 16 * s
    if expr == 'shock':
        for sg in (-1, 1): ellipse(c, ex + sg * 18 * s, ey, 11 * s, 11 * s, 4, WHITE); ellipse(c, ex + sg * 18 * s, ey, 3.5 * s, 3.5 * s, 2, INK)
        ellipse(c, hx - f * 2 * s, hy + 34 * s, 8 * s, 10 * s, 4, INK)
    elif expr == 'smug':
        for sg in (-1, 1): stroke(c, [(ex + sg * 18 * s - 9 * s, ey), (ex + sg * 18 * s + 9 * s, ey)], 5)
        arc(c, hx, hy + 26 * s, 16 * s, 10 * s, 20, 160, 5)
    elif expr == 'sad':
        for sg in (-1, 1): ellipse(c, ex + sg * 18 * s, ey, 5 * s, 5 * s, 3, INK, INK)
        arc(c, hx, hy + 44 * s, 14 * s, 10 * s, 200, 340, 5)
    else:
        blink = (int(TPG * 15) + int(x)) % 37 == 0
        for sg in (-1, 1):
            if blink: stroke(c, [(ex + sg * 18 * s - 6 * s, ey), (ex + sg * 18 * s + 6 * s, ey)], 4)
            else: ellipse(c, ex + sg * 18 * s, ey, 5 * s, 5 * s, 3, INK, INK)
    if bars:
        for k in range(6):
            bx = x - 200 * s + k * 80 * s
            stroke(c, [(bx, y - 330 * s), (bx, y + 10 * s)], 10, INK, False, None, 1.0, k)
        stroke(c, [(x - 230 * s, y - 330 * s), (x + 230 * s, y - 330 * s)], 12)

def hood(c, x, y, s=1.0):
    hy = y - 252 * s
    stroke(c, [(x - 50 * s, hy + 40 * s), (x - 48 * s, hy - 30 * s), (x, hy - 80 * s), (x + 48 * s, hy - 30 * s), (x + 50 * s, hy + 40 * s)], 7, INK, True, INK, 1.2, 2)
    for sg in (-1, 1): ellipse(c, x + sg * 16 * s, hy - 6 * s, 9 * s, 7 * s, 2, WHITE, WHITE)

def wig(c, x, y, s=1.0):
    hy = y - 252 * s
    for sg in (-1, 1):
        for k in range(3): ellipse(c, x + sg * 50 * s, hy - 20 * s + k * 28 * s, 18 * s, 16 * s, 5, WHITE, seed=k + sg)
    stroke(c, ell_pts(x, hy - 14 * s, 50 * s, 44 * s, 0, 14, math.pi, 2 * math.pi), 6, INK, True, WHITE, 1.2, 3)

def judge(c, x, y, s=1.0, f=1, ang=0.0, expr='angry'):
    man(c, x, y, s, f, (-20, 120 if ang else 20), (8, -8), expr)
    wig(c, x, y, s)

def bench(c, x0, x1, y0, y1):
    rect(c, x0, y0, x1, y1, 9, BROWN, seed=4)
    for k in range(3): stroke(c, [(x0 + 30, y0 + 40 + k * 45), (x1 - 30, y0 + 40 + k * 45)], 5, LBROWN, False, None, 1.5, k)

def gallows(c, x, gy, s=1.0, sway=0.0):
    stroke(c, [(x - 120 * s, gy), (x + 120 * s, gy)], 10)
    rect(c, x - 18 * s, gy - 560 * s, x + 18 * s, gy, 8, BROWN, seed=2)
    rect(c, x - 18 * s, gy - 560 * s, x + 260 * s, gy - 524 * s, 8, BROWN, seed=3)
    stroke(c, [(x + 18 * s, gy - 440 * s), (x + 120 * s, gy - 524 * s)], 8, INK, False, None, 1, 4)
    rx = x + 220 * s + sway
    stroke(c, [(x + 220 * s, gy - 524 * s), (rx, gy - 380 * s)], 6, LBROWN)
    ellipse(c, rx, gy - 350 * s, 28 * s, 32 * s, 6, None)

def cradle(c, x, y, s=1.0):
    stroke(c, ell_pts(x, y - 60 * s, 150 * s, 90 * s, 0, 20, 0, math.pi), 9, INK, True, LBROWN, 1.5, 2)
    stroke(c, [(x - 150 * s, y - 60 * s), (x + 150 * s, y - 60 * s)], 9)
    ellipse(c, x - 70 * s, y - 90 * s, 34 * s, 34 * s, 6, PINK, seed=5)
    stroke(c, ell_pts(x + 30 * s, y - 70 * s, 90 * s, 26 * s, 0, 14, math.pi, 2 * math.pi), 6, INK, True, LBLUE, 1.2, 6)
    for sg in (-1, 1): stroke(c, [(x + sg * 120 * s, y + 10 * s), (x + sg * 90 * s, y - 20 * s)], 7)

def crowd(c, x0, x1, gy, n, tp, s=0.6, seed=0):
    for k in range(n):
        x = x0 + (x1 - x0) * k / max(1, n - 1) + 15 * nz(k + seed, 2)
        y = gy + 30 * ((k + seed) % 2)
        ph = tp * 8 + k
        man(c, x, y, s, 1 if k % 2 else -1, (-150 + 20 * math.sin(ph), 150 - 20 * math.sin(ph)) if k % 3 == 0 else (-20, 20), (6, -6), 'shock' if k % 4 == 1 else 'n', w=7)

def glove(c, x, y, s=1.0, f=1):
    pts = [(x - 40 * s, y + 60 * s), (x - 45 * s, y - 20 * s), (x - 70 * s, y - 50 * s), (x - 58 * s, y - 62 * s), (x - 32 * s, y - 40 * s),
           (x - 34 * s, y - 100 * s), (x - 18 * s, y - 104 * s), (x - 12 * s, y - 60 * s), (x - 6 * s, y - 112 * s), (x + 10 * s, y - 110 * s),
           (x + 10 * s, y - 60 * s), (x + 22 * s, y - 102 * s), (x + 38 * s, y - 98 * s), (x + 34 * s, y - 50 * s), (x + 50 * s, y - 80 * s), (x + 62 * s, y - 72 * s), (x + 42 * s, y + 60 * s)]
    stroke(c, [(x + f * (px - x), py) for px, py in pts], 7, INK, True, YEL, 1.2, 3)
    rect(c, x - 44 * s, y + 50 * s, x + 46 * s, y + 80 * s, 6, LBROWN, seed=4)

def scroll(c, cx, cy, w, h, lines=4, torn=False, seed=0):
    rect(c, cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, 8, rgb('FFF4D6'), seed=seed)
    for sg in (-1, 1): ellipse(c, cx, cy + sg * h / 2, w / 2 + 20, 22, 8, LBROWN, seed=seed + sg)
    for k in range(lines):
        yy = cy - h / 2 + 70 + k * (h - 140) / max(1, lines - 1)
        xr = cx + w / 2 - 50 - 60 * ((k + seed) % 2)
        stroke(c, [(cx - w / 2 + 50, yy), (xr, yy + 3)], 6, DGRAY, False, None, 1.5, k + seed)
    if torn:
        pts = [(cx - w / 2 + 10, cy + 10)] + [(cx - w / 2 + 10 + (w - 20) * j / 8, cy + 10 + (30 if j % 2 else -30)) for j in range(1, 9)] + [(cx + w / 2 - 10, cy + h / 2 - 25), (cx - w / 2 + 10, cy + h / 2 - 25)]
        stroke(c, pts, 6, INK, True, WHITE, 1.5, 7)
        txt('?', 120, cx, cy + h / 4 + 10, RED)

def rat(c, x, y, s=1.0, f=1, tp=0.0, expr='n', run=False):
    ph = tp * 16 + x * 0.05
    for k in (0, 1):
        a = 25 * math.sin(ph + k * math.pi) if run else 0
        lx = x + f * (k * 40 - 20) * s
        stroke(c, [(lx, y - 20 * s), (lx + f * a * s * 0.6, y)], 6)
    stroke(c, [(x - f * 70 * s, y - 40 * s), (x - f * 130 * s, y - 70 * s + 8 * math.sin(tp * 6) * s), (x - f * 170 * s, y - 40 * s)], 5, INK, False, None, 1, 4)
    ellipse(c, x, y - 50 * s, 75 * s, 40 * s, 7, LGRAY, seed=3)
    hx = x + f * 80 * s; hy = y - 60 * s
    stroke(c, [(hx - f * 30 * s, hy - 30 * s), (hx + f * 50 * s, hy + 4 * s), (hx - f * 30 * s, hy + 30 * s)], 7, INK, True, LGRAY, 1.0, 5)
    ellipse(c, hx + f * 52 * s, hy + 4 * s, 7 * s, 7 * s, 3, INK, INK)
    ellipse(c, hx - f * 26 * s, hy - 34 * s, 22 * s, 22 * s, 6, PINK, seed=6)
    if expr == 'shock':
        ellipse(c, hx + f * 4 * s, hy - 6 * s, 10 * s, 10 * s, 3, WHITE); ellipse(c, hx + f * 4 * s, hy - 6 * s, 3 * s, 3 * s, 2, INK)
    else: ellipse(c, hx + f * 4 * s, hy - 6 * s, 4 * s, 4 * s, 2, INK, INK)

def cat(c, x, y, s=1.0, f=1, tp=0.0):
    stroke(c, [(x - f * 60 * s, y - 60 * s), (x - f * 120 * s, y - 140 * s + 15 * math.sin(tp * 5) * s), (x - f * 100 * s, y - 200 * s)], 8, INK, False, None, 1, 4)
    for k in (-1, 1): stroke(c, [(x + k * 30 * s, y - 40 * s), (x + k * 34 * s, y)], 8)
    ellipse(c, x, y - 80 * s, 70 * s, 60 * s, 8, DGRAY, seed=2)
    hx, hy = x + f * 40 * s, y - 170 * s
    for sg in (-1, 1): stroke(c, [(hx + sg * 50 * s, hy - 20 * s), (hx + sg * 44 * s, hy - 80 * s), (hx + sg * 10 * s, hy - 44 * s)], 7, INK, True, DGRAY, 1, 5 + sg)
    ellipse(c, hx, hy, 58 * s, 50 * s, 8, DGRAY, seed=3)
    for sg in (-1, 1):
        ellipse(c, hx + sg * 22 * s, hy - 8 * s, 12 * s, 10 * s, 3, YEL, seed=sg)
        stroke(c, [(hx + sg * 22 * s, hy - 16 * s), (hx + sg * 22 * s, hy)], 4)
        stroke(c, [(hx + sg * 30 * s, hy - 30 * s), (hx + sg * 8 * s, hy - 20 * s)], 5)
        for k in (-1, 1): stroke(c, [(hx + sg * 20 * s, hy + 16 * s), (hx + sg * 70 * s, hy + 16 * s + k * 10 * s)], 3, WHITE)
    stroke(c, [(hx - 14 * s, hy + 26 * s), (hx, hy + 18 * s), (hx + 14 * s, hy + 26 * s)], 4, WHITE)

def beetle(c, x, y, s=1.0, tp=0.0, rot=0.0, tie=False):
    c.save(); c.translate(x, y); c.rotate(rot)
    for k in range(3):
        for sg in (-1, 1):
            a = 8 * math.sin(tp * 18 + k + sg)
            stroke(c, [(sg * 30 * s, (-20 + k * 22) * s), (sg * 62 * s, (-30 + k * 26 + a) * s), (sg * 72 * s, (-10 + k * 30 + a) * s)], 5, INK, False, None, 0.8, k)
    ellipse(c, 0, -60 * s, 26 * s, 22 * s, 6, DGRAY, seed=4)
    for sg in (-1, 1): stroke(c, [(sg * 10 * s, -78 * s), (sg * 40 * s, -120 * s), (sg * 52 * s, -112 * s)], 4)
    ellipse(c, 0, 0, 44 * s, 58 * s, 7, GREEN, seed=2)
    stroke(c, [(0, -55 * s), (0, 56 * s)], 5)
    for sg in (-1, 1): ellipse(c, sg * 10 * s, -64 * s, 6 * s, 6 * s, 2, WHITE, WHITE)
    if tie: stroke(c, [(0, -40 * s), (-12 * s, 10 * s), (12 * s, 10 * s)], 4, INK, True, RED, 0.8)
    c.restore()

def vine(c, x, gy, s=1.0, eaten=0.0, seed=0):
    stroke(c, [(x, gy), (x - 10 * s, gy - 160 * s), (x + 5 * s, gy - 300 * s)], 9, INK, False, None, 1.5, seed)
    for k, (dx, dy) in enumerate([(-70, -260), (70, -220), (-60, -150)]):
        if nz(k + seed, 4) * 0.5 + 0.5 < eaten:
            ellipse(c, x + dx * s, gy + dy * s, 40 * s, 22 * s, 5, LBROWN, rot=0.4 * (1 if dx > 0 else -1), seed=k)
            continue
        ellipse(c, x + dx * s, gy + dy * s, 48 * s, 28 * s, 6, GREEN, rot=0.4 * (1 if dx > 0 else -1), seed=k)
    if eaten < 0.7:
        for j, (dx, dy) in enumerate([(0, 0), (-22, 0), (22, 0), (-11, 22), (11, 22), (0, 44)]):
            ellipse(c, x + 40 * s + dx * s, gy - 200 * s + dy * s, 14 * s, 14 * s, 4, PURP, seed=j)

def plot_land(c, x0, y0, x1, y1, dry=False, sign='SÓ PRA ELES'):
    rect(c, x0, y0, x1, y1, 8, LBROWN if dry else rgb('CFE8B0'), seed=3)
    if dry:
        for k in range(6):
            sx = x0 + 60 + k * (x1 - x0 - 120) / 5
            stroke(c, [(sx, y0 + 30), (sx + 25, y0 + (y1 - y0) * 0.4), (sx - 10, y0 + (y1 - y0) * 0.7), (sx + 20, y1 - 20)], 5, BROWN, False, None, 1.5, k)
    else:
        for k in range(8):
            gx = x0 + 50 + k * (x1 - x0 - 100) / 7
            stroke(c, [(gx - 12, y0 + 90 + 40 * (k % 2)), (gx, y0 + 70 + 40 * (k % 2)), (gx + 12, y0 + 90 + 40 * (k % 2))], 4, GREEN, False, None, 1, k)
    for k in range(int((x1 - x0) / 90) + 1):
        px = x0 + k * 90
        stroke(c, [(px, y0 - 50), (px, y0 + 10)], 6, BROWN)
    stroke(c, [(x0, y0 - 30), (x1, y0 - 30)], 5, BROWN)
    if sign:
        rect(c, (x0 + x1) / 2 - 210, y0 - 170, (x0 + x1) / 2 + 210, y0 - 80, 7, WHITE, seed=6)
        stroke(c, [((x0 + x1) / 2, y0 - 80), ((x0 + x1) / 2, y0 - 30)], 7, BROWN)
        txt(sign, 50, (x0 + x1) / 2, y0 - 125, INK, 0, 'Black')

def lawyer(c, x, y, s=1.0, f=1, arm=(-20, 20), expr='smug'):
    return man(c, x, y, s, f, arm, (8, -8), expr, prop='tie')

def drawer(c, x0, y0, x1, y1, n=3, open_k=-1):
    rect(c, x0, y0, x1, y1, 9, LBROWN, seed=2)
    hh = (y1 - y0) / n
    for k in range(n):
        dx = 60 if k == open_k else 0
        rect(c, x0 + 20 + dx, y0 + k * hh + 14, x1 - 20 + dx, y0 + (k + 1) * hh - 14, 7, BROWN if k != open_k else LBROWN, seed=k + 3)
        rect(c, (x0 + x1) / 2 - 40 + dx, y0 + (k + 0.5) * hh - 12, (x0 + x1) / 2 + 40 + dx, y0 + (k + 0.5) * hh + 12, 5, WHITE, seed=k)

# ---------- cenas ----------
def s0(c, t, tp):
    if t < 1.89:
        ground(c)
        pig(c, 600, GY, 1.4, -1, 'shock', tp)
        txt('1386', 190, 540, 330, RED, -4)
        if t > 0.6: txt('FRANÇA', 64, 540, 470, INK, 0, 'Black')
    elif t < 3.74:
        ground(c)
        pig(c, 560, GY, 1.3, -1, 'sad' if t > 3.21 else 'n', tp, bars=t > 3.21)
        if t > 3.21: splat_rays(c, 560, 700, t - 3.21, 10); txt('PRESO', 140, 540, 300, INK, -3)
        else: txt('UM PORCO', 130, 540, 300, INK, -3)
    elif t < 4.56:
        ground(c)
        bench(c, 320, 900, 820, GY)
        judge(c, 610, 820, 1.0, -1, 1)
        ang = -0.9 if t < 3.9 else 0.2
        gavel(c, 420, 740, ang)
        if t >= 3.9: impact(t, 3.9); splat_rays(c, 360, 800, t - 3.9, 10)
        txt('JULGADO', 130, 540, 300, INK, -3)
    else:
        ground(c)
        gallows(c, 380, GY, 1.0, 12 * math.sin(tp * 3))
        pig(c, 820, GY, 0.9, -1, 'shock', tp)
        if t > 4.56: stamp('CONDENADO', 540, 300, RED, -6, 120)
        if t > 5.11: impact(t, 5.11)

def s1(c, t, tp):
    if t < 2.38:
        ground(c)
        cradle(c, 300, GY - 20, 1.0)
        pig(c, 760, GY, 1.0, -1, 'n', tp, walk=t < 1.27)
        txt('O CRIME', 120, 540, 300, INK, -3)
        if t > 1.27:
            txt('!', 160, 300, 700, RED); splat_rays(c, 300, 900, t - 1.27, 10, RED)
    else:
        ground(c)
        bench(c, 80, 520, 820, GY)
        judge(c, 300, 820, 0.9, 1, 1 if t > 3.57 else 0)
        pig(c, 820, GY, 0.95, -1, 'shock' if t > 3.57 else 'n', tp)
        if t < 3.57: txt('TRIBUNAL', 110, 540, 300, INK)
        else: stamp('ASSASSINATO', 540, 300, RED, -5, 104); impact(t, 3.57)

def s2(c, t, tp):
    if t < 1.88:
        ground(c)
        gallows(c, 300, GY, 1.0, 8 * math.sin(tp * 3))
        crowd(c, 600, 1000, GY, 4, tp, 0.6)
        txt('RELATOS DIZEM...', 84, 540, 300, DGRAY, 0, 'Black')
    elif t < 2.92:
        ground(c)
        pig(c, 540, GY, 1.5, 1, 'smug', tp, dress=True)
        txt('VESTIDO DE GENTE', 86, 540, 300, INK, -3)
        if t < 2.2: splat_rays(c, 540, 800, t - 1.88, 12, YEL)
    else:
        ground(c)
        gallows(c, 540, GY - 120, 0.7, 8 * math.sin(tp * 3))
        crowd(c, 60, 1020, GY + 40, 7, tp, 0.55, 3)
        if t > 3.55: txt('MULTIDÃO', 130, 540, 300, INK, -3)

def s3(c, t, tp):
    ground(c)
    man(c, 380, GY, 1.1, 1, (-20, 70) if t > 1.27 else (-20, 20), (8, -8), 'smug' if t > 1.27 else 'n')
    hood(c, 380, GY, 1.1)
    if t < 1.27: txt('O CARRASCO', 110, 540, 300, INK, -3)
    if t > 1.27:
        glove(c, 720, 820, 1.3, 1); glove(c, 860, 840, 1.1, -1)
        splat_rays(c, 790, 790, t - 1.27, 10, YEL)
        txt('+ LUVAS NOVAS', 96, 540, 300, RED, -4)
        txt('pelo serviço', 60, 790, 1010 - 30, DGRAY, 0, 'Bold')

def s4(c, t, tp):
    if t < 1.19:
        ground(c)
        man(c, 540, GY, 1.2, 1, (-20, 20), (8, -8), 'angry')
        stroke(c, [(420, 540), (380, 560)], 6); stroke(c, [(660, 540), (700, 560)], 6)
        txt('NÃO ERA PIADA', 110, 540, 300, INK, -3)
    else:
        v = int(counter(0, 196, t, 1.5, 2.6))
        n = min(8, int(v / 25) + 1)
        for k in range(n):
            scroll(c, 230 + (k % 4) * 205, 920 - (k // 4) * 200 + 6 * math.sin(k), 150, 160, 3, seed=k)
        txt(f'~{max(v, 1) if v < 196 else 200}', 170, 540, 280, RED, -3)
        txt('PROCESSOS', 80, 540, 420, INK, 0, 'Black')
        if t > 3.52:
            rat(c, 200, 1040, 0.6, 1, tp); pig(c, 540, GY, 0.55, 1, 'n', tp); beetle(c, 880, 990, 0.8, tp)

def s5(c, t, tp):
    if t < 1.42:
        calendar(c, 540, 620, 'XVI', 'SÉCULO')
        ground(c)
    elif t < 3.48:
        ground(c)
        eaten = smoothstep((t - 2.0) / 1.2)
        wheat(c, 90, 990, GY, 14, tp, eaten, 3)
        for k, x in enumerate((240, 560, 840)): rat(c, x + 30 * math.sin(tp * 2 + k), GY, 0.85, 1 if k % 2 else -1, tp, 'n', True)
        txt('RATOS', 140, 540, 300, INK, -3)
        if t > 2.18: txt('comeram a cevada', 62, 540, 430, DGRAY, 0, 'Bold')
    else:
        ground(c)
        lawyer(c, 400, GY, 1.1, 1, (-20, 70) if t > 3.91 else (-20, 20))
        for k, x in enumerate((680, 830)): rat(c, x, GY, 0.8, -1, tp, 'n')
        if t > 3.91: stamp('ADVOGADO', 540, 300, RED, -5, 130); splat_rays(c, 400, 800, t - 3.91, 10)

def s6(c, t, tp):
    if t < 1.04:
        ground(c)
        lawyer(c, 540, GY, 1.2, 1, (-20, 150))
        txt('A DEFESA', 130, 540, 300, INK, -3)
    else:
        ground(c)
        building(c, 900, GY, 0.65)
        txt('TRIBUNAL', 46, 900, 1090 - 300, INK, 0, 'Black')
        for k, x in enumerate((120, 250)): rat(c, x, GY, 0.7, 1, tp, 'shock' if t > 2.96 else 'n')
        if t > 2.45:
            cat(c, 500, GY, 1.0, -1, tp)
            if t < 2.7: splat_rays(c, 500, 900, t - 2.45, 10)
        if t > 2.96: txt('MEDO DOS GATOS', 96, 540, 300, RED, -3)
        else: txt('não iam ao tribunal', 66, 540, 300, INK, 0, 'Black')

def s7(c, t, tp):
    if t < 1.81:
        calendar(c, 540, 620, '1587', 'ANO')
        ground(c)
    elif t < 4.48:
        ground(c)
        eaten = smoothstep((t - 2.4) / 1.6)
        for k, x in enumerate((180, 420, 660, 900)): vine(c, x, GY, 1.0, eaten, k * 3)
        for k in range(5):
            bx = 150 + k * 190 + 20 * math.sin(tp * 3 + k); by = 880 + 50 * math.sin(tp * 2 + k * 1.7)
            beetle(c, bx, by, 0.6, tp, 0.5 * math.sin(tp + k))
        txt('BESOUROS', 130, 540, 300, INK, -3)
        if t > 2.71: txt('nos vinhedos', 62, 540, 430, DGRAY, 0, 'Bold')
    else:
        ground(c)
        lawyer(c, 330, GY, 1.1, 1, (-20, 70) if t > 5.88 else (-20, 20))
        beetle(c, 720, 900, 1.6, tp, 0.0, tie=True)
        if t > 5.88: stamp('ADVOGADO', 540, 300, RED, -5, 130); splat_rays(c, 720, 900, t - 5.88, 10)
        else: txt('os insetos também', 76, 540, 300, INK, 0, 'Black')

def s8(c, t, tp):
    if t < 2.92:
        ground(c)
        plot_land(c, 160, 760, 920, GY - 10, False, 'SÓ PRA ELES' if t > 0.99 else '')
        for k in range(4): beetle(c, 300 + k * 160, 940 + 30 * math.sin(tp * 3 + k), 0.5, tp, 1.4 + 0.2 * math.sin(tp * 2 + k))
        txt('A VILA OFERECEU', 96, 540, 300, INK, -3)
    else:
        ground(c)
        dry = t > 4.34
        plot_land(c, 500, 860, 1020, GY - 10, dry, '')
        lawyer(c, 300, GY, 1.1, 1, (-140, 140) if t < 3.58 else (-60, 60), 'angry' if t > 3.58 else 'n')
        beetle(c, 620, 790, 0.7, tp, 0.0, tie=True)
        if t > 3.58 and t < 4.34: stamp('RECUSOU', 540, 300, RED, -5, 140); impact(t, 3.58)
        if t > 4.34: stamp('RUIM DEMAIS', 540, 300, RED, -5, 116); splat_rays(c, 760, 960, t - 4.34, 10, BROWN)

def s9(c, t, tp):
    if t < 1.52:
        scroll(c, 540, 700, 520, 560, 5)
        txt('O VEREDITO', 120, 540, 300, INK, -3)
    elif t < 3.48:
        drawer(c, 200, 600, 560, GY, 3, 1)
        scroll(c, 800, 780, 300, 380, 3, torn=True)
        stamp('SUMIU', 540, 300, RED, -5, 150)
        if t < 1.8: impact(t, 1.52); splat_rays(c, 800, 780, t - 1.52, 10)
    elif t < 5.49:
        ground(c)
        pig(c, 600, GY, 1.2, -1, 'sad', tp, bars=True)
        txt('VOCÊ DEFENDERIA', 92, 540, 300, INK, -3)
        txt('O PORCO?', 110, 540, 420, RED, -3)
    else:
        ground(c)
        pig(c, 700, GY, 1.0, -1, 'smug', tp, dress=True)
        man(c, 280, GY, 1.0, 1, (-150, 150), (8, -8), 'smile')
        txt('SIGA', 200, 540, 330, RED, -4)
        heart(c, 540 + 10 * math.sin(tp * 5), 560, 0.7)

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

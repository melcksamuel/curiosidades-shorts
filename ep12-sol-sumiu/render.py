# Ep12 — E se o Sol sumisse? — estilo STICKMAN SKETCH (traço de marcador, fundo branco, toques de cor chapada)
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

# ---------- objetos do episódio (e se o Sol sumisse?) ----------
STARS = [(80, 180), (260, 380), (420, 140), (760, 160), (930, 520), (980, 300), (170, 560), (640, 260), (330, 700), (850, 760), (110, 900), (1000, 880)]

def stars_bg(c, tp, fill=True):
    for k, (x, y) in enumerate(STARS):
        r = 16 + 6 * ((k * 7) % 3)
        tw = 1 + 0.25 * math.sin(tp * 4 + k)
        stroke(c, [(x - r * tw, y), (x + r * tw, y)], 5, INK, False, None, 0.8, k)
        stroke(c, [(x, y - r * tw), (x, y + r * tw)], 5, INK, False, None, 0.8, k + 3)
        if fill and k % 3 == 0: ellipse(c, x + 30, y + 26, 6, 6, 3, YEL, seed=k)

def sun(c, x, y, r, tp, face=False, smile=True):
    rot = tp * 0.6
    for k in range(12):
        a = rot + k * math.pi / 6
        r0 = r * 1.18; r1 = r * (1.45 + 0.08 * math.sin(tp * 5 + k))
        stroke(c, [(x + r0 * math.cos(a), y + r0 * math.sin(a)), (x + r1 * math.cos(a), y + r1 * math.sin(a))], 8, INK, False, None, 1.2, k)
    ellipse(c, x, y, r, r, 9, YEL, seed=5)
    if face:
        for sg in (-1, 1): ellipse(c, x + sg * r * 0.32, y - r * 0.15, r * 0.07, r * 0.09, 3, INK, INK)
        if smile: arc(c, x, y + r * 0.05, r * 0.4, r * 0.35, 20, 160, 7)
        else: ellipse(c, x, y + r * 0.35, r * 0.12, r * 0.16, 5, INK)

def ghost(c, x, y, r, col=DGRAY, n=16, w=6):
    # contorno tracejado de algo que sumiu
    for k in range(n):
        a0 = k * 2 * math.pi / n; a1 = a0 + math.pi / n
        stroke(c, ell_pts(x, y, r, r, 0, 4, a0, a1), w, col, False, None, 1.0, k)

def earth(c, x, y, r, frozen=False, seed=0):
    ellipse(c, x, y, r, r, 9, LBLUE if frozen else BLUE, seed=7 + seed)
    blobs = [[(-0.6, -0.3), (-0.2, -0.55), (0.1, -0.2), (-0.3, 0.1)], [(0.2, 0.2), (0.6, 0.0), (0.55, 0.45), (0.25, 0.55)]]
    for k, bl in enumerate(blobs):
        stroke(c, [(x + px * r, y + py * r) for px, py in bl], 7, INK, True, WHITE if frozen else GREEN, 1.5, 8 + k)
    if frozen:
        stroke(c, ell_pts(x, y - r * 0.75, r * 0.5, r * 0.18, 0, 16), 6, INK, True, WHITE, 1.2, 12)

def moon(c, x, y, r):
    ellipse(c, x, y, r, r, 9, LGRAY, seed=4)
    for k, (dx, dy, rr) in enumerate([(-0.35, -0.3, 0.18), (0.3, 0.1, 0.24), (-0.1, 0.45, 0.12)]):
        ellipse(c, x + dx * r, y + dy * r, rr * r, rr * r, 5, WHITE, seed=k)

def hatch(c, x0, y0, x1, y1, gap=34, w=5):
    c.save(); c.rectangle(x0, y0, x1 - x0, y1 - y0); c.clip()
    k = 0; s = x0 - (y1 - y0)
    while s < x1:
        stroke(c, [(s, y1), (s + (y1 - y0), y0)], w, INK, False, None, 1.5, k); s += gap; k += 1
    c.restore()

def xmark(c, x, y, r, w=14):
    stroke(c, [(x - r, y - r), (x + r, y + r)], w, RED); stroke(c, [(x + r, y - r), (x - r, y + r)], w, RED)

def watch(c, cx, cy, r, secs, size=None):
    m = int(secs // 60); s = int(secs % 60)
    rect(c, cx - 22, cy - r - 50, cx + 22, cy - r - 10, 7, LGRAY)
    stroke(c, [(cx + r * 0.7, cy - r * 0.82), (cx + r * 0.86, cy - r * 0.98)], 12)
    ellipse(c, cx, cy, r, r, 10, WHITE, seed=6)
    frac = (secs % 60) / 60
    pts = [(cx, cy)] + ell_pts(cx, cy, r * 0.8, r * 0.8, -math.pi / 2, 24, 0, 2 * math.pi * max(0.01, frac))
    if frac > 0.02: stroke(c, pts, 5, INK, True, LBLUE, 0.8)
    txt(f'{m}:{s:02d}', size or int(r * 0.52), cx, cy + 6, INK)

def leaf(c, x, y, s=1.0, col=GREEN):
    pts = [(x, y + 160 * s), (x - 120 * s, y + 20 * s), (x - 70 * s, y - 120 * s), (x, y - 170 * s), (x + 70 * s, y - 120 * s), (x + 120 * s, y + 20 * s)]
    stroke(c, pts, 9, INK, True, col, 2.0, 3)
    stroke(c, [(x, y + 220 * s), (x, y - 130 * s)], 7)
    for k in range(3):
        yy = y - 60 * s + k * 60 * s
        for sg in (-1, 1): stroke(c, [(x, yy + 30 * s), (x + sg * 70 * s, yy - 10 * s)], 5)

def plant(c, x, gy, wilt=0.0, s=1.0, seed=0):
    col = tuple(GREEN[j] + (LBROWN[j] - GREEN[j]) * wilt for j in range(3))
    h = 200 * s
    top = (x + 90 * s * wilt, gy - h * (1 - 0.45 * wilt))
    mid = (x + 10 * s * wilt, gy - h * 0.55)
    stroke(c, [(x, gy), mid, top], 7, INK, False, None, 1.2, seed)
    for k, (px, py) in enumerate([mid, top]):
        for sg in (-1, 1):
            droop = wilt * 60 * s
            ellipse(c, px + sg * 40 * s, py + droop * 0.6, 40 * s, 18 * s, 5, col, rot=sg * (0.5 - 1.3 * wilt), seed=seed + k * 2 + sg)
    stroke(c, [(x - 60 * s, gy), (x + 60 * s, gy)], 6, INK, False, None, 1, seed + 9)
    rect(c, x - 45 * s, gy, x + 45 * s, gy + 70 * s, 7, LBROWN, seed=seed + 4)

def plate(c, x, y, s=1.0):
    ellipse(c, x, y, 150 * s, 50 * s, 8, WHITE, seed=3)
    ellipse(c, x, y, 95 * s, 30 * s, 5, WHITE, seed=4)

def fish(c, x, y, s=1.0, f=1, tp=0.0):
    w = 12 * math.sin(tp * 9)
    stroke(c, [(x - f * 70 * s, y), (x - f * 125 * s, y - 40 * s + w), (x - f * 125 * s, y + 40 * s + w)], 6, INK, True, RED, 1.2, 5)
    ellipse(c, x, y, 85 * s, 50 * s, 8, YEL, seed=2)
    ellipse(c, x + f * 45 * s, y - 10 * s, 7 * s, 7 * s, 3, INK, INK)
    arc(c, x + f * 60 * s, y + 12 * s, 14 * s, 8 * s, 20, 160, 4)

def bubbles_up(c, x, y, tp, n=5, spread=60, hgt=300):
    for k in range(n):
        per = 1.1 + 0.2 * (k % 3)
        u = ((tp + k * 0.37) % per) / per
        bx = x + (k - n / 2) * spread / n * 2 + 10 * math.sin(tp * 6 + k)
        ellipse(c, bx, y - u * hgt, 9 + 4 * (k % 3), 9 + 4 * (k % 3), 4, WHITE, seed=k)

def vent(c, x, gy, s=1.0, tp=0.0):
    stroke(c, [(x - 150 * s, gy), (x - 60 * s, gy - 300 * s), (x - 40 * s, gy - 320 * s), (x + 40 * s, gy - 320 * s), (x + 60 * s, gy - 300 * s), (x + 150 * s, gy)], 9, INK, True, BROWN, 2.0, 6)
    hatch(c, x - 40 * s, gy - 320 * s, x + 40 * s, gy - 290 * s, 18, 4)
    for k in range(4):
        per = 1.3; u = ((tp + k * 0.33) % per) / per
        r = (30 + 60 * u) * s
        ellipse(c, x + 30 * math.sin(tp * 3 + k) * s, gy - (340 + 330 * u) * s, r, r * 0.8, 6, DGRAY if k % 2 else LGRAY, seed=k)
    heatwaves(c, x, gy - 340 * s, tp, RED, 3, 50 * s, 180 * s)

def microbe(c, x, y, s=1.0, tp=0.0, seed=0, glasses=False):
    wob = 0.08 * math.sin(tp * 5 + seed)
    for k in range(6):
        a = k * math.pi / 3 + wob
        stroke(c, [(x + 52 * s * math.cos(a), y + 40 * s * math.sin(a)), (x + 72 * s * math.cos(a + 0.2), y + 58 * s * math.sin(a + 0.2))], 5)
    ellipse(c, x, y, 55 * s, 42 * s, 7, GREEN, rot=wob, seed=seed)
    for sg in (-1, 1): ellipse(c, x + sg * 17 * s, y - 8 * s, 5 * s, 5 * s, 2, INK, INK)
    arc(c, x, y + 4 * s, 18 * s, 12 * s, 20, 160, 5)
    if glasses:
        for sg in (-1, 1): rect(c, x + sg * 17 * s - 14 * s, y - 18 * s, x + sg * 17 * s + 14 * s, y - 2 * s, 4, INK, INK, 0, 0.5)
        stroke(c, [(x - 4 * s, y - 12 * s), (x + 4 * s, y - 12 * s)], 4)

def snow(c, tp, x0=0, x1=1080, y0=120, y1=1080, n=12, speed=220):
    for k in range(n):
        x = x0 + (x1 - x0) * ((k * 0.618) % 1) + 18 * math.sin(tp * 2 + k)
        y = y0 + ((tp * speed + k * 97) % (y1 - y0))
        flake(c, x, y, 16 + 6 * (k % 3))

def ice_block(c, x0, y0, x1, y1):
    rect(c, x0, y0, x1, y1, 9, None, seed=8)
    stroke(c, [(x0 + 30, y0 + 40), (x0 + 30, y0 + 140)], 8, WHITE)
    stroke(c, [(x1 - 40, y1 - 120), (x1 - 40, y1 - 40)], 8, LBLUE)

def shiver(tp): return 5 * math.sin(tp * 47)

def counter(v0, v1, t, a, b):
    u = smoothstep((t - a) / max(0.01, b - a)); return v0 + (v1 - v0) * u

# ---------- cenas ----------
def s0(c, t, tp):
    if t < 2.75:
        ground(c)
        if t < 0.63:
            sun(c, 800, 330, 110, tp, face=True)
            man(c, 420, GY, 1.1, 1, (-25, 30), (8, -8), 'smile')
        else:
            ghost(c, 800, 330, 110)
            splat_rays(c, 800, 330, t - 0.63, 12, YEL)
            if t < 1.67: txt('?', 150, 800, 330, RED)
            # a luz que já estava a caminho continua chegando
            for k in range(4):
                u = ((tp * 1.2 + k * 0.25) % 1)
                x = 760 - 300 * u; y = 380 + 330 * u
                stroke(c, [(x, y), (x - 50, y + 55)], 8, YEL)
            man(c, 420, GY, 1.1, 1, (-25, 30), (8, -8), 'smile')
            if t < 1.67: txt('SUMIU', 130, 330, 290, RED, -4)
    else:
        secs = counter(0, 500, t, 2.75, 4.2)
        watch(c, 540, 600, 240, secs)
        man(c, 880, 960, 0.55, -1, (-130, 130) if t > 4.2 else (-15, 15), (8, -8), 'shock' if t > 4.2 else 'n')
        if t > 4.2: impact(t, 4.2); splat_rays(c, 540, 600, t - 4.2, 12)

def s1(c, t, tp):
    stars_bg(c, tp, False)
    sun(c, 150, 620, 115, tp)
    earth(c, 930, 640, 85)
    man(c, 930, 555, 0.28, -1, (-20, 20), (8, -8), 'n', w=5)
    p = smoothstep((t - 0.6) / 2.3)
    xf = 290 + (850 - 290) * p
    for kind, yy, col in ((0, 560, YEL), (1, 700, BLUE)):
        start = 0.6 if kind == 0 else 1.0
        if t < start: continue
        pts = [(290 + j * 12, yy + 22 * math.sin((290 + j * 12) * 0.045 - tp * 9)) for j in range(int((xf - 290) / 12) + 1)]
        if len(pts) > 1: stroke(c, pts, 9, col, False, None, 0.6, kind)
    if t > 0.91: txt('LUZ', 64, 540, 480, INK, 0, 'ExtraBold')
    if t > 1.29: txt('GRAVIDADE', 64, 540, 800, BLUE, 0, 'ExtraBold')
    if t > 1.87: txt('150 milhões de km', 54, 540, 900, DGRAY, 0, 'Bold')
    if t > 2.9: splat_rays(c, 930, 640, t - 2.9, 12, YEL)

def s2(c, t, tp):
    if t < 1.51:
        watch(c, 540, 600, 240, 500)
        if t > 0.93: impact(t, 0.93); splat_rays(c, 540, 600, t - 0.93, 12, RED)
    elif t < 2.95:
        hatch(c, -300, -300, 1400, GY, 30, 6)
        ghost(c, 800, 330, 110, WHITE, 16, 8)
        ground(c)
        rect(c, 80, 190, 1000, 395, 0.1, WHITE, WHITE, 0, 0)
        txt('TUDO APAGA', 130, 540, 290, INK, -3)
        man(c, 540, GY, 1.1, 1, (-140, 140), (14, -14), 'shock')
    elif t < 4.31:
        stars_bg(c, tp, False)
        if t < 3.33: moon(c, 540, 600, 190)
        else:
            ghost(c, 540, 600, 190)
            splat_rays(c, 540, 600, t - 3.33, 12, DGRAY)
            xmark(c, 540, 600, 150)
        txt('LUA', 140, 540, 300, INK)
    else:
        stars_bg(c, tp, True)
        for k, (x, y) in enumerate([(250, 420), (540, 330), (830, 450)]): star(c, x, y, 40 + 8 * math.sin(tp * 4 + k))
        ground(c)
        man(c, 540, GY, 1.1, 1, (-160, 20), (8, -8), 'smile')
        if t > 4.55: txt('ESTRELAS: CONTINUAM', 76, 540, 240, INK, 0, 'Black')

def earth_pos(t):
    if t < 1.11:
        a = math.radians(90 + (1.11 - t) * 60)
        return 540 + 300 * math.cos(a), 600 + 300 * math.sin(a)
    return 540 + 260 * (t - 1.11), 900

def s3(c, t, tp):
    if t < 2.72:
        stars_bg(c, tp, False)
        ghost(c, 540, 600, 90)
        for k in range(24):
            a0 = k * 2 * math.pi / 24
            stroke(c, ell_pts(540, 600, 300, 300, 0, 3, a0, a0 + math.pi / 24), 4, LGRAY, False, None, 0.8, k)
        ex, ey = earth_pos(t)
        if t > 1.11:
            for k in range(int((ex - 540) / 50)):
                stroke(c, [(540 + k * 50, 900), (540 + k * 50 + 26, 900)], 6, RED)
            for k in range(3): stroke(c, [(ex - 110 - 30 * k, ey - 40 + 40 * k), (ex - 170 - 30 * k, ey - 40 + 40 * k)], 5, INK)
        earth(c, ex, ey, 60)
        if 1.11 < t < 1.8: txt('TANGENTE!', 90, 540, 1000, RED, -3)
        if t > 1.94: txt('LINHA RETA', 70, ex, 780, INK, 0, 'Black')
    else:
        v = counter(0, 30, t, 2.82, 3.9)
        speedo(c, 540, 680, 280, v, 30)
        txt(f'{int(round(v))} km/s', 110, 540, 860, RED)
        ex = 760 + ((tp * 500) % 500)
        earth(c, 200 + ((tp * 260) % 700), 1000, 55)
        txt('por segundo', 54, 540, 360, DGRAY, 0, 'Bold')

def s4(c, t, tp):
    if t < 0.86:
        calendar(c, 540, 620, '1', 'DIA')
        man(c, 880, GY, 0.7, -1, (-20, 20), (6, -6), 'n')
        ground(c)
    elif t < 2.09:
        lvl = counter(0.75, 0.35, t, 0.9, 2.0)
        thermo(c, 360, 760, lvl)
        temp = counter(15, -5, t, 0.9, 2.0)
        txt(f'{int(round(temp))}°C', 150, 720, 640, BLUE if temp < 0 else INK)
        txt('esfria...', 64, 720, 790, DGRAY, 0, 'Bold')
    else:
        snow(c, tp)
        ground(c)
        x = 540 + shiver(tp)
        man(c, x, GY, 1.1, 1, (-60, 60), (4, -4), 'shock')
        txt('-20°C', 170, 540, 300, BLUE, -3)
        txt('POR DIA', 70, 540, 420, INK, 0, 'Black')

def s5(c, t, tp):
    if t < 0.91:
        calendar(c, 540, 620, '3', 'DIA')
        man(c, 880, GY, 0.7, -1, (-20, 20), (6, -6), 'shock')
        ground(c)
    elif t < 1.88:
        snow(c, tp, n=10)
        earth(c, 540, 680, 280, frozen=True)
        txt('O MUNDO INTEIRO', 96, 540, 280, INK)
    else:
        snow(c, tp, n=8)
        ground(c)
        rect(c, 330, 720, 750, GY, 0.1, LBLUE, LBLUE, 0, 1)
        man(c, 540, GY, 1.1, 1, (-30, 30), (6, -6), 'shock')
        ice_block(c, 330, 720, 750, GY)
        txt('ABAIXO DE 0°C', 110, 540, 300, BLUE, -3)

def s6(c, t, tp):
    if t < 1.37:
        d = int(counter(3, 30, t, 0.1, 1.2))
        calendar(c, 540, 620, str(d), 'DIA')
        txt('SEMANAS', 110, 540, 300, INK)
        snow(c, tp, n=6, y1=1000)
    elif t < 2.49:
        leaf(c, 540, 700, 1.4)
        ghost(c, 800, 330, 80)
        xmark(c, 800, 330, 70, 12)
        txt('FOTOSSÍNTESE', 96, 540, 1010 - 20, INK)
    elif t < 3.65:
        ground(c)
        w = smoothstep((t - 3.0) / 0.6)
        for k, x in enumerate([240, 440, 640, 840]): plant(c, x, GY - 70, w, 1.0, k * 5)
        if t > 3.09: txt('MORREM', 130, 540, 300, RED, -3)
        else: txt('AS PLANTAS', 110, 540, 300, INK)
    else:
        u = counter(1, 0, t, 3.8, 4.4)
        bar(c, 240, 440, 840, 520, u, GREEN)
        txt('COMIDA', 70, 540, 380, INK, 0, 'Black')
        ground(c)
        man(c, 420, GY, 1.1, 1, (-20, 20), (6, -6), 'sad')
        rect(c, 600, 930, 920, 960, 8, LBROWN, seed=5)
        for xx in (630, 890): stroke(c, [(xx, 960), (xx, GY)], 8)
        plate(c, 760, 915, 0.8)
        if t > 4.15: stamp('ACABOU', 540, 640, RED, -5, 120)

def s7(c, t, tp):
    # corte do oceano: gelo em cima, água embaixo
    c.set_source_rgb(*LBLUE); c.rectangle(-400, 320, 1900, 1500); c.fill()
    for k in range(10):
        y = 620 + k * 110
        pts = [(-300 + j * 40, y + 10 * math.sin(j * 0.8 + tp * 3 + k)) for j in range(45)]
        stroke(c, pts, 4, BLUE, False, None, 0.6, k)
    h = 60 + 130 * smoothstep((t - 0.5) / 1.2)
    rect(c, -400, 320, 1900, 320 + h, 9, WHITE, seed=2)
    for k in range(5):
        x = 80 + k * 220
        stroke(c, [(x, 330), (x + 30, 320 + h * 0.5), (x + 5, 320 + h - 10)], 5, INK, False, None, 1.5, k)
    stroke(c, [(-400, 1820), (1900, 1820)], 9)
    hatch(c, -400, 1820, 1900, 1900, 30, 5)
    man(c, 110, 320, 0.7, 1, (-20, 20), (6, -6), 'n' if t < 1.91 else 'smile')
    fish(c, 400 + 260 * math.sin(tp * 0.9), 1400, 1.0, 1 if math.cos(tp * 0.9) > 0 else -1, tp)
    fish(c, 760 - 200 * math.sin(tp * 0.7), 1530, 0.7, -1 if math.cos(tp * 0.7) > 0 else 1, tp + 1)
    bubbles_up(c, 620, 1700, tp, 5, 60, 400)
    if t > 0.76: txt('CONGELA POR CIMA', 76, 600, 230, INK, 0, 'Black')
    if t > 2.6: txt('LÍQUIDA', 120, 540, 1160, BLUE, -3)

def s8(c, t, tp):
    if t < 4.89:
        for k in range(6):
            y = 220 + k * 140
            pts = [(-300 + j * 40, y + 10 * math.sin(j * 0.8 + tp * 2 + k)) for j in range(45)]
            stroke(c, pts, 4, LBLUE, False, None, 0.6, k)
        stroke(c, [(-400, GY), (1900, GY)], 8)
        hatch(c, -400, GY, 1900, GY + 60, 30, 5)
        vent(c, 540, GY, 1.0, tp)
        if t > 0.72 and t < 2.06: txt('VULCÃO NO FUNDO DO MAR', 60, 540, 230, INK, 0, 'Black')
        n = 0 if t < 2.06 else min(5, 1 + int((t - 2.06) * 4))
        pos = [(700, 820, 1.0), (360, 880, 0.8), (760, 1000, 0.7), (300, 1010, 0.6), (830, 700, 0.6)]
        for k in range(n):
            x, y, s = pos[k]
            microbe(c, x + 6 * math.sin(tp * 3 + k), y + 6 * math.cos(tp * 2.5 + k), s, tp, k, glasses=(k == 0 and t > 3.34))
        if t > 2.06 and t < 2.64: txt('BACTÉRIAS', 110, 540, 300, GREEN, -3)
        if t > 3.34: stamp('SOBREVIVEM', 540, 230, GREEN, -4, 110)
    else:
        ghost(c, 540, 560, 120)
        xmark(c, 540, 560, 105)
        microbe(c, 540, 900, 1.6, tp, 0, glasses=True)
        txt('SEM SOL', 140, 540, 220, RED, -4)

def s9(c, t, tp):
    if t < 2.69:
        ground(c)
        sun(c, 540, 500, 160, tp, face=True)
        man(c, 230, GY, 0.9, 1, (-150, 150), (8, -8), 'smile')
        if t < 1.56: txt('CALMA', 130, 540, 230, INK)
        else: stamp('IMPOSSÍVEL', 650, 1080, RED, -5, 120)
    elif t < 5.6:
        secs = 500 if t > 3.95 else 0
        watch(c, 540, 600, 240, secs)
        if t < 3.95:
            man(c, 900, GY, 0.6, -1, (-20, 150), (8, -8), 'n')
            txt('?', 150, 900, 760, RED)
        if t > 3.95: impact(t, 3.95)
    else:
        ground(c)
        sun(c, 820, 330, 100, tp, face=True)
        man(c, 420, GY, 1.1, 1, (-150, 150), (8, -8), 'smile')
        txt('SIGA', 200, 360, 330, RED, -4)
        heart(c, 720 + 10 * math.sin(tp * 5), 640, 0.8)
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

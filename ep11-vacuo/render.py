# Ep11 — O que acontece com o corpo no vácuo do espaço — estilo STICKMAN SKETCH (traço de marcador, fundo branco, toques de cor chapada)
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
# ---------- objetos do episódio (espaço / vácuo) ----------
STARS = [(-250, 300), (-120, 820), (80, 180), (170, 560), (120, 1020), (330, 900), (420, 140), (760, 160), (930, 520),
         (1000, 980), (880, 1060), (1180, 260), (1300, 760), (640, 1080), (260, 380), (980, 300)]

def space_bg(c, tp):
    for k, (x, y) in enumerate(STARS):
        r = 16 + 6 * ((k * 7) % 3)
        tw = 1 + 0.25 * math.sin(tp * 4 + k)
        stroke(c, [(x - r * tw, y), (x + r * tw, y)], 5, INK, False, None, 0.8, k)
        stroke(c, [(x, y - r * tw), (x, y + r * tw)], 5, INK, False, None, 0.8, k + 3)
        if k % 4 == 0: ellipse(c, x + 40, y + 30, 6, 6, 3, YEL, seed=k)
    # planetinha no canto
    ellipse(c, 1250, 1060, 180, 180, 9, BLUE, seed=7)
    stroke(c, [(1090, 1000), (1140, 965), (1175, 1010), (1125, 1060)], 7, INK, True, GREEN, 1.5, 8)

def floater(c, x, y, s=1.0, expr='shock', arm=(-120, 120), leg=(25, -25), rot=None, helmet=False, inflate=0.0, tp=0.0):
    r = 0.12 * math.sin(tp * 1.3 + x * 0.01) if rot is None else rot
    c.save(); c.translate(x, y + 10 * math.sin(tp * 2.1)); c.rotate(r)
    if inflate > 0:
        ellipse(c, 0, 0 + 75 * s - 115 * s, (45 + 70 * inflate) * s, (70 + 50 * inflate) * s, 8, SKIN, seed=5)
    if helmet:
        rect(c, -50 * s, -80 * s, 50 * s, 40 * s, 8, LGRAY, seed=2)
    man(c, 0, 150 * s, s * (1 + 0.15 * inflate), 1, arm, leg, expr)
    hy = 150 * s - 252 * s * (1 + 0.15 * inflate)
    if helmet:
        stroke(c, ell_pts(0, hy, 72 * s, 72 * s, 0, 28), 7, BLUE, True, None, 1.2, 4)
        arc(c, -20 * s, hy - 20 * s, 40 * s, 40 * s, 200, 250, 6, LBLUE)
    c.restore()
    return (x, y + hy)

def face(c, cx, cy, r, tp, bubbles=True, t=0.0):
    ellipse(c, cx, cy, r, r, 10, WHITE, seed=3)
    for sg in (-1, 1):
        ellipse(c, cx + sg * r * 0.36, cy - r * 0.28, r * 0.17, r * 0.17, 7, WHITE, seed=sg + 4)
        ellipse(c, cx + sg * r * 0.36, cy - r * 0.26, r * 0.06, r * 0.06, 4, INK, INK)
        stroke(c, [(cx + sg * r * 0.2, cy - r * 0.55), (cx + sg * r * 0.52, cy - r * 0.62)], 8)
    my = cy + r * 0.42
    ellipse(c, cx, my, r * 0.42, r * 0.3, 9, INK, seed=6)
    ellipse(c, cx, my + r * 0.13, r * 0.3, r * 0.15, 6, RED, seed=7)
    stroke(c, [(cx, my + r * 0.04), (cx, my + r * 0.2)], 5, INK)
    if bubbles:
        for k in range(9):
            per = 0.9 + 0.13 * (k % 3)
            u = ((tp + k * 0.31) % per) / per
            bx = cx + (k - 4) * r * 0.07 + 18 * math.sin(tp * 8 + k)
            by = my + r * 0.05 - u * r * 0.9
            rr = (10 + 6 * (k % 3)) * (0.6 + 0.6 * u)
            if u < 0.92: ellipse(c, bx, by, rr, rr, 4, LBLUE, seed=k)
            else:
                for q in range(5):
                    a = q * 2 * math.pi / 5
                    stroke(c, [(bx + rr * math.cos(a), by + rr * math.sin(a)), (bx + 2 * rr * math.cos(a), by + 2 * rr * math.sin(a))], 4, BLUE)

def lungs(c, cx, cy, s=1.0, crack=0.0):
    stroke(c, [(cx, cy - 260 * s), (cx, cy - 90 * s)], 16, INK)
    stroke(c, [(cx, cy - 90 * s), (cx - 70 * s, cy - 40 * s)], 12, INK); stroke(c, [(cx, cy - 90 * s), (cx + 70 * s, cy - 40 * s)], 12, INK)
    for sg in (-1, 1):
        pts = [(cx + sg * 40 * s, cy - 150 * s), (cx + sg * 120 * s, cy - 180 * s), (cx + sg * 200 * s, cy - 80 * s), (cx + sg * 220 * s, cy + 80 * s),
               (cx + sg * 190 * s, cy + 170 * s), (cx + sg * 60 * s, cy + 160 * s), (cx + sg * 40 * s, cy)]
        stroke(c, pts, 9, INK, True, RED, 2.0, sg + 3)
        for k in range(3):
            yy = cy - 40 * s + k * 60 * s
            stroke(c, [(cx + sg * 80 * s, yy), (cx + sg * 150 * s, yy + 20 * s)], 5, SKIN)
    if crack > 0:
        for sg in (-1, 1):
            pts = [(cx + sg * 150 * s, cy - 130 * s), (cx + sg * 110 * s, cy - 50 * s), (cx + sg * 170 * s, cy + 10 * s), (cx + sg * 120 * s, cy + 90 * s), (cx + sg * 160 * s, cy + 150 * s)]
            m = max(2, int(len(pts) * min(1, crack)))
            stroke(c, pts[:m], 10, INK, False, None, 2.5, 9 + sg)

def brain(c, cx, cy, s=1.0):
    pts = ell_pts(cx, cy, 230 * s, 160 * s, 0, 30)
    pts = [(x + 14 * math.sin(k * 1.7) * s, y + 14 * math.cos(k * 2.3) * s) for k, (x, y) in enumerate(pts)]
    stroke(c, pts, 10, INK, True, SKIN, 1.5, 2)
    stroke(c, [(cx, cy - 150 * s), (cx + 10 * s, cy - 60 * s), (cx - 10 * s, cy + 20 * s), (cx, cy + 150 * s)], 7)
    for k, (dx, dy) in enumerate([(-130, -60), (-90, 50), (110, -70), (140, 40), (-160, 10), (60, 80)]):
        stroke(c, [(cx + dx * s - 40 * s, cy + dy * s), (cx + dx * s - 10 * s, cy + dy * s - 25 * s), (cx + dx * s + 20 * s, cy + dy * s + 10 * s), (cx + dx * s + 45 * s, cy + dy * s - 15 * s)], 6, INK, False, None, 1.2, k)

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

def chamber(c, x0, y0, x1, y1, alarm=False, tp=0.0):
    rect(c, x0, y0, x1, y1, 10, None, seed=5)
    rect(c, x0 - 30, y0 - 30, x1 + 30, y0, 9, LGRAY, seed=6)
    rect(c, x0 - 30, y1, x1 + 30, y1 + 30, 9, LGRAY, seed=7)
    for k in range(4): ellipse(c, x0 + 30 + k * (x1 - x0 - 60) / 3, y0 - 15, 7, 7, 3, INK, INK)
    stroke(c, [(x1 - 10, y0 + 80), (x1 + 50, y0 + 80), (x1 + 50, y0 + 200), (x1 - 10, y0 + 200)], 7, INK, True, DGRAY, 1)
    lit = alarm and int(tp * 6) % 2 == 0
    ellipse(c, (x0 + x1) / 2, y0 - 70, 36, 30, 8, RED if lit else LGRAY, seed=8)
    if lit:
        for k in range(6):
            a = math.pi + k * math.pi / 5
            stroke(c, [((x0 + x1) / 2 + 55 * math.cos(a), y0 - 70 + 45 * math.sin(a)), ((x0 + x1) / 2 + 90 * math.cos(a), y0 - 70 + 75 * math.sin(a))], 6, RED)

def jets(c, x, y, tp, n=6):
    for k in range(n):
        a = -0.6 + k * 0.5 + 0.08 * math.sin(tp * 20 + k)
        L = 60 + 40 * ((tp * 9 + k) % 2)
        stroke(c, [(x + 40 * math.cos(a), y + 40 * math.sin(a)), (x + (40 + L) * math.cos(a), y + (40 + L) * math.sin(a))], 6, BLUE)

def ecg(c, x0, x1, y, t, flat_t):
    rect(c, x0 - 40, y - 230, x1 + 40, y + 200, 10, WHITE, seed=4)
    pts = []
    for k in range(80):
        x = x0 + (x1 - x0) * k / 79
        tt = t - (79 - k) * 0.02
        ph = (tt % 0.8) / 0.8
        v = 0
        if tt < flat_t:
            if 0.40 < ph < 0.44: v = -150
            elif 0.44 < ph < 0.48: v = 80
            elif 0.30 < ph < 0.36: v = -20
        pts.append((x, y + v))
    stroke(c, pts, 7, GREEN if t < flat_t else RED, False, None, 0.6, 2)

def stamp(s, cx, cy, col=RED, rot=-6, size=130): txt(s, size, cx, cy, col, rot)

# ---------- cenas ----------
def s0(c, t, tp):
    space_bg(c, tp)
    if t < 1.52:
        floater(c, 540, 760, 1.25, 'shock', tp=tp)
        txt('ESPAÇO', 150, 540, 280)
    elif t < 2.87:
        hx, hy = floater(c, 540, 760, 1.25, 'shock', tp=tp)
        stroke(c, ell_pts(hx, hy, 95, 95, 0, 28), 7, BLUE, True, None, 1.2, 4)
        stroke(c, [(hx - 110, hy - 110), (hx + 110, hy + 110)], 14, RED); stroke(c, [(hx + 110, hy - 110), (hx - 110, hy + 110)], 14, RED)
        txt('SEM TRAJE', 120, 540, 260, RED, -4)
    elif t < 4.02:
        floater(c, 540, 760, 1.2, 'shock', inflate=0.4, tp=tp)
        burst(c, 830, 470, 130, 12, YEL); txt('BUM', 66, 830, 470, INK)
        stroke(c, [(720, 360), (940, 580)], 14, RED); stroke(c, [(940, 360), (720, 580)], 14, RED)
        txt('NÃO EXPLODE', 96, 540, 240, INK, -3)
    else:
        te = t - 4.58
        stopwatch(c, 540, 600, 240, '15s', 0.25 * smoothstep(te / 0.5) if te > 0 else 0.0)
        floater(c, 880, 980, 0.6, 'shock', tp=tp)
        if t > 4.58: impact(t, 4.58)

def s1(c, t, tp):
    space_bg(c, tp)
    if t < 1.19:
        stopwatch(c, 540, 600, 230, '0s', 0.0)
        floater(c, 880, 980, 0.6, 'shock', tp=tp)
    elif t < 1.79:
        hx, hy = floater(c, 540, 760, 1.3, 'n', arm=(-40, 40), tp=tp)
        for sg in (-1, 1): ellipse(c, hx + sg * 48, hy + 18, 30, 26, 5, RED, seed=sg + 2)
        txt('PRENDER O AR?', 96, 540, 260, INK)
    elif t < 3.72:
        lungs(c, 540, 680, 1.4, min(1, (t - 1.79) * 3))
        if t > 1.79: impact(t, 1.79); splat_rays(c, 540, 680, t - 1.79, 12, RED)
        stamp('RASGA!', 540, 260)
    else:
        hx, hy = floater(c, 500, 760, 1.25, 'smile', arm=(-140, 140), tp=tp)
        for k in range(3):
            off = (tp * 220 + k * 70) % 260
            stroke(c, [(hx + 70 + off, hy + 10 + j * 0) for j in range(1)] + [(hx + 70 + off + 30 * j, hy + 20 * math.sin(j + tp * 8) + (k - 1) * 30) for j in range(1, 5)], 6, LBLUE, False, None, 0.6, k)
        txt('SOLTE O AR', 120, 540, 260, GREEN, -3)

def s2(c, t, tp):
    space_bg(c, tp)
    if t < 1.91:
        v = 80 * (1 - smoothstep((t - 0.9) / 1.0))
        speedo(c, 540, 700, 280, v)
        txt('PRESSÃO', 130, 540, 300)
        txt(str(int(v * 1.25)) + '%', 100, 540, 830, RED)
    elif t < 3.55:
        face(c, 540, 700, 300, tp)
        if t > 2.93: stamp('FERVE!', 540, 1120, RED, -5, 140)
    else:
        thermo(c, 330, 760, 0.55)
        txt('37°C', 170, 700, 600, INK)
        txt('sem esquentar', 64, 700, 760, DGRAY, 0, 'Bold')
        face(c, 760, 960, 90, tp)

def s3(c, t, tp):
    space_bg(c, tp)
    if t < 1.17:
        stopwatch(c, 540, 600, 230, '10s', 10 / 60)
        floater(c, 880, 980, 0.6, 'shock', tp=tp)
    elif t < 3.4:
        floater(c, 540, 760, 1.2, 'shock', tp=tp)
        if t < 2.05:
            for k, (dx, dy) in enumerate([(-90, -40), (80, -10), (-60, 90), (100, 120), (0, -200)]):
                ellipse(c, 540 + dx, 700 + dy, 14, 20, 4, BLUE, seed=k)
        else:
            heatwaves(c, 540, 640, tp, LBLUE, 5, 180, 300)
        if t > 2.28: txt('VAPOR', 140, 540, 250, BLUE, -4)
    elif t < 4.27:
        floater(c, 540, 760, 1.15, 'shock', inflate=min(1, (t - 3.4) * 3), tp=tp)
        stamp('INCHA!', 540, 250)
    else:
        floater(c, 540, 760, 1.15, 'smile', arm=(-150, 150), inflate=1.0, tp=tp)
        stamp('A PELE SEGURA', 540, 250, GREEN, 4, 100)

def s4(c, t, tp):
    space_bg(c, tp)
    if t < 1.2:
        stopwatch(c, 540, 600, 230, '15s', 0.25)
        floater(c, 880, 980, 0.6, 'shock', tp=tp)
    elif t < 2.7:
        brain(c, 540, 560, 1.2)
        fr = max(0, 1 - (t - 1.2) / 1.3)
        bar(c, 240, 860, 840, 940, fr, BLUE)
        txt('O2', 90, 540, 1040 - 20, INK)
    else:
        hx, hy = floater(c, 540, 760, 1.25, 'x', arm=(-70, 60), leg=(15, -5), rot=0.25 + 0.08 * math.sin(tp * 1.5), tp=tp)
        for k in range(3):
            u = ((tp * 0.8 + k * 0.33) % 1)
            txt('z', 60 + 20 * k, hx + 100 + 60 * k, hy - 60 - 120 * u, DGRAY, 0, 'Bold')
        stamp('APAGOU', 540, 250)

def s5(c, t, tp):
    space_bg(c, tp)
    if t < 1.49:
        rect(c, 380, 480, 700, 800, 10, LBLUE, seed=2)
        stroke(c, [(420, 530), (500, 520)], 8, WHITE)
        for k in range(3): flake(c, 320 + k * 220, 940, 45)
        if t > 0.41:
            stroke(c, [(320, 420), (760, 860)], 16, RED); stroke(c, [(760, 420), (320, 860)], 16, RED)
        txt('CONGELA?', 130, 540, 270)
    else:
        floater(c, 470, 760, 1.15, 'n', tp=tp)
        heatwaves(c, 470, 600, tp, RED, 3, 170, 180)
        thermo(c, 880, 760, 0.55)
        if t > 2.51: txt('o calor fica', 80, 540, 270, RED, 0, 'ExtraBold')
        else: txt('VÁCUO', 150, 540, 270)

def s6(c, t, tp):
    if t < 1.87:
        calendar(c, 540, 640, '1966', 'TESTE')
        man(c, 880, GY, 0.7, -1, (-20, 20), (6, -6), 'n')
        ground(c)
    else:
        leak = t >= 3.63
        chamber(c, 200, 380, 880, 1060, leak, tp)
        hx, hy = floater(c, 540, 760, 1.05, 'shock' if leak else 'n', arm=(-30, 30) if not leak else (-140, 140), rot=0.0 if not leak else None, helmet=True, tp=tp)
        if leak:
            jets(c, 590, 740, tp); jets(c, 470, hy + 40, tp + 0.3, 4)
            txt('PSSSS', 70, 740, 600, BLUE, -8, 'ExtraBold')
            stamp('VAZOU!', 540, 150)
        else:
            txt('NASA', 120, 540, 460, INK)
            txt('câmara de vácuo', 54, 540, 1010, DGRAY, 0, 'Bold')

def s7(c, t, tp):
    space_bg(c, tp)
    if t < 2.34:
        floater(c, 420, 800, 1.05, 'shock', helmet=True, tp=tp)
        bubble(c, 560, 300, 980, 520, 520, 640)
        txt('?', 170, 770, 420, RED)
    elif t < 4.61:
        face(c, 540, 700, 300, tp)
        txt('a última lembrança', 66, 540, 1120, DGRAY, 0, 'ExtraBold')
    else:
        floater(c, 540, 760, 1.2, 'smile', arm=(-150, 150), rot=0.0, tp=tp)
        for k in range(4): star(c, 260 + k * 190, 470 + 40 * (k % 2), 34)
        stamp('SOBREVIVEU!', 540, 250, GREEN, -4, 120)

def s8(c, t, tp):
    space_bg(c, tp)
    if t < 1.37:
        stopwatch(c, 540, 600, 230, '90s', min(1.0, t / 0.8))
    elif t < 3.94:
        x0, x1 = 160, 980
        u = smoothstep((t - 1.37) / 1.4)
        bar(c, x0, 600, x1, 690, u, YEL)
        for v, lab, col in [(0, '0s', INK), (15, '15s', INK), (90, '90s', RED)]:
            xx = x0 + (x1 - x0) * v / 90
            stroke(c, [(xx, 570), (xx, 720)], 8, col)
            txt(lab, 64, xx, 780, col)
        txt('apaga', 44, x0 + (x1 - x0) * 15 / 90, 850, DGRAY, 0, 'Bold')
        if t > 2.72: txt('LIMITE', 90, 820, 470, RED, -4)
        if t < 2.72: txt('testes com animais', 58, 540, 300, DGRAY, 0, 'ExtraBold')
    else:
        ecg(c, 180, 900, 700, t, 4.67)
        heart(c, 540, 1010, 0.9, RED if t < 4.67 else LGRAY)
        if t > 4.67: stamp('FIM', 540, 300, RED, 0, 200)

def s9(c, t, tp):
    space_bg(c, tp)
    if t < 1.79:
        floater(c, 540, 760, 1.2, 'shock', tp=tp)
        txt('?', 260, 860, 380, RED)
    elif t < 2.21:
        floater(c, 540, 760, 1.2, 'smile', arm=(-20, -140), rot=0.0, tp=tp)
        bubble(c, 220, 230, 860, 420, 520, 520); txt('COMENTA', 100, 540, 325, INK)
    elif t < 4.5:
        floater(c, 540, 760, 1.2, 'smile', arm=(-150, 150), rot=0.0, tp=tp)
        txt('SIGA', 220, 540, 330, RED, -4)
        heart(c, 860 + 10 * math.sin(tp * 5), 640, 0.9)
    else:
        floater(c, 820, 900, 0.7, 'shock', tp=tp)
        stopwatch(c, 470, 600, 230, '15s', 0.25)
        if t > 5.58: impact(t, 5.58)
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

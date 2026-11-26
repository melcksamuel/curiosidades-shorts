# Ep10 — A Grande Inundação de Melaço (Boston, 1919) — estilo STICKMAN SKETCH (traço de marcador, fundo branco, toques de cor chapada)
# Legendas: uma palavra por vez, Montserrat Bold branca em caixa preta arredondada, corte seco.
import cairo, math, json, sys, os, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
D = json.load(open('aud/durs.json'))
STARTS = np.concatenate([[0], np.cumsum(D)[:-1]])
sys.path.insert(0, '.')
from script import LINES

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
    c.set_source_rgb(*col); c.set_line_width(w); c.set_line_cap(cairo.LINE_CAP_ROUND); c.set_line_join(cairo.LINE_JOIN_ROUND)
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
    hipy, shy, hy = y - 115 * s, y - 190 * s, y - 252 * s
    for a in leg: stroke(c, [(x, hipy), d(a, 115, x, hipy)], w)
    stroke(c, [(x, shy), (x, hipy)], w)
    hands = []
    for a in arm:
        e = d(a, 95, x, shy + 8 * s); stroke(c, [(x, shy + 8 * s), e], w); hands.append(e)
    if prop == 'tie': stroke(c, [(x, shy + 4 * s), (x - 16 * s, shy + 56 * s), (x + 16 * s, shy + 56 * s)], 5, INK, True, RED, 1)
    if prop == 'medal':
        ellipse(c, x, shy + 40 * s, 13 * s, 13 * s, 5, YEL); stroke(c, [(x, shy + 6 * s), (x, shy + 28 * s)], 4, RED)
    ellipse(c, x, hy, 46 * s, 46 * s, w, WHITE, seed=3)
    ex = 15 * s; ey = hy - 6 * s; my = hy + 20 * s
    if expr in ('n', 'sad', 'smile', 'angry'):
        for sg in (-1, 1): ellipse(c, x + sg * ex, ey, 4.5 * s, 4.5 * s, 3, INK)
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

def ground(c, x0=70, x1=1010, y=1090):
    stroke(c, [(x0, y), ((x0 + x1) / 2, y + 3), (x1, y - 2)], 7, INK, False, None, 2.5, 40)
    for k in range(7):
        gx = x0 + 60 + k * 135 + nz(k, 3) * 25
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


# ---------- objetos do episódio ----------
def runner(c, x, y, s, f, tp, expr='shock', k=0):
    a = 40 * math.sin(tp * 14 + k)
    man(c, x, y, s, f, arm=(-55 * f * 0 - 60 + a * 0.6, 60 - a * 0.6), leg=(a, -a), expr=expr)

def hatch(c, x0, y0, x1, y1, step=34, seed=0):
    k = 0
    xx = x0
    while xx < x1:
        stroke(c, [(xx, y1), (min(x1, xx + (y1 - y0) * 0.5), y1 - min(y1 - y0, (x1 - xx) * 2))], 4, INK, False, None, 1, seed + k)
        xx += step; k += 1

def wave(c, x0, x1, gy, hgt, tp, seed=0, curl=True):
    # massa de melaço: topo ondulado, crista que enrola para a frente (direita)
    pts = [(x0, gy)]
    n = 14
    for k in range(n + 1):
        u = k / n
        x = x0 + (x1 - x0 - hgt * 0.35) * u
        y = gy - hgt * (0.35 + 0.65 * u ** 1.6) + 14 * math.sin(tp * 6 + k * 1.3)
        pts.append((x, y))
    if curl:
        xc, yc = pts[-1]
        pts += [(xc + hgt * 0.22, yc - hgt * 0.05), (xc + hgt * 0.36, yc + hgt * 0.12), (xc + hgt * 0.25, yc + hgt * 0.28),
                (xc + hgt * 0.30, yc + hgt * 0.55), (x1, gy)]
    else:
        pts.append((x1, gy))
    stroke(c, pts, 9, INK, True, BROWN, 2.0, seed)
    # enrolar da crista (espiral)
    xc, yc = pts[n + 1]
    sp = [(xc + hgt * 0.12 + hgt * 0.13 * (1 - u) * math.cos(4.2 * u * math.pi), yc + hgt * 0.16 + hgt * 0.13 * (1 - u) * math.sin(4.2 * u * math.pi)) for u in [k / 16 for k in range(14)]]
    if curl: stroke(c, sp, 7, LBROWN, False, None, 1.0, seed + 3)
    hatch(c, x0 + 20, gy - hgt * 0.22, x0 + (x1 - x0) * 0.5, gy - 10, 46, seed)
    # brilho e listras
    for k in range(3):
        y = gy - hgt * (0.25 + 0.18 * k)
        xa = x0 + 60 + 40 * k; xb = x0 + (x1 - x0) * (0.45 + 0.12 * k)
        if xb > xa: stroke(c, [(xa, y), ((xa + xb) / 2, y - 12), (xb, y)], 6, LBROWN, False, None, 1.5, seed + k)
    # respingos na crista
    xc, yc = pts[n + 1]
    for k in range(4):
        ang = -1.2 + 0.5 * k + 0.2 * math.sin(tp * 9 + k)
        r = 30 + 18 * ((tp * 8 + k) % 2)
        ellipse(c, xc + 40 + r * math.cos(ang), yc - 30 + r * math.sin(ang), 11, 14, 5, BROWN, seed=k)

def tank(c, cx, gy, s=1.0, painted=1.0, drips=0, tp=0.0, crack=0.0):
    w = 220 * s; h = 420 * s; top = gy - h
    rect(c, cx - w, top, cx + w, gy, 9, LGRAY, seed=4)
    if painted > 0:
        ph = h * painted
        c.set_source_rgb(*BROWN); c.rectangle(cx - w + 5, gy - ph, 2 * w - 10, ph - 5); c.fill()
        stroke(c, [(cx - w, top), (cx + w, top), (cx + w, gy), (cx - w, gy)], 9, INK, True, None, 2.0, 4)
    ellipse(c, cx, top, w, 40 * s, 9, LGRAY if painted < 1 else LBROWN, seed=5)
    for k in range(1, 4):  # anéis de rebites
        y = top + h * k / 4
        stroke(c, [(cx - w, y), (cx, y + 18 * s), (cx + w, y)], 5, INK, False, None, 1, k)
        for j in range(7): ellipse(c, cx - w + 30 * s + j * (2 * w - 60 * s) / 6, y + 6 * s + 10 * s * math.sin(j / 6 * math.pi), 5, 5, 2, INK, INK)
    for d in range(drips):
        dx = cx - w * 0.7 + d * w * 0.45
        y0 = top + h * (0.3 + 0.17 * (d % 3))
        stroke(c, [(dx, y0), (dx + 4, y0 + 40)], 7, BROWN)
        yy = y0 + 50 + ((tp * 160 + d * 47) % 220)
        if yy < gy - 10: ellipse(c, dx + 4, yy, 10, 15, 4, BROWN, seed=d)
        ellipse(c, dx + 30, gy - 8, 34, 10, 4, BROWN, seed=d)
    if crack > 0:
        pts = [(cx - 10, top + 30), (cx + 20, top + 110), (cx - 25, top + 190), (cx + 25, top + 270), (cx - 15, top + 350), (cx + 10, gy)]
        m = max(2, int(len(pts) * min(1, crack)))
        stroke(c, pts[:m], 11, INK, False, None, 2.5, 9)

def house(c, x, gy, s=1.0, rot=0.0, col=None):
    c.save(); c.translate(x, gy); c.rotate(rot)
    rect(c, -110 * s, -200 * s, 110 * s, 0, 8, WHITE, seed=int(x) % 5)
    stroke(c, [(-130 * s, -200 * s), (0, -300 * s), (130 * s, -200 * s)], 8, INK, True, col or RED, 1.5)
    rect(c, -70 * s, -160 * s, -20 * s, -110 * s, 6, LBLUE, seed=1); rect(c, 20 * s, -160 * s, 70 * s, -110 * s, 6, LBLUE, seed=2)
    rect(c, -25 * s, -80 * s, 25 * s, 0, 6, LBROWN, seed=3)
    c.restore()

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

# ---------- cenas ----------
def s0(c, t, tp):
    ground(c)
    if t < 1.77:
        txt('1919', 230, 540, 330)
        wave(c, -60, 520, GY, 430, tp)
        runner(c, 760, GY, 1.2, 1, tp)
    elif t < 4.25:
        wave(c, -60, 640, GY, 620, tp)
        runner(c, 840, GY, 1.1, 1, tp)
        if t > 2.57:
            txt('21', 230, 820, 330, RED); txt('MORTOS', 74, 820, 470, INK, 0, 'ExtraBold')
        if t > 3.55: txt('BOSTON', 84, 330, 230, INK)
    else:
        # pote/gota gigante de melaço
        dp = [(540, 420)] + [(540 + 230 * math.cos(a), 800 + 230 * math.sin(a)) for a in [math.radians(d) for d in range(-50, 231, 14)]]
        stroke(c, dp, 10, INK, True, BROWN, 2, 3)
        stroke(c, [(440, 760), (450, 700), (480, 660)], 9, LBROWN)
        man(c, 880, GY, 1.0, -1, (-135, 135), (10, -10), 'shock')
        if t > 4.65:
            txt('MELAÇO!', 150, 540, 300, RED, -5); impact(t, 4.65)
        splat_rays(c, 540, 760, t - 4.65)

def s1(c, t, tp):
    ground(c)
    if t < 1.21:
        calendar(c, 540, 560, '15', 'JAN 1919')
        man(c, 870, GY, 0.9, -1, (-20, 20), (6, -6), 'n')
    elif t < 2.76:
        clock(c, 540, 540, 230, 12, 30)
        man(c, 280, GY, 1.0, 1, (-15, 80), (6, -6), 'smile')
        # prato com sanduíche na mão
        ellipse(c, 380, GY - 200, 60, 16, 6, WHITE); rect(c, 340, GY - 236, 420, GY - 210, 6, LBROWN, seed=2)
        if t > 1.55: txt('ALMOÇO', 96, 540, 230)
    else:
        tank(c, 360, GY, 1.0, 0.0)
        man(c, 820, GY, 0.8, -1, (-20, -130), (6, -6), 'shock')
        if t > 3.74:
            n = int(8_000_000 * smoothstep((t - 3.74) / 0.9))
            txt(f'{n:,}'.replace(',', '.'), 120, 540, 300, RED)
            txt('LITROS', 80, 540, 420, INK, 0, 'ExtraBold')

def s2(c, t, tp):
    ground(c)
    if t < 2.4:
        tank(c, 400, GY, 1.0, 0.0, 4, tp)
        man(c, 850, GY, 0.85, -1, (-20, -110), (6, -6), 'shock')
        if t > 1.33: calendar(c, 840, 420, '1', 'DIA');
    elif t < 3.88:
        man(c, 540, GY, 1.3, 1, (-20, -135), (0, 0), 'smug')
        txt('?', 360, 540, 420, RED)
    else:
        pp = smoothstep((t - 3.88) / 1.6)
        tank(c, 380, GY, 1.0, pp, 0 if pp > 0.95 else 3, tp)
        # rolo de pintura
        yy = GY - 420 * pp
        man(c, 820, GY, 0.9, -1, (-20, -120 + 20 * math.sin(tp * 10)), (6, -6), 'smug')
        stroke(c, [(760, GY - 300), (640, yy)], 8)
        rect(c, 600, yy - 30, 640, yy + 30, 7, BROWN, seed=1)
        if t > 4.85: txt('MARROM', 110, 540, 230, BROWN, -4)

def s3(c, t, tp):
    ground(c)
    if t < 1.44:
        stopwatch(c, 540, 600, 230, '0s', 0.0)
        man(c, 880, GY, 0.85, -1, (-20, 20), (6, -6), 'n')
    elif t < 2.7:
        tank(c, 420, GY, 1.0, 1.0, crack=0.4)
        burst(c, 760, 420, 210); txt('BUM!', 110, 760, 420, RED, -8)
        impact(t, 1.44)
        splat_rays(c, 420, 700, t - 1.44)
        man(c, 900, GY, 0.8, -1, (-135, 135), (10, -10), 'shock')
    else:
        tank(c, 400, GY, 1.0, 1.0, crack=min(1, 0.4 + (t - 2.7) * 3))
        if t > 3.34:
            te = t - 3.34
            for k in range(6):
                a = -2.6 + k * 0.42; r = 120 + 500 * min(1, te * 2)
                ellipse(c, 400 + r * math.cos(a) * 0.9, 700 + r * math.sin(a) * 0.6 + 200 * te * te, 22, 28, 5, BROWN, seed=k)
            impact(t, 3.34); splat_rays(c, 400, 700, te)
            txt('RASGOU!', 120, 540, 230, RED, 5)
        man(c, 900, GY, 0.8, -1, (-135, 135), (10, -10), 'shock')

def s4(c, t, tp):
    ground(c)
    if t < 1.19:
        stopwatch(c, 540, 600, 230, '10s', 10 / 60)
        man(c, 880, GY, 0.85, -1, (-20, 20), (6, -6), 'shock')
    elif t < 1.96:
        wave(c, -40, 760, GY, 560, tp)
    elif t < 3.9:
        wave(c, -40, 640, GY, 760, tp)
        ruler(c, 860, GY, GY - 760, '9 m')
        man(c, 720, GY, 0.55, 1, (-135, 135), (10, -10), 'shock')
        if t > 2.88: txt('dizem relatos', 56, 860, 210, DGRAY, 0, 'Bold')
    else:
        te = t - 3.9
        sp = int(56 * smoothstep(te / 0.8))
        speedo(c, 540, 640, 260, sp)
        txt(str(sp), 150, 540, 470 + 260, RED); txt('km/h', 70, 540, 300, INK, 0, 'ExtraBold')
        for k in range(4):  # linhas de velocidade
            y = 900 + k * 45; x = 1000 - ((tp * 900 + k * 230) % 900)
            stroke(c, [(x, y), (x + 140, y)], 6, BROWN)

def s5(c, t, tp):
    ground(c)
    te = t
    xw = 380 + 260 * min(1, te / 2.4)
    wave(c, -60, xw, GY, 520, tp)
    for k, hx in enumerate([620, 860]):
        hit = xw + 80 > hx - 110
        rot = (0.35 + 0.1 * k) * smoothstep((xw + 80 - (hx - 110)) / 160) if hit else 0
        house(c, hx + (30 if hit else 0), GY, 0.85, rot, (RED, GREEN)[k])
    if t > 0.56: splat_rays(c, 640, 860, t - 0.56)
    if t > 0.56: impact(t, 0.56)
    if t > 1.0:
        # carroça / roda rolando
        rx = 300 + 200 * (t - 1.0); ra = tp * 8
        ellipse(c, rx, 560, 60, 60, 8, LBROWN, seed=2)
        for k in range(4): stroke(c, [(rx, 560), (rx + 60 * math.cos(ra + k * math.pi / 2), 560 + 60 * math.sin(ra + k * math.pi / 2))], 5)
        if t > 1.41: txt('TUDO', 140, 760, 300, RED, -6)

def s6(c, t, tp):
    ground(c)
    if t < 0.83:
        thermo(c, 340, 700, 0.2)
        for k in range(3): flake(c, 640 + k * 130, 420 + 60 * (k % 2), 45)
        txt('FRIO', 140, 700, 760, BLUE)
    elif t < 2.56:
        # gota de melaço escorrendo devagar
        yy = 420 + 80 * smoothstep((t - 0.83) / 1.7)
        stroke(c, [(540, 250), (540, yy - 40)], 30, BROWN)
        ellipse(c, 540, yy, 60, 75, 9, BROWN, seed=2)
        if t > 1.32: txt('GROSSO', 130, 540, 760, BROWN, -4)
        thermo(c, 170, 620, 0.2)
    elif t < 3.96:
        lvl = 0.0
        stroke(c, [(60, GY - 200), (300, GY - 215), (560, GY - 195), (800, GY - 210), (1020, GY - 200), (1020, GY), (60, GY)], 9, INK, True, BROWN, 2, 3)
        man(c, 540, GY, 1.6, 1, (-135 + 10 * math.sin(tp * 10), 135 - 10 * math.sin(tp * 10)), (0, 0), 'shock')
        stroke(c, [(220, GY - 205), (860, GY - 205)], 9, INK, False, None, 2, 3)
        c.set_source_rgb(*BROWN); c.rectangle(64, GY - 200, 952, 196); c.fill()
        for k in range(5): stroke(c, [(140 + k * 180, GY - 140), (200 + k * 180, GY - 150)], 5, LBROWN)
        if t > 3.34: txt('PRESO', 140, 540, 260, RED, -5)
    else:
        fly(c, 540, 700, 2.4)
        for sg in (-1, 1):
            for k in range(3): stroke(c, [(540 + sg * 50, 700 + k * 20), (540 + sg * (100 + 10 * k), 760 + k * 10)], 6)
        stroke(c, [(250, 760), (330, 730), (440, 745), (540, 728), (650, 748), (760, 732), (840, 760), (800, 840), (280, 840)], 9, INK, True, BROWN, 2, 5)
        for k in range(3): stroke(c, [(330 + k * 160, 790), (390 + k * 160, 785)], 6, LBROWN)
        if t > 4.17: qmark(c, 760, 520, 1.0); qmark(c, 330, 520, 0.8)
        man(c, 900, GY, 0.75, -1, (-20, 20), (6, -6), 'sad')

def s7(c, t, tp):
    ground(c)
    if t < 0.85:
        txt('SALDO', 220, 540, 450)
    else:
        tt = smoothstep((t - 0.85) / 0.6)
        h1 = 120 * tt
        rect(c, 230, GY - max(4, h1), 430, GY, 8, DGRAY, seed=1)
        txt(str(int(21 * tt)), 120, 330, GY - h1 - 90, INK)
        txt('mortos', 56, 330, GY - h1 - 165, DGRAY, 0, 'Bold')
        if t > 1.87:
            t2 = smoothstep((t - 1.87) / 0.7)
            h2 = 600 * t2
            rect(c, 650, GY - max(4, h2), 850, GY, 8, RED, seed=2)
            txt('~' + str(int(150 * t2)), 120, 750, GY - h2 - 90, RED); txt('feridos', 56, 750, GY - h2 - 165, DGRAY, 0, 'Bold')

def s8(c, t, tp):
    ground(c)
    if t < 1.81:
        man(c, 300, GY, 1.1, 1, (-15, 100), (0, 0), 'angry', 'bowler', 'tie')
        if t > 0.94:
            bubble(c, 330, 280, 1010, 470, 380, 640)
            txt('ANARQUISTAS!', 72, 670, 375, RED)
        for k in range(2):
            man(c, 720 + k * 170, GY, 0.7, -1, (-20, 20), (6, -6), 'shock')
            qmark(c, 720 + k * 170, 720, 0.7)
    elif t < 3.35:
        calendar(c, 540, 600, '1925', 'TRIBUNAL')
    else:
        tank(c, 330, GY, 0.85, 1.0, crack=1.0)
        gavel(c, 760, 640, -0.6 if t < 3.8 else 0.0)
        if t > 3.8:
            impact(t, 3.8); splat_rays(c, 700, 560, t - 3.8, 8)
        if t > 4.57: txt('MALFEITO', 130, 540, 260, RED, -5)

def s9(c, t, tp):
    ground(c)
    if t < 1.81:
        wave(c, -60, 560, GY, 600, tp)
        runner(c, 800, GY, 1.1, 1, tp, 'shock')
        txt('?', 260, 860, 420, RED)
    elif t < 2.23:
        man(c, 540, GY, 1.3, 1, (-20, -135), (0, 0), 'smile')
        bubble(c, 220, 260, 860, 450, 520, 650); txt('COMENTA', 100, 540, 355, INK)
    elif t < 4.52:
        man(c, 540, GY, 1.3, 1, (-30 - 10 * math.sin(tp * 6), 150), (0, 0), 'smile', None, 'tie')
        txt('SIGA', 220, 540, 400, RED, -4)
        heart(c, 820 + 10 * math.sin(tp * 5), 640, 1.0)
    else:
        wave(c, -60, 600, GY, 620, tp)
        runner(c, 840, GY, 1.1, 1, tp)
        txt('1919', 160, 540, 230)
        if t > 6.4: txt('21', 200, 850, 400, RED)
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

def render_frame(i, k):
    global JS
    t = k / FPS
    P = int(t * 15)
    tp = P / 15.0
    JS = P % 3
    SHAKE[0] = 0; SHAKE[1] = 0
    TXT.clear()
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    c = cairo.Context(surf)
    c.set_source_rgb(1, 1, 1); c.paint()
    # a tremida de impacto é aplicada depois de desenhar (translação do contexto precisa vir antes)
    c.save()
    SCENES[i](c, t, tp)
    c.restore()
    buf = np.frombuffer(surf.get_data(), np.uint8).reshape(H, W, 4)
    img = Image.fromarray(buf[..., [2, 1, 0]].copy(), 'RGB')
    if SHAKE[0]:
        dx = int(SHAKE[0]); img = Image.fromarray(np.roll(np.array(img), dx, 1))
    dr = ImageDraw.Draw(img)
    for s, size, cx, cy, col, rot, wgt in TXT:
        if not s: continue
        f = font(size, wgt)
        if rot:
            tw = int(dr.textlength(s, font=f)) + 40; th = int(size * 1.5)
            lay = Image.new('RGBA', (tw, th), (0, 0, 0, 0)); ImageDraw.Draw(lay).text((tw / 2, th / 2), s, font=f, fill=col + (255,), anchor='mm')
            lay = lay.rotate(rot, resample=Image.BICUBIC, expand=True)
            img.paste(lay, (int(cx - lay.width / 2), int(cy - lay.height / 2)), lay)
        else:
            dr.text((cx, cy), s, font=f, fill=col, anchor='mm')
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

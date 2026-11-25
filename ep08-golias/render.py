# Ep08 — Golias tinha 3 metros? — estilo PIXEL ART 2D retrô
# Render em 270x480 (pixels "gordos"), ampliado 4x por vizinho mais próximo -> 1080x1920.
import numpy as np, json, sys, subprocess, math, os
from PIL import Image, ImageDraw, ImageFont

W, H, S, FPS = 270, 480, 4, 30
D = json.load(open('aud/durs.json'))
WR = [json.load(open(f'aud/n{i}.json')) for i in range(len(D))]
# quebra tokens com várias palavras ("em 2005")
for i in range(len(WR)):
    out = []
    for a, b, x in WR[i]:
        ps = x.split()
        if len(ps) > 1:
            st = (b - a) / len(ps)
            for k, p in enumerate(ps): out.append([a + k * st, a + (k + 1) * st, p])
        else: out.append([a, b, x])
    WR[i] = out
STARTS = np.concatenate([[0], np.cumsum(D)[:-1]])
FONT = 'PressStart2P.ttf'
_fc = {}
def font(sz):
    if sz not in _fc: _fc[sz] = ImageFont.truetype(FONT, sz)
    return _fc[sz]

def norm(x): return x.lower().strip('.,!?…:;')
def wt(i, w, n=0):
    k = 0
    for a, b, x in WR[i]:
        if norm(x) == w:
            if k == n: return a
            k += 1
    print('MISSING', i, w, file=sys.stderr); return 0.0

# ---------- paleta (Sweetie-16 + extras) ----------
C = dict(ink=(26,28,44), purple=(93,39,93), red=(177,62,83), orange=(239,125,87), yel=(255,205,117),
         lgreen=(167,240,112), green=(56,183,100), teal=(37,113,121), dblue=(41,54,111), blue=(59,93,201),
         lblue=(65,166,246), cyan=(115,239,247), white=(244,244,244), lgray=(148,176,194), gray=(86,108,134),
         dgray=(51,60,87), sand=(222,172,110), dsand=(176,120,72), skin=(232,170,122), brown=(122,72,44),
         bronze=(205,142,58), dbronze=(140,88,30), tan=(214,190,140), parch=(240,220,170))

def ease_back(x):
    x = min(max(x, 0), 1); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2
def clamp01(x): return min(max(x, 0.0), 1.0)
def smooth(x): x = clamp01(x); return x * x * (3 - 2 * x)

BAYER = np.array([[0,8,2,10],[12,4,14,6],[3,11,1,9],[15,7,13,5]]) / 16.0
def grad_bg(cols, y0=0, y1=H):
    """céu em faixas com dither ordenado"""
    a = np.zeros((H, W, 3), np.uint8)
    ys = np.arange(H)[:, None]; xs = np.arange(W)[None, :]
    pos = np.clip((ys - y0) / max(1, (y1 - y0)), 0, 0.9999) * (len(cols) - 1)
    lo = np.floor(pos).astype(int); fr = pos - lo
    th = BAYER[ys % 4, xs % 4]
    idx = np.where(fr > th, lo + 1, lo); idx = np.clip(idx, 0, len(cols) - 1)
    pal = np.array(cols, np.uint8)
    return pal[np.broadcast_to(idx, (H, W))]

# ---------- sprites procedurais com contorno ----------
def spr_new(w, h): return np.zeros((h, w, 4), np.uint8)
def R(a, x0, y0, x1, y1, col):
    a[max(0,y0):max(0,y1), max(0,x0):max(0,x1), :3] = col; a[max(0,y0):max(0,y1), max(0,x0):max(0,x1), 3] = 255
def P(a, x, y, col):
    if 0 <= y < a.shape[0] and 0 <= x < a.shape[1]: a[y, x, :3] = col; a[y, x, 3] = 255
def outline(a, col=C['ink']):
    h, w = a.shape[:2]
    b = np.zeros((h + 2, w + 2, 4), np.uint8); b[1:-1, 1:-1] = a
    m = b[..., 3] > 0
    d = m.copy()
    d[1:] |= m[:-1]; d[:-1] |= m[1:]; d[:, 1:] |= m[:, :-1]; d[:, :-1] |= m[:, 1:]
    o = d & ~m
    b[o, :3] = col; b[o, 3] = 255
    return b

def char(kind, phase=0, pose='idle'):
    """boneco genérico em grade 24x38 (antes do contorno)"""
    a = spr_new(24, 38)
    step = (phase % 2) if pose == 'walk' else 0
    if kind == 'golias':
        body, skirt, limb, head = C['bronze'], C['red'], C['skin'], C['skin']
    elif kind == 'davi':
        body, skirt, limb, head = C['tan'], C['tan'], C['skin'], C['skin']
    elif kind == 'josefo':
        body, skirt, limb, head = C['blue'], C['blue'], C['skin'], C['skin']
    else:  # arqueólogo
        body, skirt, limb, head = C['sand'], C['dsand'], C['skin'], C['skin']
    # pernas
    R(a, 7, 27 - step, 10, 35 - step, C['dbronze'] if kind == 'golias' else limb)
    R(a, 12, 27 + step - step, 15, 35, C['dbronze'] if kind == 'golias' else limb)
    R(a, 6, 35 - step, 10, 37 - step, C['brown']); R(a, 12, 35, 16, 37, C['brown'])
    # corpo
    if kind == 'josefo':
        R(a, 5, 13, 17, 35, body); R(a, 5, 24, 17, 25, C['dblue'])
    else:
        R(a, 6, 13, 16, 23, body); R(a, 6, 22, 16, 28, skirt); R(a, 6, 22, 16, 23, C['brown'])
    if kind == 'golias':
        for yy in range(14, 22, 2):
            for xx in range(7 + (yy // 2) % 2, 16, 2): P(a, xx, yy, C['dbronze'])
    # braços
    if pose in ('up',):
        R(a, 3, 4, 6, 14, limb); R(a, 16, 4, 19, 14, limb)
    elif pose == 'sling':
        R(a, 3, 13, 6, 22, limb); R(a, 16, 5, 19, 14, limb)
    elif pose == 'dig':
        sw = phase % 2
        R(a, 16, 13 + sw * 3, 19, 21 + sw * 3, limb); R(a, 3, 13, 6, 21, limb)
    elif pose == 'hold':
        R(a, 3, 13, 6, 20, limb); R(a, 16, 13, 19, 20, limb)
    else:
        sw = step
        R(a, 3, 13 + sw, 6, 23 + sw, limb); R(a, 16, 13 - sw, 19, 23 - sw, limb)
    if kind == 'golias':
        R(a, 3, 19, 6, 21, C['bronze']); R(a, 16, 19, 19, 21, C['bronze'])
    # cabeça
    R(a, 7, 4, 15, 13, head)
    if kind == 'golias':
        R(a, 6, 2, 16, 7, C['bronze']); R(a, 6, 6, 8, 10, C['bronze']); R(a, 14, 6, 16, 10, C['bronze'])
        R(a, 9, 0, 13, 2, C['red'])
        R(a, 7, 10, 15, 13, C['brown']); P(a, 10, 11, C['ink']); P(a, 11, 11, C['ink'])
        P(a, 9, 8, C['ink']); P(a, 12, 8, C['ink']); R(a, 8, 7, 11, 8, C['dbronze']); R(a, 11, 7, 14, 7, C['dbronze'])
        # lança
        R(a, 21, 2, 22, 37, C['brown']); R(a, 20, 0, 23, 3, C['lgray']); P(a, 21, 0, C['white'])
    elif kind == 'davi':
        R(a, 7, 3, 15, 6, C['brown']); R(a, 7, 6, 8, 9, C['brown'])
        P(a, 10, 8, C['ink']); P(a, 13, 8, C['ink']); P(a, 9, 10, (240, 140, 120)); R(a, 11, 11, 13, 12, C['red'])
    elif kind == 'josefo':
        R(a, 6, 3, 16, 6, C['white']); R(a, 7, 10, 15, 14, C['lgray'])
        P(a, 9, 8, C['ink']); P(a, 12, 8, C['ink'])
        # pergaminho na mão
        R(a, 1, 16, 8, 21, C['parch']); R(a, 1, 16, 2, 21, C['dsand']); R(a, 7, 16, 8, 21, C['dsand'])
    else:
        R(a, 5, 4, 17, 6, C['dsand']); R(a, 7, 1, 15, 5, C['dsand'])
        P(a, 9, 8, C['ink']); P(a, 12, 8, C['ink']); R(a, 10, 11, 13, 12, C['brown'])
        if pose == 'dig':
            sw = phase % 2
            R(a, 20, 10 + sw * 3, 21, 30 + sw * 3, C['brown']); R(a, 18, 30 + sw * 3, 23, 34 + sw * 3, C['lgray'])
    return outline(a)

def blit(frame, spr, x, y, height=None, flip=False, rot=0, anchor='bottom'):
    """cola sprite RGBA no frame (RGB numpy). x = centro, y = base (pés)."""
    s = spr
    if rot: s = np.rot90(s, rot)
    if flip: s = s[:, ::-1]
    if height is not None:
        sc = height / s.shape[0]
        nh = max(1, int(round(s.shape[0] * sc))); nw = max(1, int(round(s.shape[1] * sc)))
        yi = (np.arange(nh) * s.shape[0] / nh).astype(int); xi = (np.arange(nw) * s.shape[1] / nw).astype(int)
        s = s[yi][:, xi]
    h, w = s.shape[:2]
    x0 = int(round(x - w / 2)); y0 = int(round(y - h)) if anchor == 'bottom' else int(round(y - h / 2))
    fx0, fy0 = max(0, x0), max(0, y0); fx1, fy1 = min(W, x0 + w), min(H, y0 + h)
    if fx1 <= fx0 or fy1 <= fy0: return
    sub = s[fy0 - y0:fy1 - y0, fx0 - x0:fx1 - x0]
    m = sub[..., 3] > 0
    frame[fy0:fy1, fx0:fx1][m] = sub[..., :3][m]

SPR = {}
def get_char(kind, phase, pose):
    k = (kind, phase % 2, pose)
    if k not in SPR: SPR[k] = char(kind, phase, pose)
    return SPR[k]

# ---------- objetos ----------
def scroll_spr(w=34, h=22, label=None):
    a = spr_new(w, h)
    R(a, 3, 2, w - 3, h - 2, C['parch'])
    R(a, 0, 0, 4, h, C['dsand']); R(a, w - 4, 0, w, h, C['dsand'])
    R(a, 1, 0, 3, h, C['tan']); R(a, w - 3, 0, w - 1, h, C['tan'])
    rng = np.random.default_rng(3)
    for yy in range(5, h - 4, 3):
        x = 6
        while x < w - 7:
            l = int(rng.integers(2, 6))
            R(a, x, yy, min(w - 6, x + l), yy + 1, C['brown']); x += l + 2
    return outline(a)
def jar_spr():
    a = spr_new(14, 22)
    R(a, 3, 0, 11, 3, C['dsand']); R(a, 1, 3, 13, 20, C['sand']); R(a, 3, 20, 11, 22, C['dsand'])
    R(a, 2, 6, 12, 7, C['dsand']); R(a, 9, 4, 11, 18, (240, 200, 140))
    return outline(a)
def armor_spr():
    a = spr_new(30, 30)
    R(a, 4, 4, 26, 28, C['bronze']); R(a, 0, 4, 6, 12, C['bronze']); R(a, 24, 4, 30, 12, C['bronze'])
    R(a, 10, 0, 20, 5, (0, 0, 0)); a[0:5, 10:20, 3] = 0
    for yy in range(7, 27, 3):
        for xx in range(5 + (yy // 3) % 2 * 2, 25, 4): R(a, xx, yy, xx + 2, yy + 1, C['dbronze'])
    R(a, 20, 6, 22, 24, (245, 190, 100))
    return outline(a)
def shard_spr():
    a = spr_new(40, 30)
    poly = [(2, 8), (12, 1), (30, 3), (38, 12), (33, 27), (14, 29), (4, 20)]
    im = Image.new('L', (40, 30), 0); ImageDraw.Draw(im).polygon(poly, fill=255)
    m = np.array(im) > 0
    a[m, :3] = C['orange']; a[m, 3] = 255
    a[m & (np.arange(30)[:, None] > 22), :3] = C['red']
    # marcas genéricas (traços)
    for (x, y) in [(10, 10), (16, 9), (22, 10), (13, 16), (20, 17), (27, 15)]:
        R(a, x, y, x + 1, y + 4, C['ink']); R(a, x + 1, y, x + 3, y + 1, C['ink'])
    return outline(a)
def stone_spr():
    a = spr_new(5, 5); R(a, 1, 0, 4, 5, C['lgray']); R(a, 0, 1, 5, 4, C['lgray']); P(a, 1, 1, C['white'])
    return outline(a)
def check_spr():
    a = spr_new(13, 11)
    pts = [(0, 5), (1, 6), (2, 7), (3, 8), (4, 9), (5, 8), (6, 7), (7, 6), (8, 5), (9, 4), (10, 3), (11, 2), (12, 1)]
    for x, y in pts: R(a, x, y - 1, x + 1, y + 2, C['lgreen'])
    return outline(a)
SCROLL = scroll_spr(); BIGSCROLL = scroll_spr(70, 40); JAR = jar_spr(); ARMOR = armor_spr()
SHARD = shard_spr(); STONE = stone_spr(); CHECK = check_spr()

# ---------- texto pixel ----------
ACC = {'Á':('A','acute'),'À':('A','grave'),'Â':('A','circ'),'Ã':('A','tilde'),'É':('E','acute'),'Ê':('E','circ'),
       'Í':('I','acute'),'Ó':('O','acute'),'Ô':('O','circ'),'Õ':('O','tilde'),'Ú':('U','acute'),'Ç':('C','ced')}
ACCPIX = {'acute':[(4,-3),(5,-3),(3,-2),(4,-2)], 'grave':[(2,-3),(3,-3),(3,-2),(4,-2)],
          'circ':[(3,-3),(4,-3),(2,-2),(5,-2)], 'tilde':[(2,-3),(3,-3),(6,-3),(1,-2),(4,-2),(5,-2)],
          'ced':[(3,7),(4,7),(4,8),(3,9),(4,9)]}
def draw_px_text(d, x, y, txt, sz, fill):
    """texto monoespaçado Press Start 2P com acentos desenhados à mão (a fonte encolhe as maiúsculas acentuadas)"""
    f = font(sz); u = max(1, sz // 8)
    base = ''.join(ACC.get(c, (c,))[0] for c in txt)
    d.text((x, y), base, font=f, fill=fill)
    top = y + f.getbbox('A')[1]
    for k, c in enumerate(txt):
        if c in ACC:
            for px, py in ACCPIX[ACC[c][1]]:
                X = x + k * sz + px * u; Y = top + py * u
                d.rectangle((X, Y, X + u - 1, Y + u - 1), fill=fill)

def text_img(txt, sz, col, sh=C['ink']):
    w = len(txt) * sz + 8; h = sz + sz // 2 + 8
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im); d.fontmode = '1'
    ox, oy = 3, 3 + sz // 2
    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1), (-1, 1), (1, -1), (2, 2), (1, 2), (2, 1)]:
        draw_px_text(d, ox + dx, oy + dy, txt, sz, sh + (255,))
    draw_px_text(d, ox, oy, txt, sz, col + (255,))
    return np.array(im)
_tc = {}
def text(frame, txt, sz, col, cx, cy, t_in=None, t=0, sh=C['ink']):
    k = (txt, sz, col, sh)
    if k not in _tc: _tc[k] = text_img(txt, sz, col, sh)
    s = _tc[k]
    sc = 1.0
    if t_in is not None:
        if t < t_in: return
        sc = ease_back((t - t_in) / 0.25)
        if sc < 0.05: return
    blit(frame, s, cx, cy, height=s.shape[0] * sc, anchor='center')

def ruler(frame, x, ground, maxm=3.0, ppm=50, mark=None, t=0):
    top = ground - int(maxm * ppm)
    frame[top:ground, x - 3:x + 3] = C['ink']; frame[top + 1:ground, x - 2:x + 2] = C['white']
    for k in range(int(maxm * 10) + 1):
        y = ground - int(k * ppm / 10)
        L = 9 if k % 10 == 0 else (6 if k % 5 == 0 else 3)
        frame[y:y + 1, x + 2:x + 2 + L] = C['ink'] if k % 10 else C['red']
        if k % 10 == 0 and k > 0:
            text(frame, f'{k//10}M', 8, C['white'], x - 14, y)
    if mark is not None:
        y = int(ground - mark * ppm)
        frame[y - 1:y + 1, x + 2:x + 60] = C['yel']

def hp_bar(frame, frac, label, y=78):
    text(frame, label, 8, C['white'], 135, y - 12)
    frame[y - 1:y + 9, 46:225] = C['ink']; frame[y:y + 8, 47:224] = C['dgray']
    wpx = int(177 * clamp01(frac))
    if wpx > 0:
        frame[y:y + 8, 47:47 + wpx] = C['red'] if frac < 0.3 else C['green']
        frame[y:y + 2, 47:47 + wpx] = C['lgreen'] if frac >= 0.3 else C['orange']

# ---------- cenários ----------
GROUND = 350
_bgc = {}
def desert(kind='day'):
    if kind in _bgc: return _bgc[kind].copy()
    if kind == 'day':
        a = grad_bg([C['lblue'], C['cyan'], C['yel'], C['orange']], 40, 300)
    elif kind == 'dusk':
        a = grad_bg([C['dblue'], C['purple'], C['red'], C['orange']], 30, 300)
    else:
        a = grad_bg([C['ink'], C['dblue'], C['purple']], 0, 320)
    im = Image.fromarray(a); d = ImageDraw.Draw(im)
    if kind != 'night':
        d.ellipse((180, 170, 240, 230), fill=C['yel'] if kind == 'day' else C['orange'])
    else:
        rng = np.random.default_rng(5)
        for _ in range(70):
            x, y = int(rng.integers(0, W)), int(rng.integers(0, 260)); d.point((x, y), fill=C['white'])
        d.ellipse((215, 150, 245, 180), fill=C['white']); d.ellipse((225, 146, 253, 174), fill=C['purple'])
    far = C['purple'] if kind != 'day' else C['teal']
    d.polygon([(0, 290), (40, 250), (90, 280), (140, 235), (200, 275), (270, 245), (270, 352), (0, 352)], fill=far)
    near = C['dsand'] if kind != 'night' else C['dgray']
    d.polygon([(0, 320), (60, 300), (130, 315), (200, 296), (270, 312), (270, 352), (0, 352)], fill=near)
    d.rectangle((0, GROUND, W, H), fill=C['sand'] if kind != 'night' else C['gray'])
    d.rectangle((0, GROUND, W, GROUND + 1), fill=C['ink'])
    rng = np.random.default_rng(9)
    for _ in range(40):
        x, y = int(rng.integers(0, W)), int(rng.integers(GROUND + 4, H))
        d.point((x, y), fill=C['dsand'] if kind != 'night' else C['dgray'])
    a = np.array(im); _bgc[kind] = a
    return a.copy()

def cave_bg():
    if 'cave' in _bgc: return _bgc['cave'].copy()
    a = desert('night'); im = Image.fromarray(a); d = ImageDraw.Draw(im)
    d.polygon([(0, 180), (60, 170), (120, 200), (170, 190), (270, 210), (270, 352), (0, 352)], fill=C['dsand'])
    d.polygon([(0, 230), (270, 250), (270, 352), (0, 352)], fill=C['brown'])
    for y in range(200, 350, 12): d.line((0, y + 8, 270, y + 14), fill=C['dsand'])
    d.ellipse((70, 230, 200, 330), fill=C['ink']); d.rectangle((70, 280, 200, 352), fill=C['ink'])
    d.rectangle((0, GROUND, W, H), fill=C['dgray'])
    a = np.array(im); _bgc['cave'] = a; return a.copy()

def ruins_bg():
    if 'ruins' in _bgc: return _bgc['ruins'].copy()
    a = desert('day'); im = Image.fromarray(a); d = ImageDraw.Draw(im)
    d.polygon([(0, 352), (30, 280), (240, 270), (270, 352)], fill=C['dsand'])
    for x0, h in [(40, 30), (90, 18), (150, 26), (200, 14)]:
        for yy in range(0, h, 6):
            for xx in range(0, 36, 12):
                o = 6 if (yy // 6) % 2 else 0
                d.rectangle((x0 + xx + o, 276 - h + yy, x0 + xx + o + 10, 276 - h + yy + 4), fill=C['tan'], outline=C['brown'])
    d.rectangle((0, GROUND, W, H), fill=C['sand']); d.rectangle((0, GROUND, W, GROUND + 1), fill=C['ink'])
    d.rectangle((150, 330, 240, 352), fill=C['brown'])  # cova da escavação
    a = np.array(im); _bgc['ruins'] = a; return a.copy()

def tiles_bg(c1, c2):
    k = ('tiles', c1, c2)
    if k in _bgc: return _bgc[k].copy()
    a = np.zeros((H, W, 3), np.uint8); a[:] = c1
    ys, xs = np.mgrid[0:H, 0:W]
    a[((ys // 15 + xs // 15) % 2 == 0)] = c2
    _bgc[k] = a; return a.copy()

# ---------- legendas ----------
def groups(i):
    ws = WR[i]; gs = []; cur = []
    for k, (a, b, x) in enumerate(ws):
        txt = x.upper()
        if cur:
            gap = a - ws[k - 1][1]
            ln = len(' '.join(c[2] for c in cur)) + 1 + len(txt)
            if len(cur) >= 3 or gap > 0.22 or ln > 15 or ws[k - 1][2][-1:] in '.,!?…:':
                gs.append(cur); cur = []
        cur.append([a, b, txt])
    if cur: gs.append(cur)
    return gs
GROUPS = [groups(i) for i in range(len(D))]

def captions(frame, i, t):
    gs = GROUPS[i]; g = None
    for k, gg in enumerate(gs):
        end = gs[k + 1][0][0] if k + 1 < len(gs) else D[i]
        if gg[0][0] - 0.05 <= t < end: g = gg; break
    if g is None: return
    txt = ' '.join(w[2] for w in g); n = len(txt)
    sz = 16 if n * 16 <= 244 else 8
    cw = sz; tw = n * cw; bx0 = (W - tw) // 2 - 7; bx1 = bx0 + tw + 14
    cy = 380; by0 = cy - sz // 2 - 7; by1 = cy + sz // 2 + 7
    frame[by0 - 1:by1 + 1, bx0 - 1:bx1 + 1] = C['ink']
    frame[by0:by1, bx0:bx1] = C['white']
    frame[by0 + 2:by1 - 2, bx0 + 2:bx1 - 2] = C['ink']
    x = bx0 + 7
    for a, b, wd in g:
        if t >= a - 0.03:
            col = C['yel'] if a - 0.03 <= t < max(b, a + 0.18) else C['white']
            s = _tc.get(('cap', wd, sz, col))
            if s is None:
                im = Image.new('RGBA', (len(wd) * sz + 4, sz + sz // 2 + 4), (0, 0, 0, 0))
                dd = ImageDraw.Draw(im); dd.fontmode = '1'; draw_px_text(dd, 0, sz // 2, wd, sz, col + (255,))
                s = np.array(im); _tc[('cap', wd, sz, col)] = s
            pop = clamp01((t - a + 0.03) / 0.1)
            dy = int(round((1 - pop) * 4))
            hh, ww = s.shape[:2]; y0 = cy - sz // 2 - sz // 2 + dy
            sub = frame[y0:y0 + hh, x:x + ww]; m = s[:sub.shape[0], :sub.shape[1], 3] > 0
            sub[m] = s[:sub.shape[0], :sub.shape[1], :3][m]
        x += (len(wd) + 1) * cw

# ---------- cenas ----------
def sparkle(frame, x, y, t, col=C['white']):
    r = 3 + int(2 * abs(math.sin(t * 10)))
    frame[y - r:y + r + 1, x:x + 1] = col; frame[y:y + 1, x - r:x + r + 1] = col

def scene(i, t, pose_t):
    ph = int(pose_t * 4)  # fase de caminhada/anim 4 Hz
    shake = 0; flash = 0
    if i == 0:
        f = desert('dusk'); ruler(f, 30, GROUND, mark=2.9)
        bob = 0
        blit(f, get_char('golias', ph, 'idle'), 120, GROUND, height=145)
        blit(f, get_char('davi', ph, 'idle'), 210, GROUND, height=80, flip=True)
        hp_bar(f, 1.0, 'CHEFÃO: GOLIAS')
        tm = wt(0, 'metros'); text(f, '3 METROS?', 24, C['yel'], 135, 122, tm, t)
        tn = wt(0, 'não'); text(f, 'OU NÃO?', 16, C['red'], 150, 160, tn, t, sh=C['white'])
        if 0 <= t - tn < 0.35 or t < 0.3: shake = 2
    elif i == 1:
        f = desert('day'); ruler(f, 30, GROUND, mark=None)
        ts = wt(1, 'seis'); tq = wt(1, 'quase')
        val = 2.9 * smooth((t - ts) / 1.6)
        ruler(f, 30, GROUND, mark=val if t > ts else None)
        blit(f, get_char('golias', ph, 'idle'), 130, GROUND, height=145)
        blit(f, SCROLL, 215, 300, height=44, anchor='center')
        text(f, '1 SAMUEL 17', 16, C['white'], 135, 74, wt(1, 'samuel'), t)
        text(f, 'TEXTO HEBRAICO', 8, C['ink'], 135, 96, wt(1, 'hebraico'), t, sh=C['white'])
        text(f, '6 CÔVADOS', 16, C['yel'], 135, 118, ts, t); text(f, '+ 1 PALMO', 16, C['yel'], 135, 140, ts + .3, t)
        if t > tq: text(f, '~2,9 M', 24, C['white'], 175, 180, tq, t, sh=C['red'])
        if 0 <= t - tq < 0.3: shake = 2
    elif i == 2:
        f = cave_bg()
        tr = wt(2, 'rolo')
        for k, x in enumerate([95, 115, 160, 180]):
            blit(f, JAR, x, GROUND - 2, height=26 + (k % 2) * 6)
        rise = smooth((t - tr) / 0.9)
        if t > tr - 0.1:
            y = 300 - 70 * rise
            gl = int(4 + 3 * abs(math.sin(t * 6)))
            f[int(y) - 26 - gl:int(y) + 26 + gl, 135 - 44 - gl:135 + 44 + gl] = np.clip(
                f[int(y) - 26 - gl:int(y) + 26 + gl, 135 - 44 - gl:135 + 44 + gl].astype(int) + 40, 0, 255).astype(np.uint8)
            blit(f, BIGSCROLL, 135, y, height=46, anchor='center')
            if rise > 0.9: sparkle(f, 185, int(y) - 20, t); sparkle(f, 88, int(y) + 14, t + 1)
        text(f, 'MANUSCRITOS', 16, C['cyan'], 135, 70, wt(2, 'manuscritos'), t)
        text(f, 'DO MAR MORTO', 16, C['cyan'], 135, 92, wt(2, 'mar'), t)
        text(f, 'ANTES DE CRISTO', 16, C['yel'], 135, 118, wt(2, 'antes'), t)
        to = wt(2, 'outra'); text(f, '?!', 24, C['red'], 50, 165, to, t, sh=C['white'])
    elif i == 3:
        f = desert('day')
        tq = wt(3, 'quatro'); td = wt(3, 'dois')
        hm = 2.9 - 0.9 * smooth((t - tq) / 1.4)
        ruler(f, 30, GROUND, mark=hm)
        blit(f, get_char('golias', ph, 'idle'), 130, GROUND, height=50 * hm)
        # fantasma do tamanho antigo
        if t > tq:
            yy = int(GROUND - 145)
            f[yy:yy + 1:, 90:170:2] = C['red']
        text(f, '4 CÔVADOS', 16, C['yel'], 135, 76, tq, t); text(f, '+ 1 PALMO', 16, C['yel'], 135, 98, tq + .3, t)
        text(f, '~2 M', 24, C['white'], 185, 175, td, t, sh=C['green'])
        if 0 <= t - td < 0.3: shake = 2
    elif i == 4:
        f = tiles_bg(C['dblue'], (48, 62, 124))
        ts = wt(4, 'septuaginta'); tj = wt(4, 'josefo'); tc = wt(4, 'concordam'); td = wt(4, 'dois')
        text(f, '+2 FONTES', 16, C['white'], 135, 70, 0.1, t)
        if t > ts:
            blit(f, BIGSCROLL, 70, 220, height=46 * max(1e-3, ease_back((t - ts) / .25)), anchor='center')
            text(f, 'SEPTUAGINTA', 8, C['yel'], 70, 256, ts, t); text(f, '(GREGA)', 8, C['lgray'], 70, 268, ts + .1, t)
        if t > tj:
            blit(f, get_char('josefo', 0, 'hold'), 200, 280, height=110 * max(1e-3, ease_back((t - tj) / .25)))
            text(f, 'JOSEFO', 8, C['yel'], 200, 292, tj, t)
        if t > tc:
            for x in (70, 200):
                blit(f, CHECK, x + 40, 180, height=33 * max(1e-3, ease_back((t - tc) / .25)), anchor='center')
        text(f, '2 METROS', 24, C['lgreen'], 135, 330, td, t)
        if 0 <= t - td < 0.3: shake = 2
    elif i == 5:
        f = desert('day'); ruler(f, 30, GROUND, mark=2.0)
        tg = wt(5, 'gigante'); tcq = wt(5, 'couraça'); tc5 = wt(5, 'cinquenta'); tqk = wt(5, 'quilos')
        blit(f, get_char('golias', ph, 'idle'), 95, GROUND, height=100)
        blit(f, get_char('davi', ph, 'idle'), 160, GROUND, height=82, flip=True)
        text(f, 'AINDA UM GIGANTE', 16, C['white'], 135, 72, tg, t)
        if t > tcq:
            blit(f, ARMOR, 220, 190, height=64 * max(1e-3, ease_back((t - tcq) / .25)), anchor='center')
            text(f, 'COURAÇA', 8, C['yel'], 220, 232, tcq + .1, t)
            # balança
            f[262:266, 190:251] = C['ink']; f[263:265, 191:250] = C['lgray']; f[266:346, 218:222] = C['ink']
            f[340:348, 200:241] = C['ink']
        if t > tc5:
            v = int(57 * smooth((t - tc5) / 0.9))
            text(f, f'{v} KG', 24, C['yel'], 175, 128, None, t)
        if 0 <= t - tqk < 0.3: shake = 2
    elif i == 6:
        f = ruins_bg()
        tg = wt(6, 'gate'); t05 = wt(6, '2005'); tca = wt(6, 'caco'); tn = wt(6, 'nomes')
        blit(f, get_char('arq', ph, 'dig'), 120, GROUND, height=84)
        text(f, 'GATE', 24, C['white'], 135, 74, tg, t)
        text(f, 'CIDADE DE GOLIAS', 8, C['yel'], 135, 98, tg + .3, t)
        text(f, '2005', 16, C['white'], 135, 124, t05, t, sh=C['red'])
        if t > tca:
            y = 330 - 110 * smooth((t - tca) / 0.5)
            blit(f, SHARD, 205, y, height=44, anchor='center'); sparkle(f, 230, int(y) - 22, t)
        text(f, 'NOMES PARECIDOS', 8, C['yel'], 205, 180, tn, t)
        text(f, 'COM "GOLIAS"', 8, C['yel'], 205, 192, tn + .15, t)
    elif i == 7:
        f = tiles_bg((60, 40, 50), (74, 50, 60))
        tt = wt(7, 'três')
        blit(f, SHARD, 135, 230, height=120, anchor='center')
        sparkle(f, 190, 185, t); sparkle(f, 80, 270, t + .5)
        text(f, 'ESCRITO HÁ', 16, C['white'], 135, 80, 0.05, t)
        if t > tt:
            v = int(3000 * smooth((t - tt) / 0.7))
            text(f, f'~{v:,}'.replace(',', '.'), 24, C['yel'], 135, 112, None, t)
            text(f, 'ANOS', 16, C['white'], 135, 140, tt, t)
    elif i == 8:
        f = desert('day')
        td = wt(8, 'davi'); tv = wt(8, 'venceu'); tp = wt(8, 'pedra')
        hit = tv + 0.45
        fall = smooth((t - hit - 0.15) / 0.3)
        hp_bar(f, 1.0 if t < hit else 0.0, 'CHEFÃO: GOLIAS')
        gpose = get_char('golias', ph if t < hit else 0, 'idle')
        if t < hit + 0.15:
            blit(f, gpose, 190, GROUND, height=100, flip=True)
        else:
            blit(f, gpose, 185, GROUND, height=100, flip=True, rot=1 if fall > 0.5 else 0)
            for k in range(3):
                a = t * 6 + k * 2.1
                sparkle(f, int(205 + 18 * math.cos(a)), int(GROUND - 52 + 6 * math.sin(a)), t, C['yel'])
        dpose = 'sling' if td <= t < hit else 'idle'
        blit(f, get_char('davi', ph, dpose), 60, GROUND, height=78)
        if td <= t < tv:
            a = (t - td) * 18
            sx, sy = 69 + int(12 * math.cos(a)), 272 + int(12 * math.sin(a))
            f[min(sy, 276):max(sy, 276) + 1, 68:70] = C['brown']
            blit(f, STONE, sx, sy, height=8, anchor='center')
        if tv <= t < hit:
            p = (t - tv) / (hit - tv)
            sx = 70 + (180 - 70) * p; sy = 272 - 30 * math.sin(math.pi * p) + (268 - 272) * p
            blit(f, STONE, sx, sy, height=8, anchor='center')
            for k in range(1, 4):
                q = max(0, p - k * 0.06); f[int(272 - 30 * math.sin(math.pi * q) - 4 * q), int(70 + 110 * q)] = C['white']
        if t >= hit:
            text(f, 'K.O.!', 24, C['red'], 135, 140, hit, t, sh=C['white'])
            if t - hit < 0.12: flash = 1
            if t - hit < 0.35: shake = 3
        text(f, '1 PEDRA SÓ', 16, C['yel'], 135, 176, tp, t)
    else:  # 9
        ta = wt(9, 'afinal'); tc = wt(9, 'comenta'); ts = wt(9, 'siga')
        if t < ta:
            f = tiles_bg(C['ink'], (34, 36, 58))
            text(f, 'E AÍ?', 24, C['yel'], 135, 76, 0.05, t)
            # menu de jogo
            f[110:200, 40:231] = C['white']; f[112:198, 42:229] = C['dblue']
            sel = 0 if (t % 1.2) < 0.6 else 1
            text(f, '2 METROS', 16, C['white'], 145, 138, 0.15, t)
            text(f, '3 METROS', 16, C['white'], 145, 172, 0.3, t)
            if int(t * 4) % 2 == 0: text(f, '>', 16, C['yel'], 62, 138 + 34 * sel, None, t)
            text(f, 'COMENTA!', 16, C['lgreen'], 135, 228, tc, t)
            if t > ts:
                text(f, 'SIGA PRA MAIS', 16, C['white'], 135, 262, ts, t)
                text(f, 'CURIOSIDADES', 16, C['yel'], 135, 284, ts + .15, t)
            blit(f, get_char('davi', ph, 'idle'), 135, GROUND, height=60)
        else:
            f = desert('dusk'); ruler(f, 30, GROUND, mark=2.9)
            blit(f, get_char('golias', ph, 'idle'), 120, GROUND, height=145)
            blit(f, get_char('davi', ph, 'idle'), 210, GROUND, height=80, flip=True)
            hp_bar(f, 1.0, 'CHEFÃO: GOLIAS')
            text(f, '3 METROS?', 24, C['yel'], 135, 122, wt(9, 'metros', 1), t)
    captions(f, i, t)
    return f, shake, flash

PREV_COL = [C['purple'], C['lblue'], C['ink'], C['lblue'], C['dblue'], C['lblue'], C['sand'], (60, 40, 50), C['lblue'], C['ink']]
def frame_at(i, t):
    pose_t = math.floor(t * 15) / 15  # animação "on twos"
    f, shake, flash = scene(i, t, pose_t)
    # transição: dissolve em blocos diagonal
    if i > 0 and t < 0.42:
        p = t / 0.42; col = PREV_COL[i - 1]
        cs = 15
        for cy in range(0, H, cs):
            for cx in range(0, W, cs):
                v = (cx / W + cy / H) / 2 + (((cx // cs) * 7 + (cy // cs) * 13) % 5) * 0.03
                if v > p * 1.2: f[cy:cy + cs, cx:cx + cs] = col
    if flash: f = np.clip(f.astype(int) + 150, 0, 255).astype(np.uint8)
    if shake:
        k = int(t * 30)
        dx = [shake, -shake, 0, shake, -shake][k % 5]; dy = [0, shake, -shake, -shake, shake][k % 5]
        f = np.roll(np.roll(f, dx, 1), dy, 0)
    return f

def up(f):
    big = f.repeat(S, 0).repeat(S, 1)
    out = np.empty((H * S, W * S, 4), np.uint8)
    out[..., 0] = big[..., 2]; out[..., 1] = big[..., 1]; out[..., 2] = big[..., 0]; out[..., 3] = 255
    return out

if __name__ == '__main__':
    if sys.argv[1] == '--still':
        os.makedirs('stills', exist_ok=True)
        for arg in sys.argv[2:]:
            T = float(arg); i = int(np.searchsorted(STARTS, T, side='right') - 1)
            f = frame_at(i, T - STARTS[i])
            Image.fromarray(f).resize((W * 2, H * 2), Image.NEAREST).save(f'stills/s_{T:05.2f}.png')
    else:
        i = int(sys.argv[1]); n = int(round(D[i] * FPS))
        os.makedirs('out', exist_ok=True)
        p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgra', '-s', f'{W*S}x{H*S}', '-r', str(FPS), '-i', '-',
                              '-c:v', 'libx264', '-crf', '19', '-preset', 'veryfast', '-pix_fmt', 'yuv420p', f'out/s{i}.tmp.mp4'], stdin=subprocess.PIPE)
        last = None; lastk = None
        for k in range(n):
            f = frame_at(i, k / FPS)
            p.stdin.write(up(f).tobytes())
        p.stdin.close(); rc = p.wait()
        if rc == 0: os.replace(f'out/s{i}.tmp.mp4', f'out/s{i}.mp4')
        print('scene', i, 'rc', rc)

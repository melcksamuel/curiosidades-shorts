# Estilo HQ / quadrinhos — "A guerra mais curta da história" (Zanzibar, 1896)
import cairo, math, json, sys, random, subprocess, os
import numpy as np

W, H, FPS = 1080, 1920, 30
D = os.path.dirname(os.path.abspath(__file__))
DURS = json.load(open(f"{D}/aud/durs.json"))
WORDS = [json.load(open(f"{D}/aud/n{i}.json")) for i in range(len(DURS))]
FONT = "Anton"
COMIC = "Comic Relief"

INK = (0.07, 0.06, 0.08)
WHITE = (1, 1, 1)
YEL = (1.0, 0.86, 0.15)
RED = (0.90, 0.17, 0.17)
BLUE = (0.16, 0.42, 0.85)
CYAN = (0.35, 0.80, 0.92)
ORANGE = (1.0, 0.55, 0.12)
GREEN = (0.30, 0.72, 0.35)
SKIN = (0.80, 0.58, 0.40)
SAND = (0.96, 0.84, 0.58)
NAVY = (0.12, 0.17, 0.35)
GRAY = (0.55, 0.57, 0.62)
PURP = (0.55, 0.30, 0.75)

# cor de página (fora do quadro) e céu do quadro por cena
PAGE = [RED, CYAN, YEL, BLUE, ORANGE, RED, ORANGE, PURP, GREEN, YEL]
SKY = [(YEL, ORANGE), ((0.55, 0.85, 1.0), (0.95, 0.97, 1.0)), ((1.0, 0.75, 0.45), (1.0, 0.92, 0.7)),
       ((0.55, 0.80, 1.0), (0.9, 0.95, 1.0)), ((1.0, 0.85, 0.55), (1.0, 0.95, 0.8)),
       ((1.0, 0.55, 0.25), (1.0, 0.85, 0.4)), ((0.95, 0.35, 0.15), (1.0, 0.7, 0.3)),
       ((0.25, 0.25, 0.40), (0.55, 0.45, 0.55)), ((0.6, 0.88, 0.6), (0.95, 1.0, 0.9)), ((1.0, 0.8, 0.5), (1.0, 0.95, 0.85))]

PX0, PY0, PX1, PY1 = 60, 330, 1020, 1400  # quadro principal


def clamp(x, a=0, b=1): return max(a, min(b, x))
def ease_out_back(x):
    x = clamp(x); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2
def ease_out(x): x = clamp(x); return 1 - (1 - x) ** 3
def ease_io(x): x = clamp(x); return x * x * (3 - 2 * x)
def pop(t, t0, d=0.28): return ease_out_back((t - t0) / d) if t >= t0 else 0.0


def wt(sc, word, nth=0):
    k = 0
    w0 = word.lower()
    for a, b, w in WORDS[sc]:
        if w.lower().strip(".,!?…:") == w0:
            if k == nth: return a
            k += 1
    return 0.0


# ---------- fundos halftone ----------
_bgcache = {}
def halftone_bg(color, seed):
    key = (color, seed)
    if key in _bgcache: return _bgcache[key]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    step = 26
    cx = (xx % step) - step / 2; cy = (yy % step) - step / 2
    # linha alternada deslocada
    row = (yy // step).astype(int)
    cx = ((xx + (row % 2) * step / 2) % step) - step / 2
    dist = np.sqrt(cx * cx + cy * cy)
    rad = 3 + 7 * (yy / H)  # pontos crescem para baixo
    dots = dist < rad
    base = np.array(color, np.float32)
    dark = base * 0.80
    img = np.where(dots[..., None], dark, base)
    a = np.zeros((H, W, 4), np.uint8)
    a[..., 0] = (img[..., 2] * 255); a[..., 1] = (img[..., 1] * 255); a[..., 2] = (img[..., 0] * 255); a[..., 3] = 255
    surf = cairo.ImageSurface.create_for_data(memoryview(a).cast("B"), cairo.FORMAT_ARGB32, W, H, W * 4)
    _bgcache[key] = (surf, a)
    return _bgcache[key]


def set_font(ctx, size, face=FONT, bold=False):
    ctx.select_font_face(face, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size)


def stroke_fill(ctx, fill, lw=6, ink=INK):
    ctx.set_source_rgb(*fill); ctx.fill_preserve()
    ctx.set_line_width(lw); ctx.set_source_rgb(*ink); ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.stroke()


def text_center(ctx, txt, x, y, size, fill=WHITE, outline=INK, lw=10, face=FONT, maxw=None):
    set_font(ctx, size, face, bold=(face == COMIC))
    e = ctx.text_extents(txt)
    if maxw and e.width > maxw:
        size *= maxw / e.width; set_font(ctx, size, face, bold=(face == COMIC)); e = ctx.text_extents(txt)
    tx = x - e.width / 2 - e.x_bearing; ty = y - e.height / 2 - e.y_bearing
    ctx.move_to(tx, ty); ctx.text_path(txt)
    if outline:
        ctx.set_line_width(lw); ctx.set_source_rgb(*outline); ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.stroke_preserve()
    ctx.set_source_rgb(*fill); ctx.fill(); ctx.new_path()
    return e


def burst(ctx, x, y, r, s, color, txt, size, rot=0, n=14, seed=1, tcol=YEL):
    if s <= 0.01: return
    rnd = random.Random(seed)
    ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(s, s)
    pts = []
    for i in range(n * 2):
        a = i * math.pi / n
        rr = r * (1.0 if i % 2 == 0 else 0.62) * (0.9 + 0.2 * rnd.random())
        pts.append((rr * math.cos(a), rr * math.sin(a) * 0.8))
    ctx.move_to(*pts[0])
    for p in pts[1:]: ctx.line_to(*p)
    ctx.close_path()
    stroke_fill(ctx, color, 8)
    if txt:
        lines = txt.split("\n")
        for k, ln in enumerate(lines):
            text_center(ctx, ln, 0, (k - (len(lines) - 1) / 2) * size * 1.05, size, tcol, INK, 12, maxw=r * 1.45)
    ctx.restore()


DEFER = None
def caption_box(ctx, txt, x, y, size, s, bg=YEL, rot=-0.025, face=FONT, fg=INK, pad=22):
    if s <= 0.01: return
    if DEFER is not None and y < PY0 + 40:
        DEFER.append((txt, x, y, size, s, bg, rot, face, fg, pad)); return
    set_font(ctx, size, face, bold=True)
    e = ctx.text_extents(txt)
    if e.width > 900: size *= 900 / e.width; set_font(ctx, size, face, bold=True); e = ctx.text_extents(txt)
    w = e.width + pad * 2; h = size * 1.25 + pad
    ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(s, s)
    ctx.rectangle(-w / 2 + 10, -h / 2 + 10, w, h); ctx.set_source_rgba(0, 0, 0, 0.9); ctx.fill()
    ctx.rectangle(-w / 2, -h / 2, w, h); stroke_fill(ctx, bg, 6)
    ctx.move_to(-e.width / 2 - e.x_bearing, -e.height / 2 - e.y_bearing); ctx.text_path(txt)
    ctx.set_source_rgb(*fg); ctx.fill()
    ctx.restore()


def bubble(ctx, lines, x, y, tailx, taily, s, size=54):
    if s <= 0.01: return
    set_font(ctx, size, COMIC, bold=True)
    wmax = max(ctx.text_extents(l).width for l in lines)
    w = wmax + 80; h = len(lines) * size * 1.2 + 60
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    ctx.save(); ctx.scale(w / 2, h / 2); ctx.arc(0, 0, 1, 0, 2 * math.pi); ctx.restore()
    stroke_fill(ctx, WHITE, 7)
    # rabicho
    tx, ty = (tailx - x) / s, (taily - y) / s
    ang = math.atan2(ty, tx); px, py = -math.sin(ang), math.cos(ang)
    bx, by = math.cos(ang) * w * 0.38, math.sin(ang) * h * 0.38
    ctx.move_to(bx + px * 30, by + py * 30); ctx.line_to(tx, ty); ctx.line_to(bx - px * 30, by - py * 30)
    ctx.close_path(); stroke_fill(ctx, WHITE, 7)
    ctx.save(); ctx.scale(w / 2 - 4, h / 2 - 4); ctx.arc(0, 0, 1, 0, 2 * math.pi); ctx.restore()
    ctx.set_source_rgb(*WHITE); ctx.fill()
    for k, l in enumerate(lines):
        set_font(ctx, size, COMIC, bold=True)
        e = ctx.text_extents(l)
        ctx.move_to(-e.width / 2 - e.x_bearing, (k - (len(lines) - 1) / 2) * size * 1.2 - e.height / 2 - e.y_bearing)
        ctx.set_source_rgb(*INK); ctx.show_text(l); ctx.new_path()
    ctx.restore()


# ---------- objetos ----------
def clock(ctx, x, y, r, minutes, s=1.0, face=WHITE, arc_min=None):
    if s <= 0.01: return
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    ctx.arc(0, 0, r, 0, 2 * math.pi); stroke_fill(ctx, face, 12)
    if arc_min is not None and arc_min > 0:
        ctx.move_to(0, 0); ctx.arc(0, 0, r * 0.86, -math.pi / 2, -math.pi / 2 + 2 * math.pi * arc_min / 60); ctx.close_path()
        ctx.set_source_rgba(*RED, 0.75); ctx.fill()
    for i in range(12):
        a = i * math.pi / 6
        ctx.move_to(math.cos(a) * r * 0.82, math.sin(a) * r * 0.82); ctx.line_to(math.cos(a) * r * 0.94, math.sin(a) * r * 0.94)
    ctx.set_line_width(8); ctx.set_source_rgb(*INK); ctx.stroke()
    hours = 9 + minutes / 60
    for ang, ln, lw in ((hours / 12 * 2 * math.pi, 0.5, 16), (minutes / 60 * 2 * math.pi, 0.78, 10)):
        ctx.move_to(0, 0); ctx.line_to(math.sin(ang) * r * ln, -math.cos(ang) * r * ln)
        ctx.set_line_width(lw); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_source_rgb(*INK); ctx.stroke()
    ctx.arc(0, 0, 14, 0, 2 * math.pi); ctx.set_source_rgb(*RED); ctx.fill()
    ctx.restore()


def sea(ctx, y, t, col=BLUE, amp=14):
    ctx.move_to(PX0 - 20, PY1 + 20); ctx.line_to(PX0 - 20, y)
    x = PX0 - 20
    while x <= PX1 + 40:
        ctx.line_to(x, y + amp * math.sin(x / 70 + t * 2.2)); x += 20
    ctx.line_to(PX1 + 40, PY1 + 20); ctx.close_path()
    stroke_fill(ctx, col, 6)
    # espuma
    for k in range(6):
        xx = PX0 + 80 + k * 160 + 20 * math.sin(t + k)
        ctx.move_to(xx, y + 60 + (k % 2) * 50); ctx.rel_line_to(50, 0)
    ctx.set_source_rgba(1, 1, 1, 0.7); ctx.set_line_width(6); ctx.stroke()


def ship(ctx, x, y, s, t, fire=0.0, flip=False):
    """navio de guerra genérico (casco cinza, 2 chaminés)"""
    ctx.save(); ctx.translate(x, y + 6 * math.sin(t * 2 + x)); ctx.scale(-s if flip else s, s)
    ctx.move_to(-220, -40); ctx.line_to(230, -40); ctx.line_to(180, 40); ctx.line_to(-190, 40); ctx.close_path()
    stroke_fill(ctx, GRAY, 7)
    ctx.rectangle(-220, -40, 450, 18); ctx.set_source_rgb(*RED); ctx.fill()
    ctx.rectangle(-120, -100, 200, 60); stroke_fill(ctx, (0.85, 0.85, 0.82), 7)
    for cx in (-80, 10):
        ctx.rectangle(cx, -175, 40, 80); stroke_fill(ctx, (0.25, 0.25, 0.28), 7)
        ctx.rectangle(cx, -175, 40, 14); ctx.set_source_rgb(*YEL); ctx.fill()
    # canhão
    ctx.rectangle(90, -80, 140, 20); stroke_fill(ctx, (0.3, 0.3, 0.33), 6)
    # fumaça
    for k in range(3):
        ph = (t * 0.6 + k / 3) % 1
        ctx.arc(-60 + ph * 60, -200 - ph * 150, 22 + ph * 40, 0, 2 * math.pi)
        ctx.set_source_rgba(0.3, 0.3, 0.3, 0.55 * (1 - ph)); ctx.fill()
    if fire > 0:
        burst(ctx, 290, -70, 90, fire, YEL, "", 0, n=10, seed=int(x))
        burst(ctx, 290, -70, 50, fire, WHITE, "", 0, n=8, seed=int(x) + 3)
    ctx.restore()


def yacht(ctx, x, y, s, t, tilt=0.0, sink=0.0):
    if s <= 0.01: return
    ctx.save(); ctx.translate(x, y + sink + 5 * math.sin(t * 2.5)); ctx.rotate(tilt); ctx.scale(s, s)
    ctx.move_to(-170, -30); ctx.line_to(180, -30); ctx.line_to(140, 35); ctx.line_to(-150, 35); ctx.close_path()
    stroke_fill(ctx, WHITE, 7)
    ctx.rectangle(-170, -8, 350, 12); ctx.set_source_rgb(*RED); ctx.fill()
    ctx.rectangle(-80, -85, 140, 55); stroke_fill(ctx, SAND, 7)
    for wx in (-60, -20, 20): ctx.rectangle(wx, -70, 24, 22); stroke_fill(ctx, CYAN, 4)
    ctx.move_to(-5, -85); ctx.line_to(-5, -200); ctx.set_line_width(8); ctx.set_source_rgb(*INK); ctx.stroke()
    ctx.move_to(-5, -200); ctx.line_to(70, -180); ctx.line_to(-5, -160); ctx.close_path(); stroke_fill(ctx, RED, 5)
    ctx.restore()


def palace(ctx, x, y, s, t, burn=0.0, collapse=0.0):
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    ctx.translate(0, collapse * 60); ctx.rotate(collapse * 0.06)
    # corpo de 3 andares com varandas
    ctx.rectangle(-260, -330, 520, 330); stroke_fill(ctx, (0.97, 0.93, 0.82), 8)
    ctx.rectangle(-90, -440, 180, 110); stroke_fill(ctx, (0.95, 0.88, 0.75), 8)
    ctx.move_to(-110, -440); ctx.line_to(0, -500); ctx.line_to(110, -440); ctx.close_path(); stroke_fill(ctx, RED, 8)
    for row in range(3):
        for col in range(6):
            wx = -230 + col * 80; wy = -305 + row * 100
            ctx.rectangle(wx, wy, 44, 60); stroke_fill(ctx, NAVY if burn < 0.5 else ORANGE, 5)
        ctx.move_to(-260, -240 + row * 100); ctx.line_to(260, -240 + row * 100)
        ctx.set_line_width(7); ctx.set_source_rgb(*INK); ctx.stroke()
    ctx.rectangle(-45, -90, 90, 90); stroke_fill(ctx, (0.45, 0.28, 0.15), 7)
    # mastro e bandeira vermelha
    ctx.move_to(0, -500); ctx.line_to(0, -620); ctx.set_line_width(7); ctx.set_source_rgb(*INK); ctx.stroke()
    fall = clamp(burn * 1.5)
    ctx.save(); ctx.translate(0, -620 + fall * 110)
    ctx.move_to(0, 0); ctx.line_to(90, 12 + 8 * math.sin(t * 6)); ctx.line_to(0, 45); ctx.close_path(); stroke_fill(ctx, RED, 5)
    ctx.restore()
    if burn > 0:
        flames(ctx, 0, -330, 300 * burn, t)
    ctx.restore()


def flames(ctx, x, y, h, t, w=520):
    for k in range(9):
        fx = x - w / 2 + k * w / 8
        hh = h * (0.6 + 0.4 * math.sin(t * 9 + k * 1.7))
        for col, sc in ((RED, 1.0), (ORANGE, 0.72), (YEL, 0.42)):
            ctx.move_to(fx - 45 * sc, y); ctx.curve_to(fx - 40 * sc, y - hh * sc * 0.6, fx - 5, y - hh * sc * 0.8, fx + 6 * math.sin(t * 7 + k), y - hh * sc)
            ctx.curve_to(fx + 10, y - hh * sc * 0.7, fx + 40 * sc, y - hh * sc * 0.5, fx + 45 * sc, y); ctx.close_path()
            ctx.set_source_rgb(*col); ctx.fill_preserve(); ctx.set_source_rgb(*INK); ctx.set_line_width(4 if sc == 1 else 0.01); ctx.stroke()


def person(ctx, x, y, s, t, robe=WHITE, hat="turban", hatcol=WHITE, arms=None, run=0.0, mouth=False, bob=0.0, face_dir=1):
    """boneco genérico estilo HQ (pés em y)"""
    ctx.save(); ctx.translate(x, y - abs(math.sin(t * 9)) * 18 * run - bob); ctx.scale(s * face_dir, s)
    lw = 7
    # pernas
    for i, sgn in enumerate((-1, 1)):
        a = math.sin(t * 9 + i * math.pi) * 0.6 * run
        ctx.save(); ctx.translate(sgn * 22, -110); ctx.rotate(a)
        ctx.rectangle(-14, 0, 28, 110); stroke_fill(ctx, (0.25, 0.22, 0.25), lw)
        ctx.restore()
    # corpo (túnica)
    ctx.move_to(-55, -250); ctx.line_to(55, -250); ctx.line_to(75, -95); ctx.line_to(-75, -95); ctx.close_path()
    stroke_fill(ctx, robe, lw)
    ctx.move_to(0, -250); ctx.line_to(0, -100); ctx.set_source_rgba(0, 0, 0, 0.25); ctx.set_line_width(4); ctx.stroke()
    # braços
    if arms is None:
        arms = (0.25 + math.sin(t * 9) * 0.9 * run, -0.25 - math.sin(t * 9) * 0.9 * run)
    for sgn, a in zip((-1, 1), arms):
        ctx.save(); ctx.translate(sgn * 52, -240); ctx.rotate(a * sgn if False else a)
        ctx.rectangle(-13, 0, 26, 105); stroke_fill(ctx, robe, lw)
        ctx.arc(0, 112, 16, 0, 2 * math.pi); stroke_fill(ctx, SKIN, 5)
        ctx.restore()
    # cabeça
    ctx.arc(0, -300, 50, 0, 2 * math.pi); stroke_fill(ctx, SKIN, lw)
    # barba
    ctx.move_to(-38, -285); ctx.curve_to(-30, -235, 30, -235, 38, -285); ctx.close_path(); stroke_fill(ctx, (0.2, 0.15, 0.12), 5)
    # olhos
    for ex in (-17, 17):
        ctx.arc(ex + 6, -310, 8, 0, 2 * math.pi); ctx.set_source_rgb(*INK); ctx.fill()
        ctx.arc(ex + 8, -313, 3, 0, 2 * math.pi); ctx.set_source_rgb(1, 1, 1); ctx.fill()
    if mouth:
        ctx.arc(8, -275, 12 + 5 * abs(math.sin(t * 14)), 0, 2 * math.pi); ctx.set_source_rgb(0.4, 0.05, 0.05); ctx.fill()
    if hat == "turban":
        ctx.save(); ctx.translate(0, -345); ctx.scale(62, 38); ctx.arc(0, 0, 1, 0, 2 * math.pi); ctx.restore()
        stroke_fill(ctx, hatcol, lw)
        ctx.move_to(-50, -340); ctx.curve_to(-10, -365, 20, -330, 55, -350); ctx.set_line_width(4); ctx.set_source_rgb(*INK); ctx.stroke()
        ctx.arc(0, -352, 10, 0, 2 * math.pi); stroke_fill(ctx, RED, 4)
    elif hat == "cap":
        ctx.move_to(-52, -320); ctx.curve_to(-50, -375, 50, -375, 52, -320); ctx.close_path(); stroke_fill(ctx, hatcol, lw)
        ctx.rectangle(-5, -330, 75, 14); stroke_fill(ctx, INK, 3)
    ctx.restore()


def cannon(ctx, x, y, s, t, fire=0.0):
    if s <= 0.01: return
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    ctx.save(); ctx.rotate(-0.35 - fire * 0.08)
    ctx.move_to(-40, -30); ctx.line_to(150, -20); ctx.line_to(150, 20); ctx.line_to(-40, 30); ctx.close_path()
    stroke_fill(ctx, (0.35, 0.33, 0.30), 7)
    ctx.restore()
    for wx in (-20,):
        ctx.arc(wx, 20, 48, 0, 2 * math.pi); stroke_fill(ctx, (0.55, 0.35, 0.18), 7)
        for k in range(6):
            a = k * math.pi / 3
            ctx.move_to(wx, 20); ctx.line_to(wx + 44 * math.cos(a), 20 + 44 * math.sin(a))
        ctx.set_line_width(5); ctx.set_source_rgb(*INK); ctx.stroke()
    ctx.restore()


def island(ctx, x, y, s, t):
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    ctx.move_to(-260, 0); ctx.curve_to(-200, -80, 180, -110, 280, 0); ctx.close_path(); stroke_fill(ctx, SAND, 8)
    for px, ph in ((-90, 0), (60, 1.3)):
        ctx.move_to(px, -60); ctx.curve_to(px + 10, -160, px + 30, -230, px + 45, -280)
        ctx.set_line_width(18); ctx.set_source_rgb(*INK); ctx.stroke_preserve() if False else None
        ctx.set_line_width(22); ctx.set_source_rgb(*INK); ctx.stroke()
        ctx.move_to(px, -60); ctx.curve_to(px + 10, -160, px + 30, -230, px + 45, -280)
        ctx.set_line_width(12); ctx.set_source_rgb(0.6, 0.4, 0.2); ctx.stroke()
        for k in range(5):
            a = -math.pi / 2 + (k - 2) * 0.75 + 0.08 * math.sin(t * 2 + ph + k)
            cx, cy = px + 45, -280
            ctx.move_to(cx, cy)
            ctx.curve_to(cx + math.cos(a - 0.4) * 90, cy + math.sin(a - 0.4) * 90 - 20, cx + math.cos(a) * 150, cy + math.sin(a) * 120,
                         cx + math.cos(a) * 170, cy + math.sin(a) * 120 + 40)
            ctx.curve_to(cx + math.cos(a) * 110, cy + math.sin(a) * 90 + 10, cx + math.cos(a + 0.3) * 60, cy + math.sin(a + 0.3) * 40, cx, cy)
            stroke_fill(ctx, GREEN, 5)
    ctx.restore()


def crown(ctx, x, y, s, rot=0):
    if s <= 0.01: return
    ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(s, s)
    ctx.move_to(-90, 50); ctx.line_to(-100, -50); ctx.line_to(-50, 0); ctx.line_to(0, -70); ctx.line_to(50, 0); ctx.line_to(100, -50)
    ctx.line_to(90, 50); ctx.close_path(); stroke_fill(ctx, YEL, 8)
    for gx, gc in ((-50, RED), (0, BLUE), (50, GREEN)):
        ctx.arc(gx, 25, 13, 0, 2 * math.pi); stroke_fill(ctx, gc, 4)
    ctx.restore()


def scroll(ctx, x, y, s, lines, rot=0.03):
    if s <= 0.01: return
    ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(s, s)
    ctx.rectangle(-300, -170, 600, 340); stroke_fill(ctx, (0.98, 0.93, 0.78), 8)
    for yy in (-170, 170):
        ctx.save(); ctx.translate(0, yy); ctx.scale(320, 26); ctx.arc(0, 0, 1, 0, 2 * math.pi); ctx.restore(); stroke_fill(ctx, (0.88, 0.78, 0.55), 6)
    for k, (txt, col, sz) in enumerate(lines):
        text_center(ctx, txt, 0, -95 + k * 95, sz, col, None, 0, maxw=520)
    ctx.restore()


def cup(ctx, x, y, s, t):
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    for k in range(3):
        ph = (t * 0.7 + k / 3) % 1
        ctx.move_to(-40 + k * 40, -150 - ph * 120)
        ctx.curve_to(-60 + k * 40, -190 - ph * 120, -20 + k * 40, -220 - ph * 120, -40 + k * 40, -260 - ph * 120)
        ctx.set_source_rgba(1, 1, 1, 0.9 * (1 - ph)); ctx.set_line_width(12); ctx.stroke()
    ctx.move_to(-120, -130); ctx.line_to(120, -130); ctx.line_to(95, 60); ctx.line_to(-95, 60); ctx.close_path(); stroke_fill(ctx, WHITE, 8)
    ctx.arc(140, -45, 50, -math.pi / 2, math.pi / 2); ctx.set_line_width(26); ctx.set_source_rgb(*INK); ctx.stroke()
    ctx.arc(140, -45, 50, -math.pi / 2, math.pi / 2); ctx.set_line_width(12); ctx.set_source_rgb(*WHITE); ctx.stroke()
    ctx.save(); ctx.translate(0, -130); ctx.scale(118, 22); ctx.arc(0, 0, 1, 0, 2 * math.pi); ctx.restore(); stroke_fill(ctx, (0.40, 0.22, 0.10), 6)
    ctx.save(); ctx.translate(0, 75); ctx.scale(190, 26); ctx.arc(0, 0, 1, 0, 2 * math.pi); ctx.restore(); stroke_fill(ctx, WHITE, 7)
    ctx.rectangle(-95, -60, 190, 30); ctx.set_source_rgb(*RED); ctx.fill()
    ctx.restore()


def building(ctx, x, y, s, label):
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    ctx.rectangle(-200, -360, 400, 360); stroke_fill(ctx, (0.88, 0.90, 0.95), 8)
    ctx.move_to(-230, -360); ctx.line_to(0, -470); ctx.line_to(230, -360); ctx.close_path(); stroke_fill(ctx, (0.75, 0.30, 0.25), 8)
    for cx in (-150, -50, 50, 150):
        ctx.rectangle(cx - 14, -330, 28, 230); stroke_fill(ctx, WHITE, 5)
    ctx.rectangle(-50, -110, 100, 110); stroke_fill(ctx, (0.45, 0.28, 0.15), 7)
    # placa
    ctx.rectangle(-180, -440 + 70, 360, 0)
    ctx.restore()
    caption_box(ctx, label, x, y - 380 * s - 40, 46, 1.0, WHITE, 0.02)


def bill(ctx, x, y, s, t, stamp):
    if s <= 0.01: return
    ctx.save(); ctx.translate(x, y); ctx.rotate(-0.06); ctx.scale(s, s)
    ctx.move_to(-190, -240); ctx.line_to(190, -240); ctx.line_to(190, 220)
    for k in range(10):
        ctx.line_to(190 - (k + 0.5) * 38, 245 if k % 2 == 0 else 220)
    ctx.line_to(-190, 220); ctx.close_path(); stroke_fill(ctx, WHITE, 8)
    text_center(ctx, "CONTA", 0, -180, 70, INK, None, 0)
    for k in range(4):
        ctx.move_to(-150, -100 + k * 60); ctx.line_to(60, -100 + k * 60)
        ctx.set_source_rgb(0.6, 0.6, 0.6); ctx.set_line_width(10); ctx.stroke()
        text_center(ctx, "$$", 120, -100 + k * 60, 40, INK, None, 0)
    text_center(ctx, "TOTAL: $$$$", 0, 160, 58, RED, None, 0)
    ctx.restore()
    if stamp > 0.01:
        ctx.save(); ctx.translate(x + 30, y + 10); ctx.rotate(-0.3); ctx.scale(stamp, stamp)
        ctx.rectangle(-210, -60, 420, 120); ctx.set_source_rgb(*RED); ctx.set_line_width(12); ctx.stroke()
        text_center(ctx, "A CONTA É SUA!", 0, 0, 52, RED, None, 0, maxw=380)
        ctx.restore()


# ---------- cenas ----------
def scene(ctx, i, t, T):
    if i == 0:
        # relógio gigante + explosões
        m = clamp(t / (T * 0.9)) * 45
        clock(ctx, 540, 880, 300, m, ease_out_back(t / 0.5), arc_min=m)
        burst(ctx, 260, 560, 140, pop(t, 0.25), RED, "BOOM!", 70, -0.2, seed=3)
        burst(ctx, 830, 1220, 150, pop(t, wt(0, "durou")), YEL, "45\nMIN!", 68, 0.15, seed=4, tcol=RED)
        caption_box(ctx, "A GUERRA MAIS CURTA DA HISTÓRIA", 540, 300, 64, pop(t, 0.05))
    elif i == 1:
        sea(ctx, 1050, t)
        island(ctx, 540, 1080, 1.1, t)
        caption_box(ctx, "ZANZIBAR • ÁFRICA • 1896", 540, 300, 66, pop(t, 0.05))
        tm = wt(1, "sultão")
        cr = clamp((t - tm) / 0.9)
        if t > tm:
            crown(ctx, 760, 520 + 520 * ease_io(cr), 1.0, cr * 2.4)
            burst(ctx, 300, 600, 120, pop(t, tm + 0.1), WHITE, "!!!", 80, -0.1, seed=7, tcol=RED)
        else:
            crown(ctx, 760, 520, pop(t, 0.8))
    elif i == 2:
        palace(ctx, 640, 1340, 1.0, t)
        tk = wt(2, "khalid")
        person(ctx, 300, 1380, 1.25, t, robe=WHITE, hatcol=WHITE, arms=(2.6, -0.3) if t > wt(2, "declara") else None,
               run=0.0, mouth=t > wt(2, "declara"))
        if t > wt(2, "declara"):
            crown(ctx, 300, 760, pop(t, wt(2, "declara")) * 0.7, -0.1)
        bubble(ctx, ["AGORA EU", "SOU O SULTÃO!"], 600, 560, 380, 840, pop(t, wt(2, "declara")))
        caption_box(ctx, "KHALID TOMA O PALÁCIO", 540, 300, 64, pop(t, tk))
    elif i == 3:
        sea(ctx, 1150, t)
        ship(ctx, 300, 1170, 0.9, t)
        ship(ctx, 830, 1230, 0.75, t + 1)
        scroll(ctx, 540, 700, pop(t, wt(3, "ultimato") - 0.1),
               [("ULTIMATO", RED, 92), ("SAIA DO PALÁCIO", INK, 60), ("ATÉ AS 9:00!", INK, 72)])
        caption_box(ctx, "OS BRITÂNICOS QUEREM OUTRO", 540, 300, 60, pop(t, 0.05))
        clock(ctx, 880, 1000, 110, 0 if t < wt(3, "nove") else 0, pop(t, wt(3, "nove")))
    elif i == 4:
        # contador de homens + multidão
        n = int(3000 * ease_out(clamp((t - wt(4, "quase")) / 1.4)))
        caption_box(ctx, f"≈ {n:,}".replace(",", ".") + " HOMENS", 540, 300, 80, pop(t, wt(4, "quase") - 0.1), WHITE)
        sea(ctx, 1250, t)
        for k in range(7):
            person(ctx, 140 + k * 70 + (k % 2) * 20, 1180 + (k % 2) * 40, 0.55, t + k, robe=(0.95, 0.95, 0.9), hatcol=WHITE,
                   arms=(0.4, -2.4 if k % 3 == 0 else -0.3))
        cannon(ctx, 720, 1140, 1.0 * pop(t, wt(4, "canhões")), t)
        cannon(ctx, 880, 1180, 0.8 * pop(t, wt(4, "velhos")), t)
        yacht(ctx, 720, 1300, 0.9 * pop(t, wt(4, "iate")), t)
        if t > wt(4, "iate"):
            caption_box(ctx, "O IATE REAL", 720, 1000, 56, pop(t, wt(4, "iate")), WHITE, 0.04)
    elif i == 5:
        tf = wt(5, "fogo")
        clock(ctx, 540, 640, 200, 0, pop(t, 0.05))
        caption_box(ctx, "9:00", 540, 900, 90, pop(t, 0.2), WHITE, -0.05)
        sea(ctx, 1170, t)
        fire1 = 1.0 if (t > tf and (t - tf) % 0.8 < 0.3) else 0
        fire2 = 1.0 if (t > tf + 0.35 and (t - tf - 0.35) % 0.8 < 0.3) else 0
        ship(ctx, 260, 1200, 0.75, t, fire1)
        ship(ctx, 640, 1270, 0.7, t + 2, fire2)
        if t > wt(5, "ninguém"):
            bubble(ctx, ["NINGUÉM", "SE RENDE..."], 820, 470, 700, 640, pop(t, wt(5, "ninguém")), 48)
        burst(ctx, 800, 900, 170, pop(t, tf), RED, "KA-BUM!", 72, 0.12, seed=11)
    elif i == 6:
        ta = wt(6, "afunda"); tp = wt(6, "palácio")
        palace(ctx, 640, 1100, 0.85, t, burn=ease_out((t - tp + 0.2) / 1.0) if t > tp - 0.2 else 0,
               collapse=ease_io((t - wt(6, "desaba")) / 1.2) if t > wt(6, "desaba") else 0)
        sea(ctx, 1180, t)
        sk = ease_io((t - ta + 0.3) / 1.8) if t > ta - 0.3 else 0
        yacht(ctx, 300, 1220, 0.85, t, tilt=0.6 * sk, sink=180 * sk)
        sea(ctx, 1260, t + 1.3, (0.12, 0.33, 0.70), 10)
        burst(ctx, 260, 560, 130, pop(t, ta), CYAN, "GLUB\nGLUB!", 58, -0.15, seed=12, tcol=WHITE)
        burst(ctx, 820, 520, 150, pop(t, wt(6, "chamas")), YEL, "CRASH!", 70, 0.12, seed=13, tcol=RED)
    elif i == 7:
        m = clamp((t - wt(7, "quarenta")) / 1.2) * 40
        clock(ctx, 540, 620, 200, m, pop(t, 0.05), arc_min=m)
        caption_box(ctx, "≈ 40 MINUTOS", 540, 300, 70, pop(t, wt(7, "quarenta")), WHITE)
        tq = wt(7, "quinhentos"); tb = wt(7, "britânico")
        n = int(500 * ease_out(clamp((t - tq) / 1.0)))
        if t > tq - 0.1:
            s = pop(t, tq - 0.1)
            ctx.save(); ctx.translate(300, 1080); ctx.scale(max(s, 1e-3), max(s, 1e-3))
            ctx.rectangle(-210, -200, 420, 400); stroke_fill(ctx, RED, 9)
            text_center(ctx, f"~{n}", 0, -40, 150, YEL, INK, 14)
            text_center(ctx, "ZANZIBAR", 0, 120, 60, WHITE, INK, 9)
            ctx.restore()
        if t > tb - 0.6:
            s = pop(t, tb - 0.6)
            ctx.save(); ctx.translate(790, 1080); ctx.scale(max(s, 1e-3), max(s, 1e-3))
            ctx.rectangle(-190, -200, 380, 400); stroke_fill(ctx, BLUE, 9)
            text_center(ctx, "1", 0, -40, 170, YEL, INK, 14)
            text_center(ctx, "BRITÂNICO", 0, 120, 56, WHITE, INK, 9)
            ctx.restore()
            text_center(ctx, "VS", 545, 1080, 90, WHITE, INK, 12)
    elif i == 8:
        tf = wt(8, "fugiu"); ta = wt(8, "absurdo")
        if t < ta - 0.1:
            building(ctx, 760, 1360, 0.95, "CONSULADO ALEMÃO")
            px = 160 + 480 * ease_io((t - tf + 0.2) / 2.0)
            person(ctx, px, 1380, 1.0, t, robe=WHITE, hatcol=WHITE, run=1.0 if t < tf + 1.8 else 0.0, mouth=True)
            burst(ctx, 260, 560, 110, pop(t, tf), WHITE, "FUI!", 70, -0.15, seed=21, tcol=RED)
        else:
            tt = t - ta
            bill(ctx, 540, 900, pop(tt, 0.0), t, pop(t, wt(8, "conta")))
            burst(ctx, 250, 520, 120, pop(t, ta), YEL, "?!", 90, -0.2, seed=22, tcol=RED)
        caption_box(ctx, "E O MAIS ABSURDO..." if t >= ta - 0.1 else "A FUGA", 540, 300, 64, pop(t, 0.05 if t < ta - 0.1 else ta - 0.1))
    elif i == 9:
        cup(ctx, 360, 1150, 1.4, t)
        m = clamp(t / 3.0) * 38
        clock(ctx, 800, 820, 150, m, pop(t, 0.15), arc_min=m)
        caption_box(ctx, "VOCÊ SABIA?", 540, 300, 90, pop(t, wt(9, "você")), WHITE, -0.03)
        if t > wt(9, "comenta") - 0.1:
            burst(ctx, 800, 1230, 180, pop(t, wt(9, "comenta") - 0.1), RED, "SIGA PRA\nMAIS!", 62, 0.1, seed=31)


def draw_subs(ctx, i, t):
    words = [[a, b, w.strip(".,!?…:")] for a, b, w in WORDS[i]]
    groups = []; cur = []
    for k, w in enumerate(words):
        if cur and (len(cur) >= 3 or w[0] - cur[-1][1] > 0.22):
            groups.append(cur); cur = []
        cur.append(w)
    if cur: groups.append(cur)
    g = None
    for gg in groups:
        if t >= gg[0][0] - 0.05: g = gg
    if g is None: return
    if t > g[-1][1] + 0.6 and g is groups[-1]: return
    size = 76
    set_font(ctx, size)
    vis = [w for w in g if t >= w[0] - 0.03]
    widths = [ctx.text_extents(w[2].upper()).x_advance + 40 for w in g]
    total = sum(widths) + 18 * (len(g) - 1)
    if total > 1000:
        size *= 1000 / total; set_font(ctx, size)
        widths = [ctx.text_extents(w[2].upper()).x_advance + 40 * size / 76 for w in g]; total = sum(widths) + 18 * (len(g) - 1)
    x = 540 - total / 2
    for w, wd in zip(g, widths):
        if t >= w[0] - 0.03:
            s = ease_out_back((t - w[0] + 0.03) / 0.16)
            active = w[0] <= t < w[1] + 0.05
            ctx.save(); ctx.translate(x + wd / 2, 1530); ctx.rotate(-0.02); ctx.scale(max(s, 1e-3), max(s, 1e-3))
            h = size * 1.35
            ctx.rectangle(-wd / 2 + 7, -h / 2 + 7, wd, h); ctx.set_source_rgb(*INK); ctx.fill()
            ctx.rectangle(-wd / 2, -h / 2, wd, h); stroke_fill(ctx, YEL if active else WHITE, 6)
            e = ctx.text_extents(w[2].upper())
            ctx.move_to(-e.width / 2 - e.x_bearing, -e.height / 2 - e.y_bearing); ctx.set_source_rgb(*INK); ctx.show_text(w[2].upper()); ctx.new_path()
            ctx.restore()
        x += wd + 18


def shake_amount(i, t):
    hits = {0: [0.25], 5: [wt(5, "fogo")], 6: [wt(6, "afunda"), wt(6, "chamas")], 1: [wt(1, "sultão")]}
    a = 0
    for h in hits.get(i, []):
        if 0 <= t - h < 0.35: a = max(a, 16 * (1 - (t - h) / 0.35))
    return a


def frame(i, t):
    T = DURS[i]
    tq = math.floor(t * 15) / 15  # animação "on twos"
    bg, _ = halftone_bg(PAGE[i], i)
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surf)
    ctx.set_source_surface(bg); ctx.paint()
    # linhas de velocidade na página
    rnd = random.Random(i * 7)
    for k in range(40):
        a = rnd.random() * 2 * math.pi
        ctx.move_to(540 + math.cos(a) * 700, 860 + math.sin(a) * 700); ctx.line_to(540 + math.cos(a) * 1400, 860 + math.sin(a) * 1400)
    ctx.set_source_rgba(1, 1, 1, 0.35); ctx.set_line_width(5); ctx.stroke()
    sh = shake_amount(i, tq)
    sx = sh * math.sin(tq * 90); sy = sh * math.cos(tq * 77)
    ctx.save(); ctx.translate(sx, sy)
    # sombra do quadro
    ctx.rectangle(PX0 + 16, PY0 + 16, PX1 - PX0, PY1 - PY0); ctx.set_source_rgb(*INK); ctx.fill()
    # quadro
    ctx.save()
    ctx.rectangle(PX0, PY0, PX1 - PX0, PY1 - PY0); ctx.clip()
    g = cairo.LinearGradient(0, PY0, 0, PY1)
    g.add_color_stop_rgb(0, *SKY[i][0]); g.add_color_stop_rgb(1, *SKY[i][1])
    ctx.set_source(g); ctx.paint()
    # pontos halftone discretos no céu
    z = 1 + 0.035 * (tq / T)
    ctx.translate(540, 865); ctx.scale(z, z); ctx.translate(-540, -865)
    global DEFER
    DEFER = []
    scene(ctx, i, tq, T)
    dl = DEFER; DEFER = None
    ctx.restore()
    ctx.rectangle(PX0, PY0, PX1 - PX0, PY1 - PY0); ctx.set_line_width(12); ctx.set_source_rgb(*INK); ctx.stroke()
    for a in dl: caption_box(ctx, *a)
    ctx.restore()
    # textos sobre o quadro (legendas e títulos já estão no scene; caption por cima da borda)
    draw_subs(ctx, i, t)
    # transição: limpeza diagonal da cor da página anterior
    if i > 0 and t < 0.4:
        p = ease_io(t / 0.4)
        ctx.move_to(-200 + p * 2600, -100); ctx.line_to(2600, -100); ctx.line_to(2600, 2100); ctx.line_to(-200 + p * 2600 - 900, 2100); ctx.close_path()
        ctx.set_source_rgb(*PAGE[i - 1]); ctx.fill_preserve(); ctx.set_source_rgb(*INK); ctx.set_line_width(16); ctx.stroke()
    return surf


def render_scene(i):
    T = DURS[i]; n = int(round(T * FPS))
    out = f"{D}/out/s{i}.tmp.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-crf", "19", "-preset", "veryfast", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    last_key = None; last = None
    for f in range(n):
        t = f / FPS
        key = (math.floor(t * 15), None)
        # legendas mudam por palavra -> re-render quando necessário (barato o suficiente)
        surf = frame(i, t)
        p.stdin.write(bytes(surf.get_data()))
    p.stdin.close(); rc = p.wait()
    if rc == 0: os.replace(out, f"{D}/out/s{i}.mp4")
    print("scene", i, "rc", rc, flush=True)


if __name__ == "__main__":
    os.makedirs(f"{D}/out", exist_ok=True)
    if sys.argv[1] == "--still":
        for spec in sys.argv[2:]:
            i, t = spec.split(":"); i = int(i); t = float(t)
            frame(i, t).write_to_png(f"{D}/out/still_{i}_{t:.1f}.png")
    else:
        for i in map(int, sys.argv[1:]): render_scene(i)

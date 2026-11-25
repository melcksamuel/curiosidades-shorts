# Estilo whiteboard/doodle — "O médico que bebeu bactérias" (Barry Marshall, H. pylori)
import cairo, math, json, sys, random, subprocess, os
import numpy as np

W, H, FPS = 1080, 1920, 30
D = os.path.dirname(os.path.abspath(__file__))
DURS = json.load(open(f"{D}/aud/durs.json"))
WORDS = [json.load(open(f"{D}/aud/n{i}.json")) for i in range(len(DURS))]
MK = "Permanent Marker"   # fonte manuscrita (convertida de @fontsource/permanent-marker, OFL)
ANTON = "Anton"

INK = (0.10, 0.10, 0.13)
RED = (0.88, 0.16, 0.16)
BLUE = (0.13, 0.36, 0.82)
GREEN = (0.16, 0.62, 0.30)
ORANGE = (0.98, 0.55, 0.10)
PURP = (0.50, 0.28, 0.72)
SKIN = (0.98, 0.84, 0.70)
YEL = (1.0, 0.88, 0.20)
BOARD = (0.985, 0.985, 0.975)
SICK = (0.70, 0.88, 0.55)

def clamp(x, a=0, b=1): return max(a, min(b, x))
def ease_out_back(x):
    x = clamp(x); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2
def ease_out(x): x = clamp(x); return 1 - (1 - x) ** 3
def ease_io(x): x = clamp(x); return x * x * (3 - 2 * x)
def pop(t, t0, d=0.28): return ease_out_back((t - t0) / d) if t >= t0 else 0.0
def prog(t, t0, d): return ease_io((t - t0) / d) if t > t0 else 0.0

def wt(sc, word, nth=0):
    k = 0; w0 = word.lower()
    for a, b, w in WORDS[sc]:
        if w.lower().strip(".,!?…:") == w0:
            if k == nth: return a
            k += 1
    print("MISSING", sc, word, file=sys.stderr); return 0.0

# ---------------- desenho a mão ----------------
TIP = None  # posição da ponta da caneta (desenho em andamento)

def jit(pts, seed, amp=2.2, sub=3):
    rnd = random.Random(seed); out = []
    for k in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[k], pts[k + 1]
        for j in range(sub):
            u = j / sub
            out.append((x0 + (x1 - x0) * u + rnd.uniform(-amp, amp), y0 + (y1 - y0) * u + rnd.uniform(-amp, amp)))
    out.append(pts[-1]); return out

def circ_pts(cx, cy, rx, ry=None, seed=0, a0=-2.0, sweep=2 * math.pi + 0.35, n=40, amp=0.03):
    ry = rx if ry is None else ry; rnd = random.Random(seed); pts = []
    for k in range(n + 1):
        a = a0 + sweep * k / n; f = 1 + rnd.uniform(-amp, amp)
        pts.append((cx + math.cos(a) * rx * f, cy + math.sin(a) * ry * f))
    return pts

def flat_info(ctx):
    segs = []; cur = None; start = None
    for typ, pts in ctx.copy_path_flat():
        if typ == cairo.PATH_MOVE_TO: cur = pts; start = pts
        elif typ == cairo.PATH_LINE_TO:
            segs.append((cur, pts)); cur = pts
        elif typ == cairo.PATH_CLOSE_PATH and cur and start:
            segs.append((cur, start)); cur = start
    L = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in segs)
    return segs, L

def ink(ctx, build, p, col=INK, lw=8, fill=None, fa=0.85):
    """Desenha um path com efeito 'sendo desenhado' (p 0..1)."""
    global TIP
    if p <= 0.001: return
    ctx.new_path(); build(ctx)
    if fill is not None and p > 0.6:
        ctx.set_source_rgba(*fill, fa * clamp((p - 0.6) / 0.4)); ctx.fill_preserve()
    ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_line_width(lw); ctx.set_source_rgb(*col)
    if p < 0.999:
        segs, L = flat_info(ctx)
        if L > 0:
            ctx.set_dash([max(0.01, p * L), L + 50], 0)
            # ponta
            target = p * L; acc = 0
            for a, b in segs:
                sl = math.hypot(b[0] - a[0], b[1] - a[1])
                if acc + sl >= target:
                    u = (target - acc) / max(sl, 1e-6)
                    TIP = ctx.user_to_device(a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u); break
                acc += sl
    ctx.stroke(); ctx.set_dash([]); ctx.new_path()

def lines_build(pts, seed, amp=2.2, close=False):
    P = jit(pts + ([pts[0]] if close else []), seed, amp)
    def b(ctx):
        ctx.move_to(*P[0])
        for q in P[1:]: ctx.line_to(*q)
    return b

def poly_build(P):
    def b(ctx):
        ctx.move_to(*P[0])
        for q in P[1:]: ctx.line_to(*q)
    return b

def hand_text(ctx, txt, x, y, size, t, t0, dur=0.6, col=INK, rot=0.0, face=MK, hl=None, maxw=980):
    """Texto escrito da esquerda p/ direita (revelação por recorte)."""
    global TIP
    if t <= t0: return
    p = clamp((t - t0) / dur)
    ctx.save(); ctx.translate(x, y); ctx.rotate(rot)
    ctx.select_font_face(face); ctx.set_font_size(size)
    e = ctx.text_extents(txt)
    if e.width > maxw:
        size *= maxw / e.width; ctx.set_font_size(size); e = ctx.text_extents(txt)
    tx = -e.width / 2 - e.x_bearing; ty = -e.height / 2 - e.y_bearing
    if hl is not None:
        hp = clamp((t - t0 - dur) / 0.3)
        if hp > 0:
            ctx.rectangle(-e.width / 2 - 14, -e.height * 0.15, (e.width + 28) * hp, e.height * 0.75)
            ctx.set_source_rgba(*hl, 0.55); ctx.fill()
    ctx.rectangle(-e.width / 2 - 20, -e.height - 40, (e.width + 40) * p, e.height * 2 + 80); ctx.clip()
    ctx.move_to(tx, ty); ctx.set_source_rgb(*col); ctx.show_text(txt); ctx.new_path()
    if p < 1: TIP = ctx.user_to_device(-e.width / 2 + e.width * p, 0)
    ctx.restore()

def stamp(ctx, txt, x, y, size, t, t0, col=RED, rot=-0.12):
    s = pop(t, t0, 0.22)
    if s <= 0.01: return
    ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(s, s)
    ctx.select_font_face(ANTON); ctx.set_font_size(size)
    e = ctx.text_extents(txt)
    w, h = e.width + 50, size * 1.15 + 20
    rnd = random.Random(len(txt))
    pts = [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
    P = jit(pts + [pts[0]], len(txt), 3)
    ctx.move_to(*P[0]); [ctx.line_to(*q) for q in P[1:]]
    ctx.set_source_rgba(1, 1, 1, 0.9); ctx.fill_preserve()
    ctx.set_line_width(9); ctx.set_source_rgb(*col); ctx.stroke()
    ctx.move_to(-e.width / 2 - e.x_bearing, -e.height / 2 - e.y_bearing); ctx.set_source_rgb(*col); ctx.show_text(txt); ctx.new_path()
    ctx.restore()

# ---------------- objetos doodle ----------------
def doctor(ctx, x, y, s, t, t0, pose="down", tp=None, mouth="smile", face=SKIN, glass_p=0, sick=False, seed=1, d=1.1):
    """Boneco palito de jaleco. (x,y)=pés. tp = tempo para a pose (beber)."""
    P = lambda a: prog(t, t0 + a * d, 0.35 * d)
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    hy = -470; hr = 62
    # pernas
    ink(ctx, lines_build([(-50, 0), (-30, -170)], seed + 1), P(0.55), lw=9)
    ink(ctx, lines_build([(50, 0), (30, -170)], seed + 2), P(0.6), lw=9)
    # jaleco (trapézio aberto)
    coat = [(-40, hy + hr + 20), (-85, -150), (85, -150), (40, hy + hr + 20)]
    ink(ctx, lines_build(coat, seed + 3, close=True), P(0.25), lw=9, fill=(1, 1, 1), fa=1)
    ink(ctx, lines_build([(0, hy + hr + 25), (0, -150)], seed + 4), P(0.35), lw=6)
    ink(ctx, lines_build([(-40, hy + hr + 20), (0, hy + hr + 75), (40, hy + hr + 20)], seed + 5), P(0.4), lw=6)
    # braços
    sh = (0, hy + hr + 40)
    a = prog(t, tp, 0.4) if tp is not None else 0
    if pose == "drink":
        # braço direito leva copo à boca
        hx = 130 - 80 * a; hyy = -250 - 230 * a
        ink(ctx, lines_build([(-35, hy + hr + 40), (-110, -210), (-130, -250)], seed + 6), P(0.7), lw=9)
        ink(ctx, lines_build([(35, hy + hr + 40), (95 - 10 * a, -290 - 120 * a), (hx, hyy)], seed + 7), P(0.75), lw=9)
        if glass_p > 0: glass(ctx, hx + 20, hyy - 10, 0.55, glass_p, t, tilt=-0.9 * a, level=1 - 0.8 * prog(t, (tp or 0) + 0.3, 1.2))
    elif pose == "up":
        ink(ctx, lines_build([(-35, hy + hr + 40), (-120, -420), (-150, -520)], seed + 6), P(0.7), lw=9)
        ink(ctx, lines_build([(35, hy + hr + 40), (120, -420), (150, -520)], seed + 7), P(0.75), lw=9)
    elif pose == "belly":
        ink(ctx, lines_build([(-35, hy + hr + 40), (-90, -260), (-10, -230)], seed + 6), P(0.7), lw=9)
        ink(ctx, lines_build([(35, hy + hr + 40), (90, -260), (15, -250)], seed + 7), P(0.75), lw=9)
    else:
        ink(ctx, lines_build([(-35, hy + hr + 40), (-110, -230), (-125, -170)], seed + 6), P(0.7), lw=9)
        ink(ctx, lines_build([(35, hy + hr + 40), (110, -230), (125, -170)], seed + 7), P(0.75), lw=9)
    # cabeça
    ink(ctx, poly_build(circ_pts(0, hy, hr, seed=seed)), P(0.0), lw=9, fill=face, fa=1)
    # cabelo
    ink(ctx, lines_build([(-58, hy - 20), (-40, hy - 62), (-10, hy - 70), (20, hy - 66), (50, hy - 45), (60, hy - 18)], seed + 8), P(0.1), lw=10)
    # óculos
    gp = P(0.15)
    ink(ctx, poly_build(circ_pts(-24, hy - 2, 18, seed=seed + 9)), gp, lw=5)
    ink(ctx, poly_build(circ_pts(24, hy - 2, 18, seed=seed + 10)), gp, lw=5)
    ink(ctx, lines_build([(-6, hy - 4), (6, hy - 4)], seed + 11, 0.5), gp, lw=5)
    # olhos e boca
    if gp > 0.9:
        ctx.set_source_rgb(*INK)
        for ex in (-24, 24):
            ctx.arc(ex, hy - 2, 5, 0, 2 * math.pi); ctx.fill()
    mp = P(0.2)
    if mouth == "smile":
        ink(ctx, poly_build(circ_pts(0, hy + 18, 22, 14, seed=seed + 12, a0=0.3, sweep=2.5, n=12, amp=0)), mp, lw=5)
    elif mouth == "o":
        ink(ctx, poly_build(circ_pts(0, hy + 30, 10, 12, seed=seed + 12)), mp, lw=5)
    else:  # enjoado
        ink(ctx, lines_build([(-22, hy + 32), (-11, hy + 24), (0, hy + 32), (11, hy + 24), (22, hy + 32)], seed + 12, 0.5), mp, lw=5)
    ctx.restore()

def glass(ctx, x, y, s, p, t, tilt=0.0, level=0.85, bugs=True):
    ctx.save(); ctx.translate(x, y); ctx.rotate(tilt); ctx.scale(s, s)
    w0, w1, h = 70, 55, 170
    if p > 0.6 and level > 0.02:
        ly = h / 2 - h * level
        ctx.move_to(-w1 + (w0 - w1) * 0, h / 2); ctx.line_to(w1, h / 2)
        f = (ly + h / 2) / h
        ctx.line_to(w1 + (w0 - w1) * (1 - f), ly); ctx.line_to(-w1 - (w0 - w1) * (1 - f), ly); ctx.close_path()
        ctx.set_source_rgba(*SICK, 0.9 * clamp((p - 0.6) / 0.4)); ctx.fill()
        if bugs:
            rnd = random.Random(3)
            for k in range(5):
                bx = rnd.uniform(-40, 40); by = rnd.uniform(ly + 15, h / 2 - 15)
                bacterium(ctx, bx, by, 0.22, rnd.uniform(0, 3), 1, t, col=GREEN, lw=14)
    ink(ctx, lines_build([(-w0, -h / 2), (-w1, h / 2), (w1, h / 2), (w0, -h / 2)], 41, 1.5), p, lw=9)
    ctx.restore()

def bacterium(ctx, x, y, s, rot, p, t, col=GREEN, lw=10, flag=True, seed=5):
    ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(s, s)
    ph = t * 6
    pts = [(-120 + 240 * k / 60, 26 * math.sin(k / 60 * 3 * 2 * math.pi + ph)) for k in range(61)]
    ink(ctx, poly_build(pts), p, col=col, lw=lw * 2.4)
    ink(ctx, poly_build(pts), p, col=(0.75, 0.95, 0.70) if col == GREEN else (1, 1, 1), lw=lw * 1.1)
    if flag and p > 0.7:
        for k in range(4):
            fp = [(120 + 70 * j / 20, (k - 1.5) * 14 + 10 * math.sin(j / 20 * 2 * math.pi * 1.5 + ph * 1.5 + k)) for j in range(21)]
            ink(ctx, poly_build(fp), clamp((p - 0.7) / 0.3), col=col, lw=lw * 0.45)
    ctx.restore()

def stomach_pts(x, y, s):
    # forma de "J" (estômago) em torno de (x,y)
    raw = [(-60, -300), (-55, -200), (-90, -130), (-130, -20), (-120, 100), (-60, 180), (40, 200), (150, 170), (230, 110),
           (280, 40), (300, -10), (270, -40), (210, 10), (140, 60), (60, 70), (10, 30), (5, -60), (40, -150), (40, -200), (10, -300)]
    return [(x + a * s, y + b * s) for a, b in raw]

def smooth(pts, iters=2):
    for _ in range(iters):
        out = [pts[0]]
        for a, b in zip(pts[:-1], pts[1:]):
            out += [(0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]), (0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1])]
        out.append(pts[-1]); pts = out
    return pts

def stomach(ctx, x, y, s, p, fill=(1.0, 0.80, 0.80), fa=0.8, col=INK):
    P = smooth(stomach_pts(x, y, s), 3)
    ink(ctx, poly_build(P), p, col=col, lw=10, fill=fill, fa=fa)

def arrow(ctx, x0, y0, x1, y1, p, col=INK, lw=8, seed=7):
    ink(ctx, lines_build([(x0, y0), (x1, y1)], seed), clamp(p / 0.7), col=col, lw=lw)
    a = math.atan2(y1 - y0, x1 - x0); L = 34
    hp = clamp((p - 0.7) / 0.3)
    ink(ctx, poly_build([(x1 + L * math.cos(a + 2.6), y1 + L * math.sin(a + 2.6)), (x1, y1), (x1 + L * math.cos(a - 2.6), y1 + L * math.sin(a - 2.6))]), hp, col=col, lw=lw)

def xmark(ctx, x, y, r, p, col=RED):
    ink(ctx, lines_build([(x - r, y - r), (x + r, y + r)], 91, 3), clamp(p * 2), col=col, lw=18)
    ink(ctx, lines_build([(x + r, y - r), (x - r, y + r)], 92, 3), clamp(p * 2 - 1), col=col, lw=18)

def check(ctx, x, y, r, p, col=GREEN):
    ink(ctx, lines_build([(x - r, y), (x - r * 0.3, y + r * 0.7), (x + r, y - r * 0.8)], 93, 2), p, col=col, lw=18)

def australia(ctx, x, y, s, p):
    raw = [(-200, -20), (-150, -90), (-80, -100), (-40, -150), (10, -110), (50, -140), (80, -200), (120, -110), (190, -40), (210, 40),
           (170, 120), (90, 150), (40, 110), (-30, 90), (-120, 110), (-190, 70)]
    P = smooth([(x + a * s, y + b * s) for a, b in raw] + [(x + raw[0][0] * s, y + raw[0][1] * s)], 2)
    ink(ctx, poly_build(P), p, col=INK, lw=8, fill=(1.0, 0.85, 0.55), fa=0.9)

def beaker(ctx, x, y, s, p, t, level=0.6):
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    if p > 0.6:
        ctx.rectangle(-150, 200 - 380 * level, 300, 380 * level)
        ctx.set_source_rgba(1.0, 0.75, 0.25, 0.75 * clamp((p - 0.6) / 0.4)); ctx.fill()
        rnd = random.Random(9)
        for k in range(10):
            bx = rnd.uniform(-120, 120); ph = (t * 0.8 + rnd.random()) % 1
            by = 190 - ph * 380 * level
            ctx.new_path(); ctx.arc(bx, by, 8 + 6 * rnd.random(), 0, 2 * math.pi)
            ctx.set_source_rgba(1, 1, 1, 0.8); ctx.set_line_width(4); ctx.stroke()
    ink(ctx, lines_build([(-170, -200), (-150, -180), (-150, 200), (150, 200), (150, -180), (170, -200)], 51, 2), p, lw=10)
    ctx.restore()

def microscope(ctx, x, y, s, p):
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    ink(ctx, lines_build([(-130, 0), (130, 0)], 61), clamp(p * 4), lw=11)
    ink(ctx, lines_build([(60, 0), (60, -60), (20, -200), (-10, -230)], 62), clamp(p * 4 - 1), lw=11)
    ink(ctx, lines_build([(-70, -330), (-20, -170), (20, -185), (-30, -345)], 63, close=True), clamp(p * 4 - 2), lw=9, fill=(0.85, 0.9, 1.0))
    ink(ctx, lines_build([(-70, -100), (40, -100)], 64), clamp(p * 4 - 3), lw=9)
    ctx.restore()

def pig(ctx, x, y, s, p):
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    q = lambda k: clamp(p * 6 - k)
    pink = (1.0, 0.78, 0.82)
    ink(ctx, poly_build(circ_pts(0, 0, 160, 110, seed=71)), q(0), lw=9, fill=pink, fa=1)
    for lx in (-90, -40, 50, 100):
        ink(ctx, lines_build([(lx, 95), (lx, 160)], 72 + lx), q(1), lw=12)
    ink(ctx, poly_build(circ_pts(-170, -40, 85, seed=73)), q(2), lw=9, fill=pink, fa=1)
    ink(ctx, poly_build(circ_pts(-235, -20, 30, 22, seed=74)), q(3), lw=7, fill=(1.0, 0.65, 0.72), fa=1)
    if q(3) > 0.9:
        ctx.set_source_rgb(*INK)
        for nx in (-245, -225): ctx.arc(nx, -20, 5, 0, 2 * math.pi); ctx.fill()
        ctx.arc(-180, -70, 7, 0, 2 * math.pi); ctx.fill()
    ink(ctx, lines_build([(-150, -115), (-130, -165), (-110, -110)], 75), q(4), lw=8)
    spiral = [(160 + 18 * math.cos(a) + a * 6, -20 + 18 * math.sin(a)) for a in np.linspace(0, 4 * math.pi, 30)]
    ink(ctx, poly_build(spiral), q(5), lw=7)
    ctx.restore()

def calendar(ctx, x, y, s, p, t, top="JULHO", big="1984"):
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    ink(ctx, lines_build([(-150, -150), (150, -150), (150, 170), (-150, 170)], 81, close=True), p, lw=9, fill=(1, 1, 1), fa=1)
    if p > 0.6:
        ctx.rectangle(-150, -150, 300, 80); ctx.set_source_rgba(*RED, clamp((p - 0.6) / 0.4)); ctx.fill()
    ctx.restore()
    hand_text(ctx, top, x, y - 110 * s, 52 * s, t, 0.4 + (0 if p < 1 else 0), 0.4, col=(1, 1, 1))
    hand_text(ctx, big, x, y + 50 * s, 110 * s, t, 0.7, 0.5, col=INK)

def medal(ctx, x, y, s, p, t, label="NOBEL", sub=None):
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    ink(ctx, lines_build([(-70, -260), (-20, -110), (20, -110), (70, -260)], 85), clamp(p * 3), lw=9, col=BLUE)
    ink(ctx, poly_build(circ_pts(0, 0, 130, seed=86)), clamp(p * 3 - 1), lw=10, fill=(1.0, 0.82, 0.25), fa=1)
    ink(ctx, poly_build(circ_pts(0, 0, 100, seed=87)), clamp(p * 3 - 2), lw=5, col=(0.75, 0.55, 0.1))
    ctx.restore()
    if p > 0.6:
        ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
        ctx.select_font_face(ANTON); ctx.set_font_size(62)
        e = ctx.text_extents(label); ctx.move_to(-e.width / 2 - e.x_bearing, -e.height / 2 - e.y_bearing - (18 if sub else 0))
        ctx.set_source_rgba(*INK, clamp((p - 0.6) / 0.4)); ctx.show_text(label); ctx.new_path()
        if sub:
            ctx.set_font_size(44); e = ctx.text_extents(sub); ctx.move_to(-e.width / 2 - e.x_bearing, 48 - e.height / 2 - e.y_bearing)
            ctx.show_text(sub); ctx.new_path()
        ctx.restore()

def capsule(ctx, x, y, s, p):
    ctx.save(); ctx.translate(x, y); ctx.rotate(-0.35); ctx.scale(s, s)
    left = smooth([(0, -60), (-120, -60), (-180, 0), (-120, 60), (0, 60)], 2)
    right = smooth([(0, -60), (120, -60), (180, 0), (120, 60), (0, 60)], 2)
    ink(ctx, poly_build(left + [left[0]]), clamp(p * 2), lw=9, fill=RED, fa=1)
    ink(ctx, poly_build(right + [right[0]]), clamp(p * 2 - 1), lw=9, fill=(1, 1, 1), fa=1)
    ctx.restore()

def stink(ctx, x, y, s, p, t):
    for k in range(3):
        pts = [(x + k * 45 * s + 14 * math.sin(j / 3 + t * 5 + k), y - j * 12 * s) for j in range(12)]
        ink(ctx, poly_build(pts), clamp(p * 3 - k), col=GREEN, lw=8)

def qmark(ctx, x, y, size, t, t0, col=PURP):
    hand_text(ctx, "?", x, y, size, t, t0, 0.25, col=col)

def head(ctx, x, y, s, p, seed, mouth="flat"):
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    ink(ctx, poly_build(circ_pts(0, 0, 60, seed=seed)), p, lw=8, fill=SKIN, fa=1)
    ink(ctx, lines_build([(-60, 120), (-40, 70), (40, 70), (60, 120)], seed + 1), clamp(p * 2 - 0.5), lw=8)
    if p > 0.8:
        ctx.set_source_rgb(*INK)
        for ex in (-20, 20): ctx.arc(ex, -8, 6, 0, 2 * math.pi); ctx.fill()
        ctx.set_line_width(6); ctx.move_to(-20, 28); ctx.line_to(20, 22); ctx.stroke()
        ctx.move_to(-32, -30); ctx.line_to(-10, -22); ctx.move_to(32, -30); ctx.line_to(10, -22); ctx.stroke()
    ctx.restore()

# ---------------- cenas ----------------
def scene(ctx, i, t, T):
    if i == 0:
        hand_text(ctx, "BEBEU BACTÉRIAS?!", 540, 330, 112, t, 0.0, 0.55, col=RED, rot=-0.03)
        tb = wt(0, "bebeu")
        doctor(ctx, 360, 1340, 1.25, t, 0.0, d=0.55, pose="drink", tp=tb + 0.2, glass_p=prog(t, 0.3, 0.4), mouth="o" if t > tb + 0.5 else "smile")
        hand_text(ctx, "de propósito!", 560, 470, 70, t, wt(0, "propósito"), 0.5, col=BLUE, rot=0.04)
        tn = wt(0, "ganhou")
        s = pop(t, tn, 0.35)
        if s > 0.01: medal(ctx, 790, 880, 0.95 * s, prog(t, tn, 0.6), t, "NOBEL")
    elif i == 1:
        hand_text(ctx, "AUSTRÁLIA, 1984", 540, 300, 100, t, 0.0, 0.7, col=INK, hl=YEL)
        australia(ctx, 790, 560, 0.75, prog(t, 0.2, 0.8))
        tj = wt(1, "juravam")
        stomach(ctx, 430, 980, 1.15, prog(t, tj - 0.4, 1.1))
        tu = wt(1, "úlcera")
        if t > tu:
            ctx.new_path(); ctx.arc(430 + 120 * 1.15, 980 + 150 * 1.15, 32 * pop(t, tu, 0.3) + 0.01, 0, 2 * math.pi)
            ctx.set_source_rgba(*RED, 0.85); ctx.fill()
            hand_text(ctx, "ÚLCERA", 760, 1270, 64, t, tu, 0.4, col=RED)
            arrow(ctx, 680, 1250, 600, 1170, prog(t, tu + 0.2, 0.3), col=RED)
        te = wt(1, "estresse")
        hand_text(ctx, "ESTRESSE?", 230, 545, 70, t, te - 0.1, 0.45, col=PURP, rot=-0.05)
        ta = wt(1, "ácido")
        hand_text(ctx, "+ ÁCIDO?", 840, 820, 70, t, ta - 0.1, 0.4, col=ORANGE, rot=0.05)
    elif i == 2:
        hand_text(ctx, "NENHUMA BACTÉRIA", 540, 290, 96, t, 0.0, 0.5, col=INK)
        hand_text(ctx, "SOBREVIVE?", 540, 420, 96, t, wt(2, "sobreviveria") - 0.1, 0.4, col=RED, hl=YEL)
        beaker(ctx, 540, 1050, 1.0, prog(t, 0.1, 0.8), t)
        hand_text(ctx, "ÁCIDO", 540, 1110, 80, t, wt(2, "ácido"), 0.35, col=(0.6, 0.3, 0.0))
        tb = wt(2, "bactéria")
        bx = 540 + 360 * (1 - ease_out(clamp((t - tb) / 0.8)))
        bacterium(ctx, bx, 740, 0.7, 0.3, prog(t, tb - 0.1, 0.4), t)
        xmark(ctx, 540, 740, 90, prog(t, wt(2, "sobreviveria") + 0.3, 0.5))
    elif i == 3:
        hand_text(ctx, "MARSHALL", 300, 300, 92, t, wt(3, "barry"), 0.45, col=BLUE, rot=-0.04)
        hand_text(ctx, "& WARREN", 760, 380, 92, t, wt(3, "robin"), 0.45, col=GREEN, rot=0.03)
        microscope(ctx, 300, 1340, 1.0, prog(t, 0.2, 1.4))
        tz = wt(3, "achando")
        zp = prog(t, tz - 0.4, 0.8)
        ink(ctx, poly_build(circ_pts(640, 880, 280, seed=31)), zp, lw=10, fill=(0.95, 0.98, 1.0), fa=1)
        if zp > 0.5:
            ink(ctx, lines_build([(310, 1000), (380, 1060)], 32), zp, lw=5, col=(0.5, 0.5, 0.55))
        ts = wt(3, "mesma")
        rnd = random.Random(4)
        for k in range(6):
            bx = 640 + rnd.uniform(-170, 170); by = 880 + rnd.uniform(-170, 170)
            bacterium(ctx, bx, by, 0.55, rnd.uniform(0, 3), prog(t, ts + k * 0.15, 0.35), t + k)
        hand_text(ctx, "ESPIRAL!", 640, 1240, 80, t, wt(3, "espiral"), 0.4, col=GREEN, hl=YEL)
    elif i == 4:
        hand_text(ctx, "NINGUÉM ACREDITOU", 540, 300, 100, t, 0.0, 0.6, col=RED)
        for k, hx in enumerate((260, 540, 820)):
            head(ctx, hx, 560, 0.9, prog(t, 0.15 + k * 0.15, 0.4), 40 + k)
        tp = wt(4, "porquinhos")
        pig(ctx, 580, 1110, 1.05, prog(t, wt(4, "tentou"), 1.0))
        hand_text(ctx, "porquinhos", 540, 1340, 72, t, tp, 0.4, col=PURP)
        tf = wt(4, "falhou")
        stamp(ctx, "FALHOU", 560, 1050, 130, t, tf, col=RED, rot=-0.15)
    elif i == 5:
        calendar(ctx, 270, 560, 0.95, prog(t, 0.05, 0.5), t)
        tb = wt(5, "bebeu")
        doctor(ctx, 640, 1380, 1.2, t, 0.3, pose="drink", tp=tb, glass_p=prog(t, 0.8, 0.4), mouth="o" if t > tb + 0.4 else "smile")
        hand_text(ctx, "TUDO!", 860, 660, 100, t, wt(5, "inteira"), 0.35, col=GREEN, rot=0.08)
        ts = wt(5, "sem")
        hand_text(ctx, "sem avisar", 760, 330, 74, t, ts, 0.4, col=RED, rot=-0.03)
        hand_text(ctx, "nem a esposa!", 760, 440, 74, t, wt(5, "esposa") - 0.25, 0.45, col=RED, rot=-0.03)
    elif i == 6:
        t3 = wt(6, "dias"); t5 = wt(6, "vômito")
        hand_text(ctx, "DIA 3", 540, 330, 140, t, t3 - 0.1, 0.35, col=INK, hl=YEL)
        doctor(ctx, 560, 1380, 1.2, t, -2, pose="belly", mouth="sick", face=SICK)
        stink(ctx, 640, 780, 1.2, prog(t, wt(6, "hálito"), 0.6), t)
        hand_text(ctx, "MAU HÁLITO", 880, 720, 56, t, wt(6, "hálito"), 0.4, col=GREEN, rot=0.06)
        if t > t5:
            hand_text(ctx, "DIA 5-8", 540, 470, 90, t, t5, 0.35, col=RED)
            hand_text(ctx, "BLEH!", 250, 720, 110, t, t5 + 0.1, 0.3, col=GREEN, rot=-0.15)
    elif i == 7:
        hand_text(ctx, "DIA 8: EXAME", 540, 310, 110, t, 0.0, 0.55, col=INK, hl=YEL)
        ti = wt(7, "inflamado")
        red = clamp((t - ti) / 0.5)
        fill = (1.0, 0.80 - 0.35 * red, 0.80 - 0.4 * red)
        stomach(ctx, 400, 930, 1.35, prog(t, 0.2, 1.0), fill=fill, fa=0.9)
        tc = wt(7, "cheio")
        rnd = random.Random(11)
        spots = [(-90, -60), (-100, 40), (-60, 120), (10, 150), (80, 140), (160, 110), (230, 50), (-40, 60), (40, 110), (-80, -120), (120, 140), (-20, 140)]
        for k, (ox, oy) in enumerate(spots):
            bx = 400 + ox * 1.35; by = 930 + oy * 1.35
            bacterium(ctx, bx, by, 0.32, rnd.uniform(0, 3), prog(t, tc + k * 0.06, 0.25), t + k, lw=12)
        stamp(ctx, "INFLAMADO!", 700, 560, 96, t, ti, col=RED, rot=0.08)
    elif i == 8:
        th = wt(8, "helicobacter")
        bacterium(ctx, 540, 720, 1.25, -0.15, prog(t, 0.0, 0.9), t, lw=11)
        hand_text(ctx, "Helicobacter pylori", 540, 330, 92, t, th - 0.1, 0.8, col=GREEN, hl=YEL)
        ta = wt(8, "antibiótico")
        tcur = wt(8, "curar")
        capsule(ctx, 360, 1180, 0.95, prog(t, tcur - 0.3, 0.6))
        hand_text(ctx, "ANTIBIÓTICO", 720, 1080, 70, t, ta - 0.1, 0.45, col=RED, rot=0.04)
        check(ctx, 760, 1230, 70, prog(t, ta + 0.3, 0.4))
        xmark(ctx, 540, 720, 150, prog(t, ta + 0.2, 0.5))
        hand_text(ctx, "causa da maioria das úlceras", 540, 470, 62, t, wt(8, "maioria"), 0.6, col=INK)
    elif i == 9:
        tn = wt(9, "nobel")
        hand_text(ctx, "2005", 540, 290, 130, t, wt(9, "2005") - 0.1, 0.35, col=INK, hl=YEL)
        s = pop(t, tn - 0.1, 0.35)
        if s > 0.01: medal(ctx, 540, 640, 1.05 * s, prog(t, tn - 0.1, 0.6), t, "NOBEL", "2005")
        tc = wt(9, "copo")
        glass(ctx, 270, 1130, 1.0, prog(t, tc - 0.4, 0.5), t, level=0.8)
        tv = wt(9, "você")
        hand_text(ctx, "VOCÊ", 720, 1020, 110, t, tv, 0.3, col=BLUE, rot=-0.04)
        hand_text(ctx, "BEBERIA?", 720, 1150, 110, t, tv + 0.25, 0.4, col=BLUE, rot=-0.04, hl=YEL)
        ts = wt(9, "siga")
        hand_text(ctx, "SIGA PRA MAIS CURIOSIDADES!", 540, 1370, 64, t, ts, 0.9, col=RED)

# ---------------- legendas ----------------
def draw_subs(ctx, i, t):
    words = [[a, b, w.strip(".,!?…:")] for a, b, w in WORDS[i]]
    groups = []; cur = []
    for w in words:
        if cur and (len(cur) >= 3 or w[0] - cur[-1][1] > 0.22):
            groups.append(cur); cur = []
        cur.append(w)
    if cur: groups.append(cur)
    g = None
    for gg in groups:
        if t >= gg[0][0] - 0.05: g = gg
    if g is None: return
    if t > g[-1][1] + 0.6 and g is groups[-1]: return
    size = 74
    ctx.select_font_face(ANTON); ctx.set_font_size(size)
    widths = [ctx.text_extents(w[2].upper()).x_advance + 40 for w in g]
    total = sum(widths) + 16 * (len(g) - 1)
    if total > 1000:
        size *= 1000 / total; ctx.set_font_size(size)
        widths = [ctx.text_extents(w[2].upper()).x_advance + 40 * size / 74 for w in g]; total = sum(widths) + 16 * (len(g) - 1)
    x = 540 - total / 2
    for k, (w, wd) in enumerate(zip(g, widths)):
        if t >= w[0] - 0.03:
            s = ease_out_back((t - w[0] + 0.03) / 0.16)
            active = w[0] <= t < w[1] + 0.05
            ctx.save(); ctx.translate(x + wd / 2, 1530); ctx.rotate(-0.015 + 0.02 * (k % 2)); ctx.scale(max(s, 1e-3), max(s, 1e-3))
            h = size * 1.3
            pts = jit([(-wd / 2, -h / 2), (wd / 2, -h / 2), (wd / 2, h / 2), (-wd / 2, h / 2), (-wd / 2, -h / 2)], k + 7, 1.5)
            ctx.move_to(*pts[0]); [ctx.line_to(*q) for q in pts[1:]]
            ctx.set_source_rgb(*(YEL if active else (1, 1, 1))); ctx.fill_preserve()
            ctx.set_line_width(5); ctx.set_source_rgb(*INK); ctx.stroke()
            e = ctx.text_extents(w[2].upper())
            ctx.move_to(-e.width / 2 - e.x_bearing, -e.height / 2 - e.y_bearing); ctx.set_source_rgb(*INK); ctx.show_text(w[2].upper()); ctx.new_path()
            ctx.restore()
        x += wd + 16

def shake_amount(i, t):
    hits = {0: [0.15, wt(0, "ganhou")], 4: [wt(4, "falhou")], 7: [wt(7, "inflamado")], 9: [wt(9, "nobel")]}
    a = 0
    for h in hits.get(i, []):
        if 0 <= t - h < 0.3: a = max(a, 14 * (1 - (t - h) / 0.3))
    return a

_bg = None
def board_bg():
    global _bg
    if _bg is not None: return _bg
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c = cairo.Context(surf)
    c.set_source_rgb(*BOARD); c.paint()
    rnd = random.Random(2)
    for k in range(9):  # manchas fantasmas de apagador
        x, y = rnd.uniform(0, W), rnd.uniform(0, H)
        g = cairo.RadialGradient(x, y, 0, x, y, rnd.uniform(120, 300))
        g.add_color_stop_rgba(0, 0.55, 0.58, 0.65, 0.05); g.add_color_stop_rgba(1, 0.55, 0.58, 0.65, 0)
        c.set_source(g); c.paint()
    g = cairo.RadialGradient(540, 900, 500, 540, 900, 1300)
    g.add_color_stop_rgba(0, 0, 0, 0, 0); g.add_color_stop_rgba(1, 0.2, 0.2, 0.3, 0.12)
    c.set_source(g); c.paint()
    _bg = surf; return surf

def draw_marker(ctx, x, y):
    ctx.save(); ctx.translate(x, y); ctx.rotate(-0.6)
    ctx.move_to(0, 0); ctx.line_to(14, 28); ctx.line_to(-14, 28); ctx.close_path(); ctx.set_source_rgb(*INK); ctx.fill()
    ctx.rectangle(-22, 28, 44, 50); ctx.set_source_rgb(0.25, 0.25, 0.3); ctx.fill()
    ctx.rectangle(-22, 78, 44, 170); ctx.set_source_rgb(0.95, 0.95, 0.95); ctx.fill_preserve()
    ctx.set_source_rgb(*INK); ctx.set_line_width(4); ctx.stroke()
    ctx.rectangle(-22, 140, 44, 40); ctx.set_source_rgb(*BLUE); ctx.fill()
    ctx.restore()

def frame(i, t):
    global TIP
    T = DURS[i]
    tq = math.floor(t * 15) / 15
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); ctx = cairo.Context(surf)
    ctx.set_source_surface(board_bg()); ctx.paint()
    sh = shake_amount(i, tq)
    ctx.save(); ctx.translate(sh * math.sin(tq * 90), sh * math.cos(tq * 77))
    z = 1 + 0.03 * (tq / T)
    ctx.translate(540, 860); ctx.scale(z, z); ctx.translate(-540, -860)
    TIP = None
    scene(ctx, i, tq, T)
    ctx.restore()
    tip = TIP
    # apagador no fim da cena
    if i < len(DURS) - 1 and t > T - 0.35:
        p = ease_io((t - (T - 0.35)) / 0.35)
        ex = -300 + p * (W + 600)
        ctx.rectangle(-10, 0, ex + 10, H); ctx.set_source_rgb(*BOARD); ctx.fill()
        ctx.save(); ctx.translate(ex, 900); ctx.rotate(0.1)
        ctx.rectangle(-110, -260, 220, 520); ctx.set_source_rgb(0.20, 0.30, 0.55); ctx.fill()
        ctx.rectangle(-110, 180, 220, 80); ctx.set_source_rgb(0.85, 0.85, 0.85); ctx.fill()
        ctx.restore()
        tip = None
    if tip is not None: draw_marker(ctx, *tip)
    draw_subs(ctx, i, t)
    return surf

def render_scene(i):
    T = DURS[i]; n = int(round(T * FPS))
    out = f"{D}/out/s{i}.tmp.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-crf", "19", "-preset", "veryfast", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for f in range(n):
        p.stdin.write(bytes(frame(i, f / FPS).get_data()))
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

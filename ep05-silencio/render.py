"""Episódio 5 — O silêncio de Deus. Vetor 2D com brilho (estilo série Melbo & Pingo).
uso: python3 render.py --still T [--out f.png]   |   python3 render.py --chunk k N
"""
import math, random, sys, subprocess, os
import cairo
from timeline import SCENE_START, SCENE_DUR, LINES, WORDS, TOTAL, scene_at, wt, norm

W, H, FPS = 1080, 1920, 30
FONT = "Inter"
GOLD = (1.0, 0.902, 0.486)       # #FFE67C
LAV = (0.78, 0.74, 0.95)
NAVY = (0.051, 0.043, 0.141)     # #0D0B24
CARD = (0.06, 0.06, 0.14)
MINT = (0.50, 0.89, 0.77)


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease(x):
    x = clamp(x); return x * x * (3 - 2 * x)


def eob(x):  # easeOutBack
    x = clamp(x); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def lerp(a, b, t):
    return a + (b - a) * t


def lerpc(a, b, t):
    return tuple(lerp(x, y, t) for x, y in zip(a, b))


def hexc(h):
    h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def fin(T, t0, d=0.35):
    return ease((T - t0) / d)


def S(i):
    return SCENE_START[i]


def E(i):
    return SCENE_START[i] + SCENE_DUR[i]


def vis(T, i0, i1=None, fade=0.4):
    """alpha for an element visible from scene i0 to end of scene i1"""
    i1 = i0 if i1 is None else i1
    a = ease((T - S(i0)) / fade)
    b = 1 - ease((T - E(i1)) / fade)
    return clamp(min(a, b))


# ---------------- background moods ----------------
MOODS = {
    "night": (hexc("0D0B24"), hexc("1D1740"), hexc("3a2a55"), 0.25),
    "warm": (hexc("2b2119"), hexc("4a3a2a"), hexc("1a1530"), 0.0),
    "cold": (hexc("090a1c"), hexc("161a38"), hexc("23284a"), 0.12),
    "still": (hexc("06060f"), hexc("0f0e22"), hexc("15142c"), 0.0),
    "dawn": (hexc("14123a"), hexc("3b2b5e"), hexc("f2a37a"), 0.9),
}
SCENE_MOOD = ["night", "night", "night", "warm", "cold", "still", "night", "warm", "dawn", "dawn"]


def mood_at(T):
    i = scene_at(T)
    m = MOODS[SCENE_MOOD[i]]
    if i > 0:
        k = ease((T - S(i)) / 0.6)
        p = MOODS[SCENE_MOOD[i - 1]]
        m = tuple(lerpc(a, b, k) if isinstance(a, tuple) else lerp(a, b, k) for a, b in zip(p, m))
    return m


random.seed(7)
STARS = [(random.uniform(0, W), random.uniform(0, H * 0.78), random.uniform(0.8, 2.6), random.uniform(0, 6.28), random.uniform(0.5, 1.6)) for _ in range(230)]


def draw_bg(ctx, T):
    top, mid, low, horizon = mood_at(T)
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgb(0, *top); g.add_color_stop_rgb(0.55, *mid); g.add_color_stop_rgb(1, *low)
    ctx.set_source(g); ctx.paint()
    # warm center glow (like the cover)
    i = scene_at(T)
    warm = 0.0
    for k in (3, 7):
        warm = max(warm, vis(T, k, k, 0.5))
    if warm > 0:
        rg = cairo.RadialGradient(540, 700, 0, 540, 700, 900)
        rg.add_color_stop_rgba(0, 0.75, 0.55, 0.32, 0.55 * warm); rg.add_color_stop_rgba(1, 0.75, 0.55, 0.32, 0)
        ctx.set_source(rg); ctx.paint()
    # stars
    dim = 1.0 - 0.6 * mood_at(T)[3]
    for (x, y, r, ph, sp) in STARS:
        a = (0.35 + 0.65 * (0.5 + 0.5 * math.sin(T * sp * 2 + ph))) * dim * 0.75
        ctx.set_source_rgba(1, 0.97, 0.88, a)
        ctx.arc(x, y + T * 2.0 % 1, r, 0, 6.283); ctx.fill()
    # horizon glow
    if horizon > 0.01:
        rg = cairo.RadialGradient(540, 1250, 0, 540, 1250, 950)
        rg.add_color_stop_rgba(0, 1.0, 0.72, 0.5, 0.6 * horizon)
        rg.add_color_stop_rgba(0.5, 0.95, 0.55, 0.55, 0.22 * horizon)
        rg.add_color_stop_rgba(1, 0.6, 0.4, 0.6, 0)
        ctx.set_source(rg); ctx.paint()


def glow(ctx, x, y, r, col, a):
    if a <= 0.003 or r <= 1: return
    rg = cairo.RadialGradient(x, y, 0, x, y, r)
    rg.add_color_stop_rgba(0, *col, a); rg.add_color_stop_rgba(0.4, *col, a * 0.35); rg.add_color_stop_rgba(1, *col, 0)
    ctx.set_source(rg); ctx.arc(x, y, r, 0, 6.283); ctx.fill()


# ---------------- text ----------------
def font(ctx, size, bold=True, italic=False):
    ctx.select_font_face(FONT, cairo.FONT_SLANT_ITALIC if italic else cairo.FONT_SLANT_NORMAL,
                         cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size)


def text_c(ctx, s, x, y, size, col, a=1.0, bold=True, spacing=0.0, italic=False):
    if a <= 0.003: return
    font(ctx, size, bold, italic)
    if spacing:
        ws = [ctx.text_extents(c).x_advance for c in s]
        tw = sum(ws) + spacing * (len(s) - 1)
        cx = x - tw / 2
        ctx.set_source_rgba(*col, a)
        for c, w in zip(s, ws):
            ctx.move_to(cx, y); ctx.show_text(c); cx += w + spacing
    else:
        e = ctx.text_extents(s)
        ctx.set_source_rgba(*col, a)
        ctx.move_to(x - e.x_advance / 2, y); ctx.show_text(s)
    ctx.new_path()


def rrect(ctx, x, y, w, h, r):
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0); ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi); ctx.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    ctx.close_path()


def header(ctx, T, i0, i1, label, title, sub=None, y=330):
    a = vis(T, i0, i1)
    if a <= 0: return
    k = eob((T - S(i0) - 0.1) / 0.5)
    dy = (1 - k) * 30
    text_c(ctx, label, 540, y + dy, 34, GOLD, a, True, spacing=6)
    text_c(ctx, title, 540, y + 95 + dy, 76, (1, 1, 1), a * clamp(k), True)
    if sub:
        text_c(ctx, sub, 540, y + 160 + dy, 38, LAV, a * clamp(k), False)


# ---------------- props ----------------
def book(ctx, x, y, s, a, T, open_k=1.0):
    if a <= 0 or s <= 0.01: return
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    glow(ctx, 0, 0, 380, (1.0, 0.85, 0.55), 0.35 * a)
    ok = max(0.02, open_k)
    # cover
    ctx.set_source_rgba(*hexc("6b4436"), a)
    ctx.move_to(-245 * ok, -120); ctx.line_to(0, -105); ctx.line_to(245 * ok, -120)
    ctx.line_to(255 * ok, 110); ctx.line_to(0, 128); ctx.line_to(-255 * ok, 110); ctx.close_path(); ctx.fill()
    for side in (-1, 1):
        g = cairo.LinearGradient(0, 0, side * 230 * ok, 0)
        g.add_color_stop_rgba(0, *hexc("f1d9a8"), a); g.add_color_stop_rgba(0.25, *hexc("fff3d2"), a); g.add_color_stop_rgba(1, *hexc("fff6dc"), a)
        ctx.set_source(g)
        ctx.move_to(0, -95); ctx.line_to(side * 228 * ok, -108); ctx.line_to(side * 236 * ok, 96); ctx.line_to(0, 112); ctx.close_path(); ctx.fill()
        ctx.set_source_rgba(*hexc("d9b98a"), a * 0.9); ctx.set_line_width(7); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        for r in range(7):
            yy = -70 + r * 24
            L = [150, 120, 160, 100, 140, 120, 90][r]
            x0 = side * 30 * ok; x1 = side * (30 + L) * ok
            ctx.move_to(x0, yy + r * 0.5); ctx.line_to(x1, yy - side * 0 + 3); ctx.stroke()
    ctx.set_source_rgba(*hexc("e6c792"), a); ctx.rectangle(-12, -100, 24, 210); ctx.fill()
    ctx.restore()


def light_cone(ctx, a, x=540, y1=980):
    if a <= 0: return
    g = cairo.LinearGradient(0, 0, 0, y1)
    g.add_color_stop_rgba(0, 1, 0.9, 0.65, 0.30 * a); g.add_color_stop_rgba(1, 1, 0.9, 0.65, 0)
    ctx.set_source(g)
    ctx.move_to(x - 60, 0); ctx.line_to(x + 60, 0); ctx.line_to(x + 300, y1); ctx.line_to(x - 300, y1); ctx.close_path(); ctx.fill()


def card_quote(ctx, T, i, quote, ref, y=1130, karaoke_from=None):
    a = vis(T, i, i)
    if a <= 0: return
    k = eob((T - S(i) - 0.35) / 0.5)
    a *= clamp((T - S(i) - 0.3) / 0.3)
    toks = quote.split()
    font(ctx, 46, False)
    lines, cur = [], []
    for tk in toks:
        trial = " ".join(cur + [tk])
        if ctx.text_extents(trial).x_advance > 840 and cur:
            lines.append(cur); cur = [tk]
        else:
            cur.append(tk)
    lines.append(cur)
    lh = 62
    h = 70 + lh * len(lines) + 105
    yy = y + (1 - k) * 40
    ctx.set_source_rgba(*CARD, 0.88 * a); rrect(ctx, 54, yy, W - 108, h, 34); ctx.fill()
    ctx.set_source_rgba(1, 1, 1, 0.07 * a); rrect(ctx, 54, yy, W - 108, h, 34); ctx.set_line_width(2); ctx.stroke()
    # karaoke times: match tokens to spoken words of this scene
    sw = [w for w in WORDS if w["scene"] == i]
    times, p = [], 0
    for tk in toks:
        n = norm(tk); tt = None
        for q in range(p, len(sw)):
            if norm(sw[q]["txt"]) == n:
                tt = sw[q]["a"]; p = q + 1; break
        times.append(tt)
    idx = 0
    for li, ln in enumerate(lines):
        font(ctx, 46, False)
        s = " ".join(ln)
        tw = ctx.text_extents(s).x_advance
        cx = 540 - tw / 2
        by = yy + 70 + 44 + li * lh
        for tk in ln:
            tt = times[idx]; idx += 1
            spoken = tt is not None and T >= tt
            col = GOLD if spoken else (1, 1, 1)
            al = 1.0 if spoken else 0.62
            ctx.set_source_rgba(*col, a * al)
            ctx.move_to(cx, by); ctx.show_text(tk)
            cx += ctx.text_extents(tk + " ").x_advance
        ctx.new_path()
    text_c(ctx, ref, 540, yy + h - 38, 34, LAV, a, True)


# ---------------- characters ----------------
def talking(spk, T):
    for w in WORDS:
        if w["spk"] in spk and w["a"] <= T <= w["b"]:
            return 0.5 + 0.5 * abs(math.sin((T - w["a"]) * 13))
    return 0.0


def eyes(ctx, r, T, seed, look=0.0, sad=0.0, happy=0.0):
    blink = 1.0
    ph = (T + seed) % 3.3
    if ph < 0.13: blink = max(0.1, abs(ph - 0.065) / 0.065)
    for sx in (-1, 1):
        ex, ey = sx * 0.32 * r + look * 0.08 * r, -0.06 * r
        ctx.save(); ctx.translate(ex, ey); ctx.scale(0.105 * r, 0.15 * r * blink)
        ctx.set_source_rgb(*hexc("1D1740")); ctx.arc(0, 0, 1, 0, 6.283); ctx.fill(); ctx.restore()
        if blink > 0.6:
            ctx.set_source_rgba(1, 1, 1, 0.95); ctx.arc(ex + 0.03 * r, ey - 0.06 * r, 0.035 * r, 0, 6.283); ctx.fill()
        if sad > 0.01:  # brows
            ctx.set_source_rgba(*hexc("1D1740"), sad); ctx.set_line_width(0.045 * r); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            ctx.move_to(ex - sx * 0.12 * r, ey - 0.33 * r); ctx.line_to(ex + sx * 0.1 * r, ey - 0.25 * r); ctx.stroke()
        if happy > 0.01:  # cheeks
            ctx.set_source_rgba(1, 0.55, 0.55, 0.35 * happy); ctx.arc(ex + sx * 0.08 * r, ey + 0.22 * r, 0.09 * r, 0, 6.283); ctx.fill()


def mouth(ctx, r, sad, happy, talk, y=0.33):
    ctx.set_source_rgb(*hexc("1D1740")); ctx.set_line_width(0.05 * r); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    if talk > 0.05:
        ctx.save(); ctx.translate(0, y * r); ctx.scale(0.11 * r, (0.03 + 0.09 * talk) * r)
        ctx.arc(0, 0, 1, 0, 6.283); ctx.restore(); ctx.fill(); return
    curve = happy * 0.12 - sad * 0.10
    ctx.move_to(-0.13 * r, y * r); ctx.curve_to(-0.05 * r, (y + curve) * r, 0.05 * r, (y + curve) * r, 0.13 * r, y * r); ctx.stroke()


def melbo(ctx, x, y, r, T, a, sad=0.0, happy=0.0, look=0.0):
    if a <= 0.003: return
    y += math.sin(T * 1.7) * 9
    glow(ctx, x, y, r * 2.4, (1.0, 0.93, 0.7), 0.42 * a)
    ctx.push_group()
    ctx.translate(x, y)
    rg = cairo.RadialGradient(-0.35 * r, -0.4 * r, 0.05 * r, 0, 0, r)
    rg.add_color_stop_rgb(0, 1, 1, 0.98); rg.add_color_stop_rgb(0.6, *hexc("fbefd0")); rg.add_color_stop_rgb(1, *hexc("e9cf98"))
    ctx.set_source(rg); ctx.arc(0, 0, r, 0, 6.283); ctx.fill()
    ctx.set_source_rgba(1, 1, 1, 0.55); ctx.save(); ctx.translate(-0.42 * r, -0.5 * r); ctx.rotate(-0.6); ctx.scale(0.16 * r, 0.08 * r); ctx.arc(0, 0, 1, 0, 6.283); ctx.restore(); ctx.fill()
    eyes(ctx, r, T, 0.0, look, sad, happy)
    mouth(ctx, r, sad, happy, talking("M", T))
    ctx.pop_group_to_source(); ctx.paint_with_alpha(a)


def pingo(ctx, x, y, r, T, a, happy=1.0, look=0.0):
    if a <= 0.003: return
    sq = 1 + 0.035 * math.sin(T * 3.1)
    glow(ctx, x, y - 0.2 * r, r * 2.4, MINT, 0.33 * a)
    ctx.push_group()
    ctx.translate(x, y); ctx.scale(1 / sq ** 0.5, sq)
    tip = (0, -1.45 * r)
    c30, s30 = math.cos(math.radians(30)), math.sin(math.radians(30))
    ctx.move_to(*tip)
    ctx.curve_to(0.15 * r, -1.15 * r, c30 * r * 0.95, -0.85 * r, c30 * r, -s30 * r)
    ctx.arc(0, 0, r, math.radians(-30), math.radians(210))
    ctx.curve_to(-c30 * r * 0.95, -0.85 * r, -0.15 * r, -1.15 * r, *tip)
    ctx.close_path()
    rg = cairo.RadialGradient(-0.3 * r, -0.5 * r, 0.05 * r, 0, -0.2 * r, 1.3 * r)
    rg.add_color_stop_rgb(0, *hexc("c9fbe9")); rg.add_color_stop_rgb(0.5, *hexc("7fe3c4")); rg.add_color_stop_rgb(1, *hexc("2fae8a"))
    ctx.set_source(rg); ctx.fill()
    ctx.set_source_rgba(1, 1, 1, 0.6); ctx.save(); ctx.translate(-0.42 * r, -0.45 * r); ctx.rotate(-0.9); ctx.scale(0.2 * r, 0.07 * r); ctx.arc(0, 0, 1, 0, 6.283); ctx.restore(); ctx.fill()
    eyes(ctx, r, T, 1.3, look, 0, happy)
    mouth(ctx, r, 0, happy, talking("PR", T) if False else talking("P", T))
    ctx.pop_group_to_source(); ctx.paint_with_alpha(a)


def sparkle(ctx, x, y, s, a, col=(1, 0.95, 0.7)):
    if a <= 0 or s <= 0.01: return
    glow(ctx, x, y, 70 * s, col, 0.6 * a)
    ctx.set_source_rgba(1, 1, 0.95, a)
    ctx.move_to(x, y - 34 * s)
    for k in range(4):
        ang = k * math.pi / 2
        ctx.curve_to(x, y, x, y, x + 34 * s * math.sin(ang + math.pi / 2), y - 34 * s * math.cos(ang + math.pi / 2))
    ctx.close_path(); ctx.fill()


# ---------------- scenes ----------------
def sc0(ctx, T):
    a = vis(T, 0, 0)
    if a > 0:
        melbo(ctx, 540, 1330, 90, T, a, sad=0.6, happy=0, look=0)
    # ground silhouette
    ctx.set_source_rgba(*hexc("0a0920"), 1)
    ctx.move_to(0, 1380)
    for x in range(0, W + 40, 40):
        ctx.line_to(x, 1360 + 25 * math.sin(x / 170.0))
    ctx.line_to(W, H); ctx.line_to(0, H); ctx.close_path(); ctx.fill()
    if a <= 0: return
    # prayer lights rising
    launches = [S(0) + 0.15, wt(0, "ora"), wt(0, "ora", 2), wt(0, "novo"), wt(0, "outro")]
    for n, t0 in enumerate(launches):
        u = (T - t0) / 3.2
        if 0 <= u <= 1:
            x = 540 + (n - 2) * 70 + math.sin(u * 6 + n) * 30
            y = 1220 - u * 900
            al = a * (1 - u) * clamp(u * 6)
            glow(ctx, x, y, 60, (1, 0.9, 0.6), 0.7 * al)
            ctx.set_source_rgba(1, 0.98, 0.85, al); ctx.arc(x, y, 9, 0, 6.283); ctx.fill()
    # "..." bubble in sky that never answers
    t0 = wt(0, "outro")
    k = eob((T - t0) / 0.45)
    if T > t0:
        s = max(1e-3, k)
        ctx.save(); ctx.translate(540, 470); ctx.scale(s, s)
        ctx.set_source_rgba(1, 1, 1, 0.10 * a); rrect(ctx, -150, -70, 300, 140, 70); ctx.fill()
        ctx.set_source_rgba(1, 1, 1, 0.22 * a); rrect(ctx, -150, -70, 300, 140, 70); ctx.set_line_width(3); ctx.stroke()
        for d in range(3):
            pulse = 0.35 + 0.65 * (0.5 + 0.5 * math.sin(T * 5 - d * 0.9))
            fade = 1 - clamp((T - wt(0, "silêncio")) / 0.9) * 0.75
            ctx.set_source_rgba(1, 1, 1, a * pulse * fade); ctx.arc(-60 + d * 60, 0, 14, 0, 6.283); ctx.fill()
        ctx.restore()


def sc1_2_chars(ctx, T):
    # Melbo: scenes 1-2 ; then 8-9
    a12 = vis(T, 1, 2)
    if a12 > 0:
        k = ease((T - S(2)) / 0.8)
        x = lerp(540, 380, k)
        s = eob((T - S(1)) / 0.6)
        sad = 1 - ease((T - wt(2, "Davi")) / 0.6)
        happy = ease((T - wt(2, "sentiu")) / 0.6) * 0.5
        melbo(ctx, x, 1050, 125 * max(1e-3, s), T, a12, sad=sad, happy=happy, look=k * 1.0)
    a2 = vis(T, 2, 2)
    if a2 > 0:
        k = eob((T - S(2) - 0.15) / 0.7)
        x = lerp(1180, 720, k)
        pingo(ctx, x, 1070, 105, T, a2, happy=1.0, look=-1)
        bk = eob((T - wt(2, "Davi")) / 0.6)
        if T > wt(2, "Davi"):
            book(ctx, 540, 690, 0.55 * max(1e-3, bk), a2 * clamp(bk), T, bk)


def sc1(ctx, T):
    header(ctx, T, 1, 2, "EPISÓDIO 5", "O silêncio de Deus", "Melbo & Pingo", y=360)


def scripture_scene(ctx, T, i, label, title, sub, quote, ref):
    a = vis(T, i, i)
    if a <= 0: return
    light_cone(ctx, a)
    header(ctx, T, i, i, label, title, sub, y=300)
    k = eob((T - S(i) - 0.2) / 0.7)
    book(ctx, 540, 800, 0.9 * max(1e-3, k), a, T, k)
    card_quote(ctx, T, i, quote, ref)


def sc4(ctx, T):
    a = vis(T, 4, 5)
    if a <= 0: return
    header(ctx, T, 4, 4, "O PROFETA ELIAS", "Vento. Terremoto. Fogo.", "1 Reis 19", y=330)
    dimk = ease((T - wt(5, "não")) / 0.8) if T > S(5) else 0.0
    ycen = lerp(860, 640, ease((T - S(5)) / 0.8)) if T > S(5) else 860
    sc = lerp(1.0, 0.62, ease((T - S(5)) / 0.8)) if T > S(5) else 1.0
    for n, (word, col) in enumerate((("vento", hexc("9fd8ff")), ("terremoto", hexc("d9a46b")), ("fogo", hexc("ff8a4c")))):
        t0 = wt(4, word)
        k = eob((T - t0) / 0.45)
        if T < t0: continue
        x = 540 + (n - 1) * 300 * sc
        y = ycen
        al = a * clamp(k) * (1 - 0.72 * dimk)
        shake = 0
        if word == "terremoto" and T - t0 < 0.9:
            shake = math.sin((T - t0) * 60) * 10 * (1 - (T - t0) / 0.9)
        r = 120 * sc * max(1e-3, k)
        glow(ctx, x, y, r * 2.0, col, 0.35 * al)
        ctx.set_source_rgba(1, 1, 1, 0.08 * al); ctx.arc(x, y, r, 0, 6.283); ctx.fill()
        ctx.set_source_rgba(*col, 0.6 * al); ctx.set_line_width(4); ctx.arc(x, y, r, 0, 6.283); ctx.stroke()
        ctx.save(); ctx.translate(x + shake, y); ctx.scale(r / 120, r / 120)
        ctx.set_source_rgba(*col, al); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_width(10)
        if word == "vento":
            for q in range(3):
                yy = -40 + q * 40; ph = T * 3 + q
                ctx.move_to(-70, yy)
                ctx.curve_to(-20, yy - 25 * math.sin(ph), 20, yy + 25 * math.sin(ph), 55 - q * 15, yy)
                ctx.arc(55 - q * 15, yy - 14, 14, math.pi / 2, math.pi * 2.2)
                ctx.stroke()
        elif word == "terremoto":
            ctx.move_to(-75, 10); ctx.line_to(-35, -30); ctx.line_to(-5, 20); ctx.line_to(25, -40); ctx.line_to(45, 5); ctx.line_to(75, -20); ctx.stroke()
            ctx.move_to(-80, 55); ctx.line_to(80, 55); ctx.stroke()
        else:
            f = 1 + 0.08 * math.sin(T * 14)
            ctx.scale(1, f)
            ctx.move_to(0, -80); ctx.curve_to(50, -20, 60, 20, 45, 45); ctx.curve_to(30, 80, -30, 80, -45, 45)
            ctx.curve_to(-60, 15, -30, -10, -20, -40); ctx.curve_to(-5, -20, 0, -40, 0, -80); ctx.close_path(); ctx.fill()
            ctx.set_source_rgba(1, 0.9, 0.5, al); ctx.move_to(0, -10); ctx.curve_to(25, 20, 25, 50, 0, 60); ctx.curve_to(-25, 50, -25, 20, 0, -10); ctx.fill()
        ctx.restore()


def sc5(ctx, T):
    a = vis(T, 5, 5)
    if a <= 0: return
    header(ctx, T, 5, 5, "ESTÁ ESCRITO", "Uma voz mansa", "1 Reis 19:11-12", y=300)
    t0 = wt(5, "voz")
    if T > t0 - 0.3:
        for q in range(4):
            u = ((T - t0) * 0.45 + q / 4) % 1.0
            al = a * (1 - u) * 0.55 * clamp((T - t0 + 0.3) / 0.6)
            ctx.set_source_rgba(1, 0.92, 0.7, al); ctx.set_line_width(4)
            ctx.arc(540, 880, 40 + u * 330, 0, 6.283); ctx.stroke()
        glow(ctx, 540, 880, 140, (1, 0.93, 0.7), 0.7 * a * clamp((T - t0 + 0.3) / 0.6))
    card_quote(ctx, T, 5, "“...e, depois do fogo, uma voz mansa e delicada.”", "1 Reis 19:12 · ARC", y=1130)


def sc6(ctx, T):
    a = vis(T, 6, 6)
    if a <= 0: return
    header(ctx, T, 6, 6, "INTERPRETAÇÃO", "Silêncio não é ausência", None, y=330)
    gy = 820
    # soil cross-section
    ctx.set_source_rgba(*hexc("1a1230"), 0.92 * a); ctx.rectangle(60, gy, W - 120, 560); ctx.fill()
    g = cairo.LinearGradient(0, gy, 0, gy + 560)
    g.add_color_stop_rgba(0, *hexc("3a2a4a"), 0.9 * a); g.add_color_stop_rgba(1, *hexc("1a1230"), 0)
    ctx.set_source(g); ctx.rectangle(60, gy, W - 120, 560); ctx.fill()
    ctx.set_source_rgba(*GOLD, 0.5 * a); ctx.set_line_width(4); ctx.move_to(60, gy); ctx.line_to(W - 60, gy); ctx.stroke()
    text_c(ctx, "onde você não vê", 540, gy + 520, 34, LAV, a * clamp((T - wt(6, "onde")) / 0.4), False, spacing=2)
    sx, sy = 540, gy + 190
    glow(ctx, sx, sy, 110, (1, 0.85, 0.5), 0.5 * a)
    ctx.save(); ctx.translate(sx, sy); ctx.rotate(-0.4); ctx.scale(48, 30)
    ctx.set_source_rgba(*hexc("e8b25c"), a); ctx.arc(0, 0, 1, 0, 6.283); ctx.restore(); ctx.fill()
    # roots
    rk = clamp((T - wt(6, "Deus")) / 2.2)
    ctx.set_source_rgba(*hexc("f2d6a0"), 0.85 * a); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    random.seed(3)
    for n in range(7):
        ang = math.radians(25 + n * 22)
        L = (170 + random.uniform(0, 150)) * rk
        if L < 2: continue
        ctx.set_line_width(5 - n * 0.3)
        ex, ey = sx + math.cos(ang) * L, sy + 20 + math.sin(ang) * L
        ctx.move_to(sx, sy + 15); ctx.curve_to(sx + (ex - sx) * 0.3 + 20 * math.sin(n), sy + (ey - sy) * 0.5, ex - 10, ey - 30, ex, ey); ctx.stroke()
    # sprout pushing up
    pk = clamp((T - wt(6, "ainda")) / 1.2)
    if pk > 0:
        top = sy - 15 - pk * 280
        ctx.set_source_rgba(*MINT, a); ctx.set_line_width(8)
        ctx.move_to(sx, sy - 15); ctx.curve_to(sx - 10, sy - 100, sx + 10, top + 60, sx, top); ctx.stroke()
        if top < gy:
            lk = eob((gy - top) / 60.0)
            for side in (-1, 1):
                ctx.save(); ctx.translate(sx, top + 10); ctx.rotate(side * 0.7); ctx.scale(max(1e-3, lk), max(1e-3, lk))
                ctx.move_to(0, 0); ctx.curve_to(side * 25, -30, side * 60, -20, side * 70, 0); ctx.curve_to(side * 50, 15, side * 20, 15, 0, 0)
                ctx.restore(); ctx.set_source_rgba(*MINT, a); ctx.fill()
            glow(ctx, sx, top, 90, MINT, 0.45 * a * clamp(lk))


def path_scene(ctx, T):
    a = vis(T, 8, 9)
    if a <= 0: return
    # sun
    sk = ease((T - S(8)) / 4.0)
    sy = lerp(860, 760, sk)
    glow(ctx, 540, sy, 380, (1, 0.75, 0.5), 0.55 * a)
    ctx.set_source_rgba(1, 0.86, 0.62, a); ctx.arc(540, sy, 80, 0, 6.283); ctx.fill()
        # characters
    walk = ease((T - S(9) - 0.5) / (SCENE_DUR[9] - 0.5))
    yy = lerp(1110, 920, walk); sc = lerp(1.0, 0.6, walk)
    bob = abs(math.sin(T * 5)) * 10 * (1 if T > S(9) + 0.5 else 0)
    melbo(ctx, lerp(380, 480, walk), yy - bob, 115 * sc, T, a, sad=0, happy=0.8, look=1 - walk)
    pingo(ctx, lerp(700, 600, walk), yy + 20 - bob, 98 * sc, T, a, happy=1, look=-1 + walk)
    # star above
    t0 = wt(8, "sozinho")
    k = eob((T - t0 + 0.2) / 0.6)
    if T > t0 - 0.2:
        sparkle(ctx, lerp(540, 540, walk), yy - 260 * sc, max(1e-3, k) * (1 + 0.1 * math.sin(T * 4)), a * clamp(k))


def sc8(ctx, T):
    header(ctx, T, 8, 8, "PARA LEMBRAR", "Você não espera sozinho", None, y=330)


def sc9(ctx, T):
    a = vis(T, 9, 9)
    if a <= 0: return
    k = eob((T - S(9) - 0.2) / 0.6)
    yy = 250 + (1 - k) * 40
    ctx.set_source_rgba(*CARD, 0.82 * a); rrect(ctx, 80, yy, W - 160, 300, 34); ctx.fill()
    ctx.set_source_rgba(*GOLD, 0.35 * a); rrect(ctx, 80, yy, W - 160, 300, 34); ctx.set_line_width(2); ctx.stroke()
    text_c(ctx, "PRÓXIMO EPISÓDIO", 540, yy + 75, 32, GOLD, a, True, spacing=6)
    text_c(ctx, "Por que orar, se Deus", 540, yy + 155, 58, (1, 1, 1), a, True)
    text_c(ctx, "já sabe tudo?", 540, yy + 225, 58, (1, 1, 1), a, True)
    t0 = wt(9, "siga")
    pk = eob((T - t0) / 0.45)
    if T > t0:
        s = max(1e-3, pk)
        ctx.save(); ctx.translate(540, yy + 400); ctx.scale(s, s)
        ctx.set_source_rgba(*GOLD, a); rrect(ctx, -190, -48, 380, 96, 48); ctx.fill()
        text_c(ctx, "Siga a série", 0, 16, 44, NAVY, a, True)
        ctx.restore()


# ---------------- subtitles ----------------
def groups():
    G = []
    for ln in LINES:
        if ln["spk"] == "R":
            continue
        cur = []
        for w in ln["words"]:
            if cur and (len(cur) >= 4 or w["a"] - cur[-1]["b"] > 0.25 or cur[-1]["txt"][-1] in ".?!…"):
                G.append(dict(spk=ln["spk"], words=cur)); cur = []
            cur.append(w)
        if cur: G.append(dict(spk=ln["spk"], words=cur))
    for g in G:
        g["a"] = g["words"][0]["a"] - 0.05
    for n, g in enumerate(G):
        nxt = G[n + 1]["a"] if n + 1 < len(G) else 1e9
        g["b"] = min(g["words"][-1]["b"] + 0.5, nxt)
    return G


GROUPS = groups()
TAG = {"M": ("MELBO", hexc("fbefd0")), "P": ("PINGO", MINT)}


def subtitles(ctx, T):
    for g in GROUPS:
        if g["a"] <= T < g["b"]:
            break
    else:
        return
    a = clamp((T - g["a"]) / 0.12) * clamp((g["b"] - T) / 0.12)
    size = 54
    font(ctx, size, True)
    s = " ".join(w["txt"] for w in g["words"])
    while ctx.text_extents(s).x_advance > 900 and size > 36:
        size -= 2; font(ctx, size, True)
    tw = ctx.text_extents(s).x_advance
    cy = 1560
    bw, bh = tw + 80, size + 56
    ctx.set_source_rgba(*CARD, 0.72 * a); rrect(ctx, 540 - bw / 2, cy - bh / 2, bw, bh, 26); ctx.fill()
    ctx.set_source_rgba(1, 1, 1, 0.08 * a); rrect(ctx, 540 - bw / 2, cy - bh / 2, bw, bh, 26); ctx.set_line_width(2); ctx.stroke()
    if g["spk"] in TAG:
        name, col = TAG[g["spk"]]
        font(ctx, 26, True)
        nw = ctx.text_extents(name).x_advance + 14 * (len(name) - 1) * 0 + 40
        x0 = 540 - bw / 2 + 10; y0 = cy - bh / 2 - 26
        ctx.set_source_rgba(*col, 0.95 * a); rrect(ctx, x0, y0, nw + 20, 40, 20); ctx.fill()
        text_c(ctx, name, x0 + (nw + 20) / 2, y0 + 29, 26, NAVY, a, True, spacing=3)
    font(ctx, size, True)
    x = 540 - tw / 2
    for w in g["words"]:
        cur = w["a"] <= T
        spoken_now = w["a"] <= T <= w["b"] + 0.08
        col = GOLD if spoken_now else (1, 1, 1)
        al = a * (1.0 if cur else 0.5)
        ctx.set_source_rgba(*col, al)
        ctx.move_to(x, cy + size * 0.36); ctx.show_text(w["txt"])
        x += ctx.text_extents(w["txt"] + " ").x_advance
    ctx.new_path()


# ---------------- frame ----------------
def flash(ctx, T):
    for i, s in ((3, 0.85), (7, 0.85), (5, 0.25)):
        u = T - S(i)
        if -0.12 < u < 0.7:
            a = s * (clamp((u + 0.12) / 0.12) if u < 0 else (1 - u / 0.7) ** 2)
            ctx.set_source_rgba(1, 0.97, 0.88, a); ctx.paint()


def frame(ctx, T):
    i = scene_at(T)
    ctx.save()
    z = 1 + 0.03 * clamp((T - S(i)) / SCENE_DUR[i])
    ctx.translate(540, 900); ctx.scale(z, z); ctx.translate(-540, -900)
    draw_bg(ctx, T)
    sc0(ctx, T)
    sc1(ctx, T); sc1_2_chars(ctx, T)
    scripture_scene(ctx, T, 3, "ESTÁ ESCRITO", "Davi também sentiu", "Salmos 13",
                    "“Até quando te esquecerás de mim, Senhor? Para sempre?”", "Salmos 13:1 · ARC")
    sc4(ctx, T); sc5(ctx, T); sc6(ctx, T)
    scripture_scene(ctx, T, 7, "ESTÁ ESCRITO", "Aquiete-se", "Salmos 46",
                    "“Aquietai-vos e sabei que eu sou Deus.”", "Salmos 46:10 · ARC")
    path_scene(ctx, T); sc8(ctx, T); sc9(ctx, T)
    ctx.restore()
    flash(ctx, T)
    subtitles(ctx, T)
    # progress bar
    ctx.set_source_rgba(*GOLD, 0.9); ctx.rectangle(0, 0, W * clamp(T / TOTAL), 8); ctx.fill()


def render_surface(T):
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surf)
    frame(ctx, T)
    return surf


if __name__ == "__main__":
    if sys.argv[1] == "--still":
        T = float(sys.argv[2]); out = sys.argv[3] if len(sys.argv) > 3 else f"still_{T:.2f}.png"
        render_surface(T).write_to_png(out); print(out)
    elif sys.argv[1] == "--chunk":
        k, N = int(sys.argv[2]), int(sys.argv[3])
        nf = int(math.ceil(TOTAL * FPS))
        a, b = nf * k // N, nf * (k + 1) // N
        tmp = f"chunk{k}.tmp.mp4"
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                              "-c:v", "libx264", "-crf", "19", "-preset", "veryfast", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
        for f in range(a, b):
            ctx = cairo.Context(surf)
            ctx.set_operator(cairo.OPERATOR_SOURCE); ctx.set_source_rgb(0, 0, 0); ctx.paint(); ctx.set_operator(cairo.OPERATOR_OVER)
            frame(ctx, f / FPS)
            surf.flush()
            p.stdin.write(bytes(surf.get_data()))
        p.stdin.close()
        if p.wait() == 0:
            os.replace(tmp, f"chunk{k}.mp4")
        print("chunk", k, "done", b - a)

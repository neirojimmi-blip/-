"""Плашка кодового слова и финальная карточка для рилса про десктопный ChatGPT.

Стиль тот же, что в ролике про Claude: оранжевая плашка со словом,
капс-строки Montserrat, тёмный градиент с констелляцией на финалке.
Прописная строка не ставится — Pushkin нет, а fallback-курсивы запрещены.
"""
from PIL import Image, ImageDraw, ImageFont
import numpy as np, math, os

W, H, FPS = 1080, 1920, 30
F = "fonts/"
ORANGE = (255, 117, 31)
WORD = "ДЕСКТОП"


def fit(fp, t, tw, lo=20, hi=240):
    while lo < hi:
        m = (lo + hi + 1) // 2
        b = ImageFont.truetype(F + fp, m).getbbox(t)
        if b[2] - b[0] <= tw:
            lo = m
        else:
            hi = m - 1
    return ImageFont.truetype(F + fp, lo)


def eob(x):
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


# ---------- плашка на живом кадре ----------
def cta(outdir="ctab", dur=2.6, cy=1150):
    os.makedirs(outdir, exist_ok=True)
    n = int(dur * FPS)
    lead = "ПИШИ В КОММЕНТАРИЯХ"
    fl = ImageFont.truetype(F + "Montserrat-500.ttf", 42)
    base = fit("Montserrat-700.ttf", WORD, int(W * 0.62)).size
    for i in range(n):
        t = i / FPS
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        p = min(t / 0.34, 1.0)
        s = 0.6 + 0.4 * eob(p) if p < 1 else 1.0
        a = int(255 * min(p * 1.8, 1))
        if t > dur - 0.25:
            a = int(a * max(0, (dur - t) / 0.25))
        bl = d.textbbox((0, 0), lead, font=fl)
        lx = (W - (bl[2] - bl[0])) // 2 - bl[0]
        d.text((lx + 2, cy - 150 - bl[1] + 3), lead, font=fl, fill=(8, 14, 34, int(a * .7)))
        d.text((lx, cy - 150 - bl[1]), lead, font=fl, fill=(255, 255, 255, a))
        ff = ImageFont.truetype(F + "Montserrat-700.ttf", max(int(base * s), 10))
        b = d.textbbox((0, 0), WORD, font=ff)
        pw, ph = (b[2] - b[0]) + 140, (b[3] - b[1]) + 76
        x0, y0 = (W - pw) // 2, cy - ph // 2
        d.rounded_rectangle([x0 + 7, y0 + 13, x0 + pw + 7, y0 + ph + 13],
                            radius=int(24 * s), fill=(10, 16, 40, int(a * .45)))
        d.rounded_rectangle([x0, y0, x0 + pw, y0 + ph], radius=int(24 * s), fill=ORANGE + (a,))
        d.text((W // 2 - (b[2] - b[0]) // 2 - b[0], cy - (b[3] - b[1]) // 2 - b[1]),
               WORD, font=ff, fill=(255, 255, 255, a))
        if p > 0.65:
            ay = y0 + ph + 30
            d.polygon([(W // 2 - 28, ay), (W // 2 + 28, ay), (W // 2, ay + 36)],
                      fill=ORANGE + (int(a * .92),))
        im.save(f"{outdir}/{i:04d}.png")
    return n


# ---------- финальная карточка ----------
def final(outdir="finb", dur=3.6):
    os.makedirs(outdir, exist_ok=True)
    n = int(dur * FPS)
    ctx = ["ПРИШЛЮ ССЫЛКУ", "И СВОЮ НАСТРОЙКУ"]
    fpl = fit("Montserrat-700.ttf", WORD, int(W * 0.56))
    fctx = ImageFont.truetype(F + "Montserrat-500.ttf", 52)

    g = Image.new("RGB", (1, H))
    for y in range(H):
        f = y / H
        g.putpixel((0, y), (int(58 + (20 - 58) * f), int(69 + (28 - 69) * f),
                            int(96 + (51 - 96) * f)))
    bg = g.resize((W, H)).convert("RGBA")

    rng = np.random.default_rng(9)
    P = 70
    px, py = rng.uniform(0, W, P), rng.uniform(0, H, P)
    pr, pa = rng.uniform(2.0, 5.5, P), rng.uniform(.15, .6, P)
    pvy, pph = rng.uniform(-5, 5, P), rng.uniform(0, 6.28, P)

    d0 = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    b = d0.textbbox((0, 0), WORD, font=fpl)
    pw, ph = (b[2] - b[0]) + 150, (b[3] - b[1]) + 84
    CY = 900

    for i in range(n):
        t = i / FPS
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dl = ImageDraw.Draw(lay)
        pts = [(px[k], (py[k] + pvy[k] * t) % H, k) for k in range(P)]
        for a1 in range(P):
            for a2 in range(a1 + 1, P):
                dist = math.hypot(pts[a1][0] - pts[a2][0], pts[a1][1] - pts[a2][1])
                if dist < 175:
                    dl.line([pts[a1][0], pts[a1][1], pts[a2][0], pts[a2][1]],
                            fill=(255, 255, 255, int(46 * (1 - dist / 175))), width=1)
        for x, y, k in pts:
            al = int(255 * pa[k] * (.6 + .4 * math.sin(pph[k] + t * 1.6)))
            dl.ellipse([x - pr[k], y - pr[k], x + pr[k], y + pr[k]],
                       fill=(255, 255, 255, max(al, 0)))
        im = Image.alpha_composite(bg, lay)
        d = ImageDraw.Draw(im)

        p = min(t / 0.36, 1.0)
        a = int(255 * min(p * 1.9, 1))
        x0, y0 = (W - pw) // 2, CY - ph // 2
        d.rounded_rectangle([x0 + 8, y0 + 14, x0 + pw + 8, y0 + ph + 14],
                            radius=26, fill=(8, 12, 30, int(a * .5)))
        d.rounded_rectangle([x0, y0, x0 + pw, y0 + ph], radius=26, fill=ORANGE + (a,))
        d.text((W // 2 - (b[2] - b[0]) // 2 - b[0], CY - (b[3] - b[1]) // 2 - b[1]),
               WORD, font=fpl, fill=(255, 255, 255, a))

        # капс-строки под плашкой, печатаются
        yy = CY + ph // 2 + 70
        shown = int(max(0.0, t - 0.45) / 0.025)
        used = 0
        for line in ctx:
            vis = line[:max(0, shown - used)]
            used += len(line)
            if vis:
                bb = d.textbbox((0, 0), vis, font=fctx)
                lx = (W - (bb[2] - bb[0])) // 2 - bb[0]
                d.text((lx, yy - bb[1]), vis, font=fctx, fill=(255, 255, 255, 235))
            yy += 74

        # ник внизу
        fn = ImageFont.truetype(F + "Montserrat-500.ttf", 40)
        nick = "@xeniia_neuro"
        bn = d.textbbox((0, 0), nick, font=fn)
        d.text(((W - (bn[2] - bn[0])) // 2 - bn[0], 1680 - bn[1]), nick,
               font=fn, fill=(255, 255, 255, 190))
        im.convert("RGB").save(f"{outdir}/{i:04d}.png")
    return n


print("плашка кодового слова:", cta(), "кадров")
print("финальная карточка:", final(), "кадров")

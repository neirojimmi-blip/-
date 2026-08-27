"""Яркий полноэкранный хук по опубликованному эталону.

Композиция: затемнённый и размытый кадр с синим тинтом, констелляция,
крупный белый капс Montserrat вразрядку, под ним крупная оранжевая
прописная строка, внизу часы с оранжевой стрелкой.
Печать по буквам CHAR 0.022 / GAP 0.12 по скиллу, звука нет.
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np, math, os

W, H = 1080, 1920
FPS, DUR = 30, 4.60
N = int(DUR * FPS)
F = "fonts/"
ORANGE = (255, 117, 31)
CHAR, GAP, START = 0.022, 0.12, 0.30
FADE_A, FADE_B = 4.15, 4.55

CAPS = ["5 ФУНКЦИЙ CLAUDE", "О КОТОРЫХ МОЛЧАТ"]
SCRIPT = ["и вот что", "он умеет сам"]
TRACK = 9                      # разрядка как в эталоне
os.makedirs("hook2", exist_ok=True)


def fit(path, text, target, lo=30, hi=210):
    while lo < hi:
        m = (lo + hi + 1) // 2
        f = ImageFont.truetype(path, m)
        b = f.getbbox(text)
        if b[2] - b[0] <= target:
            lo = m
        else:
            hi = m - 1
    return ImageFont.truetype(path, lo)


fcap = fit(F + "Montserrat-500.ttf", CAPS[0] + "  ", int(W * 0.82))
fscr = fit(F + "MarckFull.ttf", max(SCRIPT, key=len), int(W * 0.82))

rng = np.random.default_rng(4)
P = 85
px = rng.uniform(0, W, P); py = rng.uniform(0, H, P)
pr = rng.uniform(2.2, 6.5, P); pa = rng.uniform(0.18, 0.75, P)
pvy = rng.uniform(-6, 6, P); pph = rng.uniform(0, 6.28, P)


def measure(s, f):
    d = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    return sum(d.textlength(c, font=f) + TRACK for c in s) - TRACK if s else 0


def tracked(d, s, cx, y, fill, f, shadow=True):
    x = cx - measure(s, f) / 2
    for c in s:
        if shadow:
            d.text((x + 3, y + 4), c, font=f, fill=(10, 16, 36, 150))
        d.text((x, y), c, font=f, fill=fill)
        x += d.textlength(c, font=f) + TRACK
    return x


starts = []
t0 = START
for s in CAPS + SCRIPT:
    starts.append(t0)
    t0 += len(s) * CHAR + GAP

CAP_Y, SCR_Y = 760, 1075
LH_C, LH_S = int(fcap.size * 1.34), int(fscr.size * 1.18)

for i in range(N):
    t = i / FPS
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    if t < FADE_A:
        a = 1.0
    elif t < FADE_B:
        a = 1 - (t - FADE_A) / (FADE_B - FADE_A)
    else:
        a = 0.0
    if a <= 0:
        im.save(f"hook2/{i:04d}.png")
        continue
    A = int(255 * a)

    # констелляция
    pts = []
    for k in range(P):
        y = (py[k] + pvy[k] * t) % H
        pts.append((px[k], y, k))
    for m in range(P):
        for n in range(m + 1, P):
            dx, dy = pts[m][0] - pts[n][0], pts[m][1] - pts[n][1]
            dist = math.hypot(dx, dy)
            if dist < 165:
                d.line([pts[m][0], pts[m][1], pts[n][0], pts[n][1]],
                       fill=(255, 255, 255, int(38 * (1 - dist / 165) * a)), width=1)
    for x, y, k in pts:
        al = int(255 * pa[k] * (0.6 + 0.4 * math.sin(pph[k] + t * 1.7)) * a)
        d.ellipse([x - pr[k], y - pr[k], x + pr[k], y + pr[k]], fill=(255, 255, 255, max(al, 0)))

    # капс
    for li, s in enumerate(CAPS):
        shown = int(max(0, (t - starts[li]) / CHAR))
        if shown <= 0:
            continue
        tracked(d, s[:shown], W // 2, CAP_Y + li * LH_C, (255, 255, 255, A), fcap)

    # прописные - оранжевые, с утолщением обводкой
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for li, s in enumerate(SCRIPT):
        shown = int(max(0, (t - starts[len(CAPS) + li]) / CHAR))
        if shown <= 0:
            continue
        txt = s[:shown]
        b = gd.textbbox((0, 0), txt, font=fscr)
        x = (W - (b[2] - b[0])) // 2 - b[0]
        y = SCR_Y + li * LH_S
        for ox, oy in ((-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, 1)):
            gd.text((x + ox, y + oy), txt, font=fscr, fill=ORANGE + (A,))
        gd.text((x + 3, y + 5), txt, font=fscr, fill=(120, 40, 0, int(A * 0.5)))
        gd.text((x, y), txt, font=fscr, fill=ORANGE + (A,))
    im = Image.alpha_composite(im, glow)
    im.save(f"hook2/{i:04d}.png")

print(f"кадров {N} | капс {fcap.size}px вразрядку {TRACK} | прописные {fscr.size}px")

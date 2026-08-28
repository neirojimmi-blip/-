"""Хук ролика про доступ к рабочей среде.

Лицо открыто: полоса начинается на 820, а лицо в первом плане занимает 265-566.

Кадр не размывается и не затемняется целиком - героиню видно.
Контраст под текст даёт мягкая заливка снизу, начинается ниже лица (~y 640).
"""
from PIL import Image, ImageDraw, ImageFont
import numpy as np, math, os

W, H = 1080, 1920
FPS, DUR = 30, 3.70
N = int(DUR * FPS)
F = "fonts/"
ORANGE = (255, 117, 31)
CHAR, GAP, START = 0.018, 0.10, 0.25
FADE_A, FADE_B = 3.15, 3.62

CAPS = ["ВЫИГРЫВАЕТ НЕ ТОТ,", "КТО ОБЩАЕТСЯ С ИИ"]
SCRIPT = ["а тот, кто дал", "ему доступ"]
TRACK = 9
BAND_TOP, BAND_BOT = 820, 1340        # полоса под текстом, ниже лица (лицо ~290-670)
FEATHER = 90
CAP_Y, SCR_Y = 850, 1030
os.makedirs("n3/hook", exist_ok=True)


def fit(path, text, target, lo=30, hi=220):
    while lo < hi:
        m = (lo + hi + 1) // 2
        f = ImageFont.truetype(path, m)
        b = f.getbbox(text)
        if b[2] - b[0] <= target:
            lo = m
        else:
            hi = m - 1
    return ImageFont.truetype(path, lo)


fcap = fit(F + "Montserrat-500.ttf", CAPS[0], int(W * 0.74))
fscr = fit(F + "GreatVibes.ttf", max(SCRIPT, key=len), int(W * 0.54))

rng = np.random.default_rng(6)
P = 55
px = rng.uniform(0, W, P)
py = rng.uniform(700, 1500, P)             # частицы только в зоне полосы
pr = rng.uniform(2.0, 5.2, P)
pa = rng.uniform(0.15, 0.6, P)
pvy = rng.uniform(-5, 5, P)
pph = rng.uniform(0, 6.28, P)

# выраженная тёмная полоса с мягкими краями - как в эталоне
scrim = Image.new("RGBA", (W, H), (0, 0, 0, 0))
sp = scrim.load()
PEAK = 196
for y in range(BAND_TOP - FEATHER, BAND_BOT + FEATHER):
    if y < BAND_TOP:
        a = int(PEAK * ((y - (BAND_TOP - FEATHER)) / FEATHER) ** 1.6)
    elif y > BAND_BOT:
        a = int(PEAK * (1 - (y - BAND_BOT) / FEATHER) ** 1.6)
    else:
        a = PEAK
    if a <= 0:
        continue
    for x in range(W):
        sp[x, y] = (10, 16, 40, a)


def measure(s, f):
    d = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    return sum(d.textlength(c, font=f) + TRACK for c in s) - TRACK if s else 0


starts = []
t0 = START
for s in CAPS + SCRIPT:
    starts.append(t0)
    t0 += len(s) * CHAR + GAP

LH_C, LH_S = int(fcap.size * 1.36), int(fscr.size * 0.88)

for i in range(N):
    t = i / FPS
    if t < FADE_A:
        a = 1.0
    elif t < FADE_B:
        a = 1 - (t - FADE_A) / (FADE_B - FADE_A)
    else:
        a = 0.0
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if a <= 0:
        im.save(f"n3/hook/{i:04d}.png")
        continue

    sc = scrim.copy()
    if a < 1:
        sc.putalpha(sc.split()[3].point(lambda v: int(v * a)))
    im = Image.alpha_composite(im, sc)
    d = ImageDraw.Draw(im)
    A = int(255 * a)

    for k in range(P):
        y = 700 + (py[k] - 700 + pvy[k] * t) % 800
        al = int(255 * pa[k] * (0.6 + 0.4 * math.sin(pph[k] + t * 1.7)) * a)
        d.ellipse([px[k] - pr[k], y - pr[k], px[k] + pr[k], y + pr[k]],
                  fill=(255, 255, 255, max(al, 0)))

    for li, s in enumerate(CAPS):
        shown = int(max(0, (t - starts[li]) / CHAR))
        if shown <= 0:
            continue
        txt = s[:shown]
        x = W / 2 - measure(txt, fcap) / 2
        y = CAP_Y + li * LH_C
        for c in txt:
            d.text((x + 2, y + 3), c, font=fcap, fill=(8, 14, 34, int(160 * a)))
            d.text((x, y), c, font=fcap, fill=(255, 255, 255, A))
            x += d.textlength(c, font=fcap) + TRACK

    for li, s in enumerate(SCRIPT):
        shown = int(max(0, (t - starts[len(CAPS) + li]) / CHAR))
        if shown <= 0:
            continue
        txt = s[:shown]
        b = d.textbbox((0, 0), txt, font=fscr)
        x = (W - (b[2] - b[0])) // 2 - b[0]
        y = SCR_Y + li * LH_S
        d.text((x + 2, y + 4), txt, font=fscr, fill=(8, 14, 34, int(150 * a)))
        d.text((x, y), txt, font=fscr, fill=ORANGE + (A,))
        last = (li == len(SCRIPT) - 1)
        typing = shown < len(s)
        if (typing or (last and t < FADE_A)) and int(t * 2.4) % 2 == 0:
            cx = x + (b[2] - b[0]) + 14
            d.rectangle([cx, y + 14, cx + 7, y + fscr.size + 6], fill=ORANGE + (A,))

    im.save(f"n3/hook/{i:04d}.png")

print(f"кадров {N} ({DUR} c) | капс {fcap.size}px | Great Vibes {fscr.size}px без утолщения")
print(f"печать до {round(starts[-1] + len(SCRIPT[-1]) * CHAR, 2)} c, фейд {FADE_A}-{FADE_B}")

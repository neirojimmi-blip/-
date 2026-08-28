"""Хук ролика про доступ к рабочей среде.

Прописной шрифт — настоящий Pushkin, присланный пользователем. У него длинные
росчерки (петля у «к» уходит высоко), поэтому строки ставятся по реальному
боксу чернил, а не по кеглю: иначе вторая строка наезжает на первую.
Читаемость держит лёгкая обводка stroke_width=2 и размытый тёмный ореол,
собранный из самого текста: оранжевый по узорчатому платью иначе теряется.
Многопроходное утолщение не используется, оно уже браковалось.

Белых точек нет: пользователь просила убрать.
Кадр не размывается и не затемняется целиком — героиню видно, полоса
начинается ниже лица.
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

W, H = 1080, 1920
FPS, DUR = 30, 3.70
N = int(DUR * FPS)
F = "fonts/"
ORANGE = (255, 117, 31)
CHAR, GAP, START = 0.018, 0.10, 0.25
FADE_A, FADE_B = 3.15, 3.62

CAPS = ["ВЫИГРЫВАЕТ НЕ ТОТ,", "КТО ОБЩАЕТСЯ С ИИ"]
SCRIPT = ["а тот, кто дал", "ему доступ"]
TRACK = 7
BAND_TOP, BAND_BOT = 800, 1400
FEATHER = 100
CAP_Y = 846
os.makedirs("n3/hook", exist_ok=True)

_m = ImageDraw.Draw(Image.new("RGB", (8, 8)))


def fit(path, text, target, lo=30, hi=230):
    while lo < hi:
        m = (lo + hi + 1) // 2
        b = ImageFont.truetype(path, m).getbbox(text)
        if b[2] - b[0] <= target:
            lo = m
        else:
            hi = m - 1
    return ImageFont.truetype(path, lo)


fcap = fit(F + "Montserrat-500.ttf", CAPS[0], int(W * 0.72))
fscr = fit(F + "Pushkin.ttf", max(SCRIPT, key=len), int(W * 0.66))

# полоса контраста с мягкими краями, ниже лица
scrim = Image.new("RGBA", (W, H), (0, 0, 0, 0))
sp = scrim.load()
PEAK = 214
for y in range(BAND_TOP - FEATHER, min(H, BAND_BOT + FEATHER)):
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
    return sum(_m.textlength(c, font=f) + TRACK for c in s) - TRACK if s else 0


starts, t0 = [], START
for s in CAPS + SCRIPT:
    starts.append(t0)
    t0 += len(s) * CHAR + GAP

LH_C = int(fcap.size * 1.38)

# прописные строки ставим по боксу чернил: у Pushkin высокие росчерки
boxes = [_m.textbbox((0, 0), s, font=fscr) for s in SCRIPT]
SCR_TOP = CAP_Y + LH_C * len(CAPS) + 34
tops, y = [], SCR_TOP
for b in boxes:
    tops.append(y - b[1])
    y += (b[3] - b[1]) + 26

for i in range(N):
    t = i / FPS
    a = 1.0 if t < FADE_A else (0.0 if t >= FADE_B else 1 - (t - FADE_A) / (FADE_B - FADE_A))
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

    for li, s in enumerate(CAPS):
        shown = int(max(0, (t - starts[li]) / CHAR))
        if shown <= 0:
            continue
        txt = s[:shown]
        x = W / 2 - measure(txt, fcap) / 2
        y = CAP_Y + li * LH_C
        for c in txt:
            d.text((x + 2, y + 3), c, font=fcap, fill=(8, 14, 34, int(150 * a)))
            d.text((x, y), c, font=fcap, fill=(255, 255, 255, A))
            x += d.textlength(c, font=fcap) + TRACK

    # ореол: тот же текст жирно, размыт и подложен снизу
    halo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    hd = ImageDraw.Draw(halo)
    drawn = []
    for li, s in enumerate(SCRIPT):
        shown = int(max(0, (t - starts[len(CAPS) + li]) / CHAR))
        if shown <= 0:
            continue
        txt = s[:shown]
        b = d.textbbox((0, 0), txt, font=fscr)
        x = (W - (b[2] - b[0])) // 2 - b[0]
        drawn.append((li, s, txt, b, x, tops[li], shown))
        hd.text((x, tops[li]), txt, font=fscr, fill=(6, 10, 26, int(230 * a)),
                stroke_width=14, stroke_fill=(6, 10, 26, int(230 * a)))
    if drawn:
        im = Image.alpha_composite(im, halo.filter(ImageFilter.GaussianBlur(11)))
        d = ImageDraw.Draw(im)

    for li, s, txt, b, x, y, shown in drawn:
        d.text((x, y), txt, font=fscr, fill=ORANGE + (A,),
               stroke_width=2, stroke_fill=ORANGE + (A,))
        if (shown < len(s) or (li == len(SCRIPT) - 1 and t < FADE_A)) \
                and int(t * 2.4) % 2 == 0:
            cx = x + (b[2] - b[0]) + 16
            d.rectangle([cx, y + b[1] + 12, cx + 7, y + b[3]], fill=ORANGE + (A,))

    im.save(f"n3/hook/{i:04d}.png")

print(f"кадров {N} ({DUR} с) | капс {fcap.size}px | Pushkin {fscr.size}px, обводка 2")
print(f"прописные строки: {tops} | полоса {BAND_TOP}-{BAND_BOT}, точек нет")

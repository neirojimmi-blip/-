"""Хук ролика про доступ к рабочей среде.

Прописной шрифт — настоящий Pushkin. Фраза идёт целиком:
«а тот, кто дал ему доступ к своей рабочей среде». Разбита на три строки,
а не на две: в две кегль падал до 70 px и каллиграфия переставала читаться.

Читаемость держат три вещи:
  1. компактная тёмная плашка со скруглением 30 на уровне груди — как в скилле;
     лицо она не задевает, оно занимает 265-566, плашка начинается ниже 780;
  2. размытый тёмный ореол, собранный из самого текста, — оранжевый по
     узорчатому платью иначе теряется даже на плашке;
  3. лёгкая обводка stroke_width=3. Многопроходное утолщение офсетными
     копиями не применяется, оно уже браковалось.

Строки ставятся по реальному боксу чернил, а не по кеглю: у Pushkin высокие
росчерки, петля у «к» уходит выше строки и наезжает на предыдущую.

Выключка влево: при центрировании строки разной длины расходятся веером
и блок выглядит рыхлым. По левому краю он собран и плашка выходит уже.

Белых точек нет, кадр не размывается и не затемняется целиком.
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

W, H = 1080, 1920
FPS, DUR = 30, 3.90
N = int(DUR * FPS)
F = "fonts/"
ORANGE = (255, 117, 31)
CHAR, GAP, START = 0.018, 0.10, 0.25
FADE_A, FADE_B = 3.34, 3.84

CAPS = ["ВЫИГРЫВАЕТ НЕ ТОТ,", "КТО ОБЩАЕТСЯ С ИИ"]
SCRIPT = ["а тот, кто дал ему", "доступ к своей", "рабочей среде"]
TRACK = 7
BLOCK_TOP = 772                # ниже лица
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


fcap = fit(F + "Montserrat-500.ttf", CAPS[0], int(W * 0.70))
fscr = fit(F + "Pushkin.ttf", max(SCRIPT, key=len), int(W * 0.70))


def measure(s, f):
    return sum(_m.textlength(c, font=f) + TRACK for c in s) - TRACK if s else 0


starts, t0 = [], START
for s in CAPS + SCRIPT:
    starts.append(t0)
    t0 += len(s) * CHAR + GAP
TYPED_AT = round(t0 - GAP, 2)

LH_C = int(fcap.size * 1.18)

# прописные — по боксу чернил, с запасом на росчерки
boxes = [_m.textbbox((0, 0), s, font=fscr) for s in SCRIPT]
SCR_TOP = BLOCK_TOP + LH_C * len(CAPS) + 44
tops, y = [], SCR_TOP
for b in boxes:
    tops.append(y - b[1])
    # нахлёста быть не должно: росчерки следующей строки въезжают
    # в предыдущую и фраза перестаёт читаться
    y += (b[3] - b[1]) + 8
BLOCK_BOT = y - 8

# компактная плашка по ширине самой длинной строки
w_text = max([measure(s, fcap) for s in CAPS] + [b[2] - b[0] for b in boxes])
PX, PY_T, PY_B = 40, 30, 34
LEFT = (W - w_text) / 2
px0 = LEFT - PX
px1 = (W + w_text) / 2 + PX
py0, py1 = BLOCK_TOP - PY_T, BLOCK_BOT + PY_B

RULE_Y = BLOCK_TOP + LH_C * len(CAPS) + 16   # разделитель капса и каллиграфии
RULE_W = 118

plate = Image.new("RGBA", (W, H), (0, 0, 0, 0))
pd = ImageDraw.Draw(plate)
pd.rounded_rectangle([px0, py0, px1, py1], radius=28, fill=(8, 12, 24, 205))
# тонкий световой кант — плашка перестаёт читаться как глухая плита
pd.rounded_rectangle([px0, py0, px1, py1], radius=28,
                     outline=(255, 255, 255, 26), width=2)
plate = plate.filter(ImageFilter.GaussianBlur(2))     # мягкий край

for i in range(N):
    t = i / FPS
    a = 1.0 if t < FADE_A else (0.0 if t >= FADE_B else 1 - (t - FADE_A) / (FADE_B - FADE_A))
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if a <= 0:
        im.save(f"n3/hook/{i:04d}.png")
        continue

    pl = plate.copy()
    if a < 1:
        pl.putalpha(pl.split()[3].point(lambda v: int(v * a)))
    im = Image.alpha_composite(im, pl)
    d = ImageDraw.Draw(im)
    A = int(255 * a)

    for li, s in enumerate(CAPS):
        shown = int(max(0, (t - starts[li]) / CHAR))
        if shown <= 0:
            continue
        txt = s[:shown]
        x = LEFT
        y = BLOCK_TOP + li * LH_C
        for c in txt:
            d.text((x + 2, y + 3), c, font=fcap, fill=(6, 10, 26, int(170 * a)))
            d.text((x, y), c, font=fcap, fill=(255, 255, 255, A))
            x += d.textlength(c, font=fcap) + TRACK

    # оранжевый разделитель — тот же приём, что во вставках
    rp = min(max((t - starts[len(CAPS)] + 0.10) / 0.30, 0), 1)
    if rp > 0:
        wr = RULE_W * (1 - (1 - rp) ** 3)
        d.rounded_rectangle([LEFT, RULE_Y, LEFT + wr, RULE_Y + 4],
                            radius=2, fill=ORANGE + (A,))

    # ореол под прописными — из самого текста
    halo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    hd = ImageDraw.Draw(halo)
    drawn = []
    for li, s in enumerate(SCRIPT):
        shown = int(max(0, (t - starts[len(CAPS) + li]) / CHAR))
        if shown <= 0:
            continue
        txt = s[:shown]
        b = d.textbbox((0, 0), txt, font=fscr)
        x = LEFT + 10 - b[0]
        drawn.append((li, s, txt, b, x, tops[li], shown))
        hd.text((x, tops[li]), txt, font=fscr, fill=(4, 7, 20, int(238 * a)),
                stroke_width=16, stroke_fill=(4, 7, 20, int(238 * a)))
    if drawn:
        im = Image.alpha_composite(im, halo.filter(ImageFilter.GaussianBlur(12)))
        d = ImageDraw.Draw(im)

    for li, s, txt, b, x, y, shown in drawn:
        d.text((x, y), txt, font=fscr, fill=ORANGE + (A,),
               stroke_width=3, stroke_fill=ORANGE + (A,))
        if (shown < len(s) or (li == len(SCRIPT) - 1 and t < FADE_A)) \
                and int(t * 2.4) % 2 == 0:
            cx = x + (b[2] - b[0]) + 16
            d.rectangle([cx, y + b[1] + 10, cx + 7, y + b[3]], fill=ORANGE + (A,))

    im.save(f"n3/hook/{i:04d}.png")

print(f"кадров {N} ({DUR} с) | капс {fcap.size}px | Pushkin {fscr.size}px, обводка 3")
print(f"плашка {int(px0)}..{int(px1)} x {int(py0)}..{int(py1)} | текст допечатан к {TYPED_AT} с")

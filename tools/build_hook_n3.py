"""Хук ролика про доступ к рабочей среде.

Прописной шрифт — настоящий Pushkin, фраза целиком:
«а тот, кто дал ему доступ к своей рабочей среде».

Подложка — не плашка с краями, а мягкое тёмное поле: плотность держится
там, где текст, и растворяется к краям косинусным спадом. Чёткий
прямоугольник со скруглением и световым кантом пользователь забраковала.
Разделительной линии между капсом и каллиграфией тоже нет.

Читаемость держат это поле, размытый ореол из самого текста и обводка 3 px.
Многопроходное утолщение офсетными копиями не применяется, оно браковалось.

Строки ставятся по реальному боксу чернил, а не по кеглю: у Pushkin высокие
росчерки, петля у «к» уходит выше строки. Зазор строго положительный —
при нахлёсте росчерки въезжают в соседнюю строку и фраза не читается.

Белых точек нет, кадр не размывается и не затемняется целиком.
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
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
BLOCK_TOP = 736                # ниже лица: оно занимает 265-566
os.makedirs("n3/hook", exist_ok=True)

_m = ImageDraw.Draw(Image.new("RGB", (8, 8)))


def fit(path, text, target, lo=30, hi=240):
    while lo < hi:
        m = (lo + hi + 1) // 2
        b = ImageFont.truetype(path, m).getbbox(text)
        if b[2] - b[0] <= target:
            lo = m
        else:
            hi = m - 1
    return ImageFont.truetype(path, lo)


fcap = fit(F + "Montserrat-500.ttf", CAPS[0], int(W * 0.68))
fscr = fit(F + "Pushkin.ttf", max(SCRIPT, key=len), int(W * 0.86))


def measure(s, f):
    return sum(_m.textlength(c, font=f) + TRACK for c in s) - TRACK if s else 0


starts, t0 = [], START
for s in CAPS + SCRIPT:
    starts.append(t0)
    t0 += len(s) * CHAR + GAP
TYPED_AT = round(t0 - GAP, 2)

LH_C = int(fcap.size * 1.20)

boxes = [_m.textbbox((0, 0), s, font=fscr) for s in SCRIPT]
SCR_TOP = BLOCK_TOP + LH_C * len(CAPS) + 36
tops, y = [], SCR_TOP
for b in boxes:
    tops.append(y - b[1])
    y += (b[3] - b[1]) + 8
BLOCK_BOT = y - 8

w_text = max([measure(s, fcap) for s in CAPS] + [b[2] - b[0] for b in boxes])


def soft_field(x0, x1, y0, y1, fade_x=190, fade_y=150, peak=228):
    """Тёмное поле без краёв: плато по тексту, косинусный спад по сторонам."""
    def ramp(coord, lo, hi, fade):
        r = np.ones_like(coord, dtype=float)
        left = (coord < lo)
        right = (coord > hi)
        r[left] = np.clip((coord[left] - (lo - fade)) / fade, 0, 1)
        r[right] = np.clip(((hi + fade) - coord[right]) / fade, 0, 1)
        return (1 - np.cos(np.pi * r)) / 2          # плавный вход и выход

    xs = ramp(np.arange(W, dtype=float), x0, x1, fade_x)
    ys = ramp(np.arange(H, dtype=float), y0, y1, fade_y)
    a = (peak * np.outer(ys, xs)).astype("uint8")
    fld = np.zeros((H, W, 4), dtype="uint8")
    fld[..., 0], fld[..., 1], fld[..., 2] = 8, 12, 26
    fld[..., 3] = a
    return Image.fromarray(fld, "RGBA")


FIELD = soft_field((W - w_text) / 2 - 30, (W + w_text) / 2 + 30,
                   BLOCK_TOP - 26, BLOCK_BOT + 30)

for i in range(N):
    t = i / FPS
    a = 1.0 if t < FADE_A else (0.0 if t >= FADE_B else 1 - (t - FADE_A) / (FADE_B - FADE_A))
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if a <= 0:
        im.save(f"n3/hook/{i:04d}.png")
        continue

    fld = FIELD.copy()
    if a < 1:
        fld.putalpha(fld.split()[3].point(lambda v: int(v * a)))
    im = Image.alpha_composite(im, fld)
    d = ImageDraw.Draw(im)
    A = int(255 * a)

    for li, s in enumerate(CAPS):
        shown = int(max(0, (t - starts[li]) / CHAR))
        if shown <= 0:
            continue
        txt = s[:shown]
        x = W / 2 - measure(txt, fcap) / 2
        y = BLOCK_TOP + li * LH_C
        for c in txt:
            d.text((x + 2, y + 3), c, font=fcap, fill=(6, 10, 26, int(170 * a)))
            d.text((x, y), c, font=fcap, fill=(255, 255, 255, A))
            x += d.textlength(c, font=fcap) + TRACK

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
        hd.text((x, tops[li]), txt, font=fscr, fill=(4, 7, 20, int(240 * a)),
                stroke_width=18, stroke_fill=(4, 7, 20, int(240 * a)))
    if drawn:
        im = Image.alpha_composite(im, halo.filter(ImageFilter.GaussianBlur(14)))
        d = ImageDraw.Draw(im)

    for li, s, txt, b, x, y, shown in drawn:
        d.text((x, y), txt, font=fscr, fill=ORANGE + (A,),
               stroke_width=3, stroke_fill=ORANGE + (A,))
        if (shown < len(s) or (li == len(SCRIPT) - 1 and t < FADE_A)) \
                and int(t * 2.4) % 2 == 0:
            cx = x + (b[2] - b[0]) + 18
            d.rectangle([cx, y + b[1] + 12, cx + 7, y + b[3]], fill=ORANGE + (A,))

    im.save(f"n3/hook/{i:04d}.png")

print(f"кадров {N} ({DUR} с) | капс {fcap.size}px | Pushkin {fscr.size}px")
print(f"блок {BLOCK_TOP}..{int(BLOCK_BOT)} | текст допечатан к {TYPED_AT} с")

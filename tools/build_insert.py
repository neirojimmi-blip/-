"""Мокап-вставка по скиллу: тёмный градиент #101a33 - #0a0f1c, Bebas-заголовок
с оранжевым ключевым словом, чипы-теги, крупный реальный скрин.
Низ не ниже 1450 - там зона субтитров.
Вход slide-in слева ease-out 0.28 c, выход push влево 0.25 c.

Полупрозрачные фигуры рисуются на отдельном слое и композитятся:
ImageDraw с alpha-заливкой ЗАМЕНЯЕТ альфу, а не смешивает, и пробивает дыру в карточке.
"""
from PIL import Image, ImageDraw, ImageFont
import os

W, H = 1080, 1920
FPS, DUR = 30, 2.8
N = int(DUR * FPS)
F = "fonts/"
ORANGE, GREEN = (255, 117, 31), (63, 196, 140)
CARD_TOP, CARD_BOT = 150, 1440
IN_T, OUT_T = 0.28, 0.25
os.makedirs("insseq", exist_ok=True)

HEAD_KEY, HEAD_REST = "ПАМЯТЬ", "ЧТОБЫ НЕ ПОВТОРЯТЬ"
CHIPS = [("НАСТРОЙКИ", ORANGE), ("МЕЖДУ ЧАТАМИ", GREEN)]

fh = ImageFont.truetype(F + "Oswald-Bold.ttf", 84)
fc = ImageFont.truetype(F + "Oswald-Bold.ttf", 38)
fp = ImageFont.truetype(F + "Montserrat-500.ttf", 34)


def card():
    ch = CARD_BOT - CARD_TOP
    base = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    grad = Image.new("RGB", (1, ch))
    for y in range(ch):
        f = y / ch
        grad.putpixel((0, y), (int(16 + (10 - 16) * f),
                               int(26 + (15 - 26) * f),
                               int(51 + (28 - 51) * f)))
    grad = grad.resize((W - 80, ch)).convert("RGBA")
    mask = Image.new("L", (W - 80, ch), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, W - 81, ch - 1], radius=24, fill=255)
    base.paste(grad, (40, CARD_TOP), mask)

    # полупрозрачные фигуры - отдельным слоем
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)

    y = CARD_TOP + 64 + 196
    chips = []
    total = 0
    for txt, col in CHIPS:
        b = od.textbbox((0, 0), txt, font=fc)
        w = b[2] - b[0] + 52
        chips.append((txt, col, w))
        total += w + 18
    x = (W - (total - 18)) // 2
    for txt, col, w in chips:
        od.rounded_rectangle([x, y + 6, x + w, y + 70], radius=24, fill=col + (52,))
        x += w + 18
    y += 108

    SCREEN_TOP, SCREEN_BOT = y, CARD_BOT - 70
    od.rounded_rectangle([84, SCREEN_TOP, W - 84, SCREEN_BOT], radius=20, fill=(255, 255, 255, 20))
    im = Image.alpha_composite(base, ov)

    # непрозрачные элементы поверх
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([40, CARD_TOP, W - 40, CARD_BOT], radius=24, outline=(70, 88, 158, 160), width=2)

    ty = CARD_TOP + 64
    for part, col in ((HEAD_KEY, ORANGE), (HEAD_REST, (255, 255, 255))):
        b = d.textbbox((0, 0), part, font=fh)
        d.text(((W - (b[2] - b[0])) // 2 - b[0], ty - b[1]), part, font=fh, fill=col)
        ty += 98

    x = (W - (total - 18)) // 2
    cy = CARD_TOP + 64 + 196
    for txt, col, w in chips:
        d.rounded_rectangle([x, cy + 6, x + w, cy + 70], radius=24, outline=col + (220,), width=2)
        b = d.textbbox((0, 0), txt, font=fc)
        d.text((x + (w - (b[2] - b[0])) // 2 - b[0], cy + 38 - (b[3] - b[1]) // 2 - b[1]),
               txt, font=fc, fill=col)
        x += w + 18

    d.rounded_rectangle([84, SCREEN_TOP, W - 84, SCREEN_BOT], radius=20,
                        outline=(120, 140, 200, 170), width=3)
    mid = (SCREEN_TOP + SCREEN_BOT) // 2 - 40
    for i, m in enumerate(["СЮДА ВСТАНЕТ ТВОЙ СКРИН", "настройки памяти Claude"]):
        f2 = fc if i == 0 else fp
        b = d.textbbox((0, 0), m, font=f2)
        d.text(((W - (b[2] - b[0])) // 2 - b[0], mid), m, font=f2,
               fill=(235, 242, 255) if i == 0 else (185, 200, 235))
        mid += 64
    return im


base = card()
for i in range(N):
    t = i / FPS
    if t < IN_T:
        dx = int(-W * (1 - t / IN_T) ** 3)
    elif t > DUR - OUT_T:
        dx = int(-W * ((t - (DUR - OUT_T)) / OUT_T) ** 2)
    else:
        dx = 0
    fr = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fr.paste(base, (dx, 0), base)
    fr.save(f"insseq/{i:04d}.png")

print(f"вставка: {N} кадров, карточка {CARD_TOP}-{CARD_BOT}, slide-in {IN_T}c / push-out {OUT_T}c")

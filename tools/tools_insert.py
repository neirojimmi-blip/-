"""Мокап-вставка по скиллу: тёмный градиент, заголовок с оранжевым ключевым
словом, чипы-теги, РЕАЛЬНЫЙ скрин крупно. Низ карточки не ниже 1450.
Вход push справа 0.30 c, выход влево 0.25 c. Без тряски.
Высота карточки подгоняется под скрин, заголовок ужимается под ширину.
"""
from PIL import Image, ImageDraw, ImageFont
import os

W, H = 1080, 1920
FPS = 30
F = "fonts/"
ORANGE, GREEN = (255, 117, 31), (63, 196, 140)
CARD_TOP, CARD_MAX_BOT = 150, 1440
IN_T, OUT_T = 0.30, 0.25
PAD = 40


def _fit_head(key, rest, maxw):
    for size in range(80, 30, -2):
        f = ImageFont.truetype(F + "Oswald-Bold.ttf", size)
        d = ImageDraw.Draw(Image.new("RGB", (8, 8)))
        w = d.textlength(key, font=f) + 20 + d.textlength(rest, font=f)
        if w <= maxw:
            return f, w
    return ImageFont.truetype(F + "Oswald-Bold.ttf", 32), maxw


def build(outdir, shot_path, key, rest, chips, dur=2.9):
    os.makedirs(outdir, exist_ok=True)
    N = int(dur * FPS)
    inner = W - 80 - PAD * 2
    fh, headw = _fit_head(key, rest, inner)
    fc = ImageFont.truetype(F + "Oswald-Bold.ttf", 36)

    shot = Image.open(shot_path).convert("RGB")
    sw = inner
    sh_h = int(shot.height * sw / shot.width)
    head_h = fh.size + 26
    chip_h = 62 + 26
    max_shot_h = CARD_MAX_BOT - (CARD_TOP + 56 + head_h + chip_h + 46)
    if sh_h > max_shot_h:
        sh_h = max_shot_h
        sw = int(shot.width * sh_h / shot.height)
    shot = shot.resize((sw, sh_h), Image.LANCZOS)

    card_bot = CARD_TOP + 56 + head_h + chip_h + sh_h + 46
    card_bot = min(card_bot, CARD_MAX_BOT)
    ch = card_bot - CARD_TOP

    base = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    g = Image.new("RGB", (1, ch))
    for y in range(ch):
        f = y / ch
        g.putpixel((0, y), (int(16 + (10 - 16) * f), int(26 + (15 - 26) * f), int(51 + (28 - 51) * f)))
    g = g.resize((W - 80, ch)).convert("RGBA")
    m = Image.new("L", (W - 80, ch), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, W - 81, ch - 1], radius=24, fill=255)
    base.paste(g, (40, CARD_TOP), m)

    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    cy = CARD_TOP + 56 + head_h
    chs, tot = [], 0
    for txt, col in chips:
        b = od.textbbox((0, 0), txt, font=fc)
        w = b[2] - b[0] + 46
        chs.append((txt, col, w))
        tot += w + 16
    x = (W - (tot - 16)) // 2
    for txt, col, w in chs:
        od.rounded_rectangle([x, cy, x + w, cy + 58], radius=24, fill=col + (52,))
        x += w + 16
    im = Image.alpha_composite(base, ov)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([40, CARD_TOP, W - 40, card_bot], radius=24, outline=(70, 88, 158, 160), width=2)

    ty = CARD_TOP + 56
    b1 = d.textbbox((0, 0), key, font=fh)
    b2 = d.textbbox((0, 0), rest, font=fh)
    sx = (W - headw) // 2
    d.text((sx - b1[0], ty - b1[1]), key, font=fh, fill=ORANGE)
    d.text((sx + (b1[2] - b1[0]) + 20 - b2[0], ty - b2[1]), rest, font=fh, fill=(255, 255, 255))

    x = (W - (tot - 16)) // 2
    for txt, col, w in chs:
        d.rounded_rectangle([x, cy, x + w, cy + 58], radius=24, outline=col + (220,), width=2)
        b = d.textbbox((0, 0), txt, font=fc)
        d.text((x + (w - (b[2] - b[0])) // 2 - b[0], cy + 29 - (b[3] - b[1]) // 2 - b[1]), txt, font=fc, fill=col)
        x += w + 16

    px, py = (W - sw) // 2, cy + chip_h
    sd = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sd).rounded_rectangle([px - 5, py - 5, px + sw + 5, py + sh_h + 5], radius=16, fill=(255, 255, 255, 240))
    im = Image.alpha_composite(im, sd)
    im.paste(shot, (px, py))
    ImageDraw.Draw(im).rounded_rectangle([px - 5, py - 5, px + sw + 5, py + sh_h + 5], radius=16,
                                         outline=(120, 140, 200, 200), width=3)

    for i in range(N):
        t = i / FPS
        if t < IN_T:
            dx = int(W * (1 - t / IN_T) ** 3)
        elif t > dur - OUT_T:
            dx = int(-W * ((t - (dur - OUT_T)) / OUT_T) ** 2)
        else:
            dx = 0
        fr = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        fr.paste(im, (dx, 0), im)
        fr.save(f"{outdir}/{i:04d}.png")
    return N, card_bot

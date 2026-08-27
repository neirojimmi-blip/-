"""Полноэкранная вставка по скиллу.

Лицо не перекрывается вообще: карточка занимает весь кадр, героиня в это
время не видна. Низ до 1560 оставлен пустым - там субтитры и ник-бейдж,
они остаются читаемыми поверх вставки.
Вход zoom-in, выход - короткое затухание. Без тряски.
"""
from PIL import Image, ImageDraw, ImageFont
import os

W, H = 1080, 1920
FPS = 30
F = "fonts/"
ORANGE, GREEN = (255, 117, 31), (63, 196, 140)
SAFE_BOT = 1560          # ниже - зона субтитров и бейджа
CONTENT_TOP = 330


def bg_card(key, rest, chips):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    g = Image.new("RGB", (1, H))
    for y in range(H):
        f = y / H
        g.putpixel((0, y), (int(16 + (10 - 16) * f), int(26 + (15 - 26) * f), int(51 + (28 - 51) * f)))
    im.paste(g.resize((W, H)).convert("RGBA"), (0, 0))
    d = ImageDraw.Draw(im)

    for size in range(78, 30, -2):
        fh = ImageFont.truetype(F + "Oswald-Bold.ttf", size)
        w = d.textlength(key, font=fh) + 20 + d.textlength(rest, font=fh)
        if w <= W - 110:
            break
    b1 = d.textbbox((0, 0), key, font=fh)
    b2 = d.textbbox((0, 0), rest, font=fh)
    tw = (b1[2] - b1[0]) + 20 + (b2[2] - b2[0])
    sx, ty = (W - tw) // 2, 132
    d.text((sx - b1[0], ty - b1[1]), key, font=fh, fill=ORANGE)
    d.text((sx + (b1[2] - b1[0]) + 20 - b2[0], ty - b2[1]), rest, font=fh, fill=(255, 255, 255))

    fc = ImageFont.truetype(F + "Oswald-Bold.ttf", 36)
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    cy = 240
    chs, tot = [], 0
    for txt, col in chips:
        bb = od.textbbox((0, 0), txt, font=fc)
        w = bb[2] - bb[0] + 46
        chs.append((txt, col, w))
        tot += w + 16
    x = (W - (tot - 16)) // 2
    for txt, col, w in chs:
        od.rounded_rectangle([x, cy, x + w, cy + 58], radius=24, fill=col + (52,))
        x += w + 16
    im = Image.alpha_composite(im, ov)
    d = ImageDraw.Draw(im)
    x = (W - (tot - 16)) // 2
    for txt, col, w in chs:
        d.rounded_rectangle([x, cy, x + w, cy + 58], radius=24, outline=col + (225,), width=2)
        bb = d.textbbox((0, 0), txt, font=fc)
        d.text((x + (w - (bb[2] - bb[0])) // 2 - bb[0], cy + 29 - (bb[3] - bb[1]) // 2 - bb[1]),
               txt, font=fc, fill=col)
        x += w + 16
    return im


def place(im, shot_path):
    """Вписывает реальный скрин в свободную зону, крупно."""
    box_w, box_h = W - 120, SAFE_BOT - CONTENT_TOP
    sh = Image.open(shot_path).convert("RGB")
    sc = min(box_w / sh.width, box_h / sh.height)
    sh = sh.resize((int(sh.width * sc), int(sh.height * sc)), Image.LANCZOS)
    px, py = (W - sh.width) // 2, CONTENT_TOP + (box_h - sh.height) // 2
    fr = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(fr).rounded_rectangle([px - 6, py - 6, px + sh.width + 6, py + sh.height + 6],
                                         radius=18, fill=(255, 255, 255, 245))
    out = Image.alpha_composite(im, fr)
    out.paste(sh, (px, py))
    ImageDraw.Draw(out).rounded_rectangle([px - 6, py - 6, px + sh.width + 6, py + sh.height + 6],
                                          radius=18, outline=(120, 140, 200, 210), width=3)
    return out


def build(outdir, shot_path, key, rest, chips, dur=2.9):
    os.makedirs(outdir, exist_ok=True)
    N = int(dur * FPS)
    card = place(bg_card(key, rest, chips), shot_path)
    for i in range(N):
        t = i / FPS
        z = 1.0
        if i < 10:
            z = 1.28 + (1.0 - 1.28) * (i / 10)      # zoom-in по скиллу
        fr = card
        if z != 1.0:
            nw, nh = int(W * z), int(H * z)
            fr = card.resize((nw, nh), Image.LANCZOS).crop(
                ((nw - W) // 2, (nh - H) // 2, (nw - W) // 2 + W, (nh - H) // 2 + H))
        a = 255
        if t < 0.10:
            a = int(255 * t / 0.10)
        elif t > dur - 0.18:
            a = int(255 * max(0, (dur - t) / 0.18))
        if a < 255:
            fr = fr.copy()
            fr.putalpha(a)
        fr.save(f"{outdir}/{i:04d}.png")
    return N

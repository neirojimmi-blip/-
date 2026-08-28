"""Плашки с текстом по сценарию про десктопный ChatGPT.

Каждая — короткая последовательность с появлением и уходом,
в фирменной палитре, в нижней трети, чтобы не закрывать лицо.
"""
from PIL import Image, ImageDraw, ImageFont
import os

W, H = 1080, 1920
FPS = 30
F = "fonts/"
ORANGE = (255, 117, 31)
NAVY = (46, 64, 120)
CY = 1330                      # нижняя треть, выше зоны субтитров


def fit(fname, text, target, lo=28, hi=110):
    while lo < hi:
        m = (lo + hi + 1) // 2
        f = ImageFont.truetype(F + fname, m)
        if ImageFont.truetype(F + fname, m).getlength(text) <= target:
            lo = m
        else:
            hi = m - 1
    return ImageFont.truetype(F + fname, lo)


def build(outdir, text, dur=3.0, accent=None, plate=True):
    os.makedirs(outdir, exist_ok=True)
    N = int(dur * FPS)
    f = fit("Montserrat-700.ttf", text, int(W * 0.82))
    d0 = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    tw = d0.textlength(text, font=f)
    bb = d0.textbbox((0, 0), text, font=f)
    th = bb[3] - bb[1]
    for i in range(N):
        t = i / FPS
        a = 1.0
        if t < 0.22:
            a = t / 0.22
        elif t > dur - 0.28:
            a = max(0.0, (dur - t) / 0.28)
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        if a <= 0:
            im.save(f"{outdir}/{i:04d}.png")
            continue
        A = int(255 * a)
        d = ImageDraw.Draw(im)
        y0 = CY - th // 2 - 30
        if plate:
            ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(ov).rounded_rectangle(
                [(W - tw) / 2 - 44, y0 - 16, (W + tw) / 2 + 44, y0 + th + 46],
                radius=24, fill=(10, 16, 40, int(212 * a)))
            im = Image.alpha_composite(im, ov)
            d = ImageDraw.Draw(im)
        x = (W - tw) / 2
        parts = ([(text, (255, 255, 255))] if not (accent and accent in text)
                 else [(p, c) for p, c in zip(text.split(accent, 1)[:1]
                                              + [accent] + text.split(accent, 1)[1:],
                                              ((255, 255, 255), ORANGE, (255, 255, 255)))
                       if p])

        # тень — отдельным слоем: полупрозрачный текст поверх подложки
        # затирал бы её альфу и пробивал дыру до фона
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ds = ImageDraw.Draw(sh)
        xs = x
        for part, _ in parts:
            ds.text((xs + 2, y0 - bb[1] + 18), part, font=f, fill=(8, 12, 30, int(150 * a)))
            xs += ds.textlength(part, font=f)
        im = Image.alpha_composite(im, sh)
        d = ImageDraw.Draw(im)

        for part, col in parts:
            d.text((x, y0 - bb[1] + 16), part, font=f, fill=col + (A,))
            x += d.textlength(part, font=f)
        im.save(f"{outdir}/{i:04d}.png")
    return N, f.size


TITLES = [
    # длительность подогнана под фразу в озвучке, чтобы плашки не наезжали
    ("t_hook",   "Я УДАЛИЛА CHATGPT ИЗ БРАУЗЕРА", 3.0, "CHATGPT"),
    ("t_before", "ИИ ОБЪЯСНЯЕТ → ТЫ ДЕЛАЕШЬ",      3.6, "ТЫ ДЕЛАЕШЬ"),
    ("t_after",  "ИИ ДЕЛАЕТ → ТЫ ПРОВЕРЯЕШЬ",      2.3, "ИИ ДЕЛАЕТ"),
    ("t_brow",   "САМ РАБОТАЕТ В БРАУЗЕРЕ",        4.4, "САМ"),
    ("t_plug",   "GOOGLE DRIVE → ТАБЛИЦА → CANVA", 3.6, None),
    ("t_out",    "ТЫ СТАВИШЬ ЗАДАЧУ. АГЕНТ ДЕЛАЕТ.", 4.2, "АГЕНТ ДЕЛАЕТ."),
]
for name, txt, dur, acc in TITLES:
    n, sz = build(name, txt, dur, acc)
    print(f"{name}: {n} кадров, {sz}px — {txt}")

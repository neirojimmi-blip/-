"""Хук по скиллу xeniia-reel-style.

Тёмная компактная плашка на уровне груди, лицо полностью открыто:
без тинта, без размытия кадра, без часов. Печать по буквам с курсором.
Звук печати НЕ добавляется - синтетические клики забракованы дважды.
"""
from PIL import Image, ImageDraw, ImageFont
import os

W, H = 1080, 1920
FPS = 30
DUR = 4.30
N = int(DUR * FPS)
F = "fonts/"

CAPS = ["5 ФУНКЦИЙ CLAUDE", "О КОТОРЫХ МОЛЧАТ"]
CHAR, GAP, START = 0.022, 0.12, 0.35
FADE_START, FADE_END = 3.85, 4.20

PLATE_RGBA = (8, 12, 24, int(255 * 0.58))
RADIUS = 30
PLATE_CY = 1060                      # уровень груди, лицо занимает ~290-670
TRACK = 7                            # разрядка 6-9 px по скиллу
SIZE = 63

font = ImageFont.truetype(F + "Montserrat-500.ttf", SIZE)
os.makedirs("hookseq", exist_ok=True)


def measure(s):
    d = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    return sum(d.textlength(c, font=font) + TRACK for c in s) - TRACK if s else 0


line_w = [measure(s) for s in CAPS]
LH = int(SIZE * 1.42)
pad_x, pad_y = 52, 34
plate_w = int(max(line_w) + pad_x * 2)
plate_h = int(LH * len(CAPS) + pad_y * 2)
plate_x = (W - plate_w) // 2
plate_y = PLATE_CY - plate_h // 2

starts = []
t0 = START
for s in CAPS:
    starts.append(t0)
    t0 += len(s) * CHAR + GAP


def draw_tracked(d, s, cx, y, alpha):
    x = cx - measure(s) / 2
    for c in s:
        d.text((x, y), c, font=font, fill=(255, 255, 255, alpha))
        x += d.textlength(c, font=font) + TRACK
    return x


for i in range(N):
    t = i / FPS
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    if t < FADE_START:
        a = 1.0
    elif t < FADE_END:
        a = 1 - (t - FADE_START) / (FADE_END - FADE_START)
    else:
        a = 0.0
    if a <= 0:
        im.save(f"hookseq/{i:04d}.png")
        continue

    # плашка появляется вместе с первой буквой
    if t >= START:
        pa = int(PLATE_RGBA[3] * a * min((t - START) / 0.18, 1))
        d.rounded_rectangle([plate_x, plate_y, plate_x + plate_w, plate_y + plate_h],
                            radius=RADIUS, fill=PLATE_RGBA[:3] + (pa,))

    alpha = int(255 * a)
    cur_x = cur_y = None
    for li, s in enumerate(CAPS):
        shown = int(max(0, (t - starts[li]) / CHAR))
        if shown <= 0:
            continue
        txt = s[:shown]
        y = plate_y + pad_y + li * LH
        endx = draw_tracked(d, txt, W // 2, y, alpha)
        if shown < len(s):
            cur_x, cur_y = endx, y
        elif li == len(CAPS) - 1:
            cur_x, cur_y = endx, y

    # курсор-палочка
    if cur_x is not None and t < FADE_START and int(t * 2.2) % 2 == 0:
        d.rectangle([cur_x + 4, cur_y + 8, cur_x + 10, cur_y + SIZE + 4],
                    fill=(255, 255, 255, alpha))

    im.save(f"hookseq/{i:04d}.png")

print(f"кадров {N} | плашка {plate_w}x{plate_h} @ y={plate_y}..{plate_y+plate_h} | лицо ~290-670 -> не пересекается")
print(f"печать: строки стартуют на {[round(s,3) for s in starts]}, фейд {FADE_START}-{FADE_END}")

"""Вставки к ролику про доступ к рабочей среде.

Это схемы, а не скриншоты чужого интерфейса: рисовать поддельные экраны
продукта нельзя. Кодовые слова во второй карточке — настоящие, из активных
автоворонок аккаунта (Chatplace, бот @xeniia_neuro).

Вставка занимает весь кадр: по правилу пользователя плашка либо
полноэкранная, либо внизу — частично перекрывать лицо нельзя.
Содержимое не опускается ниже 1450, там зона субтитров.

Оформление: тёплое свечение из центра, виньетка, надзаголовок вразрядку,
линия под заголовком прочерчивается, строки выезжают по очереди снизу.
Статика рисуется один раз, по кадрам двигаются только плитки — иначе
полноразмерный рендер каждого кадра считается слишком долго.

Полупрозрачные фигуры — только отдельным слоем: ImageDraw с alpha-заливкой
заменяет альфу, а не смешивает, и пробивает дыру в подложке.
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
import os

W, H = 1080, 1920
FPS = 30
F = "fonts/"
ORANGE, GREEN = (255, 117, 31), (63, 196, 140)
CENTER_Y = 780
IN_T, OUT_T = 0.30, 0.26
STAGGER = 0.09

fe = ImageFont.truetype(F + "Montserrat-500.ttf", 34)
fh = ImageFont.truetype(F + "Oswald-Bold.ttf", 84)
fr = ImageFont.truetype(F + "Oswald-Bold.ttf", 46)
fnum = ImageFont.truetype(F + "Oswald-Bold.ttf", 34)
fc = ImageFont.truetype(F + "Oswald-Bold.ttf", 40)
fn = ImageFont.truetype(F + "Montserrat-500.ttf", 32)

_m = ImageDraw.Draw(Image.new("RGB", (8, 8)))


def ease_out(x):
    return 1 - (1 - x) ** 3


def wrap(text, font, maxw):
    out, line = [], ""
    for w in text.split():
        t = (line + " " + w).strip()
        if _m.textlength(t, font=font) <= maxw:
            line = t
        else:
            out.append(line)
            line = w
    if line:
        out.append(line)
    return out


def background():
    """Градиент + тёплое свечение из центра + виньетка."""
    y = np.linspace(0, 1, H)[:, None]
    base = np.stack([16 + (10 - 16) * y, 26 + (15 - 26) * y, 51 + (28 - 51) * y], -1)
    base = np.repeat(base, W, axis=1)

    yy, xx = np.mgrid[0:H, 0:W]
    r = np.hypot((xx - W / 2) / (W * 0.95), (yy - CENTER_Y) / (H * 0.52))
    glow = np.clip(1 - r, 0, 1) ** 2.4
    base += glow[..., None] * np.array([46, 22, 6])

    vign = np.clip(np.hypot((xx - W / 2) / (W * 0.72),
                            (yy - H / 2) / (H * 0.72)) - 0.62, 0, 1) ** 1.6
    base *= (1 - 0.55 * vign)[..., None]
    return Image.fromarray(np.clip(base, 0, 255).astype("uint8")).convert("RGBA")


BG = background()


def tile_row(idx, txt, col, width):
    """Плитка строки схемы: номер, подложка, рамка, текст."""
    h = 96
    im = Image.new("RGBA", (width, h), (0, 0, 0, 0))
    ov = Image.new("RGBA", (width, h), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    od.rounded_rectangle([0, 0, width - 1, h - 1], radius=22, fill=col + (44,))
    od.rounded_rectangle([0, 0, width - 1, h - 1], radius=22, outline=col + (200,), width=3)
    od.rounded_rectangle([18, 22, 70, 74], radius=14, fill=col + (70,))
    im = Image.alpha_composite(im, ov)
    d = ImageDraw.Draw(im)
    n = str(idx)
    b = d.textbbox((0, 0), n, font=fnum)
    d.text((44 - (b[2] - b[0]) / 2 - b[0], 48 - (b[3] - b[1]) / 2 - b[1]), n,
           font=fnum, fill=col)
    b = d.textbbox((0, 0), txt, font=fr)
    d.text((94 + (width - 94 - (b[2] - b[0])) / 2 - b[0], 48 - (b[3] - b[1]) / 2 - b[1]),
           txt, font=fr, fill=(255, 255, 255))
    return im


def tile_chip(txt, col):
    b = _m.textbbox((0, 0), txt, font=fc)
    w, h = b[2] - b[0] + 58, 78
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ov = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    od.rounded_rectangle([0, 0, w - 1, h - 1], radius=26, fill=col + (50,))
    od.rounded_rectangle([0, 0, w - 1, h - 1], radius=26, outline=col + (180,), width=2)
    im = Image.alpha_composite(im, ov)
    d = ImageDraw.Draw(im)
    d.text(((w - (b[2] - b[0])) / 2 - b[0], (h - (b[3] - b[1])) / 2 - b[1]), txt,
           font=fc, fill=(255, 255, 255))
    return im


def track(d, text, font, y, fill, tr=8):
    total = sum(d.textlength(c, font=font) + tr for c in text) - tr
    x = (W - total) / 2
    for c in text:
        d.text((x, y), c, font=font, fill=fill)
        x += d.textlength(c, font=font) + tr


def build(name, dur, eyebrow, head, key, rows=None, chips=None, note=None):
    os.makedirs(name, exist_ok=True)
    n = int(dur * FPS)
    head_lines = wrap(head, fh, W - 200)
    note_lines = wrap(note, fn, W - 220) if note else []

    row_tiles, chip_lines = [], []
    if rows:
        rw = 700
        row_tiles = [tile_row(i + 1, t, c, rw) for i, (t, c) in enumerate(rows)]
    if chips:
        tiles = [tile_chip(t, c) for t, c in chips]
        cur, wsum = [], 0
        for tl in tiles:
            if wsum + tl.width + 16 > W - 150 and cur:
                chip_lines.append((cur, wsum - 16))
                cur, wsum = [], 0
            cur.append(tl)
            wsum += tl.width + 16
        if cur:
            chip_lines.append((cur, wsum - 16))

    body_h = 0
    if row_tiles:
        body_h = 96 * len(row_tiles) + 58 * (len(row_tiles) - 1)
    if chip_lines:
        body_h = sum(l[0][0].height + 18 for l in chip_lines) - 18
    head_h = 46 + 22 + 96 * len(head_lines) + 30
    note_h = (24 + 44 * len(note_lines)) if note_lines else 0
    total_h = head_h + 34 + body_h + note_h
    top = int(CENTER_Y - total_h / 2)
    if top + total_h > 1420:
        top = 1420 - total_h
    top = max(150, top)

    # статика: фон, надзаголовок, заголовок
    static = BG.copy()
    d = ImageDraw.Draw(static)
    track(d, eyebrow, fe, top, (150, 168, 210))
    y = top + 46 + 22
    for line in head_lines:
        seg = [(w, ORANGE if w in key.split() else (255, 255, 255),
                d.textlength(w + " ", font=fh)) for w in line.split()]
        x = (W - sum(s[2] for s in seg)) / 2
        for word, col, wd in seg:
            d.text((x, y), word, font=fh, fill=col)
            x += wd
        y += 96
    rule_y = y + 16
    body_y = top + head_h + 34

    for i in range(n):
        t = i / FPS
        fr_im = static.copy()
        d = ImageDraw.Draw(fr_im)

        # линия под заголовком прочерчивается
        p = min(max((t - 0.16) / 0.34, 0), 1)
        if p > 0:
            half = 210 * ease_out(p)
            d.rounded_rectangle([W / 2 - half, rule_y, W / 2 + half, rule_y + 5],
                                radius=3, fill=ORANGE)

        y = body_y
        k = 0
        for j, tl in enumerate(row_tiles):
            a = min(max((t - (0.30 + j * STAGGER)) / 0.26, 0), 1)
            if a > 0:
                e = ease_out(a)
                lay = tl.copy()
                lay.putalpha(lay.split()[3].point(lambda v: int(v * e)))
                fr_im.alpha_composite(lay, (int((W - tl.width) / 2),
                                            int(y + 26 * (1 - e))))
            y += 96
            if j < len(row_tiles) - 1:
                if a >= 1:
                    d.polygon([(W / 2 - 18, y + 12), (W / 2 + 18, y + 12),
                               (W / 2, y + 42)], fill=ORANGE)
                y += 58
            k += 1

        for line, lw in chip_lines:
            x = (W - lw) / 2
            for tl in line:
                a = min(max((t - (0.30 + k * STAGGER)) / 0.26, 0), 1)
                if a > 0:
                    e = ease_out(a)
                    lay = tl.copy()
                    lay.putalpha(lay.split()[3].point(lambda v: int(v * e)))
                    fr_im.alpha_composite(lay, (int(x), int(y + 22 * (1 - e))))
                x += tl.width + 16
                k += 1
            y += line[0].height + 18

        if note_lines:
            a = min(max((t - (0.30 + k * STAGGER)) / 0.3, 0), 1)
            yy = y + 24
            for ln in note_lines:
                b = d.textbbox((0, 0), ln, font=fn)
                d.text(((W - (b[2] - b[0])) / 2 - b[0], yy - b[1]), ln, font=fn,
                       fill=tuple(int(c * a) + int(20 * (1 - a)) for c in (150, 168, 210)))
                yy += 44

        if t < IN_T:
            dx = -W * (1 - ease_out(t / IN_T))
        elif t > dur - OUT_T:
            dx = -W * ease_out((t - (dur - OUT_T)) / OUT_T)
        else:
            dx = 0
        if dx:
            shifted = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            shifted.paste(fr_im, (int(dx), 0))
            fr_im = shifted
        fr_im.convert("RGBA").save(f"{name}/{i:04d}.png")
    print(f"{name}: {n} кадров, {dur} с, блок {top}..{top+total_h}")


CODES = ["ИНСТРУКЦИЯ", "КУРС", "МОНТАЖ", "АГЕНТ", "КАЛЕНДАРЬ", "СКИЛЛ",
         "АНАЛИЗ", "ПОРТРЕТ", "СОВЕТ", "ДНЕВНИК"]

build("n3/ins_conn", 3.70, "КАК ЭТО УСТРОЕНО", "ДОСТУП К РАБОЧЕЙ СРЕДЕ", "ДОСТУП",
      rows=[("ВАША ЯЗЫКОВАЯ МОДЕЛЬ", ORANGE),
            ("CHATPLACE", GREEN),
            ("ДИРЕКТ И КОММЕНТАРИИ", ORANGE)])

build("n3/ins_code", 3.30, "ЖИВЫЕ ВОРОНКИ АККАУНТА", "КОДОВОЕ СЛОВО ПОД РИЛС",
      "КОДОВОЕ СЛОВО",
      chips=[(c, ORANGE if i % 2 == 0 else GREEN) for i, c in enumerate(CODES)],
      note="20 активных автоворонок @xeniia_neuro")

build("n3/ins_funnel", 3.70, "ЧТО ДЕЛАЕТ БОТ", "ВЕДЁТ ДО ЗАЯВКИ САМ", "ЗАЯВКИ",
      rows=[("ОТВЕТ НА КОДОВОЕ СЛОВО", GREEN),
            ("МАТЕРИАЛЫ И ИНСТРУКЦИИ", ORANGE),
            ("НАПОМИНАНИЯ", GREEN),
            ("ЗАЯВКА", ORANGE)])

build("n3/ins_auto", 4.50, "И ЭТО ТОЖЕ НЕ ВРУЧНУЮ", "ВОРОНКУ МОДЕЛЬ ПРОПИШЕТ САМА",
      "САМА",
      rows=[("СЦЕНАРИЙ ШАГОВ", ORANGE),
            ("ТЕКСТЫ СООБЩЕНИЙ", GREEN),
            ("КНОПКИ И УСЛОВИЯ", ORANGE)])

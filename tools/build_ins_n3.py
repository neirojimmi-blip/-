"""Вставки к ролику про доступ к рабочей среде.

Это схемы, а не скриншоты чужого интерфейса: рисовать поддельные экраны
продукта нельзя. Кодовые слова во второй карточке — настоящие, из активных
автоворонок аккаунта (Chatplace, бот @xeniia_neuro).

Вставка занимает весь кадр: по правилу пользователя плашка либо
полноэкранная, либо внизу — частично перекрывать лицо нельзя.
Содержимое центруется и не опускается ниже 1450, там зона субтитров.

Полупрозрачные фигуры — только отдельным слоем: ImageDraw с alpha-заливкой
заменяет альфу, а не смешивает, и пробивает дыру в карточке.
"""
from PIL import Image, ImageDraw, ImageFont
import os

W, H = 1080, 1920
FPS = 30
F = "fonts/"
ORANGE, GREEN = (255, 117, 31), (63, 196, 140)
CW = W - 80                 # ширина карточки
CENTER_Y = 760              # центр карточки: ниже лица, выше субтитров
PAD_TOP, PAD_BOT = 78, 70
IN_T, OUT_T = 0.28, 0.25

fh = ImageFont.truetype(F + "Oswald-Bold.ttf", 84)
fr = ImageFont.truetype(F + "Oswald-Bold.ttf", 46)
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


def chip_rows(chips):
    rows, cur, wsum = [], [], 0
    for txt, col in chips:
        b = _m.textbbox((0, 0), txt, font=fc)
        cw = b[2] - b[0] + 54
        if wsum + cw + 16 > CW - 80 and cur:
            rows.append((cur, wsum))
            cur, wsum = [], 0
        cur.append((txt, col, cw))
        wsum += cw + 16
    if cur:
        rows.append((cur, wsum))
    return rows


def build(name, dur, head, key, rows=None, chips=None, note=None):
    os.makedirs(name, exist_ok=True)
    n = int(dur * FPS)

    head_lines = wrap(head, fh, CW - 120)
    note_lines = wrap(note, fn, CW - 140) if note else []
    crows = chip_rows(chips) if chips else []

    h = PAD_TOP + 96 * len(head_lines) + 46
    if rows:
        h += 96 * len(rows) + 66 * (len(rows) - 1)
    if crows:
        h += 92 * len(crows)
    if note_lines:
        h += 20 + 44 * len(note_lines)
    h += PAD_BOT

    top = max(150, int(CENTER_Y - h / 2))
    if top + h > 1400:
        top = 1400 - h

    # фон на весь кадр: частичная плашка закрывала бы лицо
    g = Image.new("RGB", (1, H))
    for y in range(H):
        f = y / H
        g.putpixel((0, y), (int(16 + (10 - 16) * f), int(26 + (15 - 26) * f),
                            int(51 + (28 - 51) * f)))
    card = g.resize((W, H)).convert("RGBA")

    # 1) полупрозрачные подложки — отдельным слоем
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    y = top + PAD_TOP + 96 * len(head_lines) + 46
    if rows:
        for i, (txt, col) in enumerate(rows):
            bw = max(_m.textlength(txt, font=fr) + 96, 520)
            x0 = (W - bw) / 2
            od.rounded_rectangle([x0, y, x0 + bw, y + 96], radius=22, fill=col + (46,))
            od.rounded_rectangle([x0, y, x0 + bw, y + 96], radius=22,
                                 outline=col + (190,), width=3)
            y += 96
            if i < len(rows) - 1:
                od.polygon([(W / 2 - 20, y + 16), (W / 2 + 20, y + 16), (W / 2, y + 48)],
                           fill=ORANGE + (205,))
                y += 66
    for row, wsum in crows:
        x = (W - (wsum - 16)) / 2
        for txt, col, cw in row:
            od.rounded_rectangle([x, y, x + cw, y + 74], radius=24, fill=col + (52,))
            od.rounded_rectangle([x, y, x + cw, y + 74], radius=24,
                                 outline=col + (170,), width=2)
            x += cw + 16
        y += 92

    card = Image.alpha_composite(card, ov)
    d = ImageDraw.Draw(card)

    # 2) текст поверх — непрозрачный
    y = top + PAD_TOP
    for line in head_lines:
        seg = [(w, ORANGE if w in key.split() else (255, 255, 255),
                d.textlength(w + " ", font=fh)) for w in line.split()]
        x = (W - sum(s[2] for s in seg)) / 2
        for word, col, wd in seg:
            d.text((x, y), word, font=fh, fill=col)
            x += wd
        y += 96
    y += 46
    if rows:
        for i, (txt, col) in enumerate(rows):
            b = d.textbbox((0, 0), txt, font=fr)
            d.text(((W - (b[2] - b[0])) / 2 - b[0], y + 48 - (b[3] - b[1]) / 2 - b[1]),
                   txt, font=fr, fill=(255, 255, 255))
            y += 96 + (66 if i < len(rows) - 1 else 0)
    for row, wsum in crows:
        x = (W - (wsum - 16)) / 2
        for txt, col, cw in row:
            b = d.textbbox((0, 0), txt, font=fc)
            d.text((x + (cw - (b[2] - b[0])) / 2 - b[0], y + 37 - (b[3] - b[1]) / 2 - b[1]),
                   txt, font=fc, fill=(255, 255, 255))
            x += cw + 16
        y += 92
    if note_lines:
        y += 20
        for line in note_lines:
            b = d.textbbox((0, 0), line, font=fn)
            d.text(((W - (b[2] - b[0])) / 2 - b[0], y - b[1]), line, font=fn,
                   fill=(150, 168, 210))
            y += 44

    for i in range(n):
        t = i / FPS
        if t < IN_T:
            dx = -W * (1 - ease_out(t / IN_T))
        elif t > dur - OUT_T:
            dx = -W * ease_out((t - (dur - OUT_T)) / OUT_T)
        else:
            dx = 0
        f = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        f.paste(card, (int(dx), 0))
        f.save(f"{name}/{i:04d}.png")
    print(f"{name}: {n} кадров, {dur} с, содержимое {top}..{top+h}")


CODES = ["ИНСТРУКЦИЯ", "КУРС", "МОНТАЖ", "АГЕНТ", "КАЛЕНДАРЬ", "СКИЛЛ",
         "АНАЛИЗ", "ПОРТРЕТ", "СОВЕТ", "ДНЕВНИК"]

build("n3/ins_conn", 3.70, "ДОСТУП К РАБОЧЕЙ СРЕДЕ", "ДОСТУП",
      rows=[("ВАША ЯЗЫКОВАЯ МОДЕЛЬ", ORANGE),
            ("CHATPLACE", GREEN),
            ("ДИРЕКТ И КОММЕНТАРИИ", ORANGE)])

build("n3/ins_code", 3.30, "КОДОВОЕ СЛОВО ПОД РИЛС", "КОДОВОЕ СЛОВО",
      chips=[(c, ORANGE if i % 2 == 0 else GREEN) for i, c in enumerate(CODES)],
      note="20 активных автоворонок аккаунта @xeniia_neuro")

build("n3/ins_funnel", 3.70, "ВЕДЁТ ДО ЗАЯВКИ САМ", "ЗАЯВКИ",
      rows=[("ОТВЕТ НА КОДОВОЕ СЛОВО", GREEN),
            ("МАТЕРИАЛЫ И ИНСТРУКЦИИ", ORANGE),
            ("НАПОМИНАНИЯ", GREEN),
            ("ЗАЯВКА", ORANGE)])

build("n3/ins_auto", 4.50, "ВОРОНКУ МОДЕЛЬ ПРОПИШЕТ САМА", "САМА",
      rows=[("СЦЕНАРИЙ ШАГОВ", ORANGE),
            ("ТЕКСТЫ СООБЩЕНИЙ", GREEN),
            ("КНОПКИ И УСЛОВИЯ", ORANGE)])

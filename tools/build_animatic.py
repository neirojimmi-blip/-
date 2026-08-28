"""Раскадровка рилса про десктопный ChatGPT — немой ролик под готовую озвучку.

Показывает, что происходит в каждую секунду: где ты в кадре, где идёт запись
экрана (с номером и длиной), где всплывают плашки. Нужна, чтобы снимать экраны
под уже готовый хронометраж, а не подгонять потом.
"""
from PIL import Image, ImageDraw, ImageFont
import json, os, math

W, H, FPS = 1080, 1920, 30
F = "fonts/"
ORANGE = (255, 117, 31)
NAVY = (46, 64, 120)

edl = json.load(open("reelb_edl.json"))
TL = json.load(open("timing_b.json"))
SPEECH = edl["avatar_duration"]
TOTAL = SPEECH + edl["endcard"]["dur"]
N = int(TOTAL * FPS)

f_big = ImageFont.truetype(F + "Montserrat-700.ttf", 150)
f_lbl = ImageFont.truetype(F + "Montserrat-700.ttf", 54)
f_txt = ImageFont.truetype(F + "Montserrat-500.ttf", 40)
f_sm = ImageFont.truetype(F + "Montserrat-500.ttf", 34)
f_tc = ImageFont.truetype(F + "Montserrat-500.ttf", 38)


def grad(c0, c1):
    g = Image.new("RGB", (1, H))
    for y in range(H):
        k = y / H
        g.putpixel((0, y), tuple(int(a + (b - a) * k) for a, b in zip(c0, c1)))
    return g.resize((W, H)).convert("RGBA")


BG_FACE = grad((46, 64, 120), (20, 28, 51))
BG_REC = grad((16, 22, 46), (8, 12, 26))


def over(im, draw_fn):
    """Полупрозрачные фигуры — только отдельным слоем: ImageDraw с RGBA-заливкой
    затирает альфу основы, а не смешивается с ней."""
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(lay))
    return Image.alpha_composite(im, lay)


def wrap(d, text, font, maxw):
    out, line = [], ""
    for w in text.split():
        t = (line + " " + w).strip()
        if d.textlength(t, font=font) <= maxw:
            line = t
        else:
            out.append(line)
            line = w
    if line:
        out.append(line)
    return out


def centered(d, lines, font, y, fill, gap=12):
    for ln in lines:
        b = d.textbbox((0, 0), ln, font=font)
        d.text(((W - (b[2] - b[0])) // 2 - b[0], y - b[1]), ln, font=font, fill=fill)
        y += (b[3] - b[1]) + gap
    return y


seqs = {t["seq"]: t for t in edl["titles"]}
cache = {}


def title_frame(seq, idx):
    key = (seq, idx)
    if key not in cache:
        p = f"{seq}/{idx:04d}.png"
        cache[key] = Image.open(p).convert("RGBA") if os.path.exists(p) else None
        if len(cache) > 8:
            cache.pop(next(iter(cache)))
    return cache[key]


os.makedirs("anim", exist_ok=True)
end0 = SPEECH

for i in range(N):
    t = i / FPS

    # --- финальная карточка ---
    if t >= end0:
        k = int((t - end0) * FPS)
        p = f"finb/{k:04d}.png"
        if os.path.exists(p):
            Image.open(p).convert("RGB").save(f"anim/{i:04d}.png")
            continue

    ins = next((x for x in edl["inserts"] if x["at"] <= t < x["at"] + x["dur"]), None)
    im = (BG_REC if ins else BG_FACE).copy()
    d = ImageDraw.Draw(im)

    if ins:
        # рамка записи экрана
        d.rounded_rectangle([54, 300, W - 54, 1500], radius=28,
                            outline=ORANGE + (200,), width=5)
        lab = f"ЗАПИСЬ {ins['n']}"
        b = d.textbbox((0, 0), lab, font=f_big)
        d.text(((W - (b[2] - b[0])) // 2 - b[0], 470 - b[1]), lab, font=f_big, fill=ORANGE)
        y = centered(d, wrap(d, ins["note"].upper(), f_lbl, W - 220), f_lbl, 720,
                     (255, 255, 255), 16)
        y = centered(d, [f"В МОНТАЖЕ {ins['dur']:.1f} С · СНЯТЬ {ins['shoot']} С"],
                     f_txt, y + 46, (170, 186, 224))
        # шкала длины врезки; подложка полупрозрачная, поэтому отдельным слоем
        p = (t - ins["at"]) / ins["dur"]
        im = over(im, lambda dd: dd.rounded_rectangle(
            [180, 1320, W - 180, 1348], radius=14, fill=(255, 255, 255, 40)))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle([180, 1320, 180 + (W - 360) * p, 1348], radius=14, fill=ORANGE)
    else:
        # кадр с аватаром — силуэт-заглушка, всё полупрозрачное
        cx, cy = W // 2, 760

        def silhouette(dd):
            dd.ellipse([cx - 210, cy - 210, cx + 210, cy + 210], fill=(255, 255, 255, 16))
            dd.ellipse([cx - 66, cy - 96, cx + 66, cy + 36], fill=(255, 255, 255, 54))
            dd.pieslice([cx - 140, cy + 46, cx + 140, cy + 320], 180, 360,
                        fill=(255, 255, 255, 54))

        im = over(im, silhouette)
        d = ImageDraw.Draw(im)
        centered(d, ["ТЫ В КАДРЕ", "ОЗВУЧКА С АВАТАРА HEYGEN"], f_txt, 1050,
                 (176, 192, 230), 14)

    # текущая реплика — сверху, чтобы было слышно глазами
    cur = next((r for r in TL if r["start"] <= t <= r["end"]), None)
    if cur:
        lines = wrap(d, cur["text"], f_sm, W - 200)
        yy = 150
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        hgt = len(lines) * 48 + 34
        ImageDraw.Draw(ov).rounded_rectangle([70, yy - 24, W - 70, yy - 24 + hgt],
                                             radius=20, fill=(8, 12, 30, 165))
        im = Image.alpha_composite(im, ov)
        d = ImageDraw.Draw(im)
        centered(d, lines, f_sm, yy, (226, 234, 250), 10)

    # плашки — как они лягут в готовом ролике
    for tt in edl["titles"]:
        if tt["at"] <= t < tt["at"] + tt["dur"]:
            fr = title_frame(tt["seq"], int((t - tt["at"]) * FPS))
            if fr is not None:
                im = Image.alpha_composite(im, fr)
                d = ImageDraw.Draw(im)

    tc = f"{int(t // 60):01d}:{t % 60:05.2f}"
    d.text((W - 210, 60), tc, font=f_tc, fill=(255, 255, 255, 150))
    im.convert("RGB").save(f"anim/{i:04d}.png")

print(f"раскадровка: {N} кадров, {TOTAL:.1f} с")

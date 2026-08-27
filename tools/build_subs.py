"""Субтитры двумя стилями: терминал как основа, караоке на смысловых пиках.

Рисуется только полоса 1080x300 и накладывается на y=1420 - так в разы легче,
чем гонять полный кадр.
"""
from PIL import Image, ImageDraw, ImageFont
import os, re

W, SH, Y0 = 1080, 300, 1420
FPS = 30
F = "fonts/"
ORANGE = (255, 117, 31)
BASE_Y = 96

KEY = {"память","чатами","монтаж","видеороликов","субтитрами","переходами","монтажом",
       "нарезки","crm","календарём","сервисам","артефакты","excel","презентации",
       "таблицы","агент","браузере","курс","claude"}

MAXW = W - 130
_cache = {}


def fit(fname, base, text):
    """Подгоняет кегль, чтобы строка влезла в кадр."""
    k = (fname, base, text)
    if k in _cache:
        return _cache[k]
    d = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    size = base
    while size > 22:
        f = ImageFont.truetype(F + fname, size)
        if d.textlength(text, font=f) <= MAXW:
            break
        size -= 2
    f = ImageFont.truetype(F + fname, size)
    _cache[k] = f
    return f


def load():
    out = []
    for l in open("subs4.ass", encoding="utf-8"):
        if not l.startswith("Dialogue:"):
            continue
        p = l.split(",", 8)
        def sec(ts):
            h, m, s = ts.split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)
        txt = re.sub(r"\{[^}]*\}", "", p[8]).strip()
        out.append([sec(p[1]), sec(p[2]), txt])
    return out


def norm(w):
    return re.sub(r"[^a-zа-яё0-9]", "", w.lower())


segs = load()
peak = [any(norm(w) in KEY for w in s[2].split()) for s in segs]
DUR = max(s[1] for s in segs) + 0.2
N = int(DUR * FPS)
os.makedirs("subseq", exist_ok=True)

for i in range(N):
    t = i / FPS
    im = Image.new("RGBA", (W, SH), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cur = None
    for k, (st, en, txt) in enumerate(segs):
        if st <= t <= en:
            cur = (k, st, en, txt)
            break
    if cur:
        k, st, en, txt = cur
        words = txt.split()
        if peak[k]:
            # караоке: вся фраза видна, текущее слово оранжевым
            fkar = fit("Montserrat-700.ttf", 54, txt)
            tot = d.textlength(txt, font=fkar)
            x = (W - tot) / 2
            idx = min(int((t - st) / max(en - st, 0.01) * len(words)), len(words) - 1)
            for wi, wd in enumerate(words):
                col = ORANGE if wi == idx else (255, 255, 255)
                for ox, oy in ((-3, 0), (3, 0), (0, -3), (0, 3), (-2, -2), (2, 2)):
                    d.text((x + ox, BASE_Y + oy), wd, font=fkar, fill=(8, 12, 30, 235))
                d.text((x, BASE_Y), wd, font=fkar, fill=col)
                x += d.textlength(wd + " ", font=fkar)
        else:
            # терминал: печать за 0.2 c и мигающий курсор
            fterm = fit("Montserrat-500.ttf", 50, txt)
            prog = min((t - st) / 0.20, 1.0)
            shown = txt[: max(1, int(len(txt) * prog))]
            b = d.textbbox((0, 0), shown, font=fterm)
            w = b[2] - b[0]
            d.rounded_rectangle([(W - w) / 2 - 32, BASE_Y - 18, (W + w) / 2 + 46, BASE_Y + 66],
                                radius=24, fill=(10, 16, 40, 218))
            d.text(((W - w) / 2 - b[0], BASE_Y - b[1] + 8), shown, font=fterm, fill=(255, 255, 255))
            if int(t * 2.6) % 2 == 0:
                cx = (W + w) / 2 + 12
                d.rectangle([cx, BASE_Y + 2, cx + 6, BASE_Y + 52], fill=ORANGE)
    im.save(f"subseq/{i:04d}.png")

print(f"кадров {N} ({DUR:.2f} c) | реплик {len(segs)} | караоке на {sum(peak)}, терминал на {len(segs)-sum(peak)}")

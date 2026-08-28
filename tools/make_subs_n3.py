"""Субтитры двумя стилями по расшифровке слов.

Терминал — база: реплика допечатывается за 0.2 с, справа мигает курсор.
Караоке — на смысловых пиках: вся фраза видна, текущее слово оранжевым.
Рисуется полоса 1080x300 и кладётся на y=1420, над ник-бейджем.
"""
from PIL import Image, ImageDraw, ImageFont
import json, os, re

W, SH, Y0 = 1080, 300, 1420
FPS, TEMPO = 30, 1.15
F = "fonts/"
ORANGE = (255, 117, 31)
BASE_Y = 96
MAXW = W - 130

KEY = {"доступ", "рабочей", "среде", "чат", "плейс", "языковой", "языковая",
       "модели", "модель", "кодовое", "слово", "рилс", "воронке", "воронки",
       "воронку", "заявки", "напоминания", "инструкции", "инструкцию",
       "инструкция", "бесплатно", "комментариях", "директ", "самостоятельно"}

_cache = {}


def fit(fname, base, text):
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
    _cache[k] = ImageFont.truetype(F + fname, size)
    return _cache[k]


def norm(w):
    return re.sub(r"[^a-zа-яё0-9]", "", w.lower())


# распознавание слышит бренды на слух — правим написание, тайминги не трогаем
FIX = {"джипяти": "джипити", "плейс": "чатплейс"}
DROP_BEFORE = {("чат", "плейс")}

words = []
for w in json.load(open("n3/words.json")):
    if words and (words[-1]["w"], w["w"]) in DROP_BEFORE:
        words.pop()                      # «чат плейс» -> одно слово «чатплейс»
    w = dict(w, w=FIX.get(w["w"], w["w"]))
    words.append(w)
for w in words:
    w["t"] /= TEMPO
LAST = 40.82 / TEMPO

# по три слова в реплику
segs = []
for i in range(0, len(words), 3):
    grp = words[i:i + 3]
    st = grp[0]["t"]
    nxt = words[i + 3]["t"] if i + 3 < len(words) else LAST
    # стык без дыр: тянем до следующей реплики, если пауза короткая
    en = nxt if nxt - st < 3.2 else st + 2.2
    segs.append([st, en, " ".join(g["w"] for g in grp).upper()])

peak = [any(norm(w) in KEY for w in s[2].split()) for s in segs]
DUR = segs[-1][1] + 0.2
N = int(DUR * FPS)
os.makedirs("n3/subseq", exist_ok=True)

for i in range(N):
    t = i / FPS
    im = Image.new("RGBA", (W, SH), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cur = next(((k, s) for k, s in enumerate(segs) if s[0] <= t <= s[1]), None)
    if cur:
        k, (st, en, txt) = cur
        if peak[k]:
            wds = txt.split()
            fkar = fit("Montserrat-700.ttf", 54, txt)
            tot = d.textlength(txt, font=fkar)
            x = (W - tot) / 2
            idx = min(int((t - st) / max(en - st, 0.01) * len(wds)), len(wds) - 1)
            for wi, wd in enumerate(wds):
                col = ORANGE if wi == idx else (255, 255, 255)
                for ox, oy in ((-3, 0), (3, 0), (0, -3), (0, 3), (-2, -2), (2, 2)):
                    d.text((x + ox, BASE_Y + oy), wd, font=fkar, fill=(8, 12, 30, 235))
                d.text((x, BASE_Y), wd, font=fkar, fill=col)
                x += d.textlength(wd + " ", font=fkar)
        else:
            fterm = fit("Montserrat-500.ttf", 50, txt)
            prog = min((t - st) / 0.20, 1.0)
            shown = txt[: max(1, int(len(txt) * prog))]
            b = d.textbbox((0, 0), shown, font=fterm)
            w = b[2] - b[0]
            d.rounded_rectangle([(W - w) / 2 - 32, BASE_Y - 18, (W + w) / 2 + 46, BASE_Y + 66],
                                radius=24, fill=(10, 16, 40, 218))
            d.text(((W - w) / 2 - b[0], BASE_Y - b[1] + 8), shown, font=fterm,
                   fill=(255, 255, 255))
            if int(t * 2.6) % 2 == 0:
                cx = (W + w) / 2 + 12
                d.rectangle([cx, BASE_Y + 2, cx + 6, BASE_Y + 52], fill=ORANGE)
    im.save(f"n3/subseq/{i:04d}.png")

gaps = [round(segs[i + 1][0] - segs[i][1], 2) for i in range(len(segs) - 1)]
print(f"кадров {N} ({DUR:.2f} с) | реплик {len(segs)} | "
      f"караоке {sum(peak)}, терминал {len(segs)-sum(peak)}")
print(f"максимальная дыра между репликами: {max(gaps):.2f} с")

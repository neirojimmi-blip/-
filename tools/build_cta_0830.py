"""Концевая плашка ролика 2026-08-30 — в стиле хука.

Пользователь прислала референс хука и попросила такую же надпись в конце:
«Пиши Семья в комментариях и я отправлю инструкции в директ», ярко.

Повторяется ритм хука: белый капс — оранжевая строка — белый капс — оранжевый
мазок. Четвёртой строкой добавлено обещание про директ.

Прописная строка Pushkin не ставится. `brand/fonts/Pushkin.ttf` — не то
начертание, что в хуке исходника: слово «семья» в нём сливается в нечитаемый
росчерк даже на кегле 230. Кодовое слово читают, чтобы его набрать, поэтому оно
идёт оранжевым капсом Montserrat и делается самым крупным элементом плашки.
Роль оранжевого акцента из хука при этом сохраняется.

Плашка кладётся поверх кадра как PNG с альфой, без тёмной подложки — как в хуке:
читаемость держится на тени.
"""
import math

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1920
ORANGE = (255, 117, 31)
WHITE = (255, 255, 255)
OUT = "work/cta_0830.png"
MONT = "brand/fonts/Montserrat-Variable.ttf"

LINE_1 = "ПИШИ"
HERO = "СЕМЬЯ"
LINE_2 = "В КОММЕНТАРИЯХ"
TAIL = "И Я ОТПРАВЛЮ ИНСТРУКЦИИ В ДИРЕКТ"

BLOCK_TOP = 655          # хук в исходнике начинается примерно здесь
SUBS_TOP = 1240          # ниже нельзя: там впечённые субтитры


def mont(size, weight=800):
    f = ImageFont.truetype(MONT, size)
    f.set_variation_by_axes([weight])
    return f


def measure(font, text, track=0):
    b = font.getbbox(text)
    return b[2] - b[0] + track * max(len(text) - 1, 0), b


def fit(weight, text, target_w, track=0, lo=20, hi=280):
    """Подбор кегля так, чтобы строка заняла target_w по ширине."""
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if measure(mont(mid, weight), text, track)[0] <= target_w:
            lo = mid
        else:
            hi = mid - 1
    return mont(lo, weight)


def draw_line(img, text, font, y, fill, track=0):
    """Строка по центру с мягкой тенью; возвращает нижнюю границу."""
    w, b = measure(font, text, track)
    x0 = (W - w) // 2

    def put(layer, dx, dy, col):
        d = ImageDraw.Draw(layer)
        x = x0
        for ch in text:
            d.text((x - b[0] + dx, y - b[1] + dy), ch, font=font, fill=col)
            x += font.getlength(ch) + track

    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    put(sh, 0, 8, (0, 0, 0, 190))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(11)))
    put(img, 0, 0, fill)
    return y + (b[3] - b[1])


def brush(img, cx, y, width, thick):
    """Оранжевый мазок как под «К 1 СЕНТЯБРЯ»: слегка выгнут, сужается к краям."""
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    top, bot = [], []
    for i in range(161):
        u = i / 160
        x = cx - width / 2 + width * u
        arc = math.sin(math.pi * u) * thick * 0.5
        t = thick * (0.22 + 0.78 * math.sin(math.pi * u) ** 0.55)
        top.append((x, y - arc - t / 2))
        bot.append((x, y - arc + t / 2))
    ImageDraw.Draw(lay).polygon(top + bot[::-1], fill=ORANGE + (255,))
    sh = lay.filter(ImageFilter.GaussianBlur(10))
    img.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, 0)))
    img.alpha_composite(sh)
    img.alpha_composite(lay)


card = Image.new("RGBA", (W, H), (0, 0, 0, 0))

f_caps = fit(800, LINE_2, int(W * 0.90))            # кегль задаёт длинная строка
f_hero = fit(800, HERO, int(W * 0.72))              # кодовое слово — самое крупное
f_tail = fit(600, TAIL, int(W * 0.84), track=2, hi=64)

y = BLOCK_TOP
y = draw_line(card, LINE_1, f_caps, y, WHITE) + 14
y = draw_line(card, HERO, f_hero, y, ORANGE) + 14
y = draw_line(card, LINE_2, f_caps, y, WHITE)

brush(card, W // 2, y + 52, measure(f_caps, LINE_2)[0] * 1.04, 22)
y = draw_line(card, TAIL, f_tail, y + 92, WHITE, track=2)

card.save(OUT)
print(f"плашка: капс {f_caps.size}, кодовое слово {f_hero.size}, хвост {f_tail.size}; "
      f"блок {BLOCK_TOP}–{y} px, субтитры с {SUBS_TOP} px "
      f"({'ок' if y < SUBS_TOP else 'ПЕРЕКРЫТИЕ'})")

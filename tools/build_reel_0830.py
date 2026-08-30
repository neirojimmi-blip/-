"""Монтаж ролика «Родители, важная новость к 1 сентября» (2026-08-30).

Исходник пришёл уже собранным: один непрерывный план говорящей головы,
впечённые субтитры, хук и две вставки-скрина. Склеек в нём нет ни одной —
поэтому планы нарезаются здесь заново.

Переходы: punch-зум на склейке плюс flash и glitch на композите, типы
чередуются. Whip и zoom-рывок из скилла НЕ применяются — пользователь
забраковала тряску («не надо делать трясучку эту»), а zoom-рывок вдобавок
наезжал поверх плана и срезал макушку. Glitch ослаблен со сдвига ±22 px
до ±14 px — к более спокойному монтажу.

Речь не режется и не ускоряется: субтитры впечены в исходник, любое изменение
темпа их рассинхронизирует. Планы режутся встык, сумма ровно 868 кадров.

## Как считается кадр

По вводным пользователя: ноги резать можно, макушку и лицо — нельзя.
Поэтому вертикальный якорь не задаётся руками: сверху снимается не больше
HEAD_SAFE (5.5 % — над волосами свободно 7.19 %), всё остальное уходит вниз,
в ноги. Лицо занимает 8–22 % высоты и при таком правиле не задевается никогда.

По горизонтали кадр центрируется, пока это возможно, и сдвигается вправо
ровно настолько, чтобы не срезать впечённый текст. Субтитры в исходнике НЕ
центральные: они прижаты вправо, а «РОДИТЕЛЬСКИЙ КОНТРОЛЬ» на 14.8–17.6 с
доходит до 98 % ширины — из-за него этот план и держится широким.

Замеренные поля (в процентах ширины/высоты кадра):

    макушка         7.19 % сверху      лицо            8–22 % высоты
    хук-титр        0–3.4 с, в анимации касается краёв
    скрин ChatGPT   8.9–12.1 с   слева 3.9 %   справа 2.5 %
    панель          14.9–18.4 с  слева 6.3 %   справа 7.2 %
    субтитры        справа от 1.7 % (план 6) до 15 % — замер по планам
"""
import math
import subprocess

SRC = "work/src.mp4"          # исходный рилс
CTA = "work/cta_0830.png"     # концевая плашка, tools/build_cta_0830.py
OUT = "work/reel_0830.mp4"
FILT = "work/reel_0830_filter.txt"

W, H = 1080, 1920
FPS = 30
NFRAMES = 868                 # длина исходника, менять нельзя — под неё лёг голос

HEAD_TOP = 7.19               # макушка, % высоты
HEAD_SAFE = 5.5               # сколько максимум снимаем сверху, % высоты
CTA_FRAME = 756               # плашка появляется на последней склейке
CTA_FADE = 0.30

# (кадр начала, зум, макс. кроп справа %, макс. кроп слева %) — пределы взяты
# из замеров впечённой графики и субтитров на этом отрезке.
PLANS = [
    (  0, 1.00,  3.0,  3.0),  # хук: титр во всю ширину, зум запрещён
    (101, 1.20,  6.0, 20.0),  # крупный
    (171, 1.02,  3.0, 20.0),  # широкий
    (243, 1.00,  1.7,  3.1),  # выезжает скрин ChatGPT
    (311, 1.04,  1.7,  3.1),  # скрин в кадре: поле справа всего 2.5 %
    (366, 1.20,  3.4, 20.0),  # крупный, скрин ушёл
    (444, 1.06,  0.8,  5.5),  # «РОДИТЕЛЬСКИЙ КОНТРОЛЬ» до 98 % ширины
    (528, 1.02,  6.0,  5.5),  # широкий, панель ещё в кадре до 18.4 с
    (592, 1.20,  3.6, 20.0),  # крупный
    (691, 1.02,  3.6, 20.0),  # широкий
    (756, 1.18,  4.5, 20.0),  # финал, на нём лежит плашка
]

# Акцент на склейке. Пустая строка — чистый рез: там punch-зум и так сильный.
TRANS = {
    101: "flash",  171: "",      243: "glitch", 311: "flash",
    366: "",       444: "glitch", 528: "flash", 592: "",
    691: "glitch", 756: "flash",
}

FLASH_D, GLITCH_D = 0.10, 0.06


def even_down(v):
    return int(v) // 2 * 2


def even_up(v):
    return -((-int(math.ceil(v))) // 2) * 2


def window(z, max_right):
    """Окно кропа в пикселях.

    Считается сразу в пикселях, а не в долях: округление размера до чётного
    сдвигает границу на пиксель-другой, и на узких полях (справа бывает 0.9 %)
    этого хватает, чтобы срезать букву.
    """
    cw, ch = even_down(W / z), even_down(H / z)
    free_x, free_y = W - cw, H - ch

    right_px = max_right / 100 * W
    if free_x / 2 <= right_px:
        x = even_down(free_x / 2)               # центр, пока поля позволяют
    else:
        x = even_up(free_x - right_px)          # сдвиг вправо ровно до предела
    x = max(0, min(free_x, x))

    # сверху снимаем не больше HEAD_SAFE, остаток уходит вниз, в ноги
    y = even_down(min(free_y, HEAD_SAFE / 100 * H))
    return cw, ch, x, y


steps, labs = [], []
for i, (f0, z, mr, ml) in enumerate(PLANS):
    f1 = PLANS[i + 1][0] if i + 1 < len(PLANS) else NFRAMES
    cw, ch, x, y = window(z, mr)
    top, left, right = y / H * 100, x / W * 100, (W - cw - x) / W * 100
    assert top <= HEAD_SAFE + 0.1, f"план {i}: кроп сверху {top:.2f}% срезает макушку"
    assert right <= mr + 0.1, f"план {i}: кроп справа {right:.2f}% срезает текст"
    assert left <= ml + 0.1, f"план {i}: кроп слева {left:.2f}% срезает графику"
    steps.append(
        f"[0:v]trim=start_frame={f0}:end_frame={f1},setpts=PTS-STARTPTS,"
        f"crop={cw}:{ch}:{x}:{y},scale={W}:{H}:flags=lanczos,setsar=1[v{i}]")
    labs.append(f"[v{i}]")

steps.append(f"{''.join(labs)}concat=n={len(PLANS)}:v=1:a=0,"
             f"eq=contrast=1.03:saturation=1.06[vc]")


def terms(kind, expr):
    """Сумма окон between() для всех склеек данного типа."""
    out = [expr(f / FPS) for f, k in sorted(TRANS.items()) if k == kind]
    return "+".join(out) if out else "0"


flash = terms("flash", lambda T: f"between(t,{T:.4f},{T + FLASH_D:.4f})")
steps.append(f"[vc]eq=brightness='0.34*({flash})':"
             f"saturation='1+0.15*({flash})':eval=frame[vf]")

glitch = terms("glitch",
               lambda T: f"between(t,{T - GLITCH_D:.4f},{T + GLITCH_D:.4f})")
steps.append(f"[vf]rgbashift=rh=-14:bh=14:rv=4:bv=-4:enable='{glitch}'[vg]")

# Концевая плашка — поверх всего, её не задевают ни вспышка, ни glitch.
cta_t = CTA_FRAME / FPS
steps.append(f"[1:v]format=rgba,fade=t=in:st=0:d={CTA_FADE}:alpha=1,"
             f"setpts=PTS+{cta_t:.4f}/TB[cta]")
steps.append(f"[vg][cta]overlay=0:0:enable='gte(t,{cta_t:.4f})':"
             f"eof_action=pass:format=yuv420[vout]")

open(FILT, "w").write(";\n".join(steps))
subprocess.run([
    "ffmpeg", "-y", "-loglevel", "error", "-i", SRC,
    "-loop", "1", "-framerate", str(FPS), "-t", "5", "-i", CTA,
    "-filter_complex_script", FILT, "-map", "[vout]", "-an",
    "-c:v", "libx264", "-preset", "slow", "-crf", "17",
    "-g", "1", "-bf", "0", "-pix_fmt", "yuv420p",
    "-fps_mode", "cfr", "-video_track_timescale", "90000", OUT], check=True)

print(f"планов: {len(PLANS)}, акцентов: {sum(1 for v in TRANS.values() if v)}, "
      f"чистых резов: {sum(1 for v in TRANS.values() if not v)}; "
      f"зум {min(z for _, z, _, _ in PLANS):.2f}–{max(z for _, z, _, _ in PLANS):.2f}; "
      f"длина {NFRAMES / FPS:.3f} с (не менялась)")

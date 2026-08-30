"""Монтаж ролика «Родители, важная новость к 1 сентября» (2026-08-30).

Исходник пришёл уже собранным: один непрерывный план говорящей головы,
впечённые субтитры, хук и две вставки-скрина. Склеек в нём нет ни одной —
поэтому планы нарезаются здесь заново, а переходы ставятся по скиллу
`brand/xeniia-reel-style.SKILL.md`: punch-зум на склейке плюс whip / flash /
glitch / zoom-in, чередуя типы. Речь не режется и не ускоряется: субтитры
впечены в исходник, любое изменение темпа их рассинхронизирует.

Границы планов = паузы в речи (silencedetect), поэтому план меняется на стыке
фраз. Кадрирование ограничено измеренными полями впечённой графики:

    хук-титр (0–3.4 с)          поля 4.7 %, в анимации входа/выхода — 0 %
    скрин ChatGPT (8.9–12.1 с)  поля 3.9 % слева, 2.5 % справа, уезжает к 12.2
    панель родконтроля (14.9–18.4 с) поля 6.3 % слева, 7.2 % справа

Отсюда широкие планы на кусках с графикой и крупные — только там, где она ушла.
"""
import subprocess

SRC = "work/src.mp4"          # исходный рилс
MUS = "work/music.mp3"        # трек, присланный пользователем
OUT = "work/reel_0830.mp4"
FILT = "work/reel_0830_filter.txt"

W, H = 1080, 1920
FPS = 30
NFRAMES = 868                 # длина исходника, менять нельзя — под неё лёг голос

# Планы: (кадр начала, зум, центр кропа по X, центр кропа по Y) — доли 0..1,
# 0.5 = центр. По Y больше 0.5 = кроп ниже, то есть туфли остаются в кадре.
PLANS = [
    (  0, 1.00, 0.50, 0.50),  # хук целиком одним планом: титр во всю ширину,
                              # на входе и выходе касается краёв — зум запрещён
    (101, 1.16, 0.60, 0.66),  # крупный, сдвиг вправо («вторая камера»)
    (171, 1.03, 0.50, 0.58),  # широкий
    (243, 1.00, 0.50, 0.50),  # выезжает скрин ChatGPT — зум запрещён
    (311, 1.04, 0.50, 0.54),  # скрин ещё в кадре: целиком виден до 12.10 с
    (366, 1.17, 0.42, 0.68),  # крупный, сдвиг влево — только после ухода скрина
    (444, 1.10, 0.50, 0.60),  # панель родконтроля, поля позволяют 1.13
    (528, 1.02, 0.50, 0.52),  # широкий
    (592, 1.17, 0.56, 0.68),  # крупный
    (691, 1.04, 0.50, 0.58),  # широкий
    (756, 1.15, 0.46, 0.64),  # крупный, уводим до конца
]

# Переход на каждой склейке. Типы чередуются, подряд не повторяются.
# На склейках 243 и 311 punch-зум слабый (впечённый скрин не даёт зумить),
# поэтому там стоят flash и whip — они видны сами по себе.
TRANS = {
    101: "whip",   171: "glitch", 243: "flash",  311: "whip",
    366: "zoom",   444: "glitch", 528: "flash",  592: "whip",
    691: "zoom",   756: "glitch",
}

FLASH_D, GLITCH_D, WHIP_D, ZOOM_D = 0.10, 0.07, 0.22, 0.24


def even(v):
    return int(v) // 2 * 2


def terms(kind, expr):
    """Сумма окон между() для всех склеек данного типа."""
    out = [expr(f / FPS) for f, k in sorted(TRANS.items()) if k == kind]
    return "+".join(out) if out else "0"


steps, labs = [], []
for i, (f0, z, fx, fy) in enumerate(PLANS):
    f1 = PLANS[i + 1][0] if i + 1 < len(PLANS) else NFRAMES
    cw, ch = even(W / z), even(H / z)
    x, y = even((W - cw) * fx), even((H - ch) * fy)
    steps.append(
        f"[0:v]trim=start_frame={f0}:end_frame={f1},setpts=PTS-STARTPTS,"
        f"crop={cw}:{ch}:{x}:{y},scale={W}:{H}:flags=lanczos,setsar=1[v{i}]")
    labs.append(f"[v{i}]")

steps.append(f"{''.join(labs)}concat=n={len(PLANS)}:v=1:a=0,"
             f"eq=contrast=1.03:saturation=1.06[vc]")

# zoom-in: 1.10 -> 1 за ZOOM_D, гасится линейно
zoom = terms("zoom", lambda T:
             f"gte(on/{FPS},{T:.4f})*lte(on/{FPS},{T + ZOOM_D:.4f})"
             f"*(1-(on/{FPS}-{T:.4f})/{ZOOM_D})")
steps.append(f"[vc]zoompan=z='1+0.10*({zoom})':d=1:"
             f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
             f"s={W}x{H}:fps={FPS},setsar=1[vz]")

# flash: вспышка на FLASH_D
flash = terms("flash", lambda T: f"between(t,{T:.4f},{T + FLASH_D:.4f})")
steps.append(f"[vz]eq=brightness='0.34*({flash})':"
             f"saturation='1+0.15*({flash})':eval=frame[vf]")

# glitch: rgbashift на ±GLITCH_D
glitch = terms("glitch",
               lambda T: f"between(t,{T - GLITCH_D:.4f},{T + GLITCH_D:.4f})")
steps.append(f"[vf]rgbashift=rh=-22:bh=22:rv=6:bv=-6:enable='{glitch}'[vg]")

# whip: рывок композита по X поверх размытой копии + смаз на ±0.10 c
whip = terms("whip", lambda T:
             f"between(t,{T:.4f},{T + WHIP_D:.4f})"
             f"*150*sin(2*PI*(t-{T:.4f})/{WHIP_D})")
wblur = terms("whip", lambda T: f"between(t,{T - 0.10:.4f},{T + 0.10:.4f})")
steps.append("[vg]split=2[wa][wb]")
steps.append("[wb]boxblur=24:1[wbg]")
steps.append(f"[wa]boxblur=26:1:enable='{wblur}'[wfg]")
steps.append(f"[wbg][wfg]overlay=x='{whip}':y=0:eval=frame:"
             f"format=yuv420[vout]")

open(FILT, "w").write(";\n".join(steps))
subprocess.run([
    "ffmpeg", "-y", "-loglevel", "error", "-i", SRC,
    "-filter_complex_script", FILT, "-map", "[vout]", "-an",
    "-c:v", "libx264", "-preset", "slow", "-crf", "17",
    "-g", "1", "-bf", "0", "-pix_fmt", "yuv420p",
    "-fps_mode", "cfr", "-video_track_timescale", "90000", OUT], check=True)

print(f"планов: {len(PLANS)}, переходов: {len(TRANS)}, "
      f"длина {NFRAMES / FPS:.3f} с (не менялась)")

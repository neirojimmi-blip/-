"""Нарезка монолога про подключение модели к рабочей среде.

Речь целиком — ни одного слова не выброшено. Меняются только планы:
широкий и крупный чередуются на границах фраз, кроп якорится к верху кадра,
потому что снизу в исходнике много пустого пола. Тряски нет — пользователь
её забраковала на прошлом ролике.
"""
import subprocess

SRC = "n3/src.MOV"
OUT = "n3/cut.mp4"
SW, SH = 720, 1280
W, H = 1080, 1920
TEMPO = 1.15
FACE_X = 340

# (начало в исходнике, зум, центр по X)
PLANS = [
    (0.00,  1.16, 340),   # сейчас выигрывает не тот, кто просто общается
    (4.27,  1.02, 360),   # а тот, кто умеет давать доступ
    (7.67,  1.20, 336),   # таким образом можно подключить
    (11.95, 1.05, 360),   # клиент вам пишет кодовое слово
    (15.75, 1.18, 344),   # присылает информацию и ведёт по воронке
    (20.49, 1.03, 360),   # доводит до заявки, напоминания
    (24.81, 1.20, 336),   # то, что вы задали изначально
    (29.25, 1.06, 358),   # эти воронки модель пропишет сама
    (34.45, 1.17, 342),   # отдаю бесплатно
    (37.13, 1.00, 360),   # пиши в комментариях
]
END = 40.82


def even(v):
    return int(v) // 2 * 2


steps, labs = [], []
for i, (t0, z, cx) in enumerate(PLANS):
    t1 = PLANS[i + 1][0] if i + 1 < len(PLANS) else END
    cw, ch = even(SW / z), even(SH / z)
    x = even(max(0, min(SW - cw, cx - cw / 2)))
    y = 0                      # якорь по верху: снизу в кадре только пол
    steps.append(
        f"[0:v]trim={t0}:{t1},setpts=PTS-STARTPTS,"
        f"crop={cw}:{ch}:{x}:{y},"
        f"scale={W}:{H}:flags=lanczos,setsar=1,"
        f"eq=brightness=0.035:contrast=1.07:saturation=1.09[v{i}]")
    labs.append(f"[v{i}]")

steps.append(f"{''.join(labs)}concat=n={len(PLANS)}:v=1:a=0[vc]")
steps.append(f"[vc]setpts=PTS/{TEMPO},fps=30[vout]")
steps.append(f"[0:a]atempo={TEMPO}[aout]")

open("n3/cut_filter.txt", "w").write(";\n".join(steps))
subprocess.run([
    "ffmpeg", "-y", "-loglevel", "error", "-i", SRC,
    "-filter_complex_script", "n3/cut_filter.txt",
    "-map", "[vout]", "-map", "[aout]",
    "-c:v", "libx264", "-preset", "medium", "-crf", "17",
    "-g", "1", "-bf", "0", "-pix_fmt", "yuv420p",
    "-fps_mode", "cfr", "-video_track_timescale", "90000",
    "-c:a", "aac", "-b:a", "192k", OUT], check=True)
print(f"планов: {len(PLANS)}, ожидаемая длина {END/TEMPO:.2f} с")

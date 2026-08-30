"""Звук ролика 2026-08-30: подкладываем присланный трек под готовую озвучку.

Речь в исходнике уже обработана и впечена вместе с субтитрами, поэтому голосовая
цепочка скилла (highpass/afftdn/EQ/deesser/компрессор) здесь не применяется —
повторная обработка готового микса только испортит его. Берутся ducking, фейды
и приведение громкости к цели.

Отступление от пресета: скилл ставит музыке gain −12 дБ, но здесь озвучка снята
непривычно тихо (−25.9 dBFS RMS на речи против обычных −16), и на −12 дБ музыка
оказалась бы всего на 1.5 дБ ниже речи. Пункт 6 чек-листа («в паузах ≥10 дБ ниже
речи») жёстче пресета, поэтому gain посчитан от замера: −22 дБ даёт запас 12 дБ.

Трек начинается с 11.5 с: до этого в нём разреженное вступление, под речью
неслышное. Зацикливать не нужно — в треке 118 с.
"""
import json
import subprocess

CUT = "work/reel_0830.mp4"     # смонтированное видео, без звука
VOICE = "work/src.mp4"         # исходник, из него берётся озвучка
MUS = "work/music.mp3"
OUT = "work/reel_0830_music.mp4"       # мастер ALL-INTRA
PREVIEW = "work/reel_0830_preview.mp4"  # файл для публикации

DUR = 28.933333
MUS_START = 11.5
MUS_GAIN = 0.0753             # −22 дБ, см. docstring
FADE_IN, FADE_OUT = 0.4, 1.8
DUCK = "threshold=0.0398:ratio=6:attack=12:release=400"   # порог −28 дБ
TARGET_I, TARGET_TP = -11.5, -1.2


def mix_graph(voice, music):
    """Граф микса: музыка приглушается под речью, речь не трогаем."""
    return (
        f"[{music}:a]atrim=start={MUS_START}:duration={DUR},asetpts=PTS-STARTPTS,"
        f"aresample=48000,volume={MUS_GAIN},"
        f"afade=t=in:st=0:d={FADE_IN},"
        f"afade=t=out:st={DUR - FADE_OUT:.4f}:d={FADE_OUT}[mus];"
        f"[{voice}:a]aresample=48000,asplit=2[voc][key];"
        f"[mus][key]sidechaincompress={DUCK}[duck];"
        f"[voc][duck]amix=inputs=2:duration=first:normalize=0[mix]"
    )


# Первый проход — замер громкости микса. Второй проход не гоняем через loudnorm:
# его linear-режим промахнулся мимо цели почти на 1 LU и оставил TP выше −1.2.
# Вместо него постоянное усиление до цели плюс лимитер по true peak — так речь
# не «дышит», а потолок гарантирован.
probe = subprocess.run(
    ["ffmpeg", "-hide_banner", "-i", VOICE, "-i", MUS, "-filter_complex",
     mix_graph(0, 1) + f";[mix]loudnorm=I={TARGET_I}:TP={TARGET_TP}:LRA=9:"
     f"print_format=json[a]", "-map", "[a]", "-f", "null", "-"],
    capture_output=True, text=True, check=True)
measured = json.loads(probe.stderr[probe.stderr.rfind("{"):].strip())

gain_db = TARGET_I - float(measured["input_i"])
norm = (f"volume={gain_db:.2f}dB,"
        f"alimiter=limit={10 ** (TARGET_TP / 20):.4f}:level=disabled,"
        f"aresample=48000,apad,atrim=end={DUR}")   # apad: звук на 5 мс короче видео

subprocess.run(
    ["ffmpeg", "-y", "-loglevel", "error", "-i", CUT, "-i", VOICE, "-i", MUS,
     "-filter_complex", mix_graph(1, 2).replace("[mix]", f",{norm}[aout]"),
     "-map", "0:v", "-map", "[aout]", "-c:v", "copy",
     "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
     "-movflags", "+faststart", OUT], check=True)

# Мастер ALL-INTRA весит ~105 МБ — под выкладку пережимаем обычным GOP.
subprocess.run(
    ["ffmpeg", "-y", "-loglevel", "error", "-i", OUT,
     "-c:v", "libx264", "-preset", "slow", "-crf", "19",
     "-pix_fmt", "yuv420p", "-fps_mode", "cfr",
     "-c:a", "copy", "-movflags", "+faststart", PREVIEW], check=True)

print(f"замер: I={measured['input_i']} LUFS, TP={measured['input_tp']} dBTP; "
      f"усиление {gain_db:+.2f} дБ -> цель {TARGET_I} LUFS / {TARGET_TP} dBTP")

"""Сборка рилса про десктопный ChatGPT.

База — говорящая голова с аватара HeyGen. Поверх неё ложатся записи экрана
на весь кадр и фирменные плашки в нижней трети. Тайминги — в reelb_edl.json,
чтобы подставить записи и сдвинуть врезки можно было без правки кода.

Запуск из папки со сборкой:
    python3 build_reelb.py reelb_edl.json out.mp4
"""
import json
import os
import subprocess
import sys


def probe(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "format=duration:stream=width,height",
         "-of", "json", path],
        capture_output=True, text=True, check=True).stdout
    d = json.loads(out)
    return (float(d["format"]["duration"]),
            d["streams"][0]["width"], d["streams"][0]["height"])


def main(edl_path, out_path):
    edl = json.load(open(edl_path))
    W, H = edl["size"]
    fps = edl["fps"]
    base = edl["avatar"]
    dur, _, _ = probe(base)

    missing = [i["file"] for i in edl["inserts"] if not os.path.exists(i["file"])]
    if missing:
        print("Нет записей экрана — сборка неполная:")
        for m in missing:
            print("  ", m)
        print("Врезки без файла будут пропущены.\n")

    inputs = ["-i", base]
    steps = []
    cur = "base"
    steps.append(
        f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
        f"crop={W}:{H},setsar=1,fps={fps}[base]")

    idx = 1
    # записи экрана — на весь кадр, зона ниже 1560 остаётся под субтитры
    for ins in edl["inserts"]:
        if not os.path.exists(ins["file"]):
            continue
        at, d = ins["at"], ins["dur"]
        inputs += ["-i", ins["file"]]
        lab = f"ins{idx}"
        steps.append(
            f"[{idx}:v]trim=0:{d},setpts=PTS-STARTPTS,"
            f"scale={W}:{H}:force_original_aspect_ratio=increase,"
            f"crop={W}:{H},setsar=1,fps={fps},"
            f"setpts=PTS+{at}/TB[{lab}]")
        nxt = f"v{idx}"
        steps.append(
            f"[{cur}][{lab}]overlay=0:0:"
            f"enable='between(t,{at},{at + d})':eof_action=pass[{nxt}]")
        cur = nxt
        idx += 1

    # плашки — секвенции PNG с альфой
    for t in edl["titles"]:
        seq = t["seq"]
        if not os.path.isdir(seq):
            continue
        inputs += ["-framerate", str(fps), "-i", f"{seq}/%04d.png"]
        lab = f"t{idx}"
        steps.append(f"[{idx}:v]setpts=PTS+{t['at']}/TB[{lab}]")
        nxt = f"v{idx}"
        steps.append(f"[{cur}][{lab}]overlay=0:0:eof_action=pass[{nxt}]")
        cur = nxt
        idx += 1

    steps.append(f"[{cur}]null[vout]")

    script = "/tmp/reelb_filter.txt"
    with open(script, "w") as f:
        f.write(";\n".join(steps))

    cmd = (["ffmpeg", "-y"] + inputs +
           ["-filter_complex_script", script,
            "-map", "[vout]", "-map", "0:a?",
            "-t", f"{dur:.3f}",
            "-c:v", "libx264", "-preset", "medium", "-crf", "18",
            "-pix_fmt", "yuv420p", "-r", str(fps),
            "-c:a", "aac", "-b:a", "192k", out_path])
    print(" ".join(cmd[:12]), "...")
    subprocess.run(cmd, check=True)
    print(f"\nГотово: {out_path}  ({dur:.2f} с)")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "reelb.mp4")

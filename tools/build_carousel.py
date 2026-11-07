#!/usr/bin/env python3
"""Карусель Ксении: PNG 1080×1350 в стиле её Instagram, не «по мотивам»."""

from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FONTS = ROOT / "brand" / "fonts"
W, H = 1080, 1350

NAVY = (48, 64, 115, 255)       # #304073
ORANGE = (232, 124, 60, 255)    # #E87C3C
WHITE = (255, 255, 255, 255)
GRAY = (233, 236, 245, 255)     # #E9ECF5
MUTED = (70, 82, 130, 255)      # #465282
PAD = 80


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONTS / name), size)


def F_bebas(s): return font("BebasNeue.ttf", s)
def F_m(s): return font("Montserrat-Medium.ttf", s)
def F_sb(s): return font("Montserrat-SemiBold.ttf", s)
def F_b(s): return font("Montserrat-Bold.ttf", s)


def wrap(draw, text, fnt, max_w) -> list[str]:
    lines = []
    for para in text.split("\n"):
        words = para.split()
        if not words:
            lines.append("")
            continue
        cur = words[0]
        for w in words[1:]:
            trial = f"{cur} {w}"
            if draw.textlength(trial, font=fnt) <= max_w:
                cur = trial
            else:
                lines.append(cur)
                cur = w
        lines.append(cur)
    return lines


def draw_lines(draw, lines, fnt, fill, x, y, leading) -> int:
    yy = y
    for line in lines:
        draw.text((x, yy), line, font=fnt, fill=fill)
        yy += leading
    return yy


def tracked_width(draw, text, fnt, tracking) -> float:
    if not text:
        return 0
    return sum(draw.textlength(ch, font=fnt) for ch in text) + tracking * max(0, len(text) - 1)


def draw_tracked(draw, text, fnt, fill, x, y, tracking=3):
    cx = x
    for ch in text:
        draw.text((cx, y), ch, font=fnt, fill=fill)
        cx += draw.textlength(ch, font=fnt) + tracking
    return cx


def canvas(blue: bool) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    im = Image.new("RGBA", (W, H), NAVY if blue else WHITE)
    return im, ImageDraw.Draw(im)


def chrome(draw, kicker: str, n: int, total: int, blue: bool):
    kfill = ORANGE if blue else MUTED
    kf = F_b(18)
    nf = F_b(20)
    draw_tracked(draw, kicker.upper(), kf, kfill, PAD, 56, 4)
    num = f"{n:02d} / {total:02d}"
    nw = tracked_width(draw, num, nf, 2)
    draw_tracked(draw, num, nf, ORANGE, W - PAD - nw, 54, 2)


def check(draw, x, y, r=18):
    draw.ellipse((x, y, x + r * 2, y + r * 2), fill=ORANGE)
    # галочка
    pts = [(x + 9, y + r), (x + r - 1, y + r * 2 - 11), (x + r * 2 - 8, y + 10)]
    draw.line(pts, fill=WHITE, width=5, joint="curve")


def render_cover(s, n, total):
    im, d = canvas(True)
    chrome(d, s["kicker"], n, total, True)
    fb = F_bebas(118)
    yy = 200
    for line in s["title"]:
        d.text((PAD, yy), line, font=fb, fill=WHITE)
        yy += 118
    # круг справа, ниже заголовка — текст не пересекает
    cx, cy, r = 800, 820, 230
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=ORANGE)
    cf = F_bebas(88)
    tw = d.textlength(s["circle"], font=cf)
    d.text((cx - tw / 2, cy - 48), s["circle"], font=cf, fill=WHITE)
    body = F_m(34)
    lines = wrap(d, s["body"], body, 520)
    draw_lines(d, lines, body, WHITE, PAD, H - 90 - 48 * len(lines), 48)
    return im


def render_numbered(s, n, total):
    im, d = canvas(False)
    chrome(d, s["kicker"], n, total, False)
    d.text((PAD, 160), s["title"], font=F_bebas(88), fill=NAVY)
    yy = 300
    nf = F_bebas(56)
    bf = F_m(34)
    for i, item in enumerate(s["items"], 1):
        d.text((PAD, yy), f"{i:02d}", font=nf, fill=ORANGE)
        lines = wrap(d, item, bf, 760)
        draw_lines(d, lines, bf, NAVY, PAD + 120, yy + 8, 46)
        yy += max(110, 36 + 46 * len(lines))
    return im


def render_bigstat(s, n, total):
    im, d = canvas(True)
    chrome(d, s["kicker"], n, total, True)
    d.text((PAD, 180), s["title"], font=F_bebas(72), fill=WHITE)
    vf = F_bebas(220)
    tw = d.textlength(s["value"], font=vf)
    d.text(((W - tw) / 2, 400), s["value"], font=vf, fill=ORANGE)
    body = F_m(34)
    inner = W - PAD * 2 - 72
    lines = wrap(d, s["body"], body, inner)
    box_h = 48 + 48 * len(lines) + 28
    by = H - 90 - box_h
    d.rounded_rectangle((PAD, by, W - PAD, by + box_h), 16, fill=MUTED)
    draw_lines(d, lines, body, WHITE, PAD + 36, by + 36, 48)
    return im


def render_checks(s, n, total):
    im, d = canvas(False)
    chrome(d, s["kicker"], n, total, False)
    d.text((PAD, 150), s["title"], font=F_bebas(88), fill=NAVY)
    yy = 290
    bf = F_m(32)
    for item in s["items"]:
        check(d, PAD, yy + 6, 18)
        lines = wrap(d, item, bf, 820)
        h = draw_lines(d, lines, bf, NAVY, PAD + 58, yy, 44)
        yy = max(h, yy + 44) + 28
    return im


def render_stages(s, n, total):
    im, d = canvas(True)
    chrome(d, s["kicker"], n, total, True)
    d.text((PAD, 150), s["title"], font=F_bebas(88), fill=WHITE)
    yy = 280
    nf = F_bebas(48)
    bf = F_m(32)
    for i, item in enumerate(s["items"], 1):
        d.rounded_rectangle((PAD, yy, W - PAD, yy + 140), 16, fill=MUTED)
        d.text((PAD + 28, yy + 38), f"{i:02d}", font=nf, fill=ORANGE)
        lines = wrap(d, item, bf, 740)
        draw_lines(d, lines, bf, WHITE, PAD + 140, yy + 44, 42)
        yy += 156
    return im


def render_duties(s, n, total):
    im, d = canvas(False)
    chrome(d, s["kicker"], n, total, False)
    d.text((PAD, 150), s["title"], font=F_bebas(88), fill=NAVY)
    yy = 280
    bf = F_sb(32)
    for i, item in enumerate(s["items"], 1):
        d.rounded_rectangle((PAD, yy, W - PAD, yy + 120), 16, fill=GRAY)
        d.text((PAD + 28, yy + 34), f"{i:02d}", font=F_bebas(44), fill=ORANGE)
        lines = wrap(d, item, bf, 740)
        draw_lines(d, lines, bf, NAVY, PAD + 140, yy + 38, 42)
        yy += 136
    note_f = F_m(26)
    lines = wrap(d, s["note"], note_f, W - PAD * 2)
    draw_lines(d, lines, note_f, MUTED, PAD, yy + 16, 38)
    return im


def render_results(s, n, total):
    im, d = canvas(True)
    chrome(d, s["kicker"], n, total, True)
    d.text((PAD, 150), s["title"], font=F_bebas(88), fill=WHITE)
    yy = 280
    lf = F_bebas(36)
    bf = F_m(30)
    for row in s["items"]:
        d.rounded_rectangle((PAD, yy, W - PAD, yy + 170), 16, fill=MUTED)
        d.text((PAD + 32, yy + 28), row["label"].upper(), font=lf, fill=ORANGE)
        lines = wrap(d, row["text"], bf, 840)
        draw_lines(d, lines, bf, WHITE, PAD + 32, yy + 84, 40)
        yy += 186
    return im


def render_apply(s, n, total):
    im, d = canvas(False)
    chrome(d, s["kicker"], n, total, False)
    d.text((PAD, 150), s["title"], font=F_bebas(88), fill=NAVY)
    yy = 280
    bf = F_m(32)
    for i, item in enumerate(s["items"], 1):
        d.ellipse((PAD, yy + 8, PAD + 22, yy + 30), fill=ORANGE)
        lines = wrap(d, item, bf, 840)
        h = draw_lines(d, lines, bf, NAVY, PAD + 48, yy, 44)
        yy = max(h, yy + 44) + 36
    nf = F_m(26)
    lines = wrap(d, s["note"], nf, W - PAD * 2 - 56)
    box_h = 40 + 38 * len(lines) + 24
    d.rounded_rectangle((PAD, yy + 8, W - PAD, yy + 8 + box_h), 16, fill=GRAY)
    draw_lines(d, lines, nf, MUTED, PAD + 28, yy + 36, 38)
    return im


def render_cta(s, n, total):
    im, d = canvas(True)
    chrome(d, s["kicker"], n, total, True)
    fb = F_bebas(110)
    yy = 220
    for line in s["title"]:
        d.text((PAD, yy), line, font=fb, fill=WHITE)
        yy += 112
    body = F_m(34)
    lines = wrap(d, s["body"], body, W - PAD * 2)
    yy = draw_lines(d, lines, body, WHITE, PAD, yy + 40, 48) + 48
    # плашка действия
    af = F_sb(30)
    action_lines = wrap(d, s["action"], af, W - PAD * 2 - 64)
    box_h = 48 + 44 * len(action_lines) + 20
    d.rounded_rectangle((PAD, yy, W - PAD, yy + box_h), 16, fill=ORANGE)
    draw_lines(d, action_lines, af, WHITE, PAD + 32, yy + 32, 44)
    cf = F_b(28)
    draw_tracked(d, s["contact"], cf, ORANGE, PAD, H - 140, 2)
    return im


RENDERERS = {
    "cover": render_cover,
    "numbered": render_numbered,
    "bigstat": render_bigstat,
    "checks": render_checks,
    "stages": render_stages,
    "duties": render_duties,
    "results": render_results,
    "apply": render_apply,
    "cta": render_cta,
}


def render_one(slide: dict, n: int, total: int) -> Image.Image:
    fn = RENDERERS.get(slide["type"])
    if not fn:
        raise ValueError(f"unknown slide type {slide['type']}")
    return fn(slide, n, total).convert("RGB")


def copy_md(data: dict) -> str:
    lines = [
        f"# {data.get('topic', 'Карусель')}",
        "",
        "| № | Тип | Заголовок |",
        "|---|---|---|",
    ]
    for i, s in enumerate(data["slides"], 1):
        title = s.get("title")
        if isinstance(title, list):
            title = " ".join(title)
        lines.append(f"| {i} | {s['type']} | {title} |")
    lines += [
        "",
        "## Подпись",
        "",
        data["caption"],
        "",
        "Как применить: пост в @xeniia_neuro. Первый слайд — обложка. "
        "На обложку можно поставить настоящее фото Ксении в оранжевый круг; "
        "сгенерированное лицо не подставлять.",
        "",
        "Цифр экономии и сроков в слайдах нет — в брифе их не подтверждали.",
        "",
    ]
    return "\n".join(lines)


def contact_sheet(paths: list[Path], dest: Path) -> None:
    cols, rows = 3, 3
    tw, gap = 360, 16
    th = int(tw * H / W)
    sheet = Image.new("RGB", (cols * tw + (cols + 1) * gap,
                              rows * th + (rows + 1) * gap), NAVY[:3])
    for i, p in enumerate(paths):
        im = Image.open(p).convert("RGB").resize((tw, th), Image.Resampling.LANCZOS)
        r, c = divmod(i, cols)
        sheet.paste(im, (gap + c * (tw + gap), gap + r * (th + gap)))
    sheet.save(dest, "PNG")


def write_zip(folder: Path, pngs: list[Path]) -> Path:
    zpath = folder / f"{folder.name}.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in pngs:
            zf.write(p, p.name)
    return zpath


def write_pdf(pngs: list[Path], dest: Path) -> None:
    images = [Image.open(p).convert("RGB") for p in pngs]
    images[0].save(dest, "PDF", save_all=True, append_images=images[1:])


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python3 tools/build_carousel.py carousels/<folder>", file=sys.stderr)
        return 2
    folder = Path(sys.argv[1])
    if not folder.is_absolute():
        folder = ROOT / folder
    data = json.loads((folder / "slides.json").read_text(encoding="utf-8"))
    slides = data["slides"]
    if not 8 <= len(slides) <= 10:
        raise SystemExit(f"need 8–10 slides, got {len(slides)}")
    total = len(slides)
    pngs = []
    for i, slide in enumerate(slides, 1):
        dest = folder / f"{i:02d}.png"
        render_one(slide, i, total).save(dest, "PNG", optimize=True)
        pngs.append(dest)
        print(f"wrote {dest.relative_to(ROOT)}")
    contact_sheet(pngs, folder / "preview.png")
    (folder / "copy.md").write_text(copy_md(data), encoding="utf-8")
    zpath = write_zip(folder, pngs)
    write_pdf(pngs, folder / f"{folder.name}.pdf")
    print(f"wrote {(folder / 'preview.png').relative_to(ROOT)}")
    print(f"wrote {zpath.relative_to(ROOT)}")
    print(f"wrote {(folder / f'{folder.name}.pdf').relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

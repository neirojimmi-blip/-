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


def resolve_image(path: str, folder: Path) -> Path:
    p = Path(path)
    if p.is_absolute():
        return p
    cand = folder / p
    if cand.exists():
        return cand
    return ROOT / p


def paste_plan(im: Image.Image, path: Path, box, radius=24, pad=22, bg=WHITE):
    """Исходный чертёж на карточке. Не перерисовываем — только масштаб."""
    photo = Image.open(path).convert("RGBA")
    x0, y0, x1, y1 = (int(v) for v in box)
    w, h = x1 - x0, y1 - y0
    if w < 40 or h < 40:
        return
    card = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(card).rounded_rectangle((0, 0, w - 1, h - 1), radius, fill=bg)
    inner_w, inner_h = max(1, w - pad * 2), max(1, h - pad * 2)
    scale = min(inner_w / photo.width, inner_h / photo.height)
    nw = max(1, int(photo.width * scale))
    nh = max(1, int(photo.height * scale))
    photo = photo.resize((nw, nh), Image.Resampling.LANCZOS)
    card.paste(photo, ((w - nw) // 2, (h - nh) // 2), photo)
    im.alpha_composite(card, (x0, y0))


def render_cover(s, n, total, folder: Path):
    im, d = canvas(True)
    chrome(d, s["kicker"], n, total, True)
    fb = F_bebas(110)
    yy = 170
    for line in s["title"]:
        d.text((PAD, yy), line, font=fb, fill=WHITE)
        yy += 108
    body = F_m(32)
    if s.get("image"):
        lines = wrap(d, s["body"], body, W - PAD * 2)
        body_h = 44 * len(lines)
        paste_plan(
            im,
            resolve_image(s["image"], folder),
            (PAD, yy + 12, W - PAD, H - 86 - body_h),
            radius=24,
            pad=28,
            bg=WHITE,
        )
        draw_lines(d, lines, body, WHITE, PAD, H - 70 - body_h, 44)
        return im
    cx, cy, r = 800, 820, 230
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=ORANGE)
    cf = F_bebas(88)
    tw = d.textlength(s["circle"], font=cf)
    d.text((cx - tw / 2, cy - 48), s["circle"], font=cf, fill=WHITE)
    lines = wrap(d, s["body"], body, 520)
    draw_lines(d, lines, body, WHITE, PAD, H - 90 - 48 * len(lines), 48)
    return im


def render_plan(s, n, total, folder: Path):
    blue = bool(s.get("blue"))
    im, d = canvas(blue)
    chrome(d, s["kicker"], n, total, blue)
    title_fill = WHITE if blue else NAVY
    title = s["title"]
    d.text((PAD, 140), title, font=F_bebas(72 if len(title) > 14 else 88), fill=title_fill)
    bf = F_m(30)
    nf = F_m(24)
    body_lines = wrap(d, s["body"], bf, W - PAD * 2) if s.get("body") else []
    note_lines = wrap(d, s["note"], nf, W - PAD * 2) if s.get("note") else []
    stats = s.get("stats") or []
    stats_h = 88 if stats else 0
    footer = 20 + 42 * len(body_lines) + 34 * len(note_lines) + stats_h
    top = 250
    bottom = H - 56 - footer
    paste_plan(
        im,
        resolve_image(s["image"], folder),
        (PAD, top, W - PAD, bottom),
        radius=24,
        pad=24,
        bg=WHITE if blue else GRAY,
    )
    yy = bottom + 18
    if stats:
        col_w = (W - PAD * 2) / len(stats)
        vf, lf = F_bebas(52), F_b(22)
        for i, row in enumerate(stats):
            cx = PAD + col_w * i
            d.text((cx, yy), str(row["value"]), font=vf, fill=ORANGE)
            d.text((cx, yy + 52), row["label"].upper(), font=lf, fill=MUTED if not blue else (255, 255, 255, 200))
        yy += stats_h
    if body_lines:
        yy = draw_lines(d, body_lines, bf, title_fill, PAD, yy, 42)
    if note_lines:
        draw_lines(d, note_lines, nf, (255, 255, 255, 200) if blue else MUTED, PAD, yy + 8, 34)
    return im


def render_numbered(s, n, total, folder: Path):
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


def render_bigstat(s, n, total, folder: Path):
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


def render_checks(s, n, total, folder: Path):
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


def render_stages(s, n, total, folder: Path):
    im, d = canvas(True)
    chrome(d, s["kicker"], n, total, True)
    d.text((PAD, 150), s["title"], font=F_bebas(88), fill=WHITE)
    yy = 255
    nf = F_bebas(44)
    bf = F_m(30)
    for i, item in enumerate(s["items"], 1):
        d.rounded_rectangle((PAD, yy, W - PAD, yy + 132), 16, fill=MUTED)
        d.text((PAD + 28, yy + 34), f"{i:02d}", font=nf, fill=ORANGE)
        lines = wrap(d, item, bf, 740)
        draw_lines(d, lines, bf, WHITE, PAD + 140, yy + 36, 40)
        yy += 148
    return im


def render_duties(s, n, total, folder: Path):
    im, d = canvas(False)
    chrome(d, s["kicker"], n, total, False)
    d.text((PAD, 150), s["title"], font=F_bebas(88), fill=NAVY)
    yy = 255
    bf = F_sb(30)
    for i, item in enumerate(s["items"], 1):
        d.rounded_rectangle((PAD, yy, W - PAD, yy + 108), 16, fill=GRAY)
        d.text((PAD + 28, yy + 28), f"{i:02d}", font=F_bebas(42), fill=ORANGE)
        lines = wrap(d, item, bf, 740)
        draw_lines(d, lines, bf, NAVY, PAD + 140, yy + 32, 40)
        yy += 122
    note_f = F_m(26)
    lines = wrap(d, s["note"], note_f, W - PAD * 2)
    draw_lines(d, lines, note_f, MUTED, PAD, yy + 16, 38)
    return im


def render_results(s, n, total, folder: Path):
    im, d = canvas(True)
    chrome(d, s["kicker"], n, total, True)
    d.text((PAD, 150), s["title"], font=F_bebas(88), fill=WHITE)
    yy = 250
    lf = F_bebas(32)
    bf = F_m(28)
    for row in s["items"]:
        d.rounded_rectangle((PAD, yy, W - PAD, yy + 155), 16, fill=MUTED)
        d.text((PAD + 32, yy + 22), row["label"].upper(), font=lf, fill=ORANGE)
        lines = wrap(d, row["text"], bf, 840)
        draw_lines(d, lines, bf, WHITE, PAD + 32, yy + 72, 38)
        yy += 168
    return im


def render_apply(s, n, total, folder: Path):
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


def render_cta(s, n, total, folder: Path):
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
    if s.get("note"):
        nf = F_m(26)
        nlines = wrap(d, s["note"], nf, W - PAD * 2)
        draw_lines(d, nlines, nf, (255, 255, 255, 210), PAD, yy + box_h + 28, 38)
    cf = F_b(28)
    draw_tracked(d, s["contact"], cf, ORANGE, PAD, H - 140, 2)
    return im


RENDERERS = {
    "cover": render_cover,
    "plan": render_plan,
    "numbered": render_numbered,
    "bigstat": render_bigstat,
    "checks": render_checks,
    "stages": render_stages,
    "duties": render_duties,
    "results": render_results,
    "apply": render_apply,
    "cta": render_cta,
}


def render_one(slide: dict, n: int, total: int, folder: Path) -> Image.Image:
    fn = RENDERERS.get(slide["type"])
    if not fn:
        raise ValueError(f"unknown slide type {slide['type']}")
    return fn(slide, n, total, folder).convert("RGB")


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
        "Цифр экономии и сроков нет. 14 замечаний из демо-гайда не переносили: "
        "в источнике сказано, что они не перепроверены.",
        "",
        "Чертежи на слайдах — исходники из гайда (план квартиры и схема ЭОМ), без перерисовки. "
        "Числа 8 / 8 / 10 / 5 / 31 относятся только к этой схеме референса.",
        "",
        "Источник: практический гайд «Чертёж в Claude · DXF + MCP + нормы + AutoCAD», ноябрь 2026.",
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
        render_one(slide, i, total, folder).save(dest, "PNG", optimize=True)
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

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
CAD_BLUE = (37, 99, 235, 255)   # как AutoCAD на референсе
INK = (17, 24, 39, 255)
BG_CAD = (239, 241, 246, 255)
GRID_C = (214, 220, 232, 180)
PAD = 80
STYLE = "pikus-ig"


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


def draw_grid(im: Image.Image, step=54):
    d = ImageDraw.Draw(im)
    for x in range(0, W + 1, step):
        d.line((x, 0, x, H), fill=GRID_C, width=1)
    for y in range(0, H + 1, step):
        d.line((0, y, W, y), fill=GRID_C, width=1)


def canvas(blue: bool) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    if STYLE == "cad":
        im = Image.new("RGBA", (W, H), BG_CAD)
        draw_grid(im)
        return im, ImageDraw.Draw(im)
    im = Image.new("RGBA", (W, H), NAVY if blue else WHITE)
    return im, ImageDraw.Draw(im)


def chrome(draw, kicker: str, n: int, total: int, blue: bool):
    kf = F_b(22)
    nf = F_b(24)
    if STYLE == "cad":
        draw_tracked(draw, kicker.upper(), kf, CAD_BLUE, PAD, 56, 3)
        num = f"{n:02d} / {total:02d}"
        nw = tracked_width(draw, num, nf, 2)
        draw_tracked(draw, num, nf, MUTED, W - PAD - nw, 54, 2)
        return
    kfill = ORANGE if blue else MUTED
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


def render_hook(s, n, total, folder: Path):
    """Обложка по референсу: Claude + AutoCAD, чертёж, зачем вручную."""
    im, d = canvas(False)
    chrome(d, s["kicker"], n, total, False)
    # марки связки — текст, без поддельных логотипов
    pill_y = 100
    d.rounded_rectangle((PAD, pill_y, PAD + 168, pill_y + 52), 22, fill=WHITE)
    d.ellipse((PAD + 16, pill_y + 16, PAD + 36, pill_y + 36), fill=ORANGE)
    d.text((PAD + 44, pill_y + 12), "Claude", font=F_sb(22), fill=INK)
    plus_x = PAD + 184
    d.text((plus_x, pill_y + 10), "+", font=F_m(28), fill=MUTED)
    d.rounded_rectangle((plus_x + 40, pill_y, plus_x + 40 + 210, pill_y + 52), 22, fill=WHITE)
    d.ellipse((plus_x + 56, pill_y + 16, plus_x + 76, pill_y + 36), fill=CAD_BLUE)
    d.text((plus_x + 84, pill_y + 12), "AutoCAD", font=F_sb(22), fill=INK)
    yy = 180
    d.text((PAD, yy), "Claude +", font=F_b(86), fill=INK)
    d.text((PAD, yy + 96), "AutoCAD", font=F_b(86), fill=CAD_BLUE)
    q = s.get("question") or s.get("body") or ""
    ql = wrap(d, q, F_sb(36), W - PAD * 2)
    qy = yy + 210
    draw_lines(d, ql, F_sb(36), INK, PAD, qy, 48)
    img_top = qy + 48 * len(ql) + 24
    photo = Image.open(resolve_image(s["image"], folder))
    inner_w = W - PAD * 2 - 32
    img_h = int(inner_w * photo.height / max(1, photo.width)) + 36
    img_bot = min(H - 180, img_top + img_h)
    paste_plan(
        im,
        resolve_image(s["image"], folder),
        (PAD, img_top, W - PAD, img_bot),
        radius=20,
        pad=16,
        bg=WHITE,
    )
    pill = s.get("pill") or "ПЛАН + КОМАНДЫ + ПРОВЕРКА"
    pf = F_b(18)
    pw = tracked_width(d, pill, pf, 2) + 48
    px = (W - pw) / 2
    py = img_bot - 28
    d.rounded_rectangle((px, py, px + pw, py + 52), 18, fill=NAVY)
    draw_tracked(d, pill, pf, WHITE, px + 24, py + 16, 2)
    foot = s.get("footer") or "Как работает связка — листай"
    d.text((PAD, H - 120), foot, font=F_m(28), fill=MUTED)
    return im


def render_cover(s, n, total, folder: Path):
    im, d = canvas(True)
    chrome(d, s["kicker"], n, total, True)
    fb = F_bebas(148)
    yy = 150
    for line in s["title"]:
        d.text((PAD, yy), line, font=fb, fill=WHITE)
        yy += 142
    body = F_m(42)
    if s.get("image"):
        lines = wrap(d, s["body"], body, W - PAD * 2)
        body_h = 52 * len(lines)
        paste_plan(
            im,
            resolve_image(s["image"], folder),
            (PAD, yy + 12, W - PAD, H - 86 - body_h),
            radius=24,
            pad=28,
            bg=WHITE,
        )
        draw_lines(d, lines, body, WHITE, PAD, H - 78 - body_h, 52)
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
    title_fill = INK if STYLE == "cad" else (WHITE if blue else NAVY)
    title = s["title"]
    d.text((PAD, 130), title, font=F_b(52) if STYLE == "cad" else F_bebas(120 if len(title) > 14 else 132), fill=title_fill)
    bf = F_m(38)
    nf = F_m(28)
    body_lines = wrap(d, s["body"], bf, W - PAD * 2) if s.get("body") else []
    note_lines = wrap(d, s["note"], nf, W - PAD * 2) if s.get("note") else []
    stats = s.get("stats") or []
    stats_h = 110 if stats else 0
    footer = 24 + 48 * len(body_lines) + 36 * len(note_lines) + stats_h
    top = 280
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
        vf, lf = F_bebas(64), F_b(24)
        for i, row in enumerate(stats):
            cx = PAD + col_w * i
            lab_fill = WHITE if (STYLE != "cad" and blue) else MUTED
            d.text((cx, yy), str(row["value"]), font=vf, fill=ORANGE)
            d.text((cx, yy + 68), row["label"].upper(), font=lf, fill=lab_fill)
        yy += stats_h
    if body_lines:
        yy = draw_lines(d, body_lines, bf, title_fill, PAD, yy, 48)
    if note_lines:
        draw_lines(d, note_lines, nf, MUTED, PAD, yy + 8, 34)
    return im


def render_page(s, n, total, folder: Path):
    """Страница гайда как слайд Instagram 1080×1350. Чертежи не перерисовываем."""
    src = Image.open(resolve_image(s["image"], folder)).convert("RGBA")
    if src.size != (W, H):
        bg = NAVY if s.get("blue") else WHITE
        im = Image.new("RGBA", (W, H), bg)
        scale = min(W / src.width, H / src.height)
        nw, nh = max(1, int(src.width * scale)), max(1, int(src.height * scale))
        src = src.resize((nw, nh), Image.Resampling.LANCZOS)
        im.paste(src, ((W - nw) // 2, (H - nh) // 2), src)
    else:
        im = src
    d = ImageDraw.Draw(im)
    nf = F_b(20)
    num = f"{n:02d} / {total:02d}"
    nw = tracked_width(d, num, nf, 2)
    bx0, by0 = W - PAD - nw - 18, 36
    bx1, by1 = W - PAD + 10, 78
    d.rounded_rectangle((bx0, by0, bx1, by1), 12, fill=WHITE)
    draw_tracked(d, num, nf, ORANGE, W - PAD - nw, 44, 2)
    return im


def render_numbered(s, n, total, folder: Path):
    im, d = canvas(False)
    chrome(d, s["kicker"], n, total, False)
    d.text((PAD, 130), s["title"], font=F_bebas(136) if STYLE != "cad" else F_b(56), fill=INK if STYLE == "cad" else NAVY)
    yy = 320
    nf = F_bebas(84)
    bf = F_m(48)
    n_items = max(1, len(s["items"]))
    slot = max(150, (H - 80 - yy) // n_items)
    for i, item in enumerate(s["items"], 1):
        d.text((PAD, yy), f"{i:02d}", font=nf, fill=ORANGE)
        lines = wrap(d, item, bf, 720)
        draw_lines(d, lines, bf, NAVY, PAD + 150, yy + 14, 60)
        yy += slot
    return im


def render_bigstat(s, n, total, folder: Path):
    im, d = canvas(True)
    chrome(d, s["kicker"], n, total, True)
    d.text((PAD, 180), s["title"], font=F_bebas(72), fill=WHITE)
    val = s["value"]
    vf = F_bebas(200 if len(val) <= 4 else 140)
    tw = d.textlength(val, font=vf)
    d.text(((W - tw) / 2, 390), val, font=vf, fill=ORANGE)
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
    d.text((PAD, 120), s["title"], font=F_bebas(136) if STYLE != "cad" else F_b(56), fill=INK if STYLE == "cad" else NAVY)
    yy = 310
    bf = F_m(46)
    n_items = max(1, len(s["items"]))
    slot = max(140, (H - 90 - yy) // n_items)
    for item in s["items"]:
        check(d, PAD, yy + 10, 24)
        lines = wrap(d, item, bf, 780)
        draw_lines(d, lines, bf, NAVY, PAD + 80, yy, 58)
        yy += slot
    if s.get("note"):
        nf = F_m(26)
        nlines = wrap(d, s["note"], nf, W - PAD * 2)
        draw_lines(d, nlines, nf, MUTED, PAD, min(yy + 24, H - 40 - 38 * len(nlines)), 38)
    return im


def render_stages(s, n, total, folder: Path):
    im, d = canvas(True)
    chrome(d, s["kicker"], n, total, True)
    d.text((PAD, 120), s["title"], font=F_bebas(136) if STYLE != "cad" else F_b(56), fill=INK if STYLE == "cad" else WHITE)
    yy = 280
    nf = F_bebas(64)
    bf = F_m(42)
    n_items = max(1, len(s["items"]))
    gap = 18
    remaining = H - 70 - yy
    box_h = (remaining - gap * (n_items - 1)) // n_items
    box_h = max(140, box_h)
    for i, item in enumerate(s["items"], 1):
        d.rounded_rectangle((PAD, yy, W - PAD, yy + box_h), 18, fill=MUTED)
        lines = wrap(d, item, bf, 700)
        text_h = 50 * len(lines)
        ty = yy + max(24, (box_h - text_h) // 2 - 8)
        d.text((PAD + 28, ty), f"{i:02d}", font=nf, fill=ORANGE)
        draw_lines(d, lines, bf, WHITE, PAD + 150, ty + 6, 50)
        yy += box_h + gap
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


def render_offers(s, n, total, folder: Path):
    im, d = canvas(False)
    chrome(d, s["kicker"], n, total, False)
    d.text((PAD, 110), s["title"], font=F_b(56) if STYLE == "cad" else F_bebas(136), fill=INK if STYLE == "cad" else NAVY)
    if s.get("body"):
        bl = wrap(d, s["body"], F_m(40), W - PAD * 2)
        draw_lines(d, bl, F_m(40), MUTED, PAD, 260, 52)
        yy = 260 + 52 * len(bl) + 16
    else:
        yy = 270
    bf = F_m(40)
    tf = F_bebas(80)
    badge_f = F_b(20)
    gap = 28
    remaining = H - 70 - yy
    box_h = (remaining - gap * (len(s["offers"]) - 1)) // max(1, len(s["offers"]))
    box_h = max(240, box_h)
    for off in s["offers"]:
        d.rounded_rectangle((PAD, yy, W - PAD, yy + box_h), 24, fill=GRAY)
        lines = wrap(d, off["text"], bf, W - PAD * 2 - 72)
        content_h = 56 + 86 + 48 * len(lines)
        inner_y = yy + max(28, (box_h - content_h) // 2)
        bw = tracked_width(d, off["badge"].upper(), badge_f, 3) + 32
        d.rounded_rectangle((PAD + 36, inner_y, PAD + 36 + bw, inner_y + 40), 12, fill=ORANGE)
        draw_tracked(d, off["badge"].upper(), badge_f, WHITE, PAD + 52, inner_y + 8, 3)
        d.text((PAD + 36, inner_y + 52), off["title"], font=tf, fill=NAVY)
        draw_lines(d, lines, bf, MUTED, PAD + 36, inner_y + 148, 48)
        yy += box_h + gap
    return im


def render_cta(s, n, total, folder: Path):
    im, d = canvas(True)
    chrome(d, s["kicker"], n, total, True)
    fb = F_b(64) if STYLE == "cad" else F_bebas(140)
    tfill = INK if STYLE == "cad" else WHITE
    yy = 130
    for line in s["title"]:
        d.text((PAD, yy), line, font=fb, fill=tfill)
        yy += 132
    expl_f = F_m(38)
    for line in s.get("lines") or []:
        elines = wrap(d, line, expl_f, W - PAD * 2)
        yy = draw_lines(d, elines, expl_f, tfill, PAD, yy + 8, 40)
    yy += 24
    if s.get("qr"):
        qr = Image.open(resolve_image(s["qr"], folder)).convert("RGBA")
        side = 300
        qr = qr.resize((side, side), Image.Resampling.NEAREST)
        card = 344
        cx = (W - card) // 2
        d.rounded_rectangle((cx, yy, cx + card, yy + card), 24, fill=WHITE)
        pad_q = (card - side) // 2
        im.paste(qr, (cx + pad_q, yy + pad_q), qr)
        yy += card + 28
    if s.get("link"):
        lf = F_sb(36)
        tw = d.textlength(s["link"], font=lf)
        box_h = 92
        d.rounded_rectangle((PAD, yy, W - PAD, yy + box_h), 18, fill=ORANGE)
        d.text(((W - tw) / 2, yy + 26), s["link"], font=lf, fill=WHITE)
        yy += box_h + 20
    elif s.get("words"):
        wf = F_bebas(64)
        for word in s["words"]:
            d.rounded_rectangle((PAD, yy, W - PAD, yy + 108), 18, fill=ORANGE)
            tw = d.textlength(word, font=wf)
            d.text(((W - tw) / 2, yy + 22), word, font=wf, fill=WHITE)
            yy += 128
    elif s.get("action"):
        af = F_sb(30)
        action_lines = wrap(d, s["action"], af, W - PAD * 2 - 64)
        box_h = 48 + 44 * len(action_lines) + 20
        d.rounded_rectangle((PAD, yy, W - PAD, yy + box_h), 16, fill=ORANGE)
        draw_lines(d, action_lines, af, WHITE, PAD + 32, yy + 32, 44)
        yy += box_h + 28
    if s.get("note"):
        nf = F_m(24)
        nlines = wrap(d, s["note"], nf, W - PAD * 2)
        draw_lines(d, nlines, nf, MUTED if STYLE == "cad" else (255, 255, 255, 200), PAD, min(yy + 8, H - 160), 34)
    cf = F_b(32)
    draw_tracked(d, s["contact"], cf, ORANGE, PAD, min(yy + 20, H - 90), 2)
    return im


RENDERERS = {
    "cover": render_cover,
    "hook": render_hook,
    "page": render_page,
    "plan": render_plan,
    "numbered": render_numbered,
    "bigstat": render_bigstat,
    "checks": render_checks,
    "stages": render_stages,
    "duties": render_duties,
    "results": render_results,
    "apply": render_apply,
    "offers": render_offers,
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
        if not title:
            title = s.get("image", s["type"])
        lines.append(f"| {i} | {s['type']} | {title} |")
    lines += [
        "",
        "## Подпись",
        "",
        data["caption"],
        "",
        "Как применить: пост в @xeniia_neuro. Первый слайд — обложка. "
        "Воронка: КУРС или ВНЕДРЕНИЕ боту @pikus_ai_bot. "
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
    n = len(paths)
    cols, rows = (4, 2) if n == 8 else (3, 3)
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
    global STYLE
    STYLE = data.get("style", "pikus-ig")
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

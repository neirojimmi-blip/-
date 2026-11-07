#!/usr/bin/env python3
"""Сборка карусели Ксении: 9 слайдов PNG 1080×1350 в фирменном стиле."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FONTS = ROOT / "brand" / "fonts"
W, H = 1080, 1350

BG = (46, 64, 120, 255)
PANEL = (58, 76, 142, 255)
DEEP = (36, 53, 102, 255)
CARD = (255, 255, 255, 255)
CARD2 = (242, 245, 251, 255)
ACCENT = (255, 117, 31, 255)
TEXT = (46, 64, 120, 255)
SOFT = (90, 106, 154, 255)
WHITE = (255, 255, 255, 255)
WHITE70 = (255, 255, 255, 200)
WHITE28 = (255, 255, 255, 72)


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONTS / name), size)


def F_bebas(s): return font("BebasNeue.ttf", s)
def F_m(s): return font("Montserrat-Medium.ttf", s)
def F_sb(s): return font("Montserrat-SemiBold.ttf", s)
def F_b(s): return font("Montserrat-Bold.ttf", s)
def F_pk(s): return font("Pushkin.ttf", s)


def gradient() -> Image.Image:
    strip = Image.new("RGB", (1, H))
    px = strip.load()
    for y in range(H):
        t = y / (H - 1)
        # panel → bg → deep, plus a faint orange at the top-right via later overlay
        if t < 0.38:
            u = t / 0.38
            c = tuple(int(PANEL[i] * (1 - u) + BG[i] * u) for i in range(3))
        else:
            u = (t - 0.38) / 0.62
            c = tuple(int(BG[i] * (1 - u) + DEEP[i] * u) for i in range(3))
        px[0, y] = c
    im = strip.resize((W, H), Image.Resampling.BILINEAR).convert("RGBA")
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((620, -280, 1480, 520), fill=(255, 117, 31, 38))
    glow = glow.filter(ImageFilter.GaussianBlur(60))
    return Image.alpha_composite(im, glow)


def plus(draw: ImageDraw.ImageDraw, x: int, y: int, color=WHITE28, size=22, thick=3):
    draw.rectangle((x - size // 2, y - thick // 2, x + size // 2, y + thick // 2), fill=color)
    draw.rectangle((x - thick // 2, y - size // 2, x + thick // 2, y + size // 2), fill=color)


def chrome(im: Image.Image, account: str, n: int, total: int) -> ImageDraw.ImageDraw:
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 8), fill=ACCENT)
    d.rounded_rectangle((28, 28, W - 28, H - 28), 24, outline=(255, 255, 255, 32), width=2)
    for x, y in ((48, 48), (W - 48, 48), (48, H - 48), (W - 48, H - 48)):
        plus(d, x, y)
    f = F_sb(22)
    y = 58
    draw_tracked(d, account, f, WHITE70, 80, y, 4)
    num = f"{n:02d}"
    rest = f" / {total:02d}"
    rest_w = tracked_width(d, rest, f, 3)
    num_w = tracked_width(d, num, f, 3)
    x = W - 80 - rest_w - num_w
    draw_tracked(d, num, f, ACCENT, x, y, 3)
    draw_tracked(d, rest, f, WHITE, x + num_w, y, 3)
    return d


def tracked_width(draw, text, font, tracking) -> float:
    if not text:
        return 0
    return sum(draw.textlength(ch, font=font) for ch in text) + tracking * (len(text) - 1)


def draw_tracked(draw, text, font, fill, x, y, tracking=4):
    cx = x
    for ch in text:
        draw.text((cx, y), ch, font=font, fill=fill)
        cx += draw.textlength(ch, font=font) + tracking
    return cx


def shadow_card(im: Image.Image, box, radius=24, fill=CARD):
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    x0, y0, x1, y1 = box
    sd.rounded_rectangle((x0, y0 + 14, x1, y1 + 22), radius, fill=(23, 33, 64, 80))
    sh = sh.filter(ImageFilter.GaussianBlur(16))
    im.alpha_composite(sh)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle(box, radius, fill=fill)
    d.rounded_rectangle(box, radius, outline=(46, 64, 120, 30), width=2)
    return d


def wrap(draw, text, font, max_w) -> list[str]:
    lines = []
    for para in text.split("\n"):
        words = para.split()
        if not words:
            lines.append("")
            continue
        cur = words[0]
        for w in words[1:]:
            trial = f"{cur} {w}"
            if draw.textlength(trial, font=font) <= max_w:
                cur = trial
            else:
                lines.append(cur)
                cur = w
        lines.append(cur)
    return lines


def draw_lines(draw, lines, font, fill, x, y, leading) -> int:
    yy = y
    for line in lines:
        draw.text((x, yy), line, font=font, fill=fill)
        yy += leading
    return yy


def ink_h(draw, text, font) -> tuple[int, int]:
    b = draw.textbbox((0, 0), text, font=font)
    return b[2] - b[0], b[3] - b[1]


def draw_pushkin(draw, text, x, y, size, fill=ACCENT, min_left=80, min_right=W - 80):
    f = F_pk(size)
    bbox = draw.textbbox((x, y), text, font=f)
    dx = 0
    if bbox[0] < min_left:
        dx = min_left - bbox[0]
    if bbox[2] + dx > min_right:
        dx -= (bbox[2] + dx - min_right)
    draw.text((x + dx, y), text, font=f, fill=fill)
    return draw.textbbox((x + dx, y), text, font=f)


def paint_card(im: Image.Image, painter, pad_top=44, pad_bot=56, x0=80, x1=W - 80):
    """Рисует контент, затем подгоняет белую карточку под его высоту."""
    overlay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    painter(overlay, od)
    bbox = overlay.getbbox()
    if bbox is None:
        return ImageDraw.Draw(im)
    top = max(148, bbox[1] - pad_top)
    bot = min(H - 78, bbox[3] + pad_bot)
    shadow_card(im, (x0, top, x1, bot))
    im.alpha_composite(overlay)
    return ImageDraw.Draw(im)


def draw_stat_value(draw, value: str, x: int, y: int):
    """Bebas без стрелки — рисуем 7 → 1 смешанным набором."""
    vf = F_bebas(56)
    af = F_sb(40)
    if "→" in value:
        left, right = [p.strip() for p in value.split("→", 1)]
        draw.text((x, y), left, font=vf, fill=ACCENT)
        lw = draw.textlength(left, font=vf)
        draw.text((x + lw + 8, y + 10), "→", font=af, fill=ACCENT)
        aw = draw.textlength("→", font=af)
        draw.text((x + lw + 8 + aw + 8, y), right, font=vf, fill=ACCENT)
    else:
        draw.text((x, y), value, font=vf, fill=ACCENT)


def pill(draw, text, x, y, font):
    label = text.upper()
    pad_x, pad_y = 22, 12
    tw = tracked_width(draw, label, font, 3)
    th = 22
    box = (x, y, x + tw + pad_x * 2, y + th + pad_y * 2)
    draw.rounded_rectangle(box, 999, outline=ACCENT, width=2)
    draw_tracked(draw, label, font, ACCENT, x + pad_x, y + pad_y - 2, 3)
    return box[3]


def render_cover(im, d, s):
    y = pill(d, s["kicker"], 80, 168, F_b(20))
    fb = F_bebas(168)
    yy = y + 36
    for line in s["title"]:
        d.text((80, yy), line, font=fb, fill=WHITE)
        yy += 148
    pk_y = yy + 12
    bbox = draw_pushkin(d, s["script"], 80, pk_y, 118, min_left=80, min_right=W - 80)
    body_f = F_m(40)
    lines = wrap(d, s["body"], body_f, 860)
    draw_lines(d, lines, body_f, WHITE, 80, bbox[3] + 28, 54)
    hint = F_sb(24)
    label = "ЛИСТАЙ  →"
    tw = d.textlength(label, font=hint)
    d.text((W - 80 - tw, H - 110), label, font=hint, fill=WHITE70)


def render_card(im, s):
    def painter(_ov, d):
        d.ellipse((132, 206, 146, 220), fill=ACCENT)
        draw_tracked(d, f"СЛАЙД {s['step']}", F_b(20), ACCENT, 162, 200, 3)
        d.text((132, 250), s["title"], font=F_bebas(84), fill=TEXT)
        d.rounded_rectangle((132, 370, 220, 376), 3, fill=ACCENT)
        body_f = F_m(38)
        lines = wrap(d, s["body"], body_f, 760)
        draw_lines(d, lines, body_f, TEXT, 132, 420, 54)
    paint_card(im, painter)


def render_insight(im, d, s):
    y = pill(d, f"слайд {s['step']}", 80, 168, F_b(20))
    fb = F_bebas(96)
    yy = y + 48
    d.text((80, yy), s["title"], font=fb, fill=WHITE)
    d.text((80, yy + 96), s["title_break"], font=fb, fill=ACCENT)
    body_y = yy + 230
    if s.get("script"):
        bbox = draw_pushkin(d, s["script"], 80, yy + 210, 88)
        body_y = bbox[3] + 28
    body_f = F_m(38)
    lines = wrap(d, s["body"], body_f, 860)
    draw_lines(d, lines, body_f, WHITE, 80, body_y, 52)


def render_step(im, s):
    def painter(_ov, d):
        d.ellipse((132, 206, 146, 220), fill=ACCENT)
        draw_tracked(d, f"{s['label'].upper()} {s['number']}", F_b(20), ACCENT, 162, 200, 3)
        d.text((132, 250), s["title"], font=F_bebas(84), fill=TEXT)
        if s.get("script"):
            bbox = draw_pushkin(d, s["script"], 132, 360, 84, min_left=132, min_right=W - 132)
            rule_y = bbox[3] + 18
            body_y = rule_y + 36
        else:
            rule_y = 370
            body_y = 420
        d.rounded_rectangle((132, rule_y, 220, rule_y + 6), 3, fill=ACCENT)
        body_f = F_m(38)
        lines = wrap(d, s["body"], body_f, 760)
        draw_lines(d, lines, body_f, TEXT, 132, body_y, 54)
    paint_card(im, painter)


def render_chips(im, s):
    def painter(_ov, d):
        d.ellipse((132, 198, 146, 212), fill=ACCENT)
        draw_tracked(d, f"{s['label'].upper()} {s['number']}", F_b(20), ACCENT, 162, 192, 3)
        fb = F_bebas(76)
        yy = 240
        for line in s["title"].split("\n"):
            d.text((132, yy), line, font=fb, fill=TEXT)
            yy += 78
        d.rounded_rectangle((132, yy + 8, 220, yy + 14), 3, fill=ACCENT)
        body_f = F_m(32)
        lines = wrap(d, s["body"], body_f, 760)
        yy = draw_lines(d, lines, body_f, TEXT, 132, yy + 40, 46) + 28
        chips = s["chips"]
        gap, cols = 18, 2
        x0, cw, ch = 132, 354, 110
        cf = F_bebas(40)
        for i, chip in enumerate(chips):
            r, c = divmod(i, cols)
            x = x0 + c * (cw + gap)
            y = yy + r * (ch + gap)
            d.rounded_rectangle((x, y, x + cw, y + ch), 24, fill=CARD2)
            d.rounded_rectangle((x, y, x + cw, y + ch), 24, outline=(46, 64, 120, 30), width=2)
            fill = ACCENT if i in (0, 3) else TEXT
            tw = d.textlength(chip.upper(), font=cf)
            d.text((x + (cw - tw) / 2, y + 28), chip.upper(), font=cf, fill=fill)
    paint_card(im, painter)


def render_split(im, s):
    def painter(_ov, d):
        d.ellipse((132, 198, 146, 212), fill=ACCENT)
        draw_tracked(d, f"{s['label'].upper()} {s['number']}", F_b(20), ACCENT, 162, 192, 3)
        d.text((132, 236), s["title"], font=F_bebas(76), fill=TEXT)
        y = 340
        pw, ph, gap = 354, 300, 18
        panes = [
            (s["left_label"], s["left"], CARD2, TEXT, False),
            (s["right_label"], s["right"], BG, WHITE, True),
        ]
        for i, (lab, txt, fill, col, _hot) in enumerate(panes):
            x = 132 + i * (pw + gap)
            d.rounded_rectangle((x, y, x + pw, y + ph), 24, fill=fill)
            if not _hot:
                d.rounded_rectangle((x, y, x + pw, y + ph), 24, outline=(46, 64, 120, 30), width=2)
            draw_tracked(d, lab.upper(), F_b(18), ACCENT, x + 28, y + 28, 3)
            bf = F_sb(30)
            lines = wrap(d, txt, bf, pw - 56)
            draw_lines(d, lines, bf, col, x + 28, y + 78, 42)
        note_y = y + ph + 28
        if s.get("script"):
            bbox = draw_pushkin(d, s["script"], 132, y + ph + 16, 78, min_left=132, min_right=W - 132)
            note_y = bbox[3] + 12
        bf = F_m(30)
        lines = wrap(d, s["note"], bf, 760)
        draw_lines(d, lines, bf, TEXT, 132, note_y, 42)
    paint_card(im, painter)


def render_stats(im, s):
    def painter(_ov, d):
        d.ellipse((132, 198, 146, 212), fill=ACCENT)
        draw_tracked(d, f"СЛАЙД {s['step']}", F_b(20), ACCENT, 162, 192, 3)
        d.text((132, 236), s["title"], font=F_bebas(76), fill=TEXT)
        d.rounded_rectangle((132, 334, 220, 340), 3, fill=ACCENT)
        bf = F_m(30)
        lines = wrap(d, s["body"], bf, 760)
        yy = draw_lines(d, lines, bf, TEXT, 132, 368, 42) + 20
        cf = F_sb(28)
        uf = F_b(16)
        for st in s["stats"]:
            d.rounded_rectangle((132, yy, 948, yy + 132), 24, fill=CARD2)
            d.rounded_rectangle((132, yy, 948, yy + 132), 24, outline=(46, 64, 120, 30), width=2)
            draw_stat_value(d, st["value"], 160, yy + 22)
            if st.get("unit"):
                draw_tracked(d, st["unit"].upper(), uf, SOFT, 160, yy + 90, 2)
            cap_lines = wrap(d, st["caption"], cf, 460)
            draw_lines(d, cap_lines, cf, TEXT, 430, yy + (36 if len(cap_lines) == 1 else 24), 36)
            yy += 152
    paint_card(im, painter)


def render_offers(im, s):
    def painter(_ov, d):
        d.ellipse((132, 190, 146, 204), fill=ACCENT)
        draw_tracked(d, f"СЛАЙД {s['step']}", F_b(20), ACCENT, 162, 184, 3)
        d.text((132, 224), s["title"], font=F_bebas(76), fill=TEXT)
        bf = F_m(30)
        lines = wrap(d, s["body"], bf, 760)
        yy = draw_lines(d, lines, bf, TEXT, 132, 320, 42) + 18
        for i, o in enumerate(s["offers"]):
            hot = i == 1
            fill = BG if hot else CARD2
            d.rounded_rectangle((132, yy, 948, yy + 250), 24, fill=fill)
            if not hot:
                d.rounded_rectangle((132, yy, 948, yy + 250), 24, outline=(46, 64, 120, 30), width=2)
            lab = o["badge"].upper()
            bfnt = F_b(16)
            tw = tracked_width(d, lab, bfnt, 3)
            bx0, by0 = 164, yy + 28
            d.rounded_rectangle((bx0, by0, bx0 + tw + 28, by0 + 36), 999, fill=ACCENT)
            draw_tracked(d, lab, bfnt, WHITE, bx0 + 14, by0 + 8, 3)
            title_c = WHITE if hot else TEXT
            body_c = WHITE if hot else SOFT
            d.text((164, yy + 80), o["title"], font=F_bebas(44), fill=title_c)
            bl = wrap(d, o["text"], F_m(26), 720)
            draw_lines(d, bl, F_m(26), body_c, 164, yy + 140, 36)
            yy += 272
    paint_card(im, painter)


def render_cta(im, d, s):
    y = pill(d, s["kicker"], 80, 168, F_b(20))
    yy = y + 48
    words = s["words"]
    gap = 20
    ww = (W - 160 - gap) // 2
    hh = 150
    wf = F_bebas(68)
    for i, w in enumerate(words):
        x = 80 + i * (ww + gap)
        # shadow
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
        sd = ImageDraw.Draw(sh)
        sd.rounded_rectangle((x, yy + 10, x + ww, yy + hh + 16), 24, fill=(23, 33, 64, 80))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(12)))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((x, yy, x + ww, yy + hh), 24, fill=ACCENT)
        tw = d.textlength(w, font=wf)
        d.text((x + (ww - tw) / 2, yy + 36), w, font=wf, fill=WHITE)
    d = ImageDraw.Draw(im)
    bbox = draw_pushkin(d, s["script"], 110, yy + hh + 20, 110, min_left=88, min_right=W - 80)
    yy = bbox[3] + 36
    bf = F_m(32)
    for line in s["lines"]:
        if " — " in line:
            a, b = line.split(" — ", 1)
            af = F_b(32)
            aw = d.textlength(a, font=af)
            d.text((80, yy), a, font=af, fill=ACCENT)
            rest = " — " + b
            # wrap rest after the keyword
            d.text((80 + aw, yy), " —", font=bf, fill=WHITE)
            rest_lines = wrap(d, b, bf, 860)
            # first line continues if short
            d.text((80 + aw + d.textlength(" — ", font=bf), yy), rest_lines[0], font=bf, fill=WHITE)
            yy += 48
            for extra in rest_lines[1:]:
                d.text((80, yy), extra, font=bf, fill=WHITE)
                yy += 44
            yy += 16
        else:
            lines = wrap(d, line, bf, 860)
            yy = draw_lines(d, lines, bf, WHITE, 80, yy, 44) + 12


def render_one(slide: dict, idx: int, total: int, account: str) -> Image.Image:
    im = gradient()
    d = chrome(im, account, idx, total)
    t = slide["type"]
    if t == "cover":
        render_cover(im, d, slide)
    elif t == "card":
        render_card(im, slide)
    elif t == "insight":
        render_insight(im, d, slide)
    elif t == "step":
        render_step(im, slide)
    elif t == "chips":
        render_chips(im, slide)
    elif t == "split":
        render_split(im, slide)
    elif t == "stats":
        render_stats(im, slide)
    elif t == "offers":
        render_offers(im, slide)
    elif t == "cta":
        render_cta(im, d, slide)
    else:
        raise ValueError(t)
    return im.convert("RGB")


def copy_md(data: dict) -> str:
    rows = [
        "| № | Заголовок | Текст | Pushkin | Фото |",
        "|---|---|---|---|---|",
    ]
    photos = data.get("photos") or ["—"] * len(data["slides"])
    for i, s in enumerate(data["slides"], 1):
        title = s.get("title")
        if isinstance(title, list):
            title = " ".join(title)
        title = (title or s.get("kicker") or "").replace("\n", " ")
        if s.get("title_break"):
            title = f"{title} {s['title_break']}"
        if s.get("words"):
            title = " / ".join(s["words"])
        body = (s.get("body") or s.get("note") or " ".join(s.get("lines") or [])).replace("\n", " ")
        script = s.get("script") or "—"
        photo = photos[i - 1] if i - 1 < len(photos) else "—"
        rows.append(f"| {i} | {title} | {body} | {script} | {photo} |")
    rows += [
        "",
        "## Подпись к публикации",
        "",
        data["caption"],
        "",
        "Живых фото в репозитории нет — слайды графические и готовы к публикации. "
        "Если наложить свои кадры, текст не закрывать лицо; какой кадр на какой слайд — в таблице выше.",
        "",
        "Как применить: пост в @xeniia_neuro, будний слот 9–11 по Тюмени. "
        "Первый слайд — обложка. На КУРС и КОМАНДА в комментариях ответить заранее.",
        "",
    ]
    return "\n".join(rows)


def contact_sheet(paths: list[Path], dest: Path) -> None:
    cols, rows = 3, 3
    tw, gap = 360, 16
    th = int(tw * H / W)
    sheet = Image.new("RGB", (cols * tw + (cols + 1) * gap,
                              rows * th + (rows + 1) * gap), (46, 64, 120))
    for i, p in enumerate(paths):
        im = Image.open(p).convert("RGB").resize((tw, th), Image.Resampling.LANCZOS)
        r, c = divmod(i, cols)
        sheet.paste(im, (gap + c * (tw + gap), gap + r * (th + gap)))
    sheet.save(dest, "PNG")


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python3 tools/build_carousel.py carousels/<folder>", file=sys.stderr)
        return 2
    folder = Path(sys.argv[1])
    if not folder.is_absolute():
        folder = ROOT / folder
    data = json.loads((folder / "slides.json").read_text(encoding="utf-8"))
    slides = data["slides"]
    if len(slides) != 9:
        raise SystemExit(f"need 9 slides, got {len(slides)}")
    account = data.get("account", "@XENIIA_NEURO")
    pngs = []
    for i, slide in enumerate(slides, 1):
        dest = folder / f"{i:02d}.png"
        render_one(slide, i, 9, account).save(dest, "PNG", optimize=True)
        pngs.append(dest)
        print(f"wrote {dest.relative_to(ROOT)}")
    contact_sheet(pngs, folder / "preview.png")
    (folder / "copy.md").write_text(copy_md(data), encoding="utf-8")
    print(f"wrote {(folder / 'preview.png').relative_to(ROOT)}")
    print(f"wrote {(folder / 'copy.md').relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

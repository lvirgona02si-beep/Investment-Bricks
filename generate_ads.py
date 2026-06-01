#!/usr/bin/env python3
"""
Investment Bricks — Meta Ad Generator
Creates 3 x 1080x1350 (4:5) JPEG ads, one per targeting angle.
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import os
import textwrap

BASE = "/Users/Business/Desktop/Client Buildout/Investment Bricks"
ASSETS = os.path.join(BASE, "Assets")
OUT_DIR = os.path.join(ASSETS, "Ads")
os.makedirs(OUT_DIR, exist_ok=True)

# ── Fonts ──────────────────────────────────────────────────────────────────────
FONT_BOLD   = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
FONT_REG    = "/System/Library/Fonts/Supplemental/Arial.ttf"
FONT_SFNS   = "/System/Library/Fonts/SFNS.ttf"

# Fallback: use SFNS for everything if Arial isn't present
def load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.truetype(FONT_SFNS, size)

# ── Colours ────────────────────────────────────────────────────────────────────
ORANGE   = (253, 112,  20)
PEACH    = (243, 153,  95)
CHARCOAL = ( 30,  30,  30)
WHITE    = (255, 255, 255)
OFF_WHT  = (245, 240, 235)

W, H = 1080, 1350   # 4:5 portrait


def draw_multiline(draw, text, font, x, y, fill, max_width, line_spacing=1.18):
    """Draw left-aligned multiline text, wrapping at max_width pixels."""
    words = text.split()
    lines = []
    current = []
    for word in words:
        test = " ".join(current + [word])
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] > max_width and current:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))

    line_h = draw.textbbox((0, 0), "A", font=font)[3]
    for i, line in enumerate(lines):
        draw.text((x, y + i * line_h * line_spacing), line, font=font, fill=fill)
    return y + len(lines) * line_h * line_spacing


def draw_rounded_rect(draw, x1, y1, x2, y2, radius, fill):
    draw.rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=fill)


def add_gradient_overlay(img, start_alpha=0, end_alpha=210, start_y_frac=0.25):
    """Vertical dark gradient from transparent at top to dark at bottom."""
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    start_y = int(H * start_y_frac)
    for y in range(start_y, H):
        progress = (y - start_y) / (H - start_y)
        alpha = int(start_alpha + (end_alpha - start_alpha) * progress)
        draw.line([(0, y), (W, y)], fill=(0, 0, 0, alpha))
    base = img.convert("RGBA")
    combined = Image.alpha_composite(base, overlay)
    return combined.convert("RGB")


def add_top_gradient(img, end_alpha=140):
    """Subtle dark gradient from top (for logo legibility)."""
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    top_h = 220
    for y in range(top_h):
        alpha = int(end_alpha * (1 - y / top_h))
        draw.line([(0, y), (W, y)], fill=(0, 0, 0, alpha))
    base = img.convert("RGBA")
    combined = Image.alpha_composite(base, overlay)
    return combined.convert("RGB")


def place_logo(img):
    """Stamp the Investment Bricks logo top-left with a white pill bg."""
    logo_path = os.path.join(BASE, "Investment Bricks Logo.jpg")
    logo = Image.open(logo_path).convert("RGBA")
    logo_w = 260
    ratio = logo_w / logo.width
    logo_h = int(logo.height * ratio)
    logo = logo.resize((logo_w, logo_h), Image.LANCZOS)

    # White pill behind logo
    pad = 14
    pill = Image.new("RGBA", img.size, (0, 0, 0, 0))
    pill_draw = ImageDraw.Draw(pill)
    pill_draw.rounded_rectangle(
        [44 - pad, 48 - pad, 44 + logo_w + pad, 48 + logo_h + pad],
        radius=14, fill=(255, 255, 255, 235)
    )
    base = img.convert("RGBA")
    base = Image.alpha_composite(base, pill)
    base.paste(logo, (44, 48), logo)
    return base.convert("RGB")


def make_ad(bg_path, headline, sub, body, cta, out_name,
            enhance_brightness=1.0, enhance_saturation=1.1,
            gradient_start=0.22):
    img = Image.open(bg_path).convert("RGB")

    # Fill canvas (crop-centre)
    img_ratio = img.width / img.height
    canvas_ratio = W / H
    if img_ratio > canvas_ratio:
        new_h = H
        new_w = int(H * img_ratio)
    else:
        new_w = W
        new_h = int(W / img_ratio)
    img = img.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - W) // 2
    top  = (new_h - H) // 2
    img = img.crop((left, top, left + W, top + H))

    # Subtle colour enhancement
    img = ImageEnhance.Brightness(img).enhance(enhance_brightness)
    img = ImageEnhance.Color(img).enhance(enhance_saturation)

    # Gradients
    img = add_top_gradient(img, end_alpha=130)
    img = add_gradient_overlay(img, start_alpha=10, end_alpha=225, start_y_frac=gradient_start)

    # Logo
    img = place_logo(img)

    draw = ImageDraw.Draw(img)

    # ── Orange accent bar at very bottom ──────────────────────────────────────
    bar_h = 64
    draw.rectangle([(0, H - bar_h), (W, H)], fill=ORANGE)

    # Brand tagline inside bar
    tag_font = load_font(FONT_BOLD, 22)
    tag_text = "INVESTMENTBRICKS.COM.AU  ·  NEW PROPERTY SPECIALISTS"
    tb = draw.textbbox((0, 0), tag_text, font=tag_font)
    tx = (W - (tb[2] - tb[0])) // 2
    ty = H - bar_h + (bar_h - (tb[3] - tb[1])) // 2
    draw.text((tx, ty), tag_text, font=tag_font, fill=WHITE)

    # ── Text block ──────────────────────────────────────────────────────────
    TEXT_L = 56       # left margin
    TEXT_W = W - 112  # max text width
    BOTTOM_PAD = bar_h + 36

    # CTA button (draw first, then position text above it)
    cta_font  = load_font(FONT_BOLD, 30)
    cta_bbox  = draw.textbbox((0, 0), cta, font=cta_font)
    cta_tw    = cta_bbox[2] - cta_bbox[0]
    cta_th    = cta_bbox[3] - cta_bbox[1]
    btn_pad_x, btn_pad_y = 40, 20
    btn_w = cta_tw + btn_pad_x * 2
    btn_h = cta_th + btn_pad_y * 2
    btn_y = H - BOTTOM_PAD - btn_h
    draw_rounded_rect(draw, TEXT_L, btn_y, TEXT_L + btn_w, btn_y + btn_h, 8, ORANGE)
    # Button text
    draw.text((TEXT_L + btn_pad_x, btn_y + btn_pad_y), cta, font=cta_font, fill=WHITE)

    # Body text
    body_font = load_font(FONT_REG, 32)
    body_y = btn_y - 20
    lines = []
    words = body.split()
    current = []
    for word in words:
        test = " ".join(current + [word])
        bb = draw.textbbox((0, 0), test, font=body_font)
        if bb[2] - bb[0] > TEXT_W and current:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    line_h = draw.textbbox((0, 0), "A", font=body_font)[3] * 1.35
    body_y -= len(lines) * line_h + 18
    for i, line in enumerate(lines):
        draw.text((TEXT_L, body_y + i * line_h), line, font=body_font, fill=OFF_WHT)

    # Sub-headline
    sub_font = load_font(FONT_REG, 38)
    sub_lines = []
    words = sub.split()
    current = []
    for word in words:
        test = " ".join(current + [word])
        bb = draw.textbbox((0, 0), test, font=sub_font)
        if bb[2] - bb[0] > TEXT_W and current:
            sub_lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        sub_lines.append(" ".join(current))
    sub_line_h = draw.textbbox((0, 0), "A", font=sub_font)[3] * 1.3
    sub_y = body_y - len(sub_lines) * sub_line_h - 22
    for i, line in enumerate(sub_lines):
        draw.text((TEXT_L, sub_y + i * sub_line_h), line, font=sub_font, fill=PEACH)

    # Main headline
    hl_font = load_font(FONT_BOLD, 82)
    hl_lines = headline.split("\n")
    hl_line_h = draw.textbbox((0, 0), "A", font=hl_font)[3] * 1.15
    hl_y = sub_y - len(hl_lines) * hl_line_h - 28
    for i, line in enumerate(hl_lines):
        draw.text((TEXT_L, hl_y + i * hl_line_h), line, font=hl_font, fill=WHITE)

    # Save
    out_path = os.path.join(OUT_DIR, out_name)
    img.save(out_path, "JPEG", quality=95)
    print(f"✓  Saved: {out_path}")


# ── AD 1 — Dual Income / Cash Flow ────────────────────────────────────────────
make_ad(
    bg_path   = os.path.join(ASSETS, "Photo-1.jpeg"),
    headline  = "ONE BLOCK.\nTWO INCOMES.",
    sub       = "$1,220/week from a single duplex site.",
    body      = "Australian duplex investors are achieving 6%+ gross yields — nearly double a standard rental. See the full numbers in our free roadmap.",
    cta       = "Download Free Roadmap  →",
    out_name  = "ad-1-dual-income.jpg",
    enhance_brightness=1.05,
    gradient_start=0.20,
)

# ── AD 2 — Equity / Wealth Building ───────────────────────────────────────────
_ad2_img = next(f for f in os.listdir(ASSETS) if "ChatGPT" in f)
make_ad(
    bg_path   = os.path.join(ASSETS, _ad2_img),
    headline  = "BUILD WEALTH\nSMARTER.",
    sub       = "6.27% yield. ~$291K equity in 5 years.",
    body      = "Our Duplex Investment Roadmap breaks down the exact numbers — from land cost to dual income in 12–18 months.",
    cta       = "Get the Free Roadmap  →",
    out_name  = "ad-2-wealth-equity.jpg",
    enhance_brightness=1.0,
    enhance_saturation=1.08,
    gradient_start=0.22,
)

# ── AD 3 — Education / FOMO ───────────────────────────────────────────────────
_ad3_img = next(f for f in os.listdir(ASSETS) if "2026-05-19" in f)
make_ad(
    bg_path   = os.path.join(ASSETS, _ad3_img),
    headline  = "MOST INVESTORS\nMISS THIS.",
    sub       = "Two incomes. One land parcel. One strategy.",
    body      = "200+ Australian investors already use this. The Duplex Investment Roadmap reveals how — vacancy under 1.5% nationally means both dwellings stay tenanted.",
    cta       = "Download Free Roadmap  →",
    out_name  = "ad-3-education-fomo.jpg",
    enhance_brightness=1.08,
    enhance_saturation=1.1,
    gradient_start=0.15,
)

print("\nAll 3 ads generated in:", OUT_DIR)

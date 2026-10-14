import colorsys
import hashlib

from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

_SIZE = (260, 390)
_PADDING = 22
_TRANSLIT = {
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "g",
    "д": "d",
    "е": "e",
    "ё": "e",
    "ж": "zh",
    "з": "z",
    "и": "i",
    "й": "y",
    "к": "k",
    "л": "l",
    "м": "m",
    "н": "n",
    "о": "o",
    "п": "p",
    "р": "r",
    "с": "s",
    "т": "t",
    "у": "u",
    "ф": "f",
    "х": "kh",
    "ц": "ts",
    "ч": "ch",
    "ш": "sh",
    "щ": "shch",
    "ъ": "",
    "ы": "y",
    "ь": "",
    "э": "e",
    "ю": "yu",
    "я": "ya",
    " ": "-",
    "_": "-",
    "/": "-",
    ":": "-",
}


def slugify_title(title: str, max_len: int = 60) -> str:
    out, prev_dash = [], False
    for ch in title.lower():
        tr = _TRANSLIT.get(ch)
        if tr is None:
            tr = ch if ch.isascii() and ch.isalnum() else "-"
        if tr == "-":
            if not prev_dash and out:
                out.append("-")
            prev_dash = True
        else:
            out.append(tr)
            prev_dash = False
    slug = "".join(out).strip("-")[:max_len]
    return slug or hashlib.md5(title.encode("utf-8")).hexdigest()[:12]


def color_for(title: str, lightness: float = 0.28, saturation: float = 0.45):
    h = int(hashlib.md5(title.encode("utf-8")).hexdigest(), 16)
    hue = (h % 360) / 360.0
    r, g, b = colorsys.hls_to_rgb(hue, lightness, saturation)
    return (int(r * 255), int(g * 255), int(b * 255))


def fit_text(
    draw, text, max_width, max_height, min_size=14, max_size=32, line_gap=4, max_lines=5
):
    for size in range(max_size, min_size - 1, -1):
        font = _load_font(size)
        lines = _wrap(draw, text, font, max_width)
        if len(lines) <= max_lines and len(lines) * (size + line_gap) <= max_height:
            return font, lines
    font = _load_font(min_size)
    lines = _wrap(draw, text, font, max_width)[:max_lines]
    if lines:
        # подрезаем последнюю строку до влезающей + ellipsis
        last = lines[-1]
        while last and _text_width(draw, last + "…", font) > max_width:
            last = last[:-1]
        lines[-1] = (last.rstrip() or "…") + "…"
    return font, lines


def _wrap(draw, text, font, max_width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        test = f"{cur} {w}".strip()
        if _text_width(draw, test, font) <= max_width:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _load_font(size: int):
    try:
        return ImageFont.load_default(size=size)  # Pillow ≥ 10.1
    except TypeError:
        return ImageFont.load_default()  # старые Pillow


def _text_width(draw, text, font) -> int:
    b = draw.textbbox((0, 0), text, font=font)
    return b[2] - b[0]


def render_placeholder(kind: str, title: str, authors: tuple[str, ...]) -> bytes:
    bg = color_for(title)
    fg = (240, 240, 240)
    soft = (255, 255, 255, 42)  # watermark

    img = Image.new("RGB", _SIZE, bg)

    # ── watermark: первая буква, огромная, полупрозрачная ──────────────────
    letter = next((c.upper() for c in title if c.isalnum()), "")
    if letter:
        big = _load_font(size=240)
        overlay = Image.new("RGBA", _SIZE, (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        bbox = od.textbbox((0, 0), letter, font=big)
        od.text(
            (
                (_SIZE[0] - (bbox[2] - bbox[0])) / 2 - bbox[0],
                (_SIZE[1] - (bbox[3] - bbox[1])) / 2 - bbox[1],
            ),
            letter,
            fill=soft,
            font=big,
        )
        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

    draw = ImageDraw.Draw(img)

    # ── рамка ──────────────────────────────────────────────────────────────
    draw.rectangle(
        [
            (_PADDING - 10, _PADDING - 10),
            (_SIZE[0] - _PADDING + 10, _SIZE[1] - _PADDING + 10),
        ],
        outline=fg,
        width=1,
    )

    # ── заголовок (адаптивный) ─────────────────────────────────────────────
    max_w = _SIZE[0] - 2 * _PADDING
    title_font, title_lines = fit_text(
        draw,
        title,
        max_w,
        max_height=_SIZE[1] // 2,
        min_size=14,
        max_size=30,
    )
    line_h = title_font.size + 4 if hasattr(title_font, "size") else 22
    block_h = len(title_lines) * line_h
    y = (_SIZE[1] - block_h) // 2 - 20
    for line in title_lines:
        w = _text_width(draw, line, title_font)
        draw.text(((_SIZE[0] - w) / 2, y), line, fill=fg, font=title_font)
        y += line_h

    # ── авторы ─────────────────────────────────────────────────────────────
    if authors:
        a_text = ", ".join(authors)
        a_font, a_lines = fit_text(
            draw,
            a_text,
            max_w,
            max_height=60,
            min_size=11,
            max_size=15,
            max_lines=2,
        )
        ay = (
            _SIZE[1]
            - _PADDING
            - 8
            - len(a_lines) * (a_font.size + 2 if hasattr(a_font, "size") else 14)
        )
        for line in a_lines:
            w = _text_width(draw, line, a_font)
            draw.text(((_SIZE[0] - w) / 2, ay), line, fill=fg, font=a_font)
            ay += (a_font.size + 2) if hasattr(a_font, "size") else 14

    buf = BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()

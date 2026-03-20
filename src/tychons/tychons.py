# Copyright 2026 Chris Wells <chris@rhza.org>

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
tychons.py — Constellation-style visual identity badges for public keys.

Usage:
    from tychons import Badge

    # Default — uses built-in 64-word fallback list
    badge = Badge("ssh-rsa AAAAB3NzaC1yc2E...")

    # With a BIP-39 wordlist file
    badge = Badge("ssh-rsa AAAAB3NzaC1yc2E...", lang="en")
    badge = Badge("ssh-rsa AAAAB3NzaC1yc2E...", lang="es")

    badge.save_svg("my_key.svg")        # SVG — no Pillow required
    badge.save("my_key.png")            # PNG — requires Pillow
    print(badge.phrase)                 # e.g. "birch · nova"

BIP-39 wordlist files should be plain text, one word per line, 2048 words.
By default, tychons looks for them in ./wordlists/<lang>.txt
(e.g. ./wordlists/en.txt, ./wordlists/es.txt).
The search path can be overridden by passing wordlist_dir to Badge().
"""

import math
import struct
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from xml.sax.saxutils import escape as _xml_escape

try:
    import blake3
    HAS_BLAKE3 = True
except ImportError:
    import hashlib
    HAS_BLAKE3 = False
    warnings.warn(
        "blake3 not found, falling back to SHA-256. Install with: pip install blake3",
        stacklevel=2,
    )

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False


# Default fonts directory — expects NotoSans-Regular.ttf (and NotoSansSC-Regular.ttf
# for Chinese) placed here by the user.
DEFAULT_FONTS_DIR = Path(__file__).parent / "fonts"

# CJK language codes — matched to the wordlist filenames in wordlists/
# These trigger CJK font selection and single-line label layout.
_CJK_LANGS = {
    "chinese_simplified",
    "chinese_traditional",
    "japanese",
    "korean",
    # IETF aliases also accepted for convenience
    "zh-hans",
    "zh-hant",
    "zh",
    "ja",
    "ko",
}

# Map from lang code to wordlist filename stem (for non-obvious mappings)
_LANG_FILE_MAP: dict[str, str] = {
    "zh-hans": "chinese_simplified",
    "zh":      "chinese_simplified",
    "zh-hant": "chinese_traditional",
    "ja":      "japanese",
    "ko":      "korean",
}

# Map from wordlist filename stem to Noto Sans font filename
_LANG_FONT_MAP: dict[str, str] = {
    "chinese_simplified":  "NotoSansSC-Regular.ttf",
    "chinese_traditional": "NotoSansTC-Regular.ttf",
    "japanese":            "NotoSansJP-Regular.ttf",
    "korean":              "NotoSansKR-Regular.ttf",
}


def _is_cjk(lang: str | None) -> bool:
    """Return True if the language uses CJK characters (single-line label layout)."""
    return lang is not None and lang.lower() in _CJK_LANGS


import re as _re
_LANG_PATTERN = _re.compile(r'^[a-zA-Z0-9_-]+$')


def _validate_lang(lang: str) -> None:
    """Raise ValueError if lang contains characters outside [a-zA-Z0-9_-].

    This prevents path traversal attacks (e.g. '../../etc/passwd') from
    reaching the filesystem when constructing wordlist file paths.
    """
    if not _LANG_PATTERN.match(lang):
        raise ValueError(
            f"Invalid lang code {lang!r}: only alphanumeric characters, "
            "hyphens, and underscores are allowed."
        )


def _lang_to_filename(lang: str) -> str:
    """Resolve a lang code to its wordlist filename stem."""
    return _LANG_FILE_MAP.get(lang.lower(), lang.lower())


def _resolve_font_path(lang: str | None, fonts_dir: Path | str | None = None) -> Path:
    """Return the path to the appropriate Noto Sans font file for the given lang.

    Expected files in the fonts/ directory:
        NotoSans-Regular.ttf          — all non-CJK languages
        NotoSansSC-Regular.ttf        — Chinese Simplified
        NotoSansTC-Regular.ttf        — Chinese Traditional
        NotoSansJP-Regular.ttf        — Japanese
        NotoSansKR-Regular.ttf        — Korean

    Available from https://fonts.google.com/noto
    """
    base = Path(fonts_dir) if fonts_dir else DEFAULT_FONTS_DIR
    if lang:
        filename = _LANG_FONT_MAP.get(_lang_to_filename(lang), "NotoSans-Regular.ttf")
    else:
        filename = "NotoSans-Regular.ttf"
    return base / filename



# Built-in fallback — 64 words used when no BIP-39 file is available.
# Replace or supplement by providing a full 2048-word BIP-39 file per language.
_FALLBACK_WORDLIST: list[str] = [
    "apple","birch","cedar","dusk","ember","frost","grove","haven",
    "iris","jade","kelp","lunar","maple","nova","ocean","pine",
    "quartz","river","stone","tide","umber","vale","willow","xenon",
    "yew","zinc","amber","basil","coral","delta","echo","fern",
    "glade","hazel","isle","juniper","kite","larch","moss","nettle",
    "onyx","prism","reed","sage","thorn","veil","wren","yarrow",
    "zephyr","aspen","bay","cliff","dew","estuary","flint","gorge",
    "heath","inlet","jasper","knoll","ledge","mire","nook","ore",
]

# Default directory to search for <lang>.txt wordlist files.
DEFAULT_WORDLIST_DIR = Path(__file__).parent / "wordlists"


def load_wordlist(lang: str, wordlist_dir: Path | str | None = None) -> list[str]:
    """Load a BIP-39 wordlist for the given language code.

    Looks for a plain-text file at <wordlist_dir>/<lang>.txt containing
    exactly 2048 words, one per line. Lines beginning with '#' and blank
    lines are ignored, so standard BIP-39 files with comments are supported.

    Args:
        lang:         ISO language code matching the filename, e.g. "en", "es", "ja".
        wordlist_dir: Directory containing wordlist files. Defaults to
                      ./wordlists/ relative to this module file.

    Returns:
        List of words. Falls back to the built-in 64-word list with a warning
        if the file is missing or cannot be parsed.

    Raises:
        ValueError: If the file is found but contains fewer than 2 words
                    (indicates a corrupt or wrong file format).

    Expected file layout:
        wordlists/
            en.txt       # English BIP-39 (2048 words)
            es.txt       # Spanish
            ja.txt       # Japanese
            zh-hans.txt  # Chinese simplified
            ...

    BIP-39 wordlists are available from:
        https://github.com/trezor/python-mnemonic/tree/master/src/mnemonic/wordlist
    """
    _validate_lang(lang)
    search_dir = Path(wordlist_dir) if wordlist_dir else DEFAULT_WORDLIST_DIR
    path = search_dir / f"{_lang_to_filename(lang)}.txt"
    if not path.exists():
        raise FileNotFoundError(f"Wordlist not found: {path}")
    words = [
        line.strip() for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]
    if len(words) < 2:
        raise ValueError(f"Wordlist at {path} appears empty or corrupt")
    return words


def _resolve_wordlist(lang: str | None, wordlist_dir: Path | str | None) -> list[str]:
    """Internal helper — returns the fallback list if lang is None, otherwise
    delegates to load_wordlist()."""
    if lang is None:
        return _FALLBACK_WORDLIST
    _validate_lang(lang)  # defense-in-depth: validate before any path construction
    return load_wordlist(lang, wordlist_dir)


# ---------------------------------------------------------------------------
# Key derivation
# ---------------------------------------------------------------------------

def _derive(key: bytes, context: str, length: int = 32) -> bytes:
    """Derive deterministic bytes from a key and a context string."""
    if HAS_BLAKE3:
        return blake3.blake3(key, derive_key_context=context).digest(length=length)
    else:
        # Fallback: HMAC-SHA256 with key material as HMAC key, context as message (HKDF-like pattern)
        import hmac
        import hashlib
        # Extend output by hashing with counter if more than 32 bytes needed
        result = b""
        counter = 0
        while len(result) < length:
            result += hmac.new(key + counter.to_bytes(4, "big"), context.encode(), hashlib.sha256).digest()
            counter += 1
        return result[:length]


def _bytes_to_floats(b: bytes) -> list[float]:
    """Convert bytes to floats in [0, 1]."""
    return [x / 255.0 for x in b]


# ---------------------------------------------------------------------------
# Star and edge data
# ---------------------------------------------------------------------------

@dataclass
class Star:
    x: float          # canvas x (pixels)
    y: float          # canvas y (pixels)
    size: float       # radius in pixels
    brightness: float # 0–1
    neighbours: int   # how many NN edges to draw


@dataclass
class _Layout:
    """Grid-based layout constants for a given badge size.

    The canvas is divided into 10 equal divisions in each axis:
      - 1 division padding on every edge
      - Stars occupy x: [1..9], y: [1..7.5]  (8 wide, 6.5 tall)
      - Label occupies x: [1..9], y: [7.5..9] (8 wide, 1.5 tall)

    All values are in pixels at 1x. Multiply by scale for 2x render.
    """
    div: float        # size of one division in pixels
    pad: float        # 1 division from edge
    star_x0: float    # left bound of star zone
    star_x1: float    # right bound of star zone
    star_y0: float    # top bound of star zone
    star_y1: float    # bottom bound of star zone
    label_y0: float   # top of label zone
    label_y1: float   # bottom of label zone
    label_cx: float   # horizontal center for label
    star_w: float     # width of star zone
    star_h: float     # height of star zone
    label_h: float    # height of label zone
    font_size: float  # font size that fills label zone comfortably


def _layout(size: int) -> _Layout:
    """Compute grid layout for a badge of the given size."""
    div = size / 10.0
    pad = div                       # 1 division

    star_x0 = pad
    star_x1 = size - pad            # divisions 1–9
    star_y0 = pad
    star_y1 = size - pad * 3.5      # upper 6.5 divisions (top 3/4 of inner)

    label_y0 = star_y1
    label_y1 = size - pad           # lower 2.5 divisions (bottom 1/4 of inner)

    label_cx = size / 2.0
    star_w = star_x1 - star_x0
    star_h = star_y1 - star_y0
    label_h = label_y1 - label_y0

    # Font sized to fill 60% of label zone height (line_height = 1.2 * font_size)
    # This ensures the text is visually prominent within the label zone.
    # The worst-case 19-char string is wide but the label zone is always wide enough.
    font_size = (label_h * 0.60) / 1.20

    return _Layout(
        div=div, pad=pad,
        star_x0=star_x0, star_x1=star_x1,
        star_y0=star_y0, star_y1=star_y1,
        label_y0=label_y0, label_y1=label_y1,
        label_cx=label_cx,
        star_w=star_w, star_h=star_h, label_h=label_h,
        font_size=font_size,
    )


def _derive_stars(key: bytes, size: int) -> list[Star]:
    """Derive star positions, sizes, brightness and neighbour counts from key."""
    lo = _layout(size)
    raw = _derive(key, "tychons v1 stars", length=64)
    floats = _bytes_to_floats(raw)

    n = 6 + int(floats[0] * 4.99)
    star_min = size * 0.012
    star_max = size * 0.035
    stars = []
    idx = 1
    for _ in range(n):
        x = lo.star_x0 + floats[idx % len(floats)] * lo.star_w
        y = lo.star_y0 + floats[(idx + 1) % len(floats)] * lo.star_h
        s = star_min + floats[(idx + 2) % len(floats)] * (star_max - star_min)
        b = 0.45 + floats[(idx + 3) % len(floats)] * 0.55
        nb = 1 + int(floats[(idx + 4) % len(floats)] * 2.99)
        stars.append(Star(x=x, y=y, size=s, brightness=b, neighbours=nb))
        idx += 5
    return stars


def _nn_edges(stars: list[Star]) -> list[tuple[int, int]]:
    """Build nearest-neighbour edges respecting each star's neighbour count."""
    edges: set[tuple[int, int]] = set()
    for i, s in enumerate(stars):
        dists = sorted(
            [(j, (stars[j].x - s.x) ** 2 + (stars[j].y - s.y) ** 2)
             for j in range(len(stars)) if j != i],
            key=lambda t: t[1]
        )
        for k in range(s.neighbours):
            if k < len(dists):
                a, b = sorted((i, dists[k][0]))
                edges.add((a, b))
    return list(edges)


# ---------------------------------------------------------------------------
# Color derivation
# ---------------------------------------------------------------------------

def _derive_hue(key: bytes) -> int:
    """Derive a dominant hue (0–359) from the key."""
    raw = _derive(key, "tychons v1 hue", length=4)
    return struct.unpack(">I", raw)[0] % 360


def _star_color(hue: int, brightness: float) -> tuple[int, int, int]:
    """Map hue + brightness to an RGB color via HSL.

    Lightness is clamped to 60–88% to guarantee visibility against
    the fixed dark navy background (#080d14, ~5% lightness).
    """
    lightness = 0.60 + brightness * 0.28
    return _hsl_to_rgb(hue, 0.65, lightness)


def _line_color(hue: int, brightness: float, alpha: float) -> tuple[int, int, int, int]:
    """Line color: same hue, slightly desaturated, alpha-blended.

    Lightness floor of 50% keeps lines visible on dark background even
    at low alpha. Stars will always read brighter than their lines.
    """
    lightness = 0.50 + brightness * 0.25
    r, g, b = _hsl_to_rgb(hue, 0.50, lightness)
    return (r, g, b, int(alpha * 255))


def _hsl_to_rgb(h: int, s: float, lightness: float) -> tuple[int, int, int]:
    h = h % 360
    c = (1 - abs(2 * lightness - 1)) * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = lightness - c / 2
    if   h < 60:  r, g, b = c, x, 0
    elif h < 120: r, g, b = x, c, 0
    elif h < 180: r, g, b = 0, c, x
    elif h < 240: r, g, b = 0, x, c
    elif h < 300: r, g, b = x, 0, c
    else:         r, g, b = c, 0, x
    return (int((r + m) * 255), int((g + m) * 255), int((b + m) * 255))


# ---------------------------------------------------------------------------
# Word derivation
# ---------------------------------------------------------------------------

def _derive_words(key: bytes, wordlist: list[str]) -> tuple[str, str]:
    """Derive two independent checksum words from non-overlapping contexts."""
    raw1 = _derive(key, "tychons v1 word_1", length=4)
    raw2 = _derive(key, "tychons v1 word_2", length=4)
    w1 = wordlist[struct.unpack(">I", raw1)[0] % len(wordlist)]
    w2 = wordlist[struct.unpack(">I", raw2)[0] % len(wordlist)]
    return w1, w2


def _load_font(font_path: Path, size_px: int) -> "ImageFont.FreeTypeFont":
    """Load a font at the given pixel size, with graceful fallback.

    Tries in order:
      1. The requested font_path (Noto Sans from fonts/ dir)
      2. Common system sans-serif fonts
      3. Pillow's built-in default (always 10px — last resort only)
    """
    candidates = [
        str(font_path),
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "C:/Windows/Fonts/arial.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size_px)
        except Exception:
            continue
    # True last resort — PIL default is always 10px, warn loudly
    warnings.warn(
        "No suitable font found — text will render at 10px regardless of badge size. "
        "Place NotoSans-Regular.ttf in the fonts/ directory alongside tychons.py.",
        stacklevel=3,
    )
    return ImageFont.load_default()


def _render(
    stars: list[Star],
    edges: list[tuple[int, int]],
    hue: int,
    words: tuple[str, str],
    size: int,
    bg_color: tuple[int, int, int],
    lang: str | None = None,
    fonts_dir: Path | str | None = None,
) -> "Image.Image":
    if not HAS_PILLOW:
        raise ImportError(
            "Pillow is required for PNG rendering. "
            "Install with: pip install Pillow --break-system-packages. "
            "Use save_svg() for dependency-free output."
        )
    # Render at 2x for antialiasing, then downsample
    scale = 2
    S = size * scale
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img, "RGBA")

    # Background rounded rect
    corner = int(12 * scale)
    draw.rounded_rectangle([(0, 0), (S - 1, S - 1)], radius=corner, fill=bg_color + (255,))

    # Edges (drawn on a separate layer for alpha blending)
    edge_layer = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    edge_draw = ImageDraw.Draw(edge_layer, "RGBA")
    for i, j in edges:
        si, sj = stars[i], stars[j]
        mid_b = (si.brightness + sj.brightness) / 2
        col = _line_color(hue, mid_b, alpha=0.30 + mid_b * 0.40)
        edge_draw.line(
            [(si.x * scale, si.y * scale), (sj.x * scale, sj.y * scale)],
            fill=col,
            width=max(1, int(size * 0.008 * scale))
        )
    img = Image.alpha_composite(img, edge_layer)
    draw = ImageDraw.Draw(img, "RGBA")

    # Stars
    for star in stars:
        col = _star_color(hue, star.brightness)
        r = star.size * scale
        cx, cy = star.x * scale, star.y * scale
        draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill=col + (255,))

    # Label — grid layout, font sized by label zone height then clamped to width
    lo = _layout(size)
    label = f"{words[0]}  \u00b7  {words[1]}"
    label_col = _hsl_to_rgb(hue, 0.55, 0.72) + (220,)
    font_size_1x = int(lo.font_size)
    font = _load_font(_resolve_font_path(lang, fonts_dir), font_size_1x * scale)

    # Measure and clamp to usable width (star_w = 8 divisions)
    usable_w_2x = int(lo.star_w * scale)
    probe_img = Image.new("RGBA", (S * 2, font_size_1x * scale * 2))
    probe_draw = ImageDraw.Draw(probe_img)
    bbox = probe_draw.textbbox((0, 0), label, font=font)
    text_w = bbox[2] - bbox[0]
    if text_w > usable_w_2x:
        font_size_1x = int(font_size_1x * usable_w_2x / text_w)
        font = _load_font(_resolve_font_path(lang, fonts_dir), font_size_1x * scale)

    # Fade covers the label zone — use a separate layer for correct alpha compositing
    fade_layer = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    fade_draw = ImageDraw.Draw(fade_layer)
    fade_top = int(lo.label_y0 * scale)
    fade_height = S - fade_top
    for row in range(fade_top, S):
        alpha = int(200 * (row - fade_top) / fade_height)
        fade_draw.line([(0, row), (S - 1, row)], fill=bg_color + (alpha,))
    img = Image.alpha_composite(img, fade_layer)
    draw = ImageDraw.Draw(img, "RGBA")

    bbox = draw.textbbox((0, 0), label, font=font)
    tw = bbox[2] - bbox[0]
    tx = (S - tw) // 2
    # Place text baseline at label_y1 - 1 division from bottom edge
    ty = int(lo.label_y1 * scale) - int(lo.div * scale)
    draw.text((tx, ty), label, font=font, fill=label_col)

    # Downsample to target size with antialiasing
    img = img.resize((size, size), Image.LANCZOS)

    # Clip to rounded rect mask
    mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([(0, 0), (size - 1, size - 1)], radius=12, fill=255)
    img.putalpha(mask)

    return img


def _render_svg(
    stars: list[Star],
    edges: list[tuple[int, int]],
    hue: int,
    words: tuple[str, str],
    size: int,
    bg_color: tuple[int, int, int],
    lang: str | None = None,
    fonts_dir: Path | str | None = None,
) -> str:
    """Render the badge as an SVG string. No external dependencies required."""
    lo = _layout(size)
    cjk = _is_cjk(lang)
    br, bg, bb = bg_color
    rx = size // 10
    label_color = _hsl_to_rgb(hue, 0.55, 0.72)
    lr, lg, lb = label_color
    gradient_id = f"fade_{hue}"
    font_size = round(lo.font_size, 1)
    label = _xml_escape(f"{words[0]}  \u00b7  {words[1]}")
    _SVG_FONT_FAMILY = {
        "chinese_simplified":  "Noto Sans SC",
        "chinese_traditional": "Noto Sans TC",
        "japanese":            "Noto Sans JP",
        "korean":              "Noto Sans KR",
    }
    normalized = _lang_to_filename(lang) if lang else ""
    font_family = _SVG_FONT_FAMILY.get(normalized, "Noto Sans")

    parts: list[str] = []
    parts.append(
        f'<svg viewBox="0 0 {size} {size}" width="{size}" height="{size}" '
        f'xmlns="http://www.w3.org/2000/svg">'
    )

    # Defs: clip path for rounded corners + gradient for label fade
    parts.append(
        f'<defs>'
        f'<clipPath id="badge_clip">'
        f'<rect width="{size}" height="{size}" rx="{rx}"/>'
        f'</clipPath>'
        f'<linearGradient id="{gradient_id}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="rgb({br},{bg},{bb})" stop-opacity="0"/>'
        f'<stop offset="100%" stop-color="rgb({br},{bg},{bb})" stop-opacity="0.82"/>'
        f'</linearGradient>'
        f'</defs>'
    )

    # Clipping group — everything inside gets rounded corners
    parts.append('<g clip-path="url(#badge_clip)">')

    # Background
    parts.append(
        f'<rect width="{size}" height="{size}" fill="rgb({br},{bg},{bb})"/>'
    )

    # Edges
    for i, j in edges:
        si, sj = stars[i], stars[j]
        mid_b = (si.brightness + sj.brightness) / 2
        er, eg, eb, ea = _line_color(hue, mid_b, alpha=0.30 + mid_b * 0.40)
        opacity = round(ea / 255, 3)
        parts.append(
            f'<line '
            f'x1="{si.x:.2f}" y1="{si.y:.2f}" '
            f'x2="{sj.x:.2f}" y2="{sj.y:.2f}" '
            f'stroke="rgb({er},{eg},{eb})" stroke-opacity="{opacity}" '
            f'stroke-width="{round(size * 0.008, 2)}" stroke-linecap="round"/>'
        )

    # Stars
    for star in stars:
        sr, sg, sb = _star_color(hue, star.brightness)
        parts.append(
            f'<circle '
            f'cx="{star.x:.2f}" cy="{star.y:.2f}" r="{star.size:.2f}" '
            f'fill="rgb({sr},{sg},{sb})"/>'
        )

    # Label fade overlay — covers label zone
    parts.append(
        f'<rect x="0" y="{lo.label_y0:.2f}" width="{size}" height="{lo.label_h:.2f}" '
        f'fill="url(#{gradient_id})"/>'
    )

    # Text anchored to bottom of label zone with 1 division clearance.
    # CJK: no letter-spacing (it splits characters apart).
    # Font may be clamped smaller if the label overflows the star zone width.
    # SVG can't measure text at runtime so we use the measured advance ratios:
    #   Latin: ~0.54 per char, CJK: ~1.0 per char (full-width glyphs)
    n_chars = len(label)
    advance = 1.0 if cjk else 0.54
    estimated_w = font_size * n_chars * advance
    if estimated_w > lo.star_w:
        font_size = round(lo.star_w / (n_chars * advance), 1)
    letter_spacing = "0" if cjk else "0.04em"
    cy_text = round(lo.label_y1 - lo.div, 1)
    parts.append(
        f'<text x="{lo.label_cx:.1f}" y="{cy_text}" '
        f'text-anchor="middle" '
        f'font-family="{font_family}, sans-serif" '
        f'font-size="{font_size}" font-weight="500" '
        f'letter-spacing="{letter_spacing}" '
        f'fill="rgb({lr},{lg},{lb})" fill-opacity="0.86">'
        f'{label}'
        f'</text>'
    )

    parts.append('</g>')
    parts.append('</svg>')
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class Badge:
    """
    Generate a deterministic constellation badge for a public key.

    Args:
        public_key:   The public key as a string or bytes.
        size:         Badge size in pixels (default 128; works well from 64–256).
        bg_color:     Background RGB tuple (default dark navy).
        lang:         BIP-39 language code for the checksum words, e.g. "en", "es",
                      "zh-hans". If None, the built-in 64-word fallback list is used.
                      Also controls font selection and label layout (stacked vs single-line).
        wordlist_dir: Directory containing <lang>.txt wordlist files.
                      Defaults to ./wordlists/ relative to this module.
        fonts_dir:    Directory containing Noto Sans font files.
                      Defaults to ./fonts/ relative to this module.
                      Expected files: NotoSans-Regular.ttf, NotoSansSC-Regular.ttf,
                      NotoSansTC-Regular.ttf.
    """

    def __init__(
        self,
        public_key: str | bytes,
        size: int = 128,
        bg_color: tuple[int, int, int] = (8, 13, 20),
        lang: str | None = None,
        wordlist_dir: Path | str | None = None,
        fonts_dir: Path | str | None = None,
    ):
        if isinstance(public_key, str):
            public_key = public_key.encode("utf-8")

        if not isinstance(size, int) or size < 16 or size > 4096:
            raise ValueError(
                f"size must be an integer between 16 and 4096 inclusive, got {size!r}"
            )

        if (
            not isinstance(bg_color, tuple)
            or len(bg_color) != 3
            or not all(isinstance(c, int) and 0 <= c <= 255 for c in bg_color)
        ):
            raise ValueError(
                f"bg_color must be a 3-tuple of ints each in [0, 255], got {bg_color!r}"
            )

        self._key = public_key
        self._size = size
        self._bg = bg_color
        self._lang = lang
        self._fonts_dir = fonts_dir

        # Resolve wordlist
        wordlist = _resolve_wordlist(lang, wordlist_dir)

        # Derive all visual elements
        self._hue = _derive_hue(self._key)
        self._stars = _derive_stars(self._key, size)
        self._edges = _nn_edges(self._stars)
        self._words = _derive_words(self._key, wordlist)
        self._image: Optional["Image.Image"] = None
        self._svg: Optional[str] = None

    @property
    def words(self) -> tuple[str, str]:
        """The two derived checksum words for this key."""
        return self._words

    @property
    def phrase(self) -> str:
        """The checksum as a single display string e.g. 'birch · nova'."""
        return f"{self._words[0]} · {self._words[1]}"

    @property
    def svg(self) -> str:
        """The rendered badge as an SVG string."""
        if self._svg is None:
            self._svg = _render_svg(
                self._stars, self._edges, self._hue,
                self._words, self._size, self._bg,
                lang=self._lang, fonts_dir=self._fonts_dir,
            )
        return self._svg

    @property
    def image(self) -> "Image.Image":
        """The rendered badge as a PIL Image (RGBA). Requires Pillow."""
        if self._image is None:
            self._image = _render(
                self._stars, self._edges, self._hue,
                self._words, self._size, self._bg,
                lang=self._lang, fonts_dir=self._fonts_dir,
            )
        return self._image

    def save_svg(self, path: str | Path) -> None:
        """Save the badge as an SVG file. No Pillow required."""
        Path(path).write_text(self.svg, encoding="utf-8")

    def save(self, path: str | Path, fmt: str = "PNG") -> None:
        """Save the badge as a raster image. Requires Pillow."""
        self.image.save(path, fmt)

    def show(self) -> None:
        """Display the badge (opens system image viewer). Requires Pillow."""
        self.image.show()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    import sys

    if len(sys.argv) < 2:
        print("Usage: tychons <public_key_string> [output.svg|png] [size] [lang]")
        print("Example: tychons 'ssh-rsa AAAAB3...' badge.svg 128 en")
        sys.exit(1)

    key_input = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) > 2 else "badge.svg"
    lang = sys.argv[4] if len(sys.argv) > 4 else None

    try:
        badge_size = int(sys.argv[3]) if len(sys.argv) > 3 else 128
    except ValueError:
        print(f"Error: size must be an integer, got {sys.argv[3]!r}")
        sys.exit(1)

    try:
        badge = Badge(key_input, size=badge_size, lang=lang)
    except (ValueError, FileNotFoundError) as exc:
        print(f"Error: {exc}")
        sys.exit(1)

    if str(out_path).endswith(".svg"):
        badge.save_svg(out_path)
    else:
        badge.save(out_path)

    print(f"Badge saved to {out_path}")
    print(f"Checksum phrase: {badge.phrase}")


if __name__ == "__main__":
    main()

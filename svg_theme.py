"""
svg_theme.py
Shared typography + palette for the README SVGs.

Instrument Sans (SIL OFL 1.1) is embedded as base64 WOFF2 subsets so the
SVGs render in the right typeface on GitHub, where <img> SVGs cannot load
external fonts.
"""
import base64
from functools import lru_cache
from pathlib import Path

FONT_DIR = Path(__file__).parent / "assets" / "fonts"
FONT = "'Instrument Sans', 'Inter', -apple-system, 'Segoe UI', sans-serif"

# Atlas-style dark surface
BG = "#001E2B"
BORDER = "#1C2D38"
GRID = "#0E3040"
AXIS = "#2A4554"
INK_MUTED = "#89979B"
INK_SECONDARY = "#C1C7C6"
INK_PRIMARY = "#F9FBFA"

# Categorical series (validated: dark mode, surface #001E2B, all checks PASS)
S1 = "#1F9E5A"   # green
S2 = "#3D7FE0"   # blue
S3 = "#D95926"   # orange

# Status roles (reserved, always shipped with a text label)
GOOD = "#1F9E5A"
WARNING = "#C98500"
CRITICAL = "#E66767"
NEUTRAL = "#5C6C75"


@lru_cache(maxsize=1)
def font_face_css() -> str:
    rules = []
    for weight in (400, 500, 600):
        path = FONT_DIR / f"InstrumentSans-{weight}.woff2"
        if not path.exists():
            continue
        b64 = base64.b64encode(path.read_bytes()).decode("ascii")
        rules.append(
            "@font-face{font-family:'Instrument Sans';font-style:normal;"
            f"font-weight:{weight};src:url(data:font/woff2;base64,{b64}) format('woff2');}}"
        )
    return "\n".join(rules)


def style_block() -> str:
    return (
        "<style>\n" + font_face_css() + "\n"
        f"text{{font-family:{FONT};}}\n"
        "</style>"
    )

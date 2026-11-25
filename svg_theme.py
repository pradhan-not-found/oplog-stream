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


# Brand marks from Simple Icons (CC0 1.0, https://simpleicons.org), 24x24 viewBox
PYTHON_PATH = "M14.25.18l.9.2.73.26.59.3.45.32.34.34.25.34.16.33.1.3.04.26.02.2-.01.13V8.5l-.05.63-.13.55-.21.46-.26.38-.3.31-.33.25-.35.19-.35.14-.33.1-.3.07-.26.04-.21.02H8.77l-.69.05-.59.14-.5.22-.41.27-.33.32-.27.35-.2.36-.15.37-.1.35-.07.32-.04.27-.02.21v3.06H3.17l-.21-.03-.28-.07-.32-.12-.35-.18-.36-.26-.36-.36-.35-.46-.32-.59-.28-.73-.21-.88-.14-1.05-.05-1.23.06-1.22.16-1.04.24-.87.32-.71.36-.57.4-.44.42-.33.42-.24.4-.16.36-.1.32-.05.24-.01h.16l.06.01h8.16v-.83H6.18l-.01-2.75-.02-.37.05-.34.11-.31.17-.28.25-.26.31-.23.38-.2.44-.18.51-.15.58-.12.64-.1.71-.06.77-.04.84-.02 1.27.05zm-6.3 1.98l-.23.33-.08.41.08.41.23.34.33.22.41.09.41-.09.33-.22.23-.34.08-.41-.08-.41-.23-.33-.33-.22-.41-.09-.41.09zm13.09 3.95l.28.06.32.12.35.18.36.27.36.35.35.47.32.59.28.73.21.88.14 1.04.05 1.23-.06 1.23-.16 1.04-.24.86-.32.71-.36.57-.4.45-.42.33-.42.24-.4.16-.36.09-.32.05-.24.02-.16-.01h-8.22v.82h5.84l.01 2.76.02.36-.05.34-.11.31-.17.29-.25.25-.31.24-.38.2-.44.17-.51.15-.58.13-.64.09-.71.07-.77.04-.84.01-1.27-.04-1.07-.14-.9-.2-.73-.25-.59-.3-.45-.33-.34-.34-.25-.34-.16-.33-.1-.3-.04-.25-.02-.2.01-.13v-5.34l.05-.64.13-.54.21-.46.26-.38.3-.32.33-.24.35-.2.35-.14.33-.1.3-.06.26-.04.21-.02.13-.01h5.84l.69-.05.59-.14.5-.21.41-.28.33-.32.27-.35.2-.36.15-.36.1-.35.07-.32.04-.28.02-.21V6.07h2.09l.14.01zm-6.47 14.25l-.23.33-.08.41.08.41.23.33.33.23.41.08.41-.08.33-.23.23-.33.08-.41-.08-.41-.23-.33-.33-.23-.41-.08-.41.08z"
MONGODB_PATH = "M17.193 9.555c-1.264-5.58-4.252-7.414-4.573-8.115-.28-.394-.53-.954-.735-1.44-.036.495-.055.685-.523 1.184-.723.566-4.438 3.682-4.74 10.02-.282 5.912 4.27 9.435 4.888 9.884l.07.05A73.49 73.49 0 0111.91 24h.481c.114-1.032.284-2.056.51-3.07.417-.296.604-.463.85-.693a11.342 11.342 0 003.639-8.464c.01-.814-.103-1.662-.197-2.218zm-5.336 8.195s0-8.291.275-8.29c.213 0 .49 10.695.49 10.695-.381-.045-.765-1.76-.765-2.405z"
PYTHON_BLUE = "#3776AB"
MONGODB_GREEN = "#47A248"

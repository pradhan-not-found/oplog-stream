"""
generate_logos.py
Writes the small tech logos used in the README header row:
assets/logos/python.svg, mongodb.svg, pymongo.svg

Python and MongoDB marks: Simple Icons (CC0 1.0), https://simpleicons.org
PyMongo has no official mark; it is shown as the Python mark with a MongoDB leaf.
Run: python generate_logos.py
"""
from pathlib import Path

from svg_theme import MONGODB_GREEN, MONGODB_PATH, PYTHON_BLUE, PYTHON_PATH

OUT = Path(__file__).parent / "assets" / "logos"
OUT.mkdir(parents=True, exist_ok=True)


def svg(body: str, title: str) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" '
            f'role="img" aria-label="{title}"><title>{title}</title>{body}</svg>\n')


logos = {
    "python": svg(f'<path d="{PYTHON_PATH}" fill="{PYTHON_BLUE}"/>', "Python"),
    "mongodb": svg(f'<path d="{MONGODB_PATH}" fill="{MONGODB_GREEN}"/>', "MongoDB"),
    "pymongo": svg(
        f'<path d="{PYTHON_PATH}" fill="{PYTHON_BLUE}"/>'
        f'<g transform="translate(12.5 11.5) scale(0.48)">'
        f'<circle cx="12" cy="12" r="12.5" fill="#FFFFFF"/>'
        f'<path d="{MONGODB_PATH}" fill="{MONGODB_GREEN}"/></g>', "PyMongo"),
}
for name, content in logos.items():
    (OUT / f"{name}.svg").write_text(content, encoding="utf-8")
    print(f"[OK] assets/logos/{name}.svg")

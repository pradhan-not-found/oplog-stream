"""
mosaic.py
Pixel-mosaic arch shared by the banner and the section heading strips.
"""
import math

CELL, SQ = 12, 10.5  # grid pitch and square size


def h(x: int, y: int, salt: int = 0) -> float:
    """Deterministic 0..1 hash per cell (stable output between runs)."""
    n = (x * 374761393 + y * 668265263 + salt * 2147483647) & 0xFFFFFFFF
    n = (n ^ (n >> 13)) * 1274126177 & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) / 0xFFFF


def arch_cells(cx, cy, bands, x_min, x_max, y_max, color, jitter=5.0, cell=CELL, sq=SQ):
    """Squares on a grid inside concentric bands (r0, r1, density).

    The outermost band stays solid; inner bands dither and thin to the right.
    Outer-edge jitter only moves inward, so no stray squares float outside.
    """
    out = []
    for gy in range(0, int(y_max // cell) + 1):
        for gx in range(int(x_min // cell), int(x_max // cell) + 1):
            x, y = gx * cell, gy * cell
            r = math.hypot(x + sq / 2 - cx, y + sq / 2 - cy)
            for i, (r0, r1, dens) in enumerate(bands):
                j0 = r0 + (h(gx, gy, 1) - 0.5) * jitter
                j1 = r1 - h(gx, gy, 2) * jitter * 0.6
                if j0 <= r <= j1:
                    ang = math.atan2(cy - y, x - cx)
                    d = dens if i == 0 else dens * (0.7 + 0.3 * (ang / math.pi))
                    if h(gx, gy, 3 + i) < d:
                        out.append((x, y, color))
                    break
    return [c for c in out if 0 <= c[1] < y_max]


def to_svg(cells, sq=SQ) -> str:
    return "".join(f'<rect x="{x}" y="{y}" width="{sq}" height="{sq}" fill="{c}"/>'
                   for x, y, c in cells)

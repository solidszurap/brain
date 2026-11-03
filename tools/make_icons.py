"""
Draw Ember's app icons (its glowing drop with a face) as PNG files, standard
library only. Run once after changing the look:

    python tools/make_icons.py      -> web/icons/icon-180.png, -192, -512, icon-maskable-512.png
"""
import math
import os
import struct
import zlib

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web", "icons")
BG = (23, 19, 15)


def png(path, w, h, rows):
    raw = b"".join(b"\x00" + bytes(r) for r in rows)

    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
                + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def mix(a, b, k):
    k = max(0.0, min(1.0, k))
    return tuple(a[i] + (b[i] - a[i]) * k for i in range(3))


def inside_drop(x, y):
    """The drop: a circle at the bottom whose top narrows to a point (units: drop radius 1, centre 0,0)."""
    if y >= 0:
        return x * x + y * y <= 1
    k = min(1.0, -y / 1.32)                      # 0 at the middle, 1 at the tip
    width = math.cos(min(1.0, k) * math.pi / 2) ** 0.9
    return abs(x) <= width and -y <= 1.32


def colour(px, py, scale):
    """One sample: background, glow, body, eyes, mouth, cheeks."""
    x, y = (px - 0.5) / scale, (py - 0.56) / scale     # drop centre a bit below the middle
    c = BG
    d = math.hypot(x, y)
    c = mix(c, (255, 154, 77), max(0.0, 0.45 - d * 0.18) ** 1.4)          # glow
    if inside_drop(x, y):
        light = math.hypot(x + 0.3, y + 0.45)
        c = mix((255, 214, 140), (232, 110, 40), light / 1.2)              # body, lit from upper left
        c = mix(c, (150, 60, 20), max(0.0, (light - 1.1) * 1.5))
        for sx in (-0.36, 0.36):                                           # eyes
            ex, ey = (x - sx) / 0.2, (y + 0.1) / 0.24
            if ex * ex + ey * ey <= 1:
                c = (43, 20, 7)
                if math.hypot(x - sx + 0.06, y + 0.18) < 0.07:
                    c = (255, 243, 221)
            if math.hypot(x - sx * 1.55, y - 0.2) < 0.13:                  # cheeks
                c = mix(c, (255, 120, 95), 0.35)
        if abs(x) < 0.25 and abs(y - (0.3 + 0.1 * (1 - (x / 0.25) ** 2))) < 0.045:    # smile
            c = (58, 22, 8)
    return c


def draw(size, scale, ss=3):
    rows = []
    for j in range(size):
        row = []
        for i in range(size):
            acc = [0.0, 0.0, 0.0]
            for a in range(ss):
                for b in range(ss):
                    c = colour((i + (a + 0.5) / ss) / size, (j + (b + 0.5) / ss) / size, scale)
                    for k in range(3):
                        acc[k] += c[k]
            row += [int(round(v / ss / ss)) for v in acc]
        rows.append(row)
    return rows


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for size in (180, 192, 512):
        png(os.path.join(OUT, f"icon-{size}.png"), size, size, draw(size, 0.3))
    png(os.path.join(OUT, "icon-maskable-512.png"), 512, 512, draw(512, 0.24))   # smaller: safe zone for round masks
    print("icons written to", OUT)

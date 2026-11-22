#!/usr/bin/env python3
"""Draw a one-page infographic of Sunday 22 November 2026's world news.

Pure Python standard library only: a tiny bitmap-font renderer plus a
minimal PNG encoder. No network, no files read, no randomness, no clock
-- two runs write byte-identical output to /output/entry.png.

Layout: navy masthead with the date, then six stories (number chip,
category tag, headline, two-line summary), then a footer line.
"""

import os
import struct
import zlib

WIDTH = 1024
HEIGHT = 1024

# --- palette (r, g, b) -------------------------------------------------------
PAPER = (248, 244, 236)
INK = (26, 35, 50)
NAVY = (20, 33, 61)
GOLD = (217, 164, 65)
SLATE = (96, 104, 118)
WHITE = (255, 255, 255)
HAIRLINE = (216, 207, 190)

# --- 5x7 bitmap font ---------------------------------------------------------
# Each glyph is 7 rows of 5 bits, written as strings of 0/1.
_FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "a": ("00000", "00000", "01110", "00001", "01111", "10001", "01111"),
    "b": ("10000", "10000", "10110", "11001", "10001", "10001", "11110"),
    "c": ("00000", "00000", "01110", "10000", "10000", "10001", "01110"),
    "d": ("00001", "00001", "01101", "10011", "10001", "10001", "01111"),
    "e": ("00000", "00000", "01110", "10001", "11111", "10000", "01110"),
    "f": ("00110", "01001", "01000", "11110", "01000", "01000", "01000"),
    "g": ("00000", "01111", "10001", "10001", "01111", "00001", "01110"),
    "h": ("10000", "10000", "10110", "11001", "10001", "10001", "10001"),
    "i": ("00100", "00000", "01100", "00100", "00100", "00100", "01110"),
    "j": ("00010", "00000", "00110", "00010", "00010", "00010", "01100"),
    "k": ("10000", "10000", "10010", "10100", "11000", "10100", "10010"),
    "l": ("01100", "00100", "00100", "00100", "00100", "00100", "01110"),
    "m": ("00000", "00000", "11010", "10101", "10101", "10101", "10101"),
    "n": ("00000", "00000", "10110", "11001", "10001", "10001", "10001"),
    "o": ("00000", "00000", "01110", "10001", "10001", "10001", "01110"),
    "p": ("00000", "00000", "10110", "11001", "10001", "11110", "10000"),
    "q": ("00000", "00000", "01101", "10011", "10001", "01111", "00001"),
    "r": ("00000", "00000", "10110", "11001", "10000", "10000", "10000"),
    "s": ("00000", "00000", "01111", "10000", "01110", "00001", "11110"),
    "t": ("01000", "01000", "11100", "01000", "01000", "01001", "00110"),
    "u": ("00000", "00000", "10001", "10001", "10001", "10011", "01101"),
    "v": ("00000", "00000", "10001", "10001", "10001", "01010", "00100"),
    "w": ("00000", "00000", "10001", "10101", "10101", "10101", "01010"),
    "x": ("00000", "00000", "10001", "01010", "00100", "01010", "10001"),
    "y": ("00000", "00000", "10001", "10001", "01111", "00001", "01110"),
    "z": ("00000", "00000", "11111", "00010", "00100", "01000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    ":": ("00000", "01100", "00000", "00000", "00000", "01100", "00000"),
    ";": ("00000", "01100", "00000", "00000", "01100", "00100", "01000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    "*": ("00000", "10101", "01110", "11111", "01110", "10101", "00000"),
    "_": ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
    "[": ("01110", "01000", "01000", "01000", "01000", "01000", "01110"),
    "]": ("01110", "00010", "00010", "00010", "00010", "00010", "01110"),
    "<": ("00010", "00100", "01000", "10000", "01000", "00100", "00010"),
    ">": ("01000", "00100", "00010", "00001", "00010", "00100", "01000"),
    "#": ("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "@": ("01110", "10001", "10111", "10101", "10110", "10000", "01110"),
    "|": ("00100", "00100", "00100", "00100", "00100", "00100", "00100"),
    "\\": ("10000", "01000", "01000", "00100", "00010", "00010", "00001"),
}

_BLANK = ("00000", "00000", "00000", "00000", "00000", "00000", "00000")


def glyph(ch):
    """Bitmap rows for one character; unknown characters draw blank."""
    return _FONT.get(ch, _BLANK)


def text_width(text, scale):
    """Pixel width of text drawn at the given scale."""
    if not text:
        return 0
    return len(text) * 6 * scale - scale


def wrap_text(text, max_chars):
    """Greedy word wrap into lines of at most max_chars characters."""
    words = text.split(" ")
    lines = []
    current = ""
    for word in words:
        if not current:
            current = word
        elif len(current) + 1 + len(word) <= max_chars:
            current += " " + word
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


# --- canvas ------------------------------------------------------------------
class Canvas:
    def __init__(self, width, height, color):
        self.width = width
        self.height = height
        self.buf = bytearray(color * (width * height))

    def fill_rect(self, x, y, w, h, color):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.width, x + w)
        y1 = min(self.height, y + h)
        r, g, b = color
        for yy in range(y0, y1):
            base = (yy * self.width + x0) * 3
            for xx in range(x0, x1):
                off = base + (xx - x0) * 3
                self.buf[off] = r
                self.buf[off + 1] = g
                self.buf[off + 2] = b

    def draw_text(self, text, x, y, scale, color):
        cx = x
        for ch in text:
            rows = glyph(ch)
            for row_i, row in enumerate(rows):
                for col_i, bit in enumerate(row):
                    if bit == "1":
                        self.fill_rect(
                            cx + col_i * scale,
                            y + row_i * scale,
                            scale,
                            scale,
                            color,
                        )
            cx += 6 * scale

    def draw_text_centered(self, text, center_x, y, scale, color):
        self.draw_text(text, center_x - text_width(text, scale) // 2, y, scale, color)


# --- PNG encoder -------------------------------------------------------------
def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def encode_png(canvas):
    ihdr = struct.pack(">IIBBBBB", canvas.width, canvas.height, 8, 2, 0, 0, 0)
    raw = bytearray()
    stride = canvas.width * 3
    for y in range(canvas.height):
        raw.append(0)  # filter: none
        start = y * stride
        raw += canvas.buf[start:start + stride]
    idat = zlib.compress(bytes(raw), 6)
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", ihdr)
    png += _chunk(b"IDAT", idat)
    png += _chunk(b"IEND", b"")
    return png


# --- the day's news ----------------------------------------------------------
# All six stories were reported on Sunday 22 November 2026.
STORIES = [
    {
        "num": "1",
        "tag": "CLIMATE",
        "color": (14, 124, 123),
        "headline": "COP31 deadlock drags into Sunday",
        "body": "A new draft was tabled overnight in Antalya as nearly 200 nations split over fossil fuels.",
    },
    {
        "num": "2",
        "tag": "MIDDLE EAST",
        "color": (178, 58, 48),
        "headline": "Israel coalition talks resume on Sunday",
        "body": "Eisenkot invites Netanyahu's Likud back to the table in a bid to build a broad government.",
    },
    {
        "num": "3",
        "tag": "ASIA",
        "color": (43, 92, 158),
        "headline": "Hong Kong votes for Election Committee",
        "body": "856 candidates contest 723 seats on the body that picks the city's leader and lawmakers.",
    },
    {
        "num": "4",
        "tag": "EUROPE",
        "color": (106, 76, 147),
        "headline": "France protests living costs again",
        "body": "Crowds march nationwide for a fourth weekend as anger over rising prices keeps growing.",
    },
    {
        "num": "5",
        "tag": "UKRAINE",
        "color": (46, 125, 71),
        "headline": "Zelenskyy: NATO is Ukraine's surest shield",
        "body": "Ukraine's president repeats that alliance membership is the clearest security guarantee.",
    },
    {
        "num": "6",
        "tag": "SPORT",
        "color": (196, 116, 28),
        "headline": "Zverev faces Alcaraz in ATP Finals decider",
        "body": "World No. 1 Zverev meets Alcaraz in Turin tonight for the season-ending title.",
    },
]


def draw_poster():
    cv = Canvas(WIDTH, HEIGHT, PAPER)

    # Masthead.
    cv.fill_rect(0, 0, WIDTH, 164, NAVY)
    cv.fill_rect(0, 164, WIDTH, 4, GOLD)
    cv.draw_text_centered("THE WORLD IN ONE PAGE", WIDTH // 2, 30, 6, WHITE)
    cv.draw_text_centered("SUNDAY 22 NOVEMBER 2026", WIDTH // 2, 106, 4, GOLD)

    # Six stories, one row each.
    row_y = 180
    row_h = 132
    for story in STORIES:
        color = story["color"]
        # Number chip.
        cv.fill_rect(40, row_y + 6, 64, 64, color)
        cv.draw_text_centered(story["num"], 40 + 32, row_y + 6 + 15, 5, WHITE)
        # Category tag.
        cv.draw_text(story["tag"], 124, row_y + 2, 2, color)
        # Headline, up to two lines.
        head_lines = wrap_text(story["headline"], 35)[:2]
        hy = row_y + 18
        for line in head_lines:
            cv.draw_text(line, 124, hy, 4, INK)
            hy += 29
        # Summary, up to two lines.
        body_lines = wrap_text(story["body"], 47)[:2]
        by = hy + 4
        for line in body_lines:
            cv.draw_text(line, 124, by, 3, SLATE)
            by += 22
        # Hairline between rows.
        cv.fill_rect(40, row_y + row_h - 4, WIDTH - 80, 2, HAIRLINE)
        row_y += row_h

    # Footer.
    cv.draw_text_centered(
        "Drawn from reports published on 22 November 2026",
        WIDTH // 2,
        984,
        2,
        SLATE,
    )
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    png = encode_png(draw_poster())
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as f:
        f.write(png)


if __name__ == "__main__":
    main()

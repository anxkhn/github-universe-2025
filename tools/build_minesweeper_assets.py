"""Generate original pixel-art tiles, lettering, and launcher icon with Pillow."""

from pathlib import Path
from PIL import Image, ImageDraw

APP = Path(__file__).resolve().parents[1] / "badge25/apps/minesweeper"
GLYPHS = {
    "0": ["111", "101", "101", "101", "111"],
    "1": ["010", "110", "010", "010", "111"],
    "2": ["111", "001", "111", "100", "111"],
    "3": ["111", "001", "111", "001", "111"],
    "4": ["101", "101", "111", "001", "001"],
    "5": ["111", "100", "111", "001", "111"],
    "6": ["111", "100", "111", "101", "111"],
    "7": ["111", "001", "010", "010", "010"],
    "8": ["111", "101", "111", "101", "111"],
    "9": ["111", "101", "111", "001", "111"],
    "A": ["010", "101", "111", "101", "101"],
    "B": ["110", "101", "110", "101", "110"],
    "C": ["111", "100", "100", "100", "111"],
    "D": ["110", "101", "101", "101", "110"],
    "E": ["111", "100", "110", "100", "111"],
    "F": ["111", "100", "110", "100", "100"],
    "G": ["111", "100", "101", "101", "111"],
    "H": ["101", "101", "111", "101", "101"],
    "I": ["111", "010", "010", "010", "111"],
    "J": ["001", "001", "001", "101", "111"],
    "K": ["101", "101", "110", "101", "101"],
    "L": ["100", "100", "100", "100", "111"],
    "M": ["101", "111", "111", "101", "101"],
    "N": ["101", "111", "111", "111", "101"],
    "O": ["111", "101", "101", "101", "111"],
    "P": ["111", "101", "111", "100", "100"],
    "Q": ["111", "101", "101", "111", "001"],
    "R": ["110", "101", "110", "101", "101"],
    "S": ["111", "100", "111", "001", "111"],
    "T": ["111", "010", "010", "010", "010"],
    "U": ["101", "101", "101", "101", "111"],
    "V": ["101", "101", "101", "101", "010"],
    "W": ["101", "101", "111", "111", "101"],
    "X": ["101", "101", "010", "101", "101"],
    "Y": ["101", "101", "010", "010", "010"],
    "Z": ["111", "001", "010", "100", "111"],
    "+": ["000", "010", "111", "010", "000"],
    "-": ["000", "000", "111", "000", "000"],
    "/": ["001", "001", "010", "100", "100"],
    ":": ["000", "010", "000", "010", "000"],
    "!": ["010", "010", "010", "000", "010"],
    " ": ["000"] * 5,
}
CHARACTERS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ+-/:! "


def glyph(image, character, x, y, color, scale=1):
    draw = ImageDraw.Draw(image)
    for row, line in enumerate(GLYPHS[character]):
        for column, pixel in enumerate(line):
            if pixel == "1":
                left, top = x + column * scale, y + row * scale
                draw.rectangle((left, top, left + scale - 1, top + scale - 1), fill=color)


def build():
    tiles = Image.new("RGBA", (16 * 12, 12), (0, 0, 0, 0))
    colors = [
        "#215bc0",
        "#21703c",
        "#b52f3e",
        "#5b379e",
        "#8c3928",
        "#147c82",
        "#243744",
        "#526776",
    ]
    for index in range(12):
        x = index * 16
        draw = ImageDraw.Draw(tiles)
        hidden = index in (0, 10)
        draw.rectangle((x, 0, x + 14, 10), fill="#607f91" if hidden else "#d8e6e9")
        if hidden:
            draw.line((x, 10, x, 0, x + 14, 0), fill="#9db8c5")
            draw.line((x + 14, 1, x + 14, 10, x + 1, 10), fill="#334e60")
        if 2 <= index <= 9:
            glyph(tiles, str(index - 1), x + 6, 3, colors[index - 2])
        if index == 10:
            draw.line((x + 6, 2, x + 6, 8), fill="#ffffff")
            draw.polygon(((x + 7, 2), (x + 11, 4), (x + 7, 5)), fill="#ffda65")
            draw.line((x + 4, 8, x + 9, 8), fill="#ffffff")
        if index == 11:
            draw.line((x + 7, 1, x + 7, 9), fill="#233543")
            draw.line((x + 3, 5, x + 11, 5), fill="#233543")
            draw.line((x + 4, 2, x + 10, 8), fill="#233543")
            draw.line((x + 4, 8, x + 10, 2), fill="#233543")
            draw.ellipse((x + 4, 2, x + 10, 8), fill="#233543")
            draw.point((x + 6, 3), fill="#ffffff")
    tiles.save(APP / "tiles.png", optimize=True)
    lettering = Image.new("RGBA", (len(CHARACTERS) * 4, 6), (0, 0, 0, 0))
    for index, character in enumerate(CHARACTERS):
        glyph(lettering, character, index * 4, 0, "#f4f8fa")
    lettering.save(APP / "lettering.png", optimize=True)
    icon = Image.new("RGB", (24, 24), "#172a37")
    draw = ImageDraw.Draw(icon)
    draw.rounded_rectangle((1, 1, 22, 22), radius=4, fill="#607f91", outline="#9db8c5")
    draw.line((12, 4, 12, 20), fill="#172a37", width=2)
    draw.line((4, 12, 20, 12), fill="#172a37", width=2)
    draw.line((6, 6, 18, 18), fill="#172a37", width=2)
    draw.line((6, 18, 18, 6), fill="#172a37", width=2)
    draw.ellipse((7, 7, 17, 17), fill="#172a37")
    draw.rectangle((9, 8, 11, 10), fill="#ffda65")
    icon.save(APP / "icon.png", optimize=True)


if __name__ == "__main__":
    build()

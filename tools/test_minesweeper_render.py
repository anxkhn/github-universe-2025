"""Render exact pixel assets and assert drawing bounds and button combinations."""

import importlib.util
import sys
import types
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "badge25/apps/minesweeper"


class Shape:
    def __init__(self, x, y, width, height):
        self.box = (x, y, x + width - 1, y + height - 1)

    def stroke(self, width):
        self.outline = width
        return self


class Screen:
    def clear(self):
        self.image = Image.new("RGBA", (160, 120), self.brush)

    def draw(self, shape):
        x, y, right, bottom = shape.box
        assert 0 <= x <= right < 160 and 0 <= y <= bottom < 120, shape.box
        draw = ImageDraw.Draw(self.image)
        if hasattr(shape, "outline"):
            draw.rectangle(shape.box, outline=self.brush, width=shape.outline)
        else:
            draw.rectangle(shape.box, fill=self.brush)

    def blit(self, image, x, y):
        assert x >= 0 and y >= 0 and x + image.width <= 160 and y + image.height <= 120
        self.image.alpha_composite(image, (x, y))


class Sheet:
    def __init__(self, path, columns, rows):
        self.image = Image.open(APP / Path(path).name).convert("RGBA")
        self.width = self.image.width // columns
        self.height = self.image.height // rows

    def sprite(self, column, row):
        x, y = column * self.width, row * self.height
        return self.image.crop((x, y, x + self.width, y + self.height))


screen = Screen()
io = types.SimpleNamespace(
    BUTTON_A="A",
    BUTTON_B="B",
    BUTTON_C="C",
    BUTTON_UP="U",
    BUTTON_DOWN="D",
    pressed=set(),
    held=set(),
    released=set(),
)
sys.modules["badgeware"] = types.SimpleNamespace(
    screen=screen,
    io=io,
    SpriteSheet=Sheet,
    shapes=types.SimpleNamespace(rectangle=Shape),
    brushes=types.SimpleNamespace(color=lambda *rgb: (*rgb, 255)),
)
sys.path.insert(0, str(APP))
spec = importlib.util.spec_from_file_location("minesweeper_app", APP / "__init__.py")
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)
app.init()
app.update()
app.cursor = 31
io.pressed, io.held = {"A"}, {"A"}
app.update()
assert app.cursor == 31
io.pressed, io.held = {"B"}, {"A", "B"}
app.update()
assert app.cursor == 31 and 31 in app.game.flags and not app.game.started
io.pressed, io.held, io.released = set(), set(), {"A", "B"}
app.update()
assert app.cursor == 31
io.released = set()
app.game.flags.clear()
app.game.started = True
app.game.mines = {1, 5, 8, 15, 19, 34, 43, 50, 56, 61}
app.game.reveal(31)
app.game.flag(1)
app.update()
output = ROOT / "docs/images"
output.mkdir(parents=True, exist_ok=True)
screen.image.convert("RGB").save(output / "minesweeper.png", optimize=True)
for result in ("Won", "Lost"):
    app.game.result = result
    app.update()
for cell in range(63):
    app.cursor = cell
    app.update()
print("Minesweeper all-cell/state rendering bounds and flag-combination checks passed")

"""Render all cursor positions and outcomes with the installed Badgeware API."""

import sys
from badgeware import io, Image

sys.path.insert(0, "/system/apps/minesweeper")
app = __import__("/system/apps/minesweeper")
app.init()
io.poll()
app.update()
app.game.reveal(31)
for result in (None, "Won", "Lost"):
    app.game.result = result
    for cell in range(63):
        app.cursor = cell
        app.update()
for filename in ("icon.png", "tiles.png", "lettering.png"):
    image = Image.load("/system/apps/minesweeper/" + filename)
    print("PASS", filename, image.width, image.height)
print("PASS 189 cursor/state renders on the installed badge")

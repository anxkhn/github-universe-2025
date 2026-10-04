"""Check first-click safety, flood fill, flags, win, loss, and chording."""

import importlib.util
from pathlib import Path

path = Path(__file__).resolve().parents[1] / "badge25/apps/minesweeper/game.py"
spec = importlib.util.spec_from_file_location("minesweeper", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
Game, neighbors = module.Game, module.neighbors
for cell in range(63):
    game = Game()
    game.reveal(cell)
    assert len(game.mines) == 10
    assert not game.mines.intersection({cell} | set(neighbors(cell)))
    assert game.number(cell) == 0 and cell in game.opened
    assert game.result != "Lost"
game = Game()
game.flag(0)
game.reveal(0)
assert not game.started
game.flag(0)
game.reveal(0)
mine = next(iter(game.mines))
game.flag(mine)
game.reveal(mine)
assert game.result is None
game.flag(mine)
game.reveal(mine)
assert game.result == "Lost"
game = Game()
game.plant(0)
for cell in range(63):
    if cell not in game.mines:
        game.reveal(cell)
assert game.result == "Won"
game = Game()
game.started = True
game.mines = set(range(10))
game.reveal(18)
assert game.number(18) == 1
game.flag(9)
game.reveal(18)
assert 19 in game.opened
game = Game()
game.started = True
game.mines = set(range(10))
game.reveal(18)
game.flag(19)
game.reveal(18)
assert game.result == "Lost"
print("Minesweeper first-click safety, flood fill, flags, win/loss, and chording passed")

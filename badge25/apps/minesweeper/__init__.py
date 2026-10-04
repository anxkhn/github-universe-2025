import sys
from badgeware import screen, io, shapes, brushes, SpriteSheet

sys.path.insert(0, "/system/apps/minesweeper")
from game import Game, WIDTH, HEIGHT, MINES

CHARACTERS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ+-/:! "
game = Game()
cursor = 0
combo_held = False
a_pending = False
tiles = None
letters = None
background = brushes.color(23, 42, 55)
panel = brushes.color(44, 64, 77)
yellow = brushes.color(255, 218, 101)
red = brushes.color(190, 50, 64)


def init():
    global game, cursor, combo_held, a_pending, tiles, letters
    game = Game()
    cursor = 0
    combo_held = a_pending = False
    tiles = SpriteSheet("/system/apps/minesweeper/tiles.png", 12, 1)
    letters = SpriteSheet("/system/apps/minesweeper/lettering.png", len(CHARACTERS), 1)


def text(value, x, y):
    for character in value:
        screen.blit(letters.sprite(CHARACTERS.index(character), 0), x, y)
        x += 4


def update():
    global game, cursor, combo_held, a_pending
    restart = io.BUTTON_A in io.held and io.BUTTON_C in io.held
    flag = io.BUTTON_A in io.held and io.BUTTON_B in io.held
    if restart or flag:
        if not combo_held:
            if restart:
                game = Game()
                cursor = 0
            else:
                game.flag(cursor)
        a_pending = False
    else:
        x, y = cursor % WIDTH, cursor // WIDTH
        if io.BUTTON_A in io.pressed:
            a_pending = True
        if io.BUTTON_A in io.released and a_pending:
            x = (x - 1) % WIDTH
            a_pending = False
        if io.BUTTON_C in io.pressed:
            x = (x + 1) % WIDTH
        if io.BUTTON_UP in io.pressed:
            y = (y - 1) % HEIGHT
        if io.BUTTON_DOWN in io.pressed:
            y = (y + 1) % HEIGHT
        cursor = y * WIDTH + x
        if io.BUTTON_B in io.pressed:
            game.reveal(cursor)
    combo_held = restart or flag

    screen.brush = background
    screen.clear()
    screen.brush = panel
    screen.draw(shapes.rectangle(4, 3, 152, 14))
    text("MINES", 8, 7)
    text("%02d" % max(0, MINES - len(game.flags)), 34, 7)
    status = "YOU WIN!" if game.result == "Won" else "MINE HIT" if game.result else "SWEEPER"
    text(status, 152 - len(status) * 4, 7)
    for cell in range(WIDTH * HEIGHT):
        x, y = 8 + (cell % WIDTH) * 16, 21 + (cell // WIDTH) * 12
        if game.result == "Lost" and cell in game.mines:
            tile = 11
        elif cell in game.flags:
            tile = 10
        elif cell in game.opened:
            tile = 1 + game.number(cell)
        else:
            tile = 0
        screen.blit(tiles.sprite(tile, 0), x, y)
        if game.result == "Lost" and cell in game.mines and cell in game.opened:
            screen.brush = red
            screen.draw(shapes.rectangle(x + 1, y + 1, 13, 9).stroke(1))
        if cell == cursor:
            screen.brush = yellow
            screen.draw(shapes.rectangle(x, y, 15, 11).stroke(1))
    text("A/C:MOVE B:OPEN", 8, 107)
    text("A+B:FLAG A+C:NEW", 88, 107)


if __name__ == "__main__":
    from badgeware import run

    init()
    run(update)

import random

WIDTH = 9
HEIGHT = 7
MINES = 10


def neighbors(cell):
    x, y = cell % WIDTH, cell // WIDTH
    return [
        ny * WIDTH + nx
        for ny in range(max(0, y - 1), min(HEIGHT, y + 2))
        for nx in range(max(0, x - 1), min(WIDTH, x + 2))
        if (nx, ny) != (x, y)
    ]


class Game:
    def __init__(self):
        self.mines = set()
        self.opened = set()
        self.flags = set()
        self.started = False
        self.result = None

    def plant(self, first):
        safe = set(neighbors(first)) | {first}
        choices = [cell for cell in range(WIDTH * HEIGHT) if cell not in safe]
        for _ in range(MINES):
            self.mines.add(choices.pop(random.randrange(len(choices))))
        self.started = True

    def number(self, cell):
        return sum(other in self.mines for other in neighbors(cell))

    def flag(self, cell):
        if self.result or cell in self.opened:
            return
        if cell in self.flags:
            self.flags.remove(cell)
        else:
            self.flags.add(cell)

    def reveal(self, cell):
        if self.result or cell in self.flags:
            return
        if not self.started:
            self.plant(cell)
        if cell in self.opened:
            nearby = neighbors(cell)
            if self.number(cell) != sum(other in self.flags for other in nearby):
                return
            pending = [other for other in nearby if other not in self.flags]
        else:
            pending = [cell]
        while pending:
            current = pending.pop()
            if current in self.flags or current in self.opened:
                continue
            self.opened.add(current)
            if current in self.mines:
                self.result = "Lost"
                return
            if not self.number(current):
                pending.extend(neighbors(current))
        if len(self.opened) == WIDTH * HEIGHT - MINES:
            self.result = "Won"

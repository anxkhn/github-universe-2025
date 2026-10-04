from badgeware import screen, io, brushes, shapes, PixelFont, State

state = {"current": 0, "goal": 2000}
white = brushes.color(255, 255, 255)
blue = brushes.color(28, 163, 236)
dark = brushes.color(15, 94, 156)
green = brushes.color(0, 150, 0)


def init():
    State.load("hydrate", state)
    screen.font = PixelFont.load("/system/assets/fonts/nope.ppf")


def update():
    changed = False
    if io.BUTTON_B in io.pressed:
        state["current"] += 250
        changed = True
    if io.BUTTON_A in io.pressed:
        state["current"] = max(0, state["current"] - 250)
        changed = True
    if io.BUTTON_C in io.pressed:
        state["current"] = 0
        changed = True
    if io.BUTTON_UP in io.pressed:
        state["goal"] += 250
        changed = True
    if io.BUTTON_DOWN in io.pressed:
        state["goal"] = max(250, state["goal"] - 250)
        changed = True
    if changed:
        State.save("hydrate", state)
    screen.brush = dark
    screen.clear()
    screen.brush = green if state["current"] >= state["goal"] else blue
    screen.draw(shapes.circle(80, 48, 35))
    angle = min(360, state["current"] * 360 / state["goal"])
    screen.brush = white
    screen.draw(shapes.pie(80, 48, 32, -90, angle - 90))
    screen.brush = dark
    screen.draw(shapes.circle(80, 48, 25))
    screen.brush = white
    for text, y in (
        ("Hydrate", 2),
        (str(state["current"]) + "ml", 44),
        ("Goal: %dml" % state["goal"], 85),
        ("A:-250 B:+250 C:reset", 99),
        ("UP/DOWN: goal", 110),
    ):
        width, _ = screen.measure_text(text)
        screen.text(text, 80 - width / 2, y)

from badgeware import screen, io, brushes, shapes, PixelFont
import time

TASK, SHORT, LONG = 25 * 60, 10 * 60, 30 * 60
remaining = TASK * 1000
running = False
is_break = False
completed = 0
last_tick = None
alert_until = None
white = brushes.color(255, 255, 255)
red = brushes.color(160, 35, 35)
blue = brushes.color(40, 60, 130)


def init():
    screen.font = PixelFont.load("/system/assets/fonts/nope.ppf")


def update():
    global remaining, running, is_break, completed, last_tick, alert_until
    now = time.ticks_ms()
    if running and last_tick is not None:
        remaining = max(0, remaining - time.ticks_diff(now, last_tick))
        if remaining == 0:
            running = False
            if not is_break:
                completed += 1
            is_break = not is_break
            remaining = (
                LONG if is_break and completed % 4 == 0 else SHORT if is_break else TASK
            ) * 1000
            alert_until = time.ticks_add(now, 5000)
    last_tick = now
    if io.BUTTON_B in io.pressed:
        running = not running
    if io.BUTTON_A in io.pressed:
        running = False
        remaining = (SHORT if is_break else TASK) * 1000
    if io.BUTTON_C in io.pressed:
        running = False
        is_break = not is_break
        remaining = (SHORT if is_break else TASK) * 1000
    screen.brush = blue if is_break else red
    screen.clear()
    screen.brush = white
    seconds = (remaining + 999) // 1000
    text = "%02d:%02d" % divmod(seconds, 60)
    for label, y in (
        ("Tomato: " + ("break" if is_break else "focus"), 8),
        (text, 42),
        ("Tasks: %d" % completed, 65),
        ("B:pause" if running else "B:start", 84),
        ("A:reset C:switch", 105),
    ):
        width, _ = screen.measure_text(label)
        screen.text(label, 80 - width / 2, y)
    alert = alert_until is not None and time.ticks_diff(alert_until, now) > 0
    if alert and (now // 250) % 2:
        screen.draw(shapes.rectangle(0, 0, 160, 120).stroke(4))

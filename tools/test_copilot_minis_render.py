"""Render badge states with the existing desktop simulator and check bounds."""

import importlib.util
from pathlib import Path
import pygame

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("sim", ROOT / "badge25/simulator/badge_simulator.py")
sim = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sim)
pygame.init()
sim.SIM_ROOT = str(ROOT / "badge25")
sim._perf_monitor = None
sim.screen = sim.Screen(scale=1)
sim.io = sim.IO()
app = sim.load_game_module(str(ROOT / "badge25/apps/copilot-minis/__init__.py"))
app.init()
app.config = {}
app.receive(
    {
        "type": "state",
        "demo": True,
        "threads": [
            {
                "id": "one",
                "title": "Build conference app",
                "status": "permission",
                "revision": 1,
                "messages": ["Review ready"],
                "pending": [
                    {
                        "id": "r1",
                        "kind": "permission",
                        "detail": "Run shell command:\nuv run pytest\nAllow this command once?",
                        "choices": ["Reject", "Allow once"],
                    }
                ],
            },
            {
                "id": "two",
                "title": "Review pull request",
                "status": "running",
                "revision": 1,
                "messages": [],
                "pending": [],
            },
            {
                "id": "three",
                "title": "Run test suite",
                "status": "idle",
                "revision": 1,
                "messages": [],
                "pending": [],
            },
        ],
    }
)
original = sim.screen.text


def text(label, x, y):
    width, height = sim.screen.measure_text(label)
    assert 0 <= x and x + width <= 160, (label, x, width)
    assert 0 <= y and y + height <= 120, (label, y, height)
    original(label, x, y)


sim.screen.text = text
out = ROOT / ".badge-local"
out.mkdir(exist_ok=True)
for view in ("threads", "chat", "options"):
    app.view = view
    app.choice_request = "r1"
    app.render()
    pygame.image.save(sim.screen._surface, str(out / ("copilot-minis-" + view + ".png")))
app.threads[0]["pending"][0]["choices"] = ["A very long option " * 12]
app.choice = 0


def tap(button):
    sim.io.pressed = {button}
    sim.io.held = {button}
    app.update()
    sim.io.pressed = set()
    sim.io.held = set()
    sim.io.released = {button}
    app.update()
    sim.io.released = set()


tap(sim.io.BUTTON_C)
assert app.view == "details"
sim.io.pressed = {sim.io.BUTTON_DOWN}
app.update()
assert app.scroll == 1
sim.io.pressed = {sim.io.BUTTON_A}
app.update()
assert app.view == "options"
sim.io.pressed = {sim.io.BUTTON_A}
app.update()
assert app.view == "threads"
sim.io.pressed = {sim.io.BUTTON_B}
app.update()
assert app.view == "options", "Pending replies should open directly"
levels = []
sim.display.backlight = levels.append
sim.io.pressed = set()
for _ in range(5):
    app.update()
assert levels == [0.6] * 5, "Unread events must never dim the backlight"
app.view = "threads"
tap(sim.io.BUTTON_C)
assert app.view == "connection" and app.connected, "Info must not disconnect"
sim.io.pressed = {sim.io.BUTTON_C}
sim.io.held = {sim.io.BUTTON_C}
app.update()
app.c_started = app.ticks() - 600
sim.io.pressed = set()
app.update()
assert app.c_help, "Hold C must reveal help"
sim.io.held = set()
sim.io.released = {sim.io.BUTTON_C}
app.update()
assert not app.c_help and app.view == "connection", "Release help must not navigate"
sim.io.released = set()
sim.io.pressed = set()
app.connected = False
app.notice = "Host disconnected"
app.render()
app.receive({"type": "state", "threads": []})
assert app.view == "connection"
app.view = "chat"
app.receive({"type": "state", "threads": []})
assert app.view == "threads", "Cleared chats must return to empty list"
app.render()
print("PASS direct choices, A Back/B Select/C Read, stable brightness, safe Info and render bounds")
pygame.quit()

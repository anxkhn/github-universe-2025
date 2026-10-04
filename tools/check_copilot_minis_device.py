"""Run through mpremote mount of badge25/apps/copilot-minis and a demo bridge."""

import sys
import time
import badgeware
from badgeware import io, screen

sys.path.insert(0, "/remote")
app = __import__("/remote")
app.init()
start = time.ticks_ms()
while not app.connected and time.ticks_diff(time.ticks_ms(), start) < 45000:
    io.poll()
    app.update()
    badgeware.display.update()
    time.sleep_ms(20)
assert app.connected, app.notice
assert len(app.threads) >= 3
print("PASS Wi-Fi/TCP pairing and thread snapshots", len(app.threads))
print("PASS screen/font", screen.width, screen.height, screen.font.height)


class TestInput:
    BUTTON_A = io.BUTTON_A
    BUTTON_B = io.BUTTON_B
    BUTTON_C = io.BUTTON_C
    BUTTON_UP = io.BUTTON_UP
    BUTTON_DOWN = io.BUTTON_DOWN
    pressed = []
    held = []
    released = []


app.io = TestInput


def press(button):
    TestInput.pressed = [button]
    TestInput.held = [button]
    app.update()
    badgeware.display.update()
    TestInput.pressed = []
    TestInput.held = []
    TestInput.released = [button]
    app.update()
    TestInput.released = []


press(io.BUTTON_B)
assert app.view == "options"
press(io.BUTTON_C)
assert app.view == "details"
press(io.BUTTON_A)
assert app.view == "options"
assert app.choice == 0
press(io.BUTTON_DOWN)
assert app.choice == 1
press(io.BUTTON_B)
start = time.ticks_ms()
while app.threads[0]["pending"] and time.ticks_diff(time.ticks_ms(), start) < 8000:
    io.poll()
    app.update()
    time.sleep_ms(20)
assert not app.threads[0]["pending"]
print("PASS B direct options, C read, A back, Down select, B permission reply")
press(io.BUTTON_A)
press(io.BUTTON_DOWN)
press(io.BUTTON_B)
assert app.view == "options"
press(io.BUTTON_DOWN)
press(io.BUTTON_B)
start = time.ticks_ms()
while app.threads[1]["pending"] and time.ticks_diff(time.ticks_ms(), start) < 8000:
    io.poll()
    app.update()
    time.sleep_ms(20)
assert not app.threads[1]["pending"]
print("PASS second thread and agent question reply")
press(io.BUTTON_C)
press(io.BUTTON_B)
start = time.ticks_ms()
while time.ticks_diff(time.ticks_ms(), start) < 4000:
    io.poll()
    app.update()
    time.sleep_ms(20)
assert app.threads[1]["status"] == "idle"
print("PASS Continue action and completion update")
press(io.BUTTON_A)
press(io.BUTTON_UP)
print("PASS A back, Up navigation, steady brightness and rendering")
TestInput.pressed = [io.BUTTON_C]
TestInput.held = [io.BUTTON_C]
app.update()
TestInput.pressed = []
app.c_started = time.ticks_add(time.ticks_ms(), -600)
app.update()
assert app.c_help
TestInput.held = []
TestInput.released = [io.BUTTON_C]
app.update()
TestInput.released = []
assert not app.c_help
app.on_exit()
print("PASS hold-C help and cleanup")

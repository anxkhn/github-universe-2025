"""Run with mpremote mount . run tools/check_ir_device.py; no IR emitted."""

import sys
import os
from badgeware import screen, io

sys.path.insert(0, "/remote/badge25/apps/ir-remote")
from raw import Infrared
from signals import SLOTS, save, load

device = Infrared()
try:
    device.start()
    device.stop()
    print("PASS PIO capture assembled, started, stopped")
finally:
    device.close()

app = __import__("/remote/badge25/apps/ir-remote")
try:
    app.init()
    assert app.infrared is not None
    for _ in range(3):
        io.poll()
        app.update()
    for slot in range(len(SLOTS)):
        app.selected = slot
        app.update()
    for text in ("UP/DN slot  C sequence", "A+C delete  B+C carrier", "Saved. B: test on AC"):
        width, _ = screen.measure_text(text)
        assert width <= 148, (text, width)
    print("PASS all", len(SLOTS), "slot screens and control text widths")
    packet = {"carrier": 38000, "timings": [560, 560] * 7 + [560]}
    test_path = "/ir-remote/check.tmp.json"
    try:
        save(test_path, packet)
        assert load(test_path) == packet
        packet["carrier"] = 40000
        save(test_path, packet)
        assert load(test_path) == packet
        print("PASS writable-root storage and replacement")
    finally:
        os.remove(test_path)
finally:
    app.on_exit()

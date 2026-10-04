import sys
import os
import time
from badgeware import screen, io, brushes, shapes, PixelFont

sys.path.insert(0, "/system/apps/ir-remote")
from raw import Infrared
from signals import SLOTS, CARRIERS, load, save

DIRECTORY = "/ir-remote"
selected = 0
carrier_index = 0
macro = False
recording = False
confirm_delete = False
message = "A: learn  B: send"
infrared = None
started = 0
saved = set()
background = brushes.color(16, 35, 49)
white = brushes.color(245, 249, 252)
accent = brushes.color(100, 219, 210)


def path():
    return DIRECTORY + "/%02d.json" % selected


def init():
    global infrared, saved, message
    screen.font = PixelFont.load("/system/assets/fonts/nope.ppf")
    try:
        os.mkdir(DIRECTORY)
    except OSError:
        pass
    saved = {n for n in range(len(SLOTS)) if "%02d.json" % n in os.listdir(DIRECTORY)}
    try:
        infrared = Infrared()
    except Exception as error:
        message = "IR unavailable"
        print("IR remote:", error)


def finish():
    global recording, message
    recording = False
    try:
        timings = infrared.finish()
        save(path(), {"carrier": CARRIERS[carrier_index], "timings": timings})
        saved.add(selected)
        message = "Saved. B: test on AC"
    except (ValueError, OSError) as error:
        message = "Not saved. Try again"
        print("IR capture:", error)


def update():
    global selected, carrier_index, macro, recording, started, message, confirm_delete
    pressed = io.pressed
    if recording:
        elapsed = time.ticks_diff(time.ticks_ms(), started)
        idle = time.ticks_diff(time.ticks_us(), infrared.last_edge)
        if io.BUTTON_A in pressed:
            infrared.stop()
            recording = False
            message = "Cancelled"
        elif infrared.overflow:
            finish()
        elif infrared.count and (
            io.BUTTON_B in pressed or elapsed >= 8000 or (not macro and idle > 180000)
        ):
            finish()
        elif elapsed >= 10000:
            infrared.stop()
            recording = False
            message = "No IR. Aim closer"
    elif confirm_delete:
        if io.BUTTON_B in pressed:
            try:
                os.remove(path())
                saved.discard(selected)
                message = "Deleted"
            except OSError:
                message = "Delete failed"
            confirm_delete = False
        elif io.BUTTON_A in pressed or io.BUTTON_C in pressed:
            confirm_delete = False
            message = "Cancelled"
    elif io.BUTTON_A in io.held and io.BUTTON_C in io.held:
        if io.BUTTON_A in pressed or io.BUTTON_C in pressed:
            confirm_delete = selected in saved
            message = "B: delete  A: cancel" if confirm_delete else "Slot is empty"
    elif io.BUTTON_B in io.held and io.BUTTON_C in io.held:
        if io.BUTTON_B in pressed or io.BUTTON_C in pressed:
            carrier_index = (carrier_index + 1) % len(CARRIERS)
            message = "Carrier for next learn"
    elif io.BUTTON_UP in pressed or io.BUTTON_DOWN in pressed:
        selected = (selected + (-1 if io.BUTTON_UP in pressed else 1)) % len(SLOTS)
        message = "A: learn  B: send"
    elif io.BUTTON_C in pressed:
        macro = not macro
        message = "B finishes sequence" if macro else "Auto-finish on silence"
    elif io.BUTTON_A in pressed and infrared:
        infrared.start()
        started = time.ticks_ms()
        recording = True
        message = "Press Mi Remote now"
    elif io.BUTTON_B in pressed and infrared:
        try:
            data = load(path())
            infrared.send(data["timings"], data["carrier"])
            message = "Sent. Check the AC"
        except (OSError, ValueError) as error:
            message = "Learn this slot first" if selected not in saved else "Send failed"
            print("IR replay:", error)

    screen.brush = background
    screen.clear()
    screen.brush = accent
    screen.text("IR remote", 6, 4)
    screen.text("%d/%d" % (selected + 1, len(SLOTS)), 119, 4)
    screen.draw(shapes.rectangle(6, 20, 148, 1))
    screen.brush = white
    screen.text(SLOTS[selected], 6, 29)
    screen.brush = accent
    screen.text("LEARNING" if recording else "Saved" if selected in saved else "Not learned", 6, 44)
    screen.brush = white
    screen.text(
        "%dkHz | %s" % (CARRIERS[carrier_index] // 1000, "Sequence" if macro else "Single"), 6, 59
    )
    screen.text(message, 6, 76)
    screen.text("UP/DN slot  C sequence", 6, 94)
    screen.text("A+C delete  B+C carrier", 6, 107)


def on_exit():
    if infrared:
        infrared.close()


if __name__ == "__main__":
    from badgeware import run

    init()
    run(update)

"""Offline validation, safe replacement, capture bounds, and replay checks."""

import importlib.util
import sys
import tempfile
import types
from pathlib import Path

APP = Path(__file__).resolve().parents[1] / "badge25/apps/ir-remote"


def module(name):
    spec = importlib.util.spec_from_file_location(name, APP / (name + ".py"))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


signals = module("signals")
packet = {"carrier": 38000, "timings": [9000, 4500] + [560, 1690] * 100 + [560]}
with tempfile.TemporaryDirectory() as directory:
    path = str(Path(directory) / "00.json")
    signals.save(path, packet)
    assert signals.load(path) == packet
    replacement = {"carrier": 40000, "timings": [560, 560] * 7 + [560]}
    signals.save(path, replacement)
    for bad in ([], [560] * 16, [560] * 4097, [0] * 15, [True] * 15, [70000] * 15):
        try:
            signals.save(path, {"carrier": 38000, "timings": bad})
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid envelope accepted")
        assert signals.load(path) == replacement

sent = []


class Sender:
    def __init__(self, *args):
        sent.append(args)

    def start(self):
        pass

    def stop(self):
        sent.append("stop")

    def send(self, mark, space):
        sent.append((mark, space))

    def wait_for_send(self):
        sent.append("wait")


sys.modules["rp2"] = types.SimpleNamespace(
    PIO=types.SimpleNamespace(JOIN_RX=0),
    asm_pio=lambda **kwargs: lambda function: function,
)
sys.modules["machine"] = types.SimpleNamespace(
    Pin=type(
        "Pin",
        (),
        {
            "OUT": 1,
            "__init__": lambda self, *args, **kwargs: None,
        },
    )
)
sys.modules["board"] = types.SimpleNamespace(IR_TX=20)
sys.modules["aye_arr.pulse.send"] = types.SimpleNamespace(PulseSender=Sender)
raw = module("raw")
raw.time = types.SimpleNamespace(sleep_us=lambda duration: sent.append(("sleep", duration)))
device = raw.Infrared.__new__(raw.Infrared)
device.stop = lambda: None
device.send([9000, 100000, 560], 38000)
assert sent == [
    (20, 0, 1, 38000),
    (9000, 50000),
    "wait",
    ("sleep", 50000),
    (560, 15000),
    "wait",
    "stop",
]
device.buffer = [560] * 15
device.count = 15
device.overflow = False
assert device.finish() == [560] * 15
for count, overflow in ((14, False), (15, True)):
    device.count, device.overflow = count, overflow
    try:
        device.finish()
    except ValueError:
        pass
    else:
        raise AssertionError("Truncated or overflowing capture accepted")
print("IR envelope validation, replacement, capture bounds, and replay passed")

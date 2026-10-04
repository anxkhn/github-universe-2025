"""Saved raw envelopes, independent of any AC brand or protocol."""

import json
import os

SLOTS = (
    ["Power on", "Power off"]
    + ["Cool %dC" % t for t in range(16, 31)]
    + [
        "Auto",
        "Dry",
        "Fan only",
        "Heat",
        "Fan auto",
        "Fan low",
        "Fan medium",
        "Fan high",
        "Swing",
        "Swing off",
        "Turbo",
        "Sleep",
        "Eco",
        "Light",
        "Timer on",
        "Timer off",
        "Temp up",
        "Temp down",
        "Up",
        "Down",
        "Left",
        "Right",
        "OK",
        "Back",
    ]
    + ["Custom %d" % n for n in range(1, 9)]
)
CARRIERS = (38000, 36000, 40000, 56000)


def validate(data):
    if not isinstance(data, dict) or data.get("carrier") not in CARRIERS:
        raise ValueError("Invalid carrier")
    timings = data.get("timings")
    if not isinstance(timings, list) or not 15 <= len(timings) <= 4095 or len(timings) % 2 == 0:
        raise ValueError("Invalid envelope")
    for index, value in enumerate(timings):
        maximum = 60000 if index % 2 == 0 else 8000000
        if type(value) is not int or not 80 <= value <= maximum:
            raise ValueError("Invalid pulse")
    if sum(timings) > 8000000:
        raise ValueError("Signal exceeds 8s")
    return data


def load(path):
    with open(path) as file:
        return validate(json.load(file))


def save(path, data):
    validate(data)
    temporary = path + ".tmp"
    with open(temporary, "w") as file:
        json.dump(data, file)
    load(temporary)
    os.rename(temporary, path)

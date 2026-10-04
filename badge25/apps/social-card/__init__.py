"""Offline social card for the Universe 2025 MonaOS badge."""

import gc
from badgeware import io, screen

NAME = "Anas Khan"
PHONE = "+916306252095"
AVATAR_URL = "https://avatars.githubusercontent.com/u/83116240?v=4"
LINKS = (
    ("GitHub", "anxkhn", "https://github.com/anxkhn"),
    ("LinkedIn", "linkedin.com/in/anxkhn", "https://linkedin.com/in/anxkhn"),
    ("X", "@anxkhn", "https://x.com/anxkhn"),
    ("Website", "anaskhan.me", "https://anaskhan.me"),
    ("Contact", "+916306252095", "vcard"),
)
ASSETS = "/system/apps/social-card/assets/"
selected = 0
show_qr = False
frame_key = None


def init():
    global selected, show_qr, frame_key
    selected = 0
    show_qr = False
    frame_key = None
    gc.collect()


def update():
    global selected, show_qr, frame_key
    previous = io.BUTTON_A in io.pressed or io.BUTTON_UP in io.pressed
    following = io.BUTTON_C in io.pressed or io.BUTTON_DOWN in io.pressed
    if previous != following:
        selected = (selected + (1 if following else -1)) % len(LINKS)
    if io.BUTTON_B in io.pressed:
        show_qr = not show_qr
    key = (selected, show_qr)
    if key != frame_key:
        gc.collect()
        screen.load_into(ASSETS + ("qr-" if show_qr else "card-") + str(selected) + ".png")
        frame_key = key


def on_exit():
    global frame_key
    frame_key = None
    gc.collect()


if __name__ == "__main__":
    from badgeware import run

    init()
    run(update)

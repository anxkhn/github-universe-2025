"""Decode installed runtime PNGs on the badge with mpremote run."""

import gc
import os
from badgeware import Image, screen


def check(directory):
    count = 0
    for entry in os.ilistdir(directory):
        name, kind = entry[:2]
        if name.startswith("."):
            continue
        path = directory + "/" + name
        if kind == 0x4000:
            count += check(path)
        elif name.endswith(".png"):
            image = Image.load(path)
            assert image.width > 0 and image.height > 0, path
            if "/fireplace/" in path or "/copilot-loop/" in path:
                screen.blit(image, 0, 0)
            del image
            gc.collect()
            count += 1
    return count


count = check("/system/apps") + check("/system/assets")
print("PASS decoded", count, "runtime PNGs with Badgeware")
sprite_bytes = 0
for directory in ("/system/apps/pokedex/sprites", "/system/apps/pokedex/shiny"):
    for name in os.listdir(directory):
        if name.endswith(".png") and not name.startswith("."):
            sprite_bytes += os.stat(directory + "/" + name)[6]
print("Pokedex PNG bytes:", sprite_bytes)
stats = os.statvfs("/system")
print("Filesystem free bytes:", stats[0] * stats[3])

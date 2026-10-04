"""Run via mpremote on the 2025 badge. Does not alter Quest state."""

import gc
import os
import sys
from badgeware import io

failures = []
for name in (
    "2048",
    "fireplace",
    "system",
    "pokedex",
    "wordclock",
    "clock",
    "christmas",
    "jungle",
    "hydrate",
    "tomato",
    "tennis",
    "ir-remote",
    "minesweeper",
    "social-card",
):
    before = set(sys.modules)
    app_dir = "/system/apps/" + name
    original_path = list(sys.path)
    app = None
    try:
        os.chdir(app_dir)
        sys.path.insert(0, app_dir)
        app = __import__(app_dir)
        getattr(app, "init", lambda: None)()
        if name == "wordclock":
            app.wifi_initialized = True
            app.ntp_synced = True
        if name == "christmas":
            app.NETWORK_AVAILABLE = False
        for _ in range(3):
            io.poll()
            app.update()
        if name == "2048":
            assert app.slide_line([2, 2, 2, 2])[0] == [4, 4, 0, 0]
            app.new_game()
            app.update()
            app.do_move("L")
            app.commit()
            app.update()
        if name == "tennis":
            app.playing = True
            app.update()
        print("PASS", name)
    except Exception as error:
        failures.append(name)
        print("FAIL", name, repr(error))
    finally:
        if name == "ir-remote" and app is not None:
            app.on_exit()
        sys.path[:] = original_path
        for key in set(sys.modules) - before:
            del sys.modules[key]
        gc.collect()

menu = __import__("/system/apps/menu")
for page in range(menu.total_pages):
    menu.load_page_icons(page)
menu.update()
print("Launcher:", len(menu.apps), "apps across", menu.total_pages, "pages")
assert not failures, failures

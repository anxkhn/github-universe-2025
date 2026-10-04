"""Render every social card view on the installed MonaOS badge."""

import sys
from badgeware import io, screen

sys.path.insert(0, "/system/apps/social-card")
app = __import__("/system/apps/social-card")
app.init()
try:
    io.poll()
    for index in range(len(app.LINKS)):
        for qr in (False, True):
            app.selected = index
            app.show_qr = qr
            app.update()
            assert screen.width == 160 and screen.height == 120
            print("PASS", app.LINKS[index][0], "QR" if qr else "card")
finally:
    app.on_exit()

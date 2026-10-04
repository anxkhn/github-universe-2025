"""Copilot Minis: button-driven LAN remote for the laptop bridge."""

import json
import socket
import sys
import time

import badgeware
from badgeware import PixelFont, brushes, io, screen, shapes

try:
    import network
except ImportError:
    network = None

background = brushes.color(17, 23, 27)
foreground = brushes.color(240, 246, 252)
muted = brushes.color(170, 183, 197)
selected_brush = brushes.color(33, 48, 56)
accent = brushes.color(112, 236, 235)
rule = brushes.color(65, 80, 87)
colors = {
    "running": brushes.color(100, 190, 255),
    "idle": brushes.color(90, 215, 135),
    "permission": brushes.color(255, 195, 70),
    "question": brushes.color(255, 195, 70),
    "error": brushes.color(255, 115, 110),
    "stopped": brushes.color(255, 115, 110),
}
config = {}
wlan = None
sock = None
tx = b""
rx = b""
last_attempt = 0
last_received = 0
wifi_attempt = 0
threads = []
selected_id = None
selected = 0
view = "threads"
scroll = 0
choice = 0
choice_request = None
submitted_request = None
details_return = "chat"
notice_until = 0
c_started = None
c_help = False
notice = "Starting"
connected = False
demo = False
seen = {}
unread = False
MAX_FRAME = 32768


def ticks():
    return time.ticks_ms() if hasattr(time, "ticks_ms") else int(time.monotonic() * 1000)


def elapsed(start):
    now = ticks()
    return time.ticks_diff(now, start) if hasattr(time, "ticks_diff") else now - start


def init():
    global config, wlan, notice
    screen.font = PixelFont.load("/system/assets/fonts/ark.ppf")
    for path in ("/copilot-minis.json", "/system/apps/copilot-minis/config.json"):
        try:
            with open(path) as source:
                config = json.load(source)
            host = config.get("host", "")
            if len(host.split(".")) != 4 or not all(
                p.isdigit() and 0 <= int(p) <= 255 for p in host.split(".")
            ):
                raise ValueError("Use laptop IPv4")
            if not isinstance(config.get("token"), str) or len(config["token"]) < 32:
                raise ValueError("Invalid pairing")
            if not 1 <= int(config.get("port", 8765)) <= 65535:
                raise ValueError("Invalid port")
            break
        except (OSError, ValueError, TypeError):
            config = {}
    if not config:
        notice = "Pair on laptop first"
        return
    if network:
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        if not wlan.isconnected():
            connect_wifi()
    notice = "Connecting"


def connect_wifi():
    global notice, wifi_attempt
    wifi_attempt = ticks()
    sys.path.insert(0, "/")
    try:
        import secrets

        ssid = getattr(secrets, "WIFI_SSID", "")
        password = getattr(secrets, "WIFI_PASSWORD", "")
        if not ssid:
            notice = "Set Wi-Fi in secrets.py"
            return
        wlan.connect(ssid, password)
        notice = "Joining Wi-Fi"
    except (ImportError, OSError):
        notice = "Wi-Fi config error"
    finally:
        sys.path.pop(0)


def disconnect(message="Host disconnected"):
    global sock, tx, rx, connected, notice, last_attempt
    if sock:
        sock.close()
    sock = None
    tx = rx = b""
    connected = False
    notice = message
    last_attempt = ticks()


def queue(payload):
    global tx
    data = (json.dumps(payload) + "\n").encode()
    if len(tx) + len(data) > 4096:
        raise ValueError("Command queue full")
    tx += data


def receive(payload):
    global threads, connected, notice, last_received, demo, unread, selected, selected_id
    global view, choice_request, choice, scroll, submitted_request
    if payload.get("type") == "state":
        threads = payload.get("threads", [])
        demo = payload.get("demo", False)
        connected = True
        last_received = ticks()
        if elapsed(notice_until) >= 0:
            notice = "Demo connected" if demo else "Connected"
        for thread in threads:
            if seen.get(thread["id"]) != thread.get("revision"):
                unread = True
        if selected_id:
            for index, item in enumerate(threads):
                if item["id"] == selected_id:
                    selected = index
                    break
        selected = min(selected, max(0, len(threads) - 1))
        selected_id = threads[selected]["id"] if threads else None
        if not threads and view not in ("connection", "threads"):
            view = "threads"
            scroll = choice = 0
        thread = current()
        if thread and view not in ("threads", "details"):
            pending = thread.get("pending", [])
            rid = pending[0]["id"] if pending else None
            if rid and rid != choice_request and rid != submitted_request:
                open_options()
            elif view == "options" and choice_request and not rid:
                view = "chat"
                scroll = 0
    elif payload.get("type") in ("ack", "error"):
        notice = payload.get("message", "Network error")
        if not connected and payload.get("type") == "error":
            disconnect(notice)


def poll_network():
    global sock, tx, rx, last_attempt, last_received, notice
    if not config:
        return
    if wlan and not wlan.isconnected():
        if sock:
            disconnect("Wi-Fi disconnected")
        if elapsed(wifi_attempt) > 30000:
            connect_wifi()
        return
    if sock is None:
        if last_attempt and elapsed(last_attempt) < 3000:
            return
        last_attempt = last_received = ticks()
        try:
            sock = socket.socket()
            sock.setblocking(False)
            try:
                sock.connect((config["host"], int(config.get("port", 8765))))
            except OSError as error:
                if error.args[0] not in (11, 115, 119, 36):
                    raise
            queue({"token": config["token"]})
            notice = "Connecting to laptop"
        except OSError:
            disconnect()
            return
    try:
        if tx:
            try:
                sent = sock.send(tx)
                if sent:
                    tx = tx[sent:]
            except OSError as error:
                if error.args[0] not in (11, 115, 119, 36):
                    raise
        try:
            chunk = sock.recv(2048)
        except OSError as error:
            if error.args[0] not in (11, 115, 119, 36):
                raise
            chunk = None
        if chunk == b"":
            disconnect()
            return
        if chunk:
            rx += chunk
            if len(rx) > MAX_FRAME:
                disconnect("Host frame too large")
                return
            while b"\n" in rx:
                line, rx = rx.split(b"\n", 1)
                receive(json.loads(line))
        if elapsed(last_received) > 7000:
            disconnect("Laptop not responding")
    except (OSError, ValueError, KeyError, TypeError):
        disconnect("Connection lost")


def text_width(text):
    measured = screen.measure_text(text)
    return measured[0] if isinstance(measured, tuple) else measured


def fit(text, width=148):
    text = str(text).replace("\n", " ")
    if text_width(text) <= width:
        return text
    while text and text_width(text + "...") > width:
        text = text[:-1]
    return text + "..."


def wrap(text, width=144):
    lines = []
    for paragraph in str(text).split("\n"):
        line = ""
        for word in paragraph.split():
            candidate = line + " " + word if line else word
            if line and text_width(candidate) > width:
                lines.append(line)
                line = ""
            while text_width(word) > width:
                fragment = word
                while text_width(fragment) > width:
                    fragment = fragment[:-1]
                lines.append(fragment)
                word = word[len(fragment) :]
            line = line + " " + word if line else word
        lines.append(line)
    return lines or [""]


def current():
    return threads[selected] if threads else None


def options(thread):
    pending = thread.get("pending", [])
    if pending:
        return pending[0].get("choices", []), pending[0]["id"]
    if thread["status"] == "running":
        return ["Status update", "Stop agent"], None
    return ["Continue task", "Status update", "Stop agent"], None


def open_options():
    global view, choice, choice_request, scroll
    thread = current()
    if thread:
        choices, choice_request = options(thread)
        if choices:
            view = "options"
            choice = scroll = 0


def open_thread():
    global view, scroll
    if not current():
        return
    view = "chat"
    body = wrap("\n\n".join(current().get("messages", [])))
    scroll = max(0, len(body) - 8)
    acknowledge()
    if current().get("pending"):
        open_options()


def status_label(thread):
    return {
        "permission": "Needs approval",
        "question": "Needs reply",
        "running": "Working",
        "idle": "Ready",
        "error": "Error",
        "stopped": "Stopped",
    }.get(thread["status"], thread["status"])


def request_summary(thread):
    pending = thread.get("pending", [])
    if not pending:
        return "Choose an action"
    request = pending[0]
    if request["kind"] == "permission":
        try:
            data = json.loads(request["detail"])
            return (
                "Allow "
                + str(
                    data.get("fullCommandText") or data.get("fileName") or data.get("kind", "tool")
                )
                + "?"
            )
        except (ValueError, TypeError):
            pass
    return request["detail"]


def acknowledge():
    global unread
    for thread in threads:
        seen[thread["id"]] = thread.get("revision")
    unread = False


def submit():
    global view, notice, submitted_request, notice_until, scroll
    thread = current()
    if not thread or not connected:
        notice = "Reconnect before sending"
        return
    choices, rid = options(thread)
    if rid != choice_request or choice >= len(choices):
        notice = "Options changed. Reopen."
        view = "chat"
        return
    payload = {"session": thread["id"]}
    if rid:
        payload.update({"action": "answer", "request": rid, "choice": choice})
    else:
        payload["action"] = {
            "Continue task": "continue",
            "Status update": "status",
            "Stop agent": "stop",
        }[choices[choice]]
    try:
        queue(payload)
        notice = "Reply sent" if rid else "Action sent"
        notice_until = ticks() + 3000
        submitted_request = rid
        view = "chat"
        scroll = max(0, len(wrap("\n\n".join(thread.get("messages", [])))) - 8)
        acknowledge()
    except ValueError:
        notice = "Command queue full"


def text(label, x, y, brush=foreground):
    screen.brush = brush
    screen.text(label, x, y)


def rectangle(x, y, width, height, brush):
    screen.brush = brush
    screen.draw(shapes.rectangle(x, y, width, height))


def context_line(label, status=None):
    text(fit(label, 131), 5, 1, muted)
    rectangle(149, 5, 4, 4, colors.get(status, colors["idle"]) if connected else colors["error"])
    rectangle(4, 14, 150, 1, rule)


def help_view():
    screen.brush = background
    screen.clear()
    text("Buttons", 6, 3, accent)
    for index, line in enumerate(
        (
            "Up/Down  Move / scroll",
            "A  Back to chats",
            "B  Open / select",
            "C  Actions / details",
            "Hold C  This guide",
            "HOME  Exit app",
            "Release C to return",
        )
    ):
        text(line, 6, 23 + index * 13, foreground if index < 5 else muted)


def scrollbar(position, total, visible, y, height):
    if total <= visible:
        return
    rectangle(156, y, 1, height, rule)
    thumb = max(4, height * visible // total)
    offset = (height - thumb) * position // max(1, total - visible)
    rectangle(155, y + offset, 3, thumb, accent)


def render():
    global scroll, choice
    screen.brush = background
    screen.clear()
    if c_help:
        help_view()
        return
    thread = current()
    if view == "threads":
        context_line("Chats %d/%d" % (selected + 1 if threads else 0, len(threads)))
        if not threads:
            text("All clear" if connected else "Connecting...", 6, 37, accent)
            message = "Start a task on your laptop. It will appear here." if connected else notice
            for index, line in enumerate(wrap(message)[:4]):
                text(line, 6, 53 + index * 12, muted)
            text("Hold C for buttons", 6, 103, muted)
        else:
            first = max(0, min(selected - 1, len(threads) - 4))
            for row, item in enumerate(threads[first : first + 4]):
                y = 18 + row * 25
                active = first + row == selected
                if active:
                    rectangle(3, y, 151, 22, selected_brush)
                text(">" if active else " ", 5, y, accent)
                text(fit(item["title"], 133), 16, y)
                text(status_label(item), 16, y + 11, colors.get(item["status"], muted))
                if seen.get(item["id"]) != item.get("revision"):
                    rectangle(146, y + 15, 3, 3, accent)
            scrollbar(first, len(threads), 4, 18, 99)
    elif view == "connection":
        context_line("Connection")
        body = wrap(
            notice
            + "\nHost: "
            + config.get("host", "Not paired")
            + "\nB: retry connection\nA: back\nHold C: buttons"
        )
        for index, line in enumerate(body[:6]):
            text(line, 6, 20 + index * 12, muted)
    elif thread:
        context_line(thread["title"], thread["status"])
        if view == "options":
            choices, rid = options(thread)
            if rid != choice_request:
                text("Request changed", 6, 20, muted)
                return
            summary = wrap(request_summary(thread))
            summary_count = min(3, len(summary))
            for index, line in enumerate(summary[:summary_count]):
                text(line, 6, 19 + index * 12, colors.get(thread["status"], foreground))
            if choices:
                choice = min(choice, len(choices) - 1)
                rows = [
                    wrap("%d. %s" % (index + 1, label), 133)[:2]
                    for index, label in enumerate(choices)
                ]
                heights = [len(lines) * 12 + 3 for lines in rows]
                top = 22 + summary_count * 12
                space = 118 - top
                first = 0
                while first < choice and sum(heights[first : choice + 1]) > space:
                    first += 1
                y = top
                shown = 0
                for index in range(first, len(choices)):
                    height = heights[index]
                    if y + height > 118:
                        break
                    active = index == choice
                    rectangle(4, y, 150, height - 1, selected_brush if active else background)
                    text(">" if active else " ", 6, y + 1, accent)
                    for row, line in enumerate(rows[index]):
                        if row == 1 and len(wrap("%d. %s" % (index + 1, choices[index]), 133)) > 2:
                            line = fit(line + "...", 133)
                        text(line, 16, y + 1 + row * 12, accent if active else foreground)
                    y += height
                    shown += 1
                scrollbar(first, len(choices), shown, top, space)
            else:
                text("Answer on laptop", 6, 67, muted)
        else:
            if view == "details":
                pending = thread.get("pending", [])
                choices, rid = options(thread)
                content = pending[0]["detail"] if pending else "Choose an action"
                if details_return == "options" and choices and rid == choice_request:
                    content = choices[min(choice, len(choices) - 1)] + "\n\n" + content
            else:
                content = "\n\n".join(thread.get("messages", [])) or "Waiting for Copilot..."
            body = wrap(content)
            show_notice = elapsed(notice_until) < 0 or not connected
            visible = 7 if show_notice else 8
            scroll = min(scroll, max(0, len(body) - visible))
            for index, line in enumerate(body[scroll : scroll + visible]):
                text(line, 6, 19 + index * 12)
            scrollbar(scroll, len(body), visible, 19, 96)
            if show_notice:
                text(fit(notice if connected else "Offline. Reconnecting"), 6, 106, muted)


def update():
    global selected, selected_id, view, scroll, choice, details_return, c_started, c_help
    poll_network()
    if io.BUTTON_C in io.pressed:
        c_started = ticks()
    if (
        c_started is not None
        and io.BUTTON_C in getattr(io, "held", ())
        and elapsed(c_started) >= 500
    ):
        c_help = True
    c_tap = False
    if io.BUTTON_C in getattr(io, "released", ()):
        c_tap = not c_help
        c_started = None
        c_help = False
    if c_help:
        render()
        return
    direction = -1 if io.BUTTON_UP in io.pressed else 1 if io.BUTTON_DOWN in io.pressed else 0
    if direction:
        if view == "threads" and threads:
            selected = (selected + direction) % len(threads)
            selected_id = threads[selected]["id"]
        elif view == "options" and current():
            choices, _ = options(current())
            if choices:
                choice = (choice + direction) % len(choices)
                scroll = 0
        else:
            scroll = max(0, scroll + direction)
    if io.BUTTON_A in io.pressed:
        view = details_return if view == "details" else "threads"
        scroll = 0
        acknowledge()
    if io.BUTTON_B in io.pressed:
        if view == "threads" and threads:
            open_thread()
        elif view in ("chat", "details"):
            open_options()
        elif view == "options":
            submit()
        elif view == "connection":
            disconnect("Reconnecting")
    if c_tap:
        if view == "threads":
            view = "connection"
        elif view == "options":
            details_return = "options"
            view = "details"
            scroll = 0
        elif view == "details":
            view = details_return
        elif view == "connection":
            view = "threads"
        else:
            open_options()
    if hasattr(badgeware, "display") and hasattr(badgeware.display, "backlight"):
        badgeware.display.backlight(0.6)
    render()


def on_exit():
    disconnect()
    if hasattr(badgeware, "display") and hasattr(badgeware.display, "backlight"):
        badgeware.display.backlight(0.6)

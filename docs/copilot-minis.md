# Copilot Minis

Copilot Minis is a badge remote for Copilot CLI sessions running on a laptop.
The laptop uses GitHub's Python SDK and its installed Copilot CLI. The badge
runs an ordinary MonaOS app. No custom boot image is required.

## First-version design

The badge browses threads, reads recent messages, answers permission requests,
selects agent-provided choices, and sends preset continuation messages. Static
unread markers and "Needs reply" or "Needs approval" labels indicate attention.
Brightness stays steady. Pending requests remain visible until answered.

The interface inherits the badge's small pixel-font menus. It uses `ark.ppf`,
a 160x120 framebuffer, measured text wrapping, one compact context line, and
eight visible chat lines. Hold C shows button help on demand. Thread rows show
both a title and a status, with four rows visible. Pending
questions open directly with numbered option rows; C reads full request
details or long choices before submitting. Reject is the initial
permission selection. Approvals apply to one request only.

## Source investigation

Downloaded alongside `home/`:

- `../copilot-cli`, GitHub's distribution repository, commit
  `a9ba11a191255b3f7b323b425b717f7db14b6c74`. It contains README, changelog,
  installer, license, and repository metadata, not the CLI implementation.
- `../copilot-sdk`, open SDK source, commit
  `ef04633cc84e4ba8e79888a39259ca276f5de732`.

The installed CLI was `1.0.89-7`. SDK `1.0.16` successfully connected to it
and listed saved sessions. This prototype pins that SDK version.

## Run

From `home/`, start a deterministic demo:

```sh
uv run --no-project tools/copilot_minis.py --demo --host 0.0.0.0 --badge-host 192.168.1.3
```

Use your laptop's current LAN IPv4 address for `--badge-host`. The bridge writes
an owner-only `.badge-local/copilot-minis.json` with that address, port, and a
random pairing token. It never prints the token. Keep the bridge process running.

Start real Copilot sessions:

```sh
uv run --no-project --with github-copilot-sdk==1.0.16 tools/copilot_minis.py \
  --host 0.0.0.0 --badge-host 192.168.1.3 --cwd /path/to/project
```

Use `/new NAME | PROMPT` in the bridge terminal to start an agent. `/saved`
lists saved IDs and summaries. `/resume ID` explicitly resumes an inactive saved
session. `/send ID | PROMPT` sends a message, `/list` shows managed threads, and
`/quit` shuts down. Plain text goes to the latest selected console session.
GitHub authentication uses the installed CLI's login. Resume only sessions you
have stopped using in another terminal. This does not hijack an existing TUI.

## Install on the badge

Double-tap RESET and wait for BADGER to mount:

```sh
uv run --no-project tools/badge.py deploy --app copilot-minis
diskutil eject /Volumes/BADGER
```

Tap RESET, then copy the private pairing file to the writable root in normal
serial mode, using the current port from `mpremote devs`:

```sh
uv tool run mpremote connect /dev/cu.usbmodem101 fs cp \
  .badge-local/copilot-minis.json :/copilot-minis.json + reset
```

Launch Copilot Minis from the menu. It uses existing `/secrets.py` Wi-Fi
credentials. Both devices need the same reachable LAN and the badge needs
2.4 GHz Wi-Fi. Allow inbound TCP port 8765 on the laptop. The pairing file can
also be placed at `/system/apps/copilot-minis/config.json` before disk ejection.
Root config takes priority. Reuse the pairing file on bridge restarts.

## Controls

| View | Up/Down | A | B | C |
| --- | --- | --- | --- | --- |
| Threads | Select thread | Back/acknowledge | Open thread or pending question | Connection info |
| Chat | Scroll text | Return to threads | Open actions or reply | Open actions or reply |
| Options | Select option | Return to threads | Submit selected option | Read full choice and request |
| Details | Scroll text | Return to options | Return to options | Return to options |

HOME exits. Options include Continue, Status update, and Stop when appropriate.
Hold C for half a second to show button help. Release it to return without
triggering the short-tap action. The screen has no permanent button bar.
Permission options are Reject and Allow once. Agent-provided choices appear
verbatim, with measured wrapping and scrolling for long labels.

## Protocol and limits

TCP carries newline-delimited JSON with token authentication, 32 KiB frame
limits, and one-second state snapshots. The badge uses nonblocking sockets and
bounded buffers, so unavailable hosts do not freeze button handling. A missing
heartbeat makes the badge show disconnected and disables commands. Requests
expire after five minutes. Replies include a request ID and session ID; stale
or cross-session choices fail. Disconnects never auto-approve tools. Token
authentication does not encrypt the LAN traffic. Use a trusted hotspot for
this prototype rather than an untrusted shared network.

Snapshots contain up to 12 managed sessions, six recent messages per session,
and 700 characters per message. Full session history remains on the laptop.
Free-form-only questions stay on the laptop and can be answered through
`/answer REQUEST_ID | TEXT`. An agent being quiet is not treated as a crash.
The bridge reports explicit idle, error, shutdown, and interrupted events.

## Checks

```sh
uv run --no-project tools/test_copilot_minis.py
uv run --no-project tools/test_badge.py
SDL_VIDEODRIVER=dummy uv run --no-project --with pygame tools/test_copilot_minis_render.py
uv run --no-project tools/verify_copilot_minis.py --badge-host 192.168.1.3
uv run --no-project --with github-copilot-sdk==1.0.16 tools/test_copilot_minis_live.py
uvx ruff check tools/copilot_minis.py tools/test_copilot_minis.py badge25/apps/copilot-minis
```

Demo mode exercises the same network protocol and pending-request machinery,
but it does not call a model. Hardware and live-Copilot results are recorded
below after verification.

## Verified on October 4, 2026

- The connected RP2350 badge paired with a laptop at `192.168.1.3` over Wi-Fi.
  It received three threads and rendered the app using an 11-pixel `ark` font.
- Scripted input on the physical MicroPython runtime exercised B open, C
  options, Down selection, B submit, A back, and Up navigation. The laptop
  received a permission reply, an agent question reply, and Continue. This
  exercises the input code with injected states, not an automated press of the
  physical switches.
- The live CLI ran `pwd` in a temporary directory after a permission reply
  crossed the authenticated TCP protocol. It returned `MINIS_LIVE_OK` and
  emitted the idle event. That test used a desktop protocol client. The badge
  network test used deterministic demo agents.
- The app and original 24x24 icon were checksum-deployed to BADGER. The user
  confirmed opening it through the real launcher.
- Live inspection found `io.led` unavailable. The installed runtime accepts
  `badgeware.display.backlight(0.4)` and `0.6`. The initial pulse was removed
  after user feedback; the app sets constant brightness. Independent control
  of four zones is not exposed by the
  inspected Python API.
- Offline checks cover wrong-token rejection, cross-session reply rejection,
  one-shot request IDs, pending-request stop, bounded Unicode snapshots, and
  private pairing-file permissions.

The bridge stops when the terminal command exits. To keep agents running while
walking around, leave that terminal open and prevent the laptop from sleeping.

The redesigned interface passed the physical badge network flow, direct-option
navigation and details/back actions. The app was checksum-deployed to BADGER.
Simulator regression checks cover fixed brightness, Info without reconnecting,
direct opening of pending questions, and text bounds.

The compact content-first revision also passed physical badge permission and
question replies, Continue, and hold-C help. It was checksum-deployed. The live
bridge was restarted with zero managed threads at the user's request; saved
CLI history remains available through `/saved`. The badge returns to "All clear"
when its managed thread list is empty.

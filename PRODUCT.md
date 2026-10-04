# Copilot Minis

## Platform

Embedded MicroPython on the GitHub Universe 2025 badge.

## Users and purpose

Developers at conferences who want to leave agents running on a laptop and
monitor their chats from a wearable badge on the same network. The badge alerts
them when an agent needs permission, asks a question, finishes, or fails.

## Confirmed first version

The user approved a laptop bridge with SDK-managed Copilot CLI sessions and a
MicroPython badge app. Up/Down select threads or options, B confirms, A returns,
C opens actions or reads full option details, and HOME returns to the launcher. The bridge retains GitHub
authentication on the laptop. The badge receives bounded text and sends choices.

The user requested Copilot CLI-like terminal styling, square selectable option
rows, direct access to choices, and a readable screen that does not dim for
updates. Up/Down navigates, A backs out, and B selects throughout the app.
The user also requested minimal permanent controls so content occupies most
of the display. Button help appears while holding C; the main screen omits
branding, a LIVE label, and the fixed button bar.

The launcher avatar uses the official Copilot mark with a small dotted chat
companion to identify Minis.

## Hardware constraints

The connected board is `github_badger_2350`. The LCD is 320x240, with a 160x120
logical framebuffer. There are five front buttons and four backlight zones.
Existing MonaOS firmware, fonts, and Wi-Fi support are sufficient. Conference
networks must permit connections between devices; a 2.4 GHz hotspot is an option.

## Open decisions

Attaching to arbitrary already-running terminal sessions is a later integration.
The first version creates or explicitly resumes sessions through the bridge.
Free-text input belongs on the laptop; the badge provides preset replies and
agent-supplied choices.

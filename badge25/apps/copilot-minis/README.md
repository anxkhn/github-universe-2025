# Copilot Minis

<img src="icon.png" width="96" height="96" alt="Copilot mark with a small three-dot chat companion">

A wearable remote for Copilot CLI sessions on your laptop. Browse chats,
answer tool permissions and agent questions, and continue or stop a task over
Wi-Fi. The badge runs MicroPython on the existing MonaOS firmware.

## Start the laptop bridge

Run from the repository root, using your laptop's LAN IPv4 address:

```sh
uv run --no-project --with github-copilot-sdk==1.0.16 tools/copilot_minis.py \
  --host 0.0.0.0 --badge-host 192.168.1.3 --cwd /path/to/project
```

Start a thread with `/new NAME | PROMPT`. Both devices must share a reachable
network; the badge needs 2.4 GHz Wi-Fi. GitHub authentication stays on the laptop.

See the [setup guide](../../../docs/copilot-minis.md) for pairing, installation,
demo mode, protocol limits, and verification.

## Buttons

- Up/Down selects chats or options and scrolls text.
- B opens a chat, shows actions, or submits the highlighted choice.
- A goes back. C reads full option details or opens actions.
- Hold C for button help. Release to return. HOME exits.

Questions open directly with numbered options. The content-first interface
shows eight chat lines and keeps brightness steady.

## Icon source

The launcher icon uses GitHub's official [Copilot Octicon](https://primer.style/octicons/icon/copilot-24/),
with a small three-dot chat companion for Minis. `copilot.svg` preserves the
upstream geometry from `primer/octicons` commit
`923a31b34542702800cb90a0fd390e2e60dd92ac`. The MIT license is in
`LICENSE.octicons` and embedded in the generated PNG.

Rebuild from the repository root:

```sh
uv run --no-project --with pillow --with resvg-py tools/build_copilot_minis_icon.py
```

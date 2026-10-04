# Fireplace

A cosy animated fireplace app for the GitHub Universe 2025 badge. The speed can be adjusted to the user's preference.

This app was inspired by the fireplace from [Lenny's Podcast](https://www.lennysnewsletter.com/podcast) quietly running in the background.

## Controls

| Button | Action |
|--------|--------|
| **↑ UP** | Speed up (−50ms per press, min 50ms/frame) |
| **↓ DOWN** | Slow down (+50ms per press, max 1000ms/frame) |
| **A / B / C** | Reset to default speed |
| **HOME** | Return to menu |

The current frame duration is displayed briefly at the bottom of the screen whenever the speed is changed.

## Installation

Double-tap RESET while connected over USB. Copy the `fireplace/` folder to
`/Volumes/BADGER/apps/fireplace/` on macOS, eject, and reset. That disk location
maps to `/system/apps/fireplace/` during normal execution.

```
fireplace/
├── __init__.py       # App code
├── icon.png          # Menu icon (24x24)
└── frames/           # Extracted PNG frames (frame_0000.png … frame_0019.png)
```

## Running in the Simulator

```bash
uv run --no-project --with pygame badge25/simulator/badge_simulator.py badge25/apps/fireplace --scale 4
```

## Animation Details

- **Source**: [Pexels video](https://www.pexels.com/video/close-up-on-fire-in-fireplace-11543712/), free to use under the [Pexels License](https://www.pexels.com/license/)
- **Frames**: 20 PNGs at 160×120 pixels, center-cropped to 4:3 and evenly sampled across the clip
- **Default speed**: 100ms per frame (10 fps)

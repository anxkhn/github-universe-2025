# Smaller badge assets

Badgeware loads PNG images. WebP, AVIF, and JPEG conversion would require a
different decoder and app changes. This toolkit keeps the existing filenames,
dimensions, sprite-sheet layout, and transparency.

## Optimize locally

Install `oxipng`, then run:

```sh
# Lossless preview, no files changed
uv run --no-project --with pillow tools/optimize_assets.py

# Apply lossless recompression
uv run --no-project --with pillow tools/optimize_assets.py --apply

# Also allow 128-color PNGs for Fireplace and Copilot Loop RGB frames
uv run --no-project --with pillow tools/optimize_assets.py --lossy --apply

uv run --no-project --with pillow tools/test_optimize_assets.py
```

Every changed original goes into `.badge-local/asset-originals/` under its
SHA-256. `report.json` records byte totals and file-level results. Smaller
candidates replace originals through a temporary file. Lossless changes must
decode to identical RGBA pixels. All changes preserve dimensions and alpha.
Lossy conversion is restricted to the two animation frame directories and
accepted only when per-channel RMS error is at most 6 on a 0–255 scale.
Pixel-art sprites, icons, startup frames, and documentation renders stay lossless.

The first pass reduced 321 local PNGs from 10,535,564 to 6,788,507 bytes,
saving 3,747,057 bytes. 320 files became smaller. There were no JPEG assets.
File size does not equal filesystem space saved; small files occupy allocation
blocks, and decoded images still need RAM according to their dimensions.

Runtime repository PNGs shrank from 2,337,314 to 1,555,648 bytes. Fireplace
shrank from 765,030 to 284,624 bytes, and Copilot Loop from 369,241 to 167,936.
The installed Pokedex sprites also received lossless compression. After
deployment, all 594 installed runtime PNGs decoded on the badge, including
302 normal/shiny sprites. The badge reported 5,390,336 free filesystem bytes.

## Deploy only runtime files

The deployer excludes top-level `images/`, `badgerware/`, and `simulator/`.
The four documentation renders alone originally occupied 8,185,136 bytes.
They remain in the repository for documentation and do not belong on the badge.
The deployer does not delete already-installed files.

Double-tap RESET, deploy, eject cleanly, then reset:

```sh
uv run --no-project tools/badge.py deploy
diskutil eject /Volumes/BADGER
```

Runtime compatibility can be checked in normal serial mode:

```sh
uvx --from mpremote==1.29.0 mpremote run tools/check_assets_device.py
```

For device-only sprites, prefer copying them to local storage, optimizing
there, then doing a supervised deployment. Hundreds of small USB disk writes
are slow. A reset or USB disconnect during a write can interrupt the copy.
Do not impose a short process timeout on a bulk device write.

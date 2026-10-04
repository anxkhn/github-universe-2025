# Restore and tinker with the Universe 2025 badge

This guide restores the official MonaOS firmware, installs this fork's 31-app
bundle, configures private Wi-Fi credentials, and sets up development tools.
The workflow was tested on a physical badge and an Apple Silicon Mac on
October 4, 2026. Linux and Windows paths below are guidance, not hardware-tested
results from this session.

## 1. Identify your badge

The supported badge has five front buttons marked A, B, C, Up, and Down, plus
rear HOME/BOOT and RESET. Its USB serial identity is `2e8a:0005`,
`Pimoroni GitHub Badger MicroPython`. MicroPython reports
`GitHub Badger with RP2350`. `picotool info -a` reports board
`github_badger_2350`.

This toolkit deploys `badge25/`. The standard Pimoroni Tufty
2350 is a different board. A newer upstream version number does not make
its firmware a compatible upgrade for this device.

## 2. Install tools and clone

You need a USB data cable, Git, [uv](https://docs.astral.sh/uv/getting-started/installation/),
and [picotool](https://github.com/raspberrypi/picotool). GitHub CLI is useful for
checking releases but is not required by the toolkit.

On macOS with Homebrew already installed:

```sh
brew install uv picotool git gh
git clone --branch universe-2025 https://github.com/anxkhn/github-universe-2025.git
```

Open a terminal in the cloned `github-universe-2025` directory. All remaining host commands
assume that working directory. Python commands use uv's managed environment.
The toolkit invokes pinned `mpremote==1.29.0` through `uvx` automatically.
For interactive use, install its executable:

```sh
uv tool install mpremote
uv run --no-project tools/badge.py doctor
```

On Windows or Linux, install uv and Git using their official installers, then
install picotool using Raspberry Pi's installation instructions. Linux may
require serial group membership and picotool's USB rules. Windows serial ports
look like `COM4`; Linux ports look like `/dev/ttyACM0`.

## 3. Understand the three USB modes

| Mode | Enter it | Mac identity | Use |
| --- | --- | --- | --- |
| Normal | Tap RESET once | `/dev/cu.usbmodem...` | MicroPython REPL, state, diagnostics |
| App disk | Double-tap RESET quickly | `/Volumes/BADGER` | Copy apps, assets, launcher, config |
| BOOTSEL | Hold rear HOME/BOOT, tap RESET, release HOME/BOOT | `/Volumes/RP2350` | Firmware flashing and flash backup |

BOOTSEL can leave the display blank. BADGER mode shows USB Disk Mode. They are
different disks. The RP2350 disk's apparent 134 MB capacity is virtual and does
not represent the badge's 16 MB flash.

The BADGER disk root is the device's `/system` partition:

```text
Mac disk                       Device runtime
/Volumes/BADGER/apps/           /system/apps/
/Volumes/BADGER/assets/         /system/assets/
/Volumes/BADGER/main.py         /system/main.py
```

During normal runtime `/system` is read-only. The small root filesystem and
`/state` are writable over serial. Do not try to install apps to `/system`
using normal `mpremote fs cp`.

## 4. Back up before flashing

Enter BOOTSEL mode, then:

```sh
uv run --no-project tools/badge.py backup .badge-local/before-restore.uf2
```

This reads all 16 MB of flash into a 32 MB UF2 and verifies the result.
Choose a new filename for each backup. Full-flash backups can contain private
configuration and saved state; keep them local. This command leaves the device
in BOOTSEL mode.

To inspect manually:

```sh
picotool info -a
```

The board guard requires an installed image that identifies as
`github_badger_2350`. For a blank or corrupted device, manually confirm the
physical model before using the manual recovery commands in section 11.

## 5. Restore official factory firmware

This toolkit pins [MonaOS v4.03](https://github.com/badger/home/releases/tag/mona-os-v4.03),
the latest official 2025 badge release found during setup. It contains the
custom drivers, assets, launcher, and six factory apps.

```sh
uv run --no-project tools/badge.py download
uv run --no-project tools/badge.py flash --yes
```

The download command verifies SHA-256 before accepting the image. Flashing
verifies the firmware and filesystem after writing, then reboots. `--yes`
confirms replacement of the firmware and app filesystem. Saved state outside
the image's written ranges can survive; use the state commands below if you
want to reset specific progress.

Expected board metadata is MicroPython, board `github_badger_2350`, build date
October 20, 2025. The release tag is the bundle version, not the build date.

Factory restore does not install this fork's additional apps. Continue below.

## 6. Install the full app bundle

Download the optional Pokedex assets while the badge is in normal mode:

```sh
uv run --no-project tools/badge.py sprites
```

This fetches 151 normal and 151 shiny PNGs. They remain ignored local files
under `badge25/apps/pokedex/`. The app works offline once they are installed.

Double-tap RESET, wait for BADGER to mount, then:

```sh
uv run --no-project tools/badge.py deploy
diskutil eject /Volumes/BADGER
```

For another mount path:

```sh
uv run --no-project tools/badge.py deploy --volume /media/you/BADGER
```

The deployer checks the expected volume structure, skips matching files, copies
app code and assets without macOS metadata, and verifies each copied file's
checksum. It does not delete unrelated installed apps or overwrite credentials.
Transfers of hundreds of small files can take several minutes. Wait for the
success message and eject before pressing RESET. On Windows or Linux, safely
eject the disk with the OS file manager.

Tap RESET once. Press rear HOME to leave the startup animation. The launcher
discovers apps automatically. A/C change icons and pages, Up/Down change rows,
B launches, and rear HOME returns to the menu. This bundle has 31 user apps
across six pages. See the [app catalog](apps.md) for sources and controls.

## 7. Configure Wi-Fi and GitHub

Use a 2.4 GHz Wi-Fi network. Return to normal serial mode and run:

```sh
uv run --no-project tools/badge.py configure
```

Enter your SSID, password, GitHub username, and an optional GitHub token at the
prompts. Passwords do not appear as command-line arguments. The tool saves a
private ignored `.badge-local/secrets.py` and writes `/secrets.py` over serial.
The root config is the one the installed apps explicitly prefer.

To reuse that config later:

```sh
uv run --no-project tools/badge.py configure --file .badge-local/secrets.py
```

To also update the disk copy while BADGER is mounted:

```sh
uv run --no-project tools/badge.py configure --file .badge-local/secrets.py --volume /Volumes/BADGER
diskutil eject /Volumes/BADGER
```

Update both copies when changing credentials. The factory firmware copies some
system files to its writable root on first boot, so disk edits alone can leave
an older root config in use. `badge25/secrets.py` remains an empty template.

The Badge app needs `GITHUB_TOKEN` to exist even when its value is empty.
Unauthenticated GitHub requests need a User-Agent header and share the API's
rate limit. The bundle's Badge app already supplies headers. No token is needed
for the tested public profile fetch.

Set your timezone with Up/Down in the System app. System and Wordclock default
to UTC. Clock attempts IP-based timezone detection. No timezone was guessed
from a username or Wi-Fi name.

## 8. Unlock or reset the infrared quest

Mona's Quest listens to NEC infrared beacons through the receiver on GPIO21.
It does not use NFC or RFID. Nine beacon IDs correspond to nine locations.
The game stores completed IDs in `/state/quest.json`.

```sh
uv run --no-project tools/badge.py quest status
uv run --no-project tools/badge.py quest unlock
uv run --no-project tools/badge.py quest reset
```

Unlock sets IDs 1 through 9 completed. Reset replaces them with an empty list.
Both are optional state changes; neither modifies the receiver or game code.
The original game still accepts real beacons after reset.

## 9. Verify the setup

```sh
uv run --no-project tools/badge.py inspect
uv run --no-project tools/badge.py smoke
uv run --no-project tools/test_badge.py
```

The hardware smoke test loads and renders the eleven additions, exercises
2048 merging and Tennis gameplay, and loads icons for every launcher page.
It bypasses network work in Wordclock and Christmas so those rendering checks
do not depend on internet access. It does not replace a game playthrough or
test every live service. Serial commands interrupt the running app; the host
tool resets afterward.

During setup the physical badge connected to Wi-Fi, fetched a public GitHub
profile with HTTP 200, and synced NTP. All eleven additions passed hardware
smoke checks. The original 20 apps were installed with matching source checksums;
their external services were not all exercised.

## 10. Make your first app

Start with `badge25/apps/hello/__init__.py` or create
`badge25/apps/my_app/__init__.py`:

```python
from badgeware import screen, brushes, PixelFont, io

count = 0

def init():
    screen.font = PixelFont.load("/system/assets/fonts/nope.ppf")

def update():
    global count
    if io.BUTTON_B in io.pressed:
        count += 1
    screen.brush = brushes.color(20, 30, 40)
    screen.clear()
    screen.brush = brushes.color(255, 255, 255)
    screen.text("B presses: %d" % count, 10, 50)
```

Add a 24x24 PNG named `icon.png`. The menu uses a default icon if one is absent.
The launcher calls `init()` once, `update()` every frame, and optional
`on_exit()` when HOME exits. Do not call a blocking `run()` on app import.

Run locally:

```sh
uv run --no-project --with pygame badge25/simulator/badge_simulator.py badge25/apps/my_app
```

The simulator uses the `badge25/` asset tree. A/Z, B/X, C/Space, arrow keys,
and H/Escape emulate buttons. Hardware networking, IR, and timing can differ;
finish with a real-device test. The archived [API docs](../badge25/badgerware/)
and existing working apps are useful references.

For an interactive REPL:

```sh
mpremote devs
mpremote connect /dev/cu.usbmodem101 repl
```

Substitute the actual port. Exit with Ctrl-]. Use `mpremote run probe.py` for
multi-line device code. Do not embed literal backslash-n sequences in shell
strings. Only one serial client can own the port.

## 11. Recovery and backups

If a bad app or launcher prevents startup, enter BOOTSEL with HOME/BOOT + RESET.
This ROM bootloader works independently of installed Python apps.

Restore a full backup:

```sh
picotool load -v .badge-local/before-restore.uf2
picotool reboot
```

For a blank board whose physical identity you have confirmed, the manual
official-image recovery is:

```sh
uv run --no-project tools/badge.py download
picotool load -v .badge-local/github-badger-2350-with-filesystem.uf2
picotool reboot
```

After factory restore, deploy apps and configure credentials again. For an
exact clone of your fully configured device, take another `backup` after
deployment. That private image includes apps, sprites, settings, and state.

This repository packages the official UF2 plus a deployable filesystem rather
than inventing a new low-level firmware build. It does not include the complete
2025 custom C firmware source or publish a personalized flash dump. The
[upstream Tufty repository](https://github.com/pimoroni/tufty2350) is a source
reference, not a drop-in replacement for this board's MonaOS build.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| No badge USB device at all | Use a data-capable cable, try a direct Mac port, reconnect, check `ioreg -p IOUSB -w 0` |
| Charges but no disk | Charging does not prove USB data. Test HOME/BOOT + RESET separately |
| RP2350 works, normal USB does not | Back up, verify model, restore the official image; do not format RP2350 |
| USB Disk Mode screen but Finder has no disk | Run `diskutil list external`; if BADGER exists but is unmounted, use `diskutil mount` with its current identifier |
| Files disappear or app import fails after copying | Wait for verified deployment, eject cleanly, then reset; do not reset during writes |
| `OSError: 30` while copying serial files | `/system` is read-only normally. Deploy through BADGER disk mode |
| Serial access fails or hangs | Close Thonny, REPL terminals, and Web Serial tabs; rediscover the port |
| Interrupting an app disconnects USB | Tap RESET and stay at startup or the launcher, then retry. This occurred after testing an app and cleared after a physical reset |
| Wi-Fi status -3 | Firmware reports wrong password; check exact case and characters |
| NTP timeout | Test another host such as `time.cloudflare.com`; verify DNS and router access |
| New app not in launcher | Check its directory contains `__init__.py`, then reset |
| Badge shows zero or ERR contributions | Hold A+C once to refresh. Empty caches are re-fetched; downloads replace caches only after receiving valid JSON. Failed refreshes retain valid cached counts. ERR means no valid contribution data is available |
| Pokedex has no sprite | Run `sprites`, deploy its downloaded PNGs, eject, and reset |
| Disk copy takes a long time | Hundreds of small writes are slow. The checksum deployer skips unchanged files |
| App uses unavailable graphics or sensor APIs | Port it to the installed MonaOS API and test on hardware |

For exact command flags, run `uv run --no-project tools/badge.py --help` or
`uv run --no-project tools/badge.py deploy --help`.

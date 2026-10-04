# GitHub Universe 2025 badge toolkit

Restore, configure, and build apps for the colour-screen GitHub Universe 2025
badge with A, B, C, Up, and Down buttons. This fork contains 31 user apps,
MonaOS restoration tools, offline Pokedex downloads, and a paginated launcher.

**Start with the [restore and tinkering guide](docs/2025-guide.md).**

```sh
git clone --branch universe-2025 https://github.com/anxkhn/github-universe-2025.git
```

Open a terminal in the cloned directory:

```sh
uv run --no-project tools/badge.py doctor
```

## Repository layout

| Path | Purpose |
| --- | --- |
| [badge25/](badge25/) | Deployable system files, 31 apps, assets, simulator, and API docs |
| [tools/](tools/) | Verified download, backup, flash, deploy, configuration, quest, and checks |
| [docs/2025-guide.md](docs/2025-guide.md) | Installation, USB modes, recovery, Wi-Fi, and development |
| [docs/apps.md](docs/apps.md) | App catalog, controls, sources, and test results |
| [ir-beacon/](ir-beacon/) | Infrared beacon protocol and hardware experiments |

## USB modes

- Tap RESET once for normal operation and MicroPython serial.
- Double-tap RESET for the `BADGER` app-editing disk.
- Hold rear HOME/BOOT, tap RESET, then release HOME/BOOT for the `RP2350`
  firmware bootloader disk.

The BADGER disk root maps to `/system` on the badge. Put apps in `BADGER/apps/`.
Eject cleanly before resetting. See the guide for verified backup and restore.

## Checks

```sh
uv run --no-project tools/test_badge.py
uv run --no-project tools/check_docs.py
uvx ruff check tools badge25
```

The toolkit targets MonaOS v4.03 for board `github_badger_2350`. Wi-Fi
credentials, downloaded firmware, personal backups, and downloaded Pokemon
sprites stay local. The committed configuration template is empty.

App contributions are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md) and
[AGENTS.md](AGENTS.md). The source license is [MIT](LICENSE); imported app
attribution and asset sources are recorded in the catalog.

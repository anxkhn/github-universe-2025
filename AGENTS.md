# Working on this badge toolkit

- This fork's tested device is the GitHub Universe 2025 badge, USB serial
  `2e8a:0005`, board `github_badger_2350`. Work in `badge25/` for its apps.
  Read the directory's instructions and `docs/2025-guide.md` before hardware operations.
- Discover the current serial port. Run only one serial client at a time.
  `mpremote` commands interrupt apps; reset after device checks.
- BADGER volume root maps to `/system`, so deploy to `BADGER/apps`, not
  `BADGER/system/apps`. RP2350 is the separate firmware bootloader disk.
- Use `uv` for Python and `picotool` for verified flash operations. Back up all
  flash before restoration. Verify board identity before flashing. Never
  substitute generic Tufty firmware for the MonaOS image.
- Keep credentials, flash backups, downloaded UF2s, and downloaded Pokemon
  sprites local. `.badge-local/` and Pokedex sprite directories are ignored.
  Never embed a Wi-Fi password or token in docs, commands, commits, or output.
- Apps imported by the launcher expose `update()` and optional `init()` and
  `on_exit()`. Guard standalone `run()` calls with `if __name__ == "__main__"`.
  Use the 2025 `screen.brush`, `screen.draw`, and `io` API. The legacy docs
  contain some inaccurate examples; live module inspection takes precedence.
- Run `uv run --no-project tools/test_badge.py` and Ruff on changed Python files.
  After deployment, run `uv run --no-project tools/badge.py smoke`, then reset
  and test real launcher navigation. A rendering smoke test is not a full game
  playthrough or a live-network test.
- Preserve imported community-app attribution. Record new sources and pins in
  `docs/apps.md`. Test every addition against the installed runtime.

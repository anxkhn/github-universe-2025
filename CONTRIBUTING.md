# Contributing

This repository targets the GitHub Universe 2025 badge and its MonaOS runtime.
Add applications under `badge25/apps/<name>/`, with `__init__.py`, a 24x24
`icon.png`, and optional assets. Expose `update()` and optional `init()` and
`on_exit()`. Guard standalone `run()` calls so the launcher can import the app.

Use `screen.brush`, `screen.draw()`, and `io.BUTTON_*`. Use elapsed time for
movement. Test with the included simulator and on a physical badge before
claiming hardware compatibility.

```sh
uv run --no-project tools/test_badge.py
uv run --no-project tools/check_docs.py
uvx ruff check tools badge25
```

Format changed Python files with Ruff. Include controls, asset attribution,
test evidence, and a screenshot when submitting an app. Never commit Wi-Fi
credentials, tokens, personal backups, or downloaded third-party sprites.

Read the [tinkering guide](docs/2025-guide.md), [app catalog](docs/apps.md), and
[development instructions](AGENTS.md). Contributions use the repository's
[MIT license](LICENSE).

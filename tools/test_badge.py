"""Offline checks. Run with uv run --no-project tools/test_badge.py."""

import tempfile
import ast
from pathlib import Path
import badge

with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    config = root / "secrets.py"
    config.write_text("WIFI_SSID='test'\nWIFI_PASSWORD='test'\nGITHUB_USERNAME='test'\n")
    assert "GITHUB_TOKEN" in badge.configuration(config)
    config.write_text("import os\n")
    try:
        badge.configuration(config)
    except ValueError:
        pass
    else:
        raise AssertionError("Executable config accepted")
    source = root / "source"
    source.mkdir()
    (source / "main.py").write_text("print('test')\n")
    (source / "secrets.py").write_text("private\n")
    (source / ".DS_Store").write_bytes(b"metadata")
    volume = root / "BADGER"
    (volume / "apps/menu").mkdir(parents=True)
    (volume / "apps/menu/__init__.py").write_text("")
    (volume / "assets").mkdir()
    badge.deploy(volume, source)
    assert (volume / "main.py").read_bytes() == (source / "main.py").read_bytes()
    assert not (volume / "secrets.py").exists()
    assert not (volume / ".DS_Store").exists()
    badge.deploy(volume, source)
print("Configuration validation and verified deployment passed")

apps = badge.ROOT / "badge25/apps"
for app in (
    "2048",
    "christmas",
    "clock",
    "fireplace",
    "hydrate",
    "jungle",
    "pokedex",
    "system",
    "tennis",
    "tomato",
    "wordclock",
):
    ast.parse((apps / app / "__init__.py").read_text())
    assert (apps / app / "icon.png").read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
for sprite in ("player", "log", "creature", "branch"):
    assert (apps / "jungle/sprites" / (sprite + ".png")).is_file()
assert len(list((apps / "fireplace/frames").glob("*.png"))) == 20
for statement in ast.parse((badge.ROOT / "badge25/secrets.py").read_text()).body:
    if isinstance(statement, ast.Assign):
        assert ast.literal_eval(statement.value) == "", "Committed configuration must be empty"
print("App syntax, icons, packaged assets, and empty credential template passed")

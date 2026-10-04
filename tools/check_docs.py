"""Check local links in the toolkit's entry points and guides."""

import re
from pathlib import Path

root = Path(__file__).resolve().parents[1]
for path in [root / "README.md", *sorted((root / "docs").glob("*.md"))]:
    for target in re.findall(r"\]\(([^)]+)\)", path.read_text()):
        if "://" in target or target.startswith("#"):
            continue
        assert (path.parent / target.split("#")[0]).exists(), (path, target)
print("Toolkit documentation links passed")

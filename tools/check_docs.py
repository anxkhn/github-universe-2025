"""Check local links in the toolkit's entry points and guides."""

import re
from pathlib import Path

root = Path(__file__).resolve().parents[1]
for path in [root / "README.md", *sorted((root / "docs").glob("*.md"))]:
    content = path.read_text()
    targets = re.findall(r"\]\(([^)]+)\)", content)
    targets += re.findall(r'(?:href|src)="([^"]+)"', content)
    for target in targets:
        if "://" in target or target.startswith("#"):
            continue
        assert (path.parent / target.split("#")[0]).exists(), (path, target)
print("Toolkit documentation links passed")

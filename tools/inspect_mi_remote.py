"""Inspect a Mi Remote database archive without executing its embedded code."""

import argparse
import json
import tarfile
from pathlib import Path


def inspect(archive, brands):
    profiles = []
    with tarfile.open(archive) as dump:
        for member in dump:
            path = Path(member.name)
            if not member.isfile() or path.parent.name != "3_AC" or path.suffix != ".json":
                continue
            if not any(brand.casefold() in path.stem.casefold() for brand in brands):
                continue
            if member.size > 8 * 1024 * 1024:
                raise ValueError("Unexpectedly large brand file")
            data = json.load(dump.extractfile(member))["data"]
            for profile in data.get("others", []):
                keys = profile.get("key", {})
                profiles.append(
                    {
                        "brand": path.stem,
                        "id": profile.get("_id"),
                        "frequency": profile.get("frequency"),
                        "type": profile.get("type"),
                        "fields": sorted(keys),
                        "state_rules": any(key in keys for key in ("1518", "1522")),
                    }
                )
            tree = data.get("tree") or {}
            for node in tree.get("nodes", [])[1:]:
                profiles.append(
                    {
                        "brand": path.stem,
                        "ids": node.get("keysetids"),
                        "frequency": node.get("frequency"),
                        "tree_node": True,
                    }
                )
    return profiles


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--brands", nargs="+", default=["Kenwood", "Kenstar"])
    args = parser.parse_args()
    profiles = inspect(args.archive, args.brands)
    print(json.dumps(profiles, indent=2))
    print("Profiles:", len(profiles))

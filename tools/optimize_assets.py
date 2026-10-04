"""Optimize PNGs, preserving dimensions and backing up every changed original.

Run with uv run --no-project --with pillow tools/optimize_assets.py.
Requires oxipng. Default is a dry run; --apply writes verified candidates.
"""

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from PIL import Image, ImageChops, ImageStat

ROOT = Path(__file__).resolve().parents[1]


def candidate(path, output, lossy=False):
    shutil.copyfile(path, output)
    compression = subprocess.run(
        ["oxipng", "-q", "-o", "3", "--strip", "safe", "--nb", "--nc", "--np", str(output)],
        capture_output=True,
        text=True,
    )
    if compression.returncode:
        raise ValueError("PNG optimization failed for %s: %s" % (path, compression.stderr))
    with Image.open(path) as original:
        before = original.convert("RGBA")
        if lossy and original.mode == "RGB":
            quantized = original.quantize(
                colors=128, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE
            )
            alternative = output.with_suffix(".palette.png")
            quantized.save(alternative, optimize=True, bits=8)
            difference = ImageChops.difference(before, quantized.convert("RGBA"))
            rms = max(ImageStat.Stat(difference).rms[:3])
            if rms <= 6 and alternative.stat().st_size < output.stat().st_size:
                shutil.copyfile(alternative, output)
        with Image.open(output) as result:
            result.load()
            after = result.convert("RGBA")
            if (
                after.size != before.size
                or after.getchannel("A").tobytes() != before.getchannel("A").tobytes()
            ):
                raise ValueError("Dimensions or transparency changed: " + str(path))
            if not lossy and before.tobytes() != after.tobytes():
                raise ValueError("Lossless optimization changed pixels: " + str(path))


def optimize(root, backup, apply=False, lossy=False):
    if not shutil.which("oxipng"):
        raise ValueError("Install oxipng first, for example brew install oxipng on macOS.")
    records = []
    before_total = after_total = 0
    with tempfile.TemporaryDirectory() as directory:
        for path in sorted(root.rglob("*.png")):
            relative = path.relative_to(root)
            if any(part.startswith(".") for part in relative.parts):
                continue
            if path.is_symlink():
                raise ValueError("Refusing symlink: " + str(path))
            photographic = relative.parts[:3] in (
                ("apps", "fireplace", "frames"),
                ("apps", "copilot-loop", "frames"),
            )
            output = Path(directory) / "candidate.png"
            candidate(path, output, lossy and photographic)
            before = path.stat().st_size
            after = min(before, output.stat().st_size)
            before_total += before
            after_total += after
            if after < before:
                records.append(
                    {
                        "path": str(relative),
                        "before": before,
                        "after": after,
                        "lossy_allowed": lossy and photographic,
                    }
                )
                if apply:
                    digest = hashlib.sha256(path.read_bytes()).hexdigest()
                    original = backup / digest / relative
                    original.parent.mkdir(parents=True, exist_ok=True)
                    if not original.exists():
                        shutil.copyfile(path, original)
                    temporary = path.with_name(".optimized-" + path.name)
                    shutil.copyfile(output, temporary)
                    temporary.replace(path)
                    print("Updated", relative, flush=True)
    result = {
        "before": before_total,
        "after": after_total,
        "saved": before_total - after_total,
        "changed": len(records),
        "applied": apply,
        "files": records,
    }
    if apply:
        backup.mkdir(parents=True, exist_ok=True)
        (backup / "report.json").write_text(json.dumps(result, indent=2) + "\n")
    print(
        "%s %d images: %d -> %d bytes, saved %d bytes"
        % (
            "Optimized" if apply else "Would optimize",
            len(records),
            before_total,
            after_total,
            before_total - after_total,
        )
    )
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT / "badge25")
    parser.add_argument("--backup", type=Path, default=ROOT / ".badge-local/asset-originals")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument(
        "--lossy", action="store_true", help="Allow 128 colors for fireplace/copilot frames only"
    )
    args = parser.parse_args()
    optimize(args.root.resolve(), args.backup.resolve(), args.apply, args.lossy)


if __name__ == "__main__":
    main()

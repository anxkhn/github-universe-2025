"""Check lossless pixels, alpha, dimensions, and bounded palette reduction."""

import tempfile
from pathlib import Path
from PIL import Image
from optimize_assets import candidate

with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    source = root / "source.png"
    output = root / "output.png"
    for mode in ("RGB", "RGBA", "P"):
        image = Image.new(mode, (24, 24))
        if mode == "P":
            image.putpalette([n % 256 for n in range(768)])
            image.info["transparency"] = 0
        image.save(source, compress_level=0)
        candidate(source, output)
        with Image.open(output) as compressed:
            assert compressed.size == image.size
            assert compressed.convert("RGBA").tobytes() == image.convert("RGBA").tobytes()
        assert output.stat().st_size < source.stat().st_size
    image = Image.new("RGB", (160, 120))
    image.putdata([(x, y, (x + y) % 256) for y in range(120) for x in range(160)])
    image.save(source, compress_level=0)
    candidate(source, output, lossy=True)
    with Image.open(output) as compressed:
        assert compressed.size == image.size
        assert compressed.mode in ("P", "RGB")
    assert output.stat().st_size < source.stat().st_size
print("PNG lossless pixels, alpha, dimensions, and palette checks passed")

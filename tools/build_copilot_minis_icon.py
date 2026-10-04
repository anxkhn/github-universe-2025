"""Rasterize GitHub's Copilot mark with a small dotted Minis companion."""

import io
from pathlib import Path
import resvg_py
from PIL import Image, ImageDraw, PngImagePlugin

APP = Path(__file__).resolve().parents[1] / "badge25/apps/copilot-minis"
SOURCE = "https://github.com/primer/octicons/blob/923a31b34542702800cb90a0fd390e2e60dd92ac/icons/copilot-24.svg"
SCALE = 8
image = Image.new("RGB", (24 * SCALE, 24 * SCALE), (17, 23, 27))
svg = (APP / "copilot.svg").read_text().replace("<path ", '<path fill="#70eceb" ')
mark = Image.open(
    io.BytesIO(resvg_py.svg_to_bytes(svg_string=svg, width=20 * SCALE, height=20 * SCALE))
)
image.paste(mark, (2 * SCALE, 0), mark)
draw = ImageDraw.Draw(image)
draw.rounded_rectangle(
    (14 * SCALE, 16 * SCALE, 23 * SCALE, 23 * SCALE), radius=2 * SCALE, fill=(240, 246, 252)
)
for x in (16, 18.5, 21):
    draw.ellipse((int(x * SCALE), 19 * SCALE, int((x + 1) * SCALE), 20 * SCALE), fill=(17, 23, 27))
image = image.resize((24, 24), Image.Resampling.LANCZOS)
metadata = PngImagePlugin.PngInfo()
metadata.add_text("Source", SOURCE)
metadata.add_text(
    "Adaptation",
    "Official Copilot silhouette in cyan, with a small three-dot chat companion. tools/build_copilot_minis_icon.py",
)
metadata.add_text("License", (APP / "LICENSE.octicons").read_text())
image.save(APP / "icon.png", pnginfo=metadata)

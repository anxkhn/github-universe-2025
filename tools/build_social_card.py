"""Build original offline social-card screens. Network access is opt-in."""

import argparse
import ast
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen

import qrcode
from PIL import Image, ImageDraw, ImageOps, PngImagePlugin

from build_minesweeper_assets import GLYPHS

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "badge25/apps/social-card"
AVATAR_SHA256 = "ae2ce9e6bc767404b7a4128667a8596135e2709ccfd9e24e9d78a13921847055"
SIZE = (160, 120)
BG = "#0d1117"
INK = "#f0f6fc"
MUTED = "#aab7c5"
ACCENT = "#64beff"
GLYPHS = dict(
    GLYPHS,
    **{
        "@": ["111", "101", "111", "100", "111"],
        ".": ["000", "000", "000", "000", "010"],
    },
)


def profile():
    tree = ast.parse((APP / "__init__.py").read_text())
    return {
        node.targets[0].id: ast.literal_eval(node.value)
        for node in tree.body
        if isinstance(node, ast.Assign)
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id in ("NAME", "PHONE", "AVATAR_URL", "LINKS")
    }


def vcard(data):
    return "\r\n".join(
        [
            "BEGIN:VCARD",
            "VERSION:3.0",
            "N:Khan;Anas;;;",
            "FN:" + data["NAME"],
            "TEL;TYPE=CELL:" + data["PHONE"],
            "URL:https://anaskhan.me",
            "URL:https://github.com/anxkhn",
            "URL:https://linkedin.com/in/anxkhn",
            "URL:https://x.com/anxkhn",
            "END:VCARD",
            "",
        ]
    )


def text(image, value, x, y, color=INK, scale=1, bounds=None):
    value = value.upper()
    width, height = (len(value) * 4 - 1) * scale, 5 * scale
    assert 0 <= x and 0 <= y and x + width <= image.width and y + height <= image.height
    if bounds is not None:
        bounds.append([x, y, width, height])
    draw = ImageDraw.Draw(image)
    for index, character in enumerate(value):
        for row, pixels in enumerate(GLYPHS[character]):
            for column, pixel in enumerate(pixels):
                if pixel == "1":
                    left = x + (index * 4 + column) * scale
                    top = y + row * scale
                    draw.rectangle((left, top, left + scale - 1, top + scale - 1), fill=color)


def save(image, path, source, **metadata):
    info = PngImagePlugin.PngInfo()
    info.add_text("Source", source)
    for key, value in metadata.items():
        info.add_text(key, str(value))
    image.save(path, format="PNG", optimize=True, pnginfo=info)


def build(fetch_avatar=False):
    data = profile()
    assets = APP / "assets"
    previews = ROOT / "docs/images"
    assets.mkdir(parents=True, exist_ok=True)
    previews.mkdir(parents=True, exist_ok=True)
    avatar_path = assets / "avatar.png"
    if fetch_avatar:
        request = Request(data["AVATAR_URL"], headers={"User-Agent": "social-card-asset-builder"})
        with urlopen(request, timeout=30) as response:
            avatar_bytes = response.read(2_000_001)
        if hashlib.sha256(avatar_bytes).hexdigest() != AVATAR_SHA256:
            raise ValueError(
                "Avatar differs from the verified source; review it before updating the pin"
            )
        avatar_path.write_bytes(avatar_bytes)
    avatar_bytes = avatar_path.read_bytes()
    if hashlib.sha256(avatar_bytes).hexdigest() != AVATAR_SHA256:
        raise ValueError("Bundled avatar SHA-256 does not match the verified source")
    with Image.open(avatar_path) as source:
        portrait = ImageOps.fit(source.convert("RGB"), (48, 48), method=Image.Resampling.LANCZOS)
    provenance = "Original layout and icon: tools/build_social_card.py; bitmap alphabet: tools/build_minesweeper_assets.py"
    manifest = {
        "name": data["NAME"],
        "avatar_url": data["AVATAR_URL"],
        "avatar_sha256": AVATAR_SHA256,
        "size": list(SIZE),
        "screens": [],
    }
    contact = vcard(data)
    (assets / "anas-khan.vcf").write_bytes(contact.encode("utf-8"))
    (ROOT / "docs/anas-khan.vcf").write_bytes(contact.encode("utf-8"))
    payloads = [contact if url == "vcard" else url for _, _, url in data["LINKS"]]
    probe = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L)
    probe.add_data(contact, optimize=0)
    probe.make(fit=True)
    version = probe.version
    module_pixels = 2 if (17 + version * 4 + 8) * 2 <= 86 else 1
    manifest["phone"] = data["PHONE"]
    montage = Image.new("RGB", (len(data["LINKS"]) * 160, 240), BG)
    labels = ("GITHUB", "IN", "X", "WEB", "VCARD")
    for selected, (label, display, url) in enumerate(data["LINKS"]):
        bounds = []
        card = Image.new("RGB", SIZE, BG)
        draw = ImageDraw.Draw(card)
        card.paste(portrait, (8, 8))
        text(card, data["NAME"], 66, 10, scale=2, bounds=bounds)
        text(card, "@anxkhn", 66, 28, color=ACCENT, bounds=bounds)
        text(card, "LETS CONNECT", 66, 45, color=MUTED, bounds=bounds)
        draw.line((8, 61, 151, 61), fill="#263a4c")
        for index, (_, value, _) in enumerate(data["LINKS"]):
            y = 64 + index * 8
            if index == selected:
                draw.rectangle((6, y - 2, 153, y + 6), fill="#263a4c")
                draw.polygon(((148, y), (151, y + 2), (148, y + 4)), fill=ACCENT)
            text(
                card,
                labels[index],
                10,
                y,
                color=ACCENT if index == selected else MUTED,
                bounds=bounds,
            )
            text(card, value, 42, y, bounds=bounds)
        text(card, "A/C:LINK  B:QR", 8, 110, color=MUTED, bounds=bounds)
        filename = "card-%d.png" % selected
        save(
            card,
            assets / filename,
            provenance,
            Avatar=data["AVATAR_URL"],
            URL=url,
            Name=data["NAME"],
        )
        save(
            card,
            previews / ("social-card-%s.png" % label.lower()),
            provenance,
            Avatar=data["AVATAR_URL"],
            URL=url,
        )
        montage.paste(card, (selected * 160, 0))
        manifest["screens"].append({"file": filename, "url": url, "text_bounds": bounds})

        qr = qrcode.QRCode(
            version=version,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=module_pixels,
            border=4,
        )
        qr.add_data(payloads[selected], optimize=0)
        qr.make(fit=False)
        qr_image = qr.make_image(fill_color="black", back_color="white").convert("RGB")
        assert qr_image.width <= 90 and qr_image.height <= 90
        x, y = (160 - qr_image.width) // 2, 12
        qr_screen = Image.new("RGB", SIZE, BG)
        bounds = []
        text(qr_screen, label, (160 - (len(label) * 4 - 1)) // 2, 3, color=ACCENT, bounds=bounds)
        qr_screen.paste(qr_image, (x, y))
        text(qr_screen, display, (160 - (len(display) * 4 - 1)) // 2, 98, bounds=bounds)
        text(qr_screen, "A/C:LINK  B:BACK", 8, 110, color=MUTED, bounds=bounds)
        filename = "qr-%d.png" % selected
        save(
            qr_screen,
            assets / filename,
            provenance,
            URL=url,
            QRModulePixels=module_pixels,
            QRBorderModules=4,
        )
        save(qr_screen, previews / ("social-card-%s-qr.png" % label.lower()), provenance, URL=url)
        montage.paste(qr_screen, (selected * 160, 120))
        manifest["screens"].append(
            {
                "file": filename,
                "url": url,
                "text_bounds": bounds,
                "qr_box": [x, y, qr_image.width, qr_image.height],
                "qr_version": qr.version,
                "module_pixels": module_pixels,
                "payload": payloads[selected],
                "border_modules": 4,
            }
        )
    icon = Image.new("RGB", (24, 24), BG)
    draw = ImageDraw.Draw(icon)
    draw.rounded_rectangle((1, 3, 22, 20), radius=2, fill="#263a4c", outline=ACCENT)
    draw.ellipse((5, 6, 9, 10), fill=INK)
    draw.rectangle((4, 12, 10, 16), fill=INK)
    draw.line((13, 8, 19, 8), fill=ACCENT)
    draw.line((13, 11, 18, 11), fill=INK)
    draw.line((13, 14, 19, 14), fill=INK)
    save(icon, APP / "icon.png", provenance)
    save(montage, previews / "social-card-overview.png", provenance)
    (assets / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(
        "Built ten screens and vCard; uniform QR version", version, "module pixels", module_pixels
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fetch-avatar", action="store_true", help="Fetch the SHA-256-pinned public avatar"
    )
    build(parser.parse_args().fetch_avatar)

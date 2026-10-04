"""Check offline assets, QR modules, deterministic rebuilds and badge navigation."""

import hashlib
import importlib.util
import json
import sys
import tempfile
import types
from pathlib import Path

import qrcode
from PIL import Image, ImageChops

import build_social_card as builder

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "badge25/apps/social-card"
EXPECTED = (
    ("GitHub", "anxkhn", "https://github.com/anxkhn"),
    ("LinkedIn", "linkedin.com/in/anxkhn", "https://linkedin.com/in/anxkhn"),
    ("X", "@anxkhn", "https://x.com/anxkhn"),
    ("Website", "anaskhan.me", "https://anaskhan.me"),
    ("Contact", "+916306252095", "vcard"),
)


def asset_checks():
    data = builder.profile()
    assert data["NAME"] == "Anas Khan"
    assert data["LINKS"] == EXPECTED
    assert data["AVATAR_URL"] == "https://avatars.githubusercontent.com/u/83116240?v=4"
    manifest = json.loads((APP / "assets/manifest.json").read_text())
    assert manifest["name"] == data["NAME"]
    assert manifest["avatar_url"] == data["AVATAR_URL"]
    assert manifest["size"] == [160, 120]
    contact = (APP / "assets/anas-khan.vcf").read_bytes()
    assert contact == (ROOT / "docs/anas-khan.vcf").read_bytes()
    assert b"TEL;TYPE=CELL:+916306252095\r\n" in contact
    assert contact.startswith(b"BEGIN:VCARD\r\nVERSION:3.0\r\n")
    assert contact.endswith(b"END:VCARD\r\n")
    qr_entries = [entry for entry in manifest["screens"] if "qr_box" in entry]
    assert (
        len(
            {
                (entry["qr_version"], entry["module_pixels"], tuple(entry["qr_box"]))
                for entry in qr_entries
            }
        )
        == 1
    )
    assert (
        hashlib.sha256((APP / "assets/avatar.png").read_bytes()).hexdigest()
        == manifest["avatar_sha256"]
        == builder.AVATAR_SHA256
    )
    assert {entry["file"] for entry in manifest["screens"]} == {
        "%s-%d.png" % (kind, index) for kind in ("card", "qr") for index in range(5)
    }
    for entry in manifest["screens"]:
        index = int(entry["file"].split("-")[1].split(".")[0])
        assert entry["url"] == EXPECTED[index][2]
        with Image.open(APP / "assets" / entry["file"]) as image:
            assert image.size == (160, 120) and image.mode == "RGB"
            assert image.info["Source"] and image.info["URL"] == entry["url"]
            for x, y, width, height in entry["text_bounds"]:
                assert 0 <= x < x + width <= 160 and 0 <= y < y + height <= 120
            if "qr_box" in entry:
                qr = qrcode.QRCode(
                    version=entry["qr_version"],
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    border=4,
                    box_size=entry["module_pixels"],
                )
                qr.add_data(entry["payload"], optimize=0)
                qr.make(fit=False)
                matrix = qr.get_matrix()
                x, y, width, height = entry["qr_box"]
                pixels = entry["module_pixels"]
                assert pixels in (1, 2) and entry["border_modules"] == 4
                assert entry["qr_version"] == qr.version
                assert width == height == len(matrix) * pixels
                assert 0 <= x < x + width <= 160 and 12 <= y < y + height <= 98
                for ty, row in enumerate(matrix):
                    for tx, dark in enumerate(row):
                        expected = (0, 0, 0) if dark else (255, 255, 255)
                        for dy in range(pixels):
                            for dx in range(pixels):
                                assert (
                                    image.getpixel((x + tx * pixels + dx, y + ty * pixels + dy))
                                    == expected
                                )
                for row in range(len(matrix)):
                    for column in range(len(matrix)):
                        if min(row, column, len(matrix) - row - 1, len(matrix) - column - 1) < 4:
                            assert not matrix[row][column]
        label = EXPECTED[index][0].lower()
        suffix = "-qr" if entry["file"].startswith("qr") else ""
        with Image.open(
            ROOT / "docs/images" / ("social-card-%s%s.png" % (label, suffix))
        ) as preview:
            with Image.open(APP / "assets" / entry["file"]) as frame:
                assert preview.size == (160, 120)
                assert ImageChops.difference(preview, frame).getbbox() is None
    with Image.open(APP / "icon.png") as icon:
        assert icon.size == (24, 24) and icon.info["Source"]
    with Image.open(ROOT / "docs/images/social-card-overview.png") as overview:
        assert overview.size == (800, 240)
        for index in range(5):
            for row, kind in enumerate(("card", "qr")):
                with Image.open(APP / "assets" / ("%s-%d.png" % (kind, index))) as frame:
                    crop = overview.crop(
                        (index * 160, row * 120, (index + 1) * 160, (row + 1) * 120)
                    )
                    assert ImageChops.difference(crop, frame).getbbox() is None


def runtime_checks():
    loads = []

    class BadgeImage:
        @staticmethod
        def load(path):
            assert path.startswith("/system/apps/social-card/assets/")
            loads.append(path)
            with Image.open(APP / "assets" / Path(path).name) as image:
                return image.copy()

    class Screen:
        def load_into(self, path):
            self.image = BadgeImage.load(path)
            assert self.image.size == (160, 120)

    screen = Screen()
    io = types.SimpleNamespace(
        BUTTON_A="A", BUTTON_B="B", BUTTON_C="C", BUTTON_UP="U", BUTTON_DOWN="D", pressed=set()
    )
    old_badgeware = sys.modules.get("badgeware")
    sys.modules["badgeware"] = types.SimpleNamespace(Image=BadgeImage, screen=screen, io=io)
    try:
        spec = importlib.util.spec_from_file_location("social_card_app", APP / "__init__.py")
        app = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(app)
        assert not loads and app.frame_key is None
        assert app.LINKS == EXPECTED
        app.init()

        def press(*buttons):
            io.pressed = set(buttons)
            app.update()
            kind = "qr" if app.show_qr else "card"
            with Image.open(APP / "assets" / ("%s-%d.png" % (kind, app.selected))) as expected:
                assert ImageChops.difference(screen.image, expected).getbbox() is None

        press()
        assert app.selected == 0 and not app.show_qr and len(loads) == 1
        press()
        assert len(loads) == 1
        press("A")
        assert app.selected == 4
        press("C")
        assert app.selected == 0
        press("U")
        assert app.selected == 4
        press("D")
        assert app.selected == 0
        press("A", "C")
        assert app.selected == 0
        press("D", "C")
        assert app.selected == 1
        press("B")
        assert app.show_qr
        for index in (2, 3, 4, 0, 1):
            press("C")
            assert app.selected == index and app.show_qr
            count = len(loads)
            press()
            assert len(loads) == count
            press("B")
            assert not app.show_qr
            press("B")
        app.on_exit()
        assert app.frame_key is None
        app.init()
        press()
        assert app.selected == 0 and not app.show_qr
    finally:
        if old_badgeware is None:
            del sys.modules["badgeware"]
        else:
            sys.modules["badgeware"] = old_badgeware


def rebuild_checks():
    def equivalent(original, rebuilt):
        if original.suffix == ".png":
            with Image.open(original) as left, Image.open(rebuilt) as right:
                assert left.size == right.size and left.mode == right.mode, original.name
                assert left.tobytes() == right.tobytes(), original.name
                assert left.info == right.info, original.name
        else:
            assert original.read_bytes() == rebuilt.read_bytes(), original.name

    original_root, original_app = builder.ROOT, builder.APP
    with tempfile.TemporaryDirectory(prefix="social-card-") as directory:
        builder.ROOT = Path(directory)
        builder.APP = builder.ROOT / "badge25/apps/social-card"
        (builder.APP / "assets").mkdir(parents=True)
        for path in (Path("__init__.py"), Path("assets/avatar.png")):
            (builder.APP / path).write_bytes((APP / path).read_bytes())
        try:
            builder.build()
            assert (ROOT / "docs/anas-khan.vcf").read_bytes() == (
                builder.ROOT / "docs/anas-khan.vcf"
            ).read_bytes()
            for original in (APP / "assets").iterdir():
                equivalent(original, builder.APP / "assets" / original.name)
            equivalent(APP / "icon.png", builder.APP / "icon.png")
            for original in (ROOT / "docs/images").glob("social-card*.png"):
                equivalent(original, builder.ROOT / "docs/images" / original.name)
        finally:
            builder.ROOT, builder.APP = original_root, original_app


if __name__ == "__main__":
    asset_checks()
    runtime_checks()
    rebuild_checks()
    print(
        "Social card passed: URLs, provenance, dimensions, bounds, exact QR modules, all navigation states and offline byte-identical rebuild"
    )

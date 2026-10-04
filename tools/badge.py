"""Host-side tools for the GitHub Universe 2025 badge."""

import argparse
import ast
import getpass
import hashlib
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / ".badge-local"
FIRMWARE = "github-badger-2350-with-filesystem.uf2"
RELEASE = "mona-os-v4.03"
DIGEST = "ce0fa2e402cf1fd1e8142778f5f2902a390fcfc1fec2cf1ee3a2a722f74472d8"
URL = f"https://github.com/badger/home/releases/download/{RELEASE}/{FIRMWARE}"
MPREMOTE = ["uvx", "--from", "mpremote==1.29.0", "mpremote"]


def run(args, capture=False):
    return subprocess.run(args, check=True, text=True, capture_output=capture)


def port(explicit=None):
    if explicit:
        return explicit
    devices = run(MPREMOTE + ["devs"], capture=True).stdout.splitlines()
    matches = [line.split()[0] for line in devices if "2e8a:0005" in line]
    if len(matches) != 1:
        raise ValueError("Connect exactly one 2025 badge in normal mode, or pass --port.")
    return matches[0]


def remote(script, explicit=None, reset=True):
    device = port(explicit)
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "badge_command.py"
        path.write_text(script)
        path.chmod(0o600)
        args = MPREMOTE + ["connect", device, "run", str(path)]
        if reset:
            args += ["+", "reset"]
        try:
            run(args)
        except subprocess.CalledProcessError:
            raise ValueError(
                "Serial command failed. Tap RESET, stay at startup or the launcher, rediscover the port, then retry."
            ) from None


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def download():
    LOCAL.mkdir(exist_ok=True)
    path = LOCAL / FIRMWARE
    if not path.exists() or sha256(path) != DIGEST:
        temporary = path.with_suffix(".download")
        with urllib.request.urlopen(URL, timeout=60) as response, temporary.open("wb") as output:
            shutil.copyfileobj(response, output)
        if sha256(temporary) != DIGEST:
            temporary.unlink()
            raise ValueError("Firmware SHA-256 mismatch. Nothing was flashed.")
        temporary.replace(path)
    print(f"Verified {RELEASE}: {path}")
    return path


def board_info():
    info = run(["picotool", "info", "-a"], capture=True).stdout
    print(info)
    if "github_badger_2350" not in info:
        raise ValueError(
            "Expected an installed github_badger_2350 image. Confirm hardware manually before recovery."
        )


def configuration(path):
    values = {}
    for statement in ast.parse(path.read_text()).body:
        if not isinstance(statement, ast.Assign) or len(statement.targets) != 1:
            raise ValueError("Configuration must contain only literal assignments.")
        target = statement.targets[0]
        if not isinstance(target, ast.Name):
            raise ValueError("Configuration keys must be names.")
        value = ast.literal_eval(statement.value)
        if target.id not in {
            "WIFI_SSID",
            "WIFI_PASSWORD",
            "GITHUB_USERNAME",
            "GITHUB_TOKEN",
        } or not isinstance(value, str):
            raise ValueError("Only string Wi-Fi/GitHub configuration keys are accepted.")
        values[target.id] = value
    if not all(values.get(key) for key in ("WIFI_SSID", "WIFI_PASSWORD", "GITHUB_USERNAME")):
        raise ValueError("Fill in SSID, password, and GitHub username first.")
    values.setdefault("GITHUB_TOKEN", "")
    return "".join(f"{key} = {value!r}\n" for key, value in values.items())


def deploy_files(source):
    for path in sorted(source.rglob("*")):
        relative = path.relative_to(source)
        if relative.parts[0] in {"images", "badgerware", "simulator"}:
            continue
        if any(part.startswith(".") or part == "__pycache__" for part in relative.parts):
            continue
        if path.is_symlink():
            raise ValueError(f"Refusing symlink: {path}")
        if not path.is_file() or path.suffix not in {
            ".py",
            ".mpy",
            ".png",
            ".ppf",
            ".json",
        }:
            continue
        if path.name in {"secrets.py", "fetch_sprites.py"} or path.name.startswith("screenshot_"):
            continue
        yield path, relative


def deploy(volume, source=ROOT / "badge25", app=None):
    volume = volume.resolve()
    if (
        not volume.is_dir()
        or not (volume / "apps/menu/__init__.py").is_file()
        or not (volume / "assets").is_dir()
    ):
        raise ValueError(
            "Expected a mounted BADGER volume with apps/menu and assets. Double-tap RESET."
        )
    files = list(deploy_files(source))
    if app is not None:
        files = [
            (path, relative) for path, relative in files if relative.parts[:2] == ("apps", app)
        ]
        if not any(relative.name == "__init__.py" for _, relative in files):
            raise ValueError("App not found in the source bundle.")
    required = sum(
        path.stat().st_size for path, relative in files if not (volume / relative).exists()
    )
    required += len(files) * 4096
    if required + 512 * 1024 > shutil.disk_usage(volume).free:
        raise ValueError(
            "Not enough free space. Remove unwanted apps deliberately before deploying."
        )
    copied = 0
    for path, relative in files:
        destination = volume / relative
        if destination.is_file() and sha256(path) == sha256(destination):
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, destination)
        if sha256(path) != sha256(destination):
            raise ValueError(f"Copy verification failed: {relative}")
        copied += 1
    print(
        f"Verified {len(files)} files; copied {copied}. Eject the volume cleanly, then tap RESET."
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", help="Explicit serial port; otherwise discover USB 2e8a:0005")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor", help="List serial devices, available tools, and macOS disks")
    commands.add_parser("download", help="Download and checksum the pinned official factory UF2")
    backup = commands.add_parser("backup", help="Save and verify all flash in BOOTSEL mode")
    backup.add_argument("output", type=Path)
    flash = commands.add_parser(
        "flash", help="Flash the verified official factory image in BOOTSEL mode"
    )
    flash.add_argument(
        "--yes",
        action="store_true",
        help="Confirm replacement of firmware and app filesystem",
    )
    copy = commands.add_parser(
        "deploy", help="Copy all compatible apps and assets to the BADGER volume"
    )
    copy.add_argument("--volume", type=Path, default=Path("/Volumes/BADGER"))
    copy.add_argument("--app", help="Deploy only this app directory, preserving other apps")
    config = commands.add_parser(
        "configure",
        help="Prompt for private credentials and write the device's root config",
    )
    config.add_argument(
        "--file",
        type=Path,
        help="Use an ignored local configuration file instead of prompting",
    )
    config.add_argument(
        "--volume",
        type=Path,
        help="Also write secrets.py to the mounted BADGER volume, instead of serial",
    )
    quest = commands.add_parser("quest", help="Set the infrared quest completion state")
    quest.add_argument("action", choices=("unlock", "reset", "status"))
    commands.add_parser("inspect", help="Show firmware, installed apps, and storage")
    commands.add_parser("smoke", help="Test added apps and launcher rendering on hardware")
    commands.add_parser(
        "sprites", help="Fetch normal and shiny Pokedex PNGs locally before deployment"
    )
    args = parser.parse_args()
    if args.command == "doctor":
        for tool in ("uvx", "picotool", "git", "gh"):
            print(tool, shutil.which(tool) or "missing")
        run(MPREMOTE + ["devs"])
        if sys.platform == "darwin":
            run(["diskutil", "list", "external"])
    elif args.command == "download":
        download()
    elif args.command == "backup":
        if args.output.exists():
            raise ValueError("Backup already exists; choose a new filename.")
        board_info()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        run(["picotool", "save", "-a", "-v", str(args.output)])
        args.output.chmod(0o600)
        print("SHA-256", sha256(args.output))
    elif args.command == "flash":
        if not args.yes:
            raise ValueError("Back up first, then pass --yes to confirm filesystem replacement.")
        path = download()
        board_info()
        run(["picotool", "load", "-v", str(path)])
        run(["picotool", "reboot"])
    elif args.command == "deploy":
        deploy(args.volume, app=args.app)
    elif args.command == "configure":
        LOCAL.mkdir(exist_ok=True)
        file = args.file or LOCAL / "secrets.py"
        if not args.file:
            values = {
                "WIFI_SSID": input("2.4 GHz Wi-Fi SSID: "),
                "WIFI_PASSWORD": getpass.getpass("Wi-Fi password: "),
                "GITHUB_USERNAME": input("GitHub username: "),
                "GITHUB_TOKEN": getpass.getpass("GitHub token, optional: "),
            }
            file.touch(mode=0o600, exist_ok=True)
            file.chmod(0o600)
            file.write_text("".join(f"{key} = {value!r}\n" for key, value in values.items()))
        text = configuration(file)
        if args.volume:
            if not (args.volume / "apps/menu/__init__.py").is_file():
                raise ValueError("Expected the mounted BADGER volume.")
            (args.volume / "secrets.py").write_text(text)
            print("Disk config written. Update root config over serial too if it already exists.")
        else:
            remote(
                f"with open('/secrets.py', 'w') as output:\n    output.write({text!r})\nprint('Private configuration updated')\n",
                args.port,
            )
    elif args.command == "quest":
        if args.action == "status":
            script = "from badgeware import State\ns={'completed': []}\nState.load('quest', s)\nprint(s)\n"
        else:
            completed = list(range(1, 10)) if args.action == "unlock" else []
            script = f"from badgeware import State\ns={{'completed': {completed!r}}}\nassert State.save('quest', s) is not False\nprint(s)\n"
        remote(script, args.port)
    elif args.command == "inspect":
        remote(
            "import os,sys\nprint(sys.version)\nprint(os.uname())\nprint('Apps:', os.listdir('/system/apps'))\nprint('Storage:', os.statvfs('/system'))\n",
            args.port,
        )
    elif args.command == "smoke":
        remote((ROOT / "tools/smoke_device.py").read_text(), args.port)
    elif args.command == "sprites":
        run(
            [
                "uv",
                "run",
                "--no-project",
                str(ROOT / "badge25/apps/pokedex/fetch_sprites.py"),
                str(ROOT / "badge25/apps/pokedex"),
            ]
        )


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        sys.exit(str(error))

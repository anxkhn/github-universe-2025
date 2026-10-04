"""Supervise a demo bridge and the real badge check in one process."""

import asyncio
import argparse
import badge

from copilot_minis import Bridge, MAX_FRAME, ROOT, pairing


async def main(args):
    live_path = ROOT / ".badge-local/copilot-minis.json"
    test_path = ROOT / ".badge-local/copilot-minis-device-test.json"
    config = pairing(test_path, args.badge_host, args.bridge_port)
    bridge = Bridge(config["token"], demo=True)
    await bridge.seed_demo()
    server = await asyncio.start_server(bridge.handle, "0.0.0.0", args.bridge_port, limit=MAX_FRAME)
    try:
        async with server:
            process = await asyncio.create_subprocess_exec(
                "uv",
                "tool",
                "run",
                "mpremote",
                "connect",
                badge.port(args.port),
                "fs",
                "cp",
                str(test_path),
                ":/copilot-minis.json",
                "+",
                "mount",
                str(ROOT / "badge25/apps/copilot-minis"),
                "run",
                str(ROOT / "tools/check_copilot_minis_device.py"),
                "+",
                "fs",
                "cp",
                str(live_path),
                ":/copilot-minis.json",
                "+",
                "reset",
            )
            try:
                result = await asyncio.wait_for(process.wait(), 90)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                raise
            assert result == 0, "Badge check failed"
            assert bridge.threads["demo-build"]["messages"][-1] == "DEMO reply: Allow once"
            assert "DEMO reply: Network reconnect" in bridge.threads["demo-review"]["messages"]
            print("PASS laptop received both physical-runtime choice replies and Continue")
    finally:
        await bridge.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--badge-host", required=True, help="Laptop LAN IPv4 address")
    parser.add_argument("--port", help="Discover the badge serial port if omitted")
    parser.add_argument("--bridge-port", type=int, default=8766)
    asyncio.run(main(parser.parse_args()))

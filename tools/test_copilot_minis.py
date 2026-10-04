"""Exercise LAN authentication, isolated replies, expiry and stop behavior."""

import asyncio
import json
import tempfile
from pathlib import Path

from copilot_minis import Bridge, MAX_FRAME, pairing


async def run():
    bridge = Bridge("t" * 48, demo=True)
    await bridge.seed_demo()
    await asyncio.sleep(0)
    server = await asyncio.start_server(bridge.handle, "127.0.0.1", 0, limit=MAX_FRAME)
    port = server.sockets[0].getsockname()[1]
    async with server:
        reader, writer = await asyncio.open_connection("127.0.0.1", port)
        writer.write(b'{"token":"wrong"}\n')
        assert json.loads(await reader.readline())["type"] == "error"
        assert await reader.readline() == b""
        writer.close()
        await writer.wait_closed()

        reader, writer = await asyncio.open_connection("127.0.0.1", port)
        writer.write((json.dumps({"token": bridge.token}) + "\n").encode())
        state = json.loads(await reader.readline())
        assert len(state["threads"]) == 3
        request = state["threads"][0]["pending"][0]
        assert request["choices"][0] == "Reject"
        writer.write(
            (
                json.dumps(
                    {
                        "session": "demo-review",
                        "action": "answer",
                        "request": request["id"],
                        "choice": 1,
                    }
                )
                + "\n"
            ).encode()
        )
        assert json.loads(await reader.readline())["type"] == "error"
        await reader.readline()
        writer.write(
            (
                json.dumps(
                    {
                        "session": "demo-build",
                        "action": "answer",
                        "request": request["id"],
                        "choice": 1,
                    }
                )
                + "\n"
            ).encode()
        )
        assert json.loads(await reader.readline())["type"] == "ack"
        await asyncio.sleep(0.01)
        assert bridge.threads["demo-build"]["messages"][-1] == "DEMO reply: Allow once"
        try:
            bridge.answer("demo-build", request["id"], 1)
        except ValueError:
            pass
        else:
            raise AssertionError("A stale approval was accepted")
        await bridge.command({"session": "demo-review", "action": "stop"})
        await asyncio.sleep(0.01)
        assert bridge.threads["demo-review"]["status"] == "stopped"
        assert not bridge.threads["demo-review"]["pending"]
        for thread in bridge.threads.values():
            thread["messages"] = ["\U0001f600" * 700] * 6
        assert len(json.dumps(bridge.snapshot()).encode()) < MAX_FRAME
        for index in range(9):
            sid = "large-" + str(index)
            bridge.add(sid, "Large state")
            bridge.spawn(
                bridge.ask(sid, "question", "Long question " * 300, ["Long choice " * 30] * 32)
            )
        await asyncio.sleep(0)
        assert len(json.dumps(bridge.snapshot()).encode()) < MAX_FRAME
        writer.close()
        await writer.wait_closed()
    await bridge.close()
    print(
        "PASS authenticated TCP, cross-session rejection, one-shot replies, stop and bounded snapshots"
    )


with tempfile.TemporaryDirectory() as directory:
    path = Path(directory) / "pair.json"
    config = pairing(path, "192.168.1.3", 8765)
    assert path.stat().st_mode & 0o777 == 0o600
    assert pairing(path, "192.168.1.4", 8765)["token"] == config["token"]
asyncio.run(run())

"""Verify real CLI events and a permission reply through the badge TCP protocol."""

import asyncio
import json
import shutil
import tempfile

from copilot import CopilotClient, RuntimeConnection
from copilot_minis import Bridge, MAX_FRAME


async def main():
    with tempfile.TemporaryDirectory() as directory:
        async with CopilotClient(
            connection=RuntimeConnection.for_stdio(path=shutil.which("copilot")),
            working_directory=directory,
        ) as client:
            bridge = Bridge("x" * 48, client=client)
            sid = await bridge.attach("Minis live verification")
            server = await asyncio.start_server(bridge.handle, "127.0.0.1", 0, limit=MAX_FRAME)
            try:
                async with server:
                    reader, writer = await asyncio.open_connection(
                        "127.0.0.1", server.sockets[0].getsockname()[1]
                    )
                    writer.write((json.dumps({"token": bridge.token}) + "\n").encode())
                    await bridge.send(
                        sid,
                        "For a hardware integration test, run the shell command pwd exactly once. Do not read, modify, or create any files. Then reply MINIS_LIVE_OK. Do not use any other tools.",
                    )
                    answered = False
                    async with asyncio.timeout(100):
                        while True:
                            payload = json.loads(await reader.readline())
                            if payload["type"] != "state":
                                continue
                            thread = payload["threads"][0]
                            if thread["pending"] and not answered:
                                request = thread["pending"][0]
                                assert request["kind"] == "permission"
                                writer.write(
                                    (
                                        json.dumps(
                                            {
                                                "session": sid,
                                                "action": "answer",
                                                "request": request["id"],
                                                "choice": 1,
                                            }
                                        )
                                        + "\n"
                                    ).encode()
                                )
                                await writer.drain()
                                answered = True
                                print(
                                    "PASS real Copilot permission routed through authenticated TCP"
                                )
                            if thread["status"] == "error":
                                raise AssertionError(thread["messages"])
                            if thread["status"] == "idle" and any(
                                "MINIS_LIVE_OK" in m for m in thread["messages"]
                            ):
                                assert answered, "Model did not request a tool permission"
                                print(
                                    "PASS live shell approval, assistant message and idle event",
                                    sid,
                                )
                                break
                    writer.close()
                    await writer.wait_closed()
            finally:
                await bridge.close()


asyncio.run(main())

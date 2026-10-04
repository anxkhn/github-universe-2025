"""LAN bridge between a MonaOS badge and SDK-managed Copilot CLI sessions."""

import argparse
import asyncio
import contextlib
import hmac
import json
import secrets
import shutil
import time
import uuid
from pathlib import Path

MAX_FRAME = 32768
ROOT = Path(__file__).resolve().parents[1]


class Bridge:
    def __init__(self, token, client=None, demo=False):
        self.token = token
        self.client = client
        self.demo = demo
        self.threads = {}
        self.sessions = {}
        self.pending = {}
        self.tasks = set()
        self.closed = False

    def spawn(self, coroutine):
        task = asyncio.create_task(coroutine)
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)
        return task

    def add(self, sid, title):
        if len(self.threads) >= 12:
            raise ValueError("This prototype supports 12 managed threads.")
        self.threads[sid] = {
            "id": sid,
            "title": title[:100],
            "status": "idle",
            "revision": 0,
            "messages": [],
            "pending": [],
        }
        return self.threads[sid]

    def change(self, sid, status=None, message=None):
        thread = self.threads[sid]
        if status:
            thread["status"] = status
        if message:
            thread["messages"] = (thread["messages"] + [str(message)[-700:]])[-6:]
        thread["revision"] += 1

    def snapshot(self):
        threads = []
        for item in self.threads.values():
            thread = dict(item)
            thread["messages"] = list(item["messages"])
            thread["pending"] = [dict(self.pending[r]["public"]) for r in item["pending"][:1]]
            threads.append(thread)
        result = {"type": "state", "demo": self.demo, "threads": threads}
        # Bound the complete wire frame, including escaped Unicode and request details.
        while len(json.dumps(result).encode()) > MAX_FRAME - 1:
            longest = max(threads, key=lambda t: len(json.dumps(t)))
            if longest["messages"]:
                longest["messages"].pop(0)
            elif longest["pending"] and len(longest["pending"][0]["detail"]) > 40:
                longest["pending"][0]["detail"] = "Read full request on laptop"
            elif longest["pending"]:
                longest["pending"][0]["choices"] = [
                    label[: max(1, len(label) // 2)] for label in longest["pending"][0]["choices"]
                ]
                if all(len(label) <= 1 for label in longest["pending"][0]["choices"]):
                    raise ValueError("Request exceeds the badge frame limit. Answer on laptop.")
            else:
                raise ValueError("State exceeds the badge frame limit.")
        return result

    async def ask(self, sid, kind, detail, choices):
        if self.closed:
            return None
        rid = uuid.uuid4().hex
        future = asyncio.get_running_loop().create_future()
        public = {
            "id": rid,
            "kind": kind,
            "detail": str(detail)[:3500],
            "choices": [str(c)[:220] for c in choices[:32]],
        }
        self.pending[rid] = {
            "session": sid,
            "future": future,
            "public": public,
            "answers": choices[:32],
        }
        self.threads[sid]["pending"].append(rid)
        self.change(sid, "permission" if kind == "permission" else "question")
        print(f"\n[{sid[:8]}] {kind} {rid}\n{detail}", flush=True)
        try:
            return await asyncio.wait_for(asyncio.shield(future), 300)
        except asyncio.TimeoutError:
            self.change(sid, message="Request expired. No approval sent.")
            return None
        finally:
            self.pending.pop(rid, None)
            self.threads[sid]["pending"].remove(rid)
            remaining = self.threads[sid]["pending"]
            if remaining:
                kind = self.pending[remaining[0]]["public"]["kind"]
                self.change(sid, "permission" if kind == "permission" else "question")
            elif self.threads[sid]["status"] not in ("stopped", "error"):
                self.change(sid, "running")

    def answer(self, sid, rid, index=None, text=None):
        request = self.pending.get(rid)
        if not request or request["session"] != sid or request["future"].done():
            raise ValueError("Request expired or already answered.")
        if text is not None:
            if request["public"]["kind"] != "question" or not isinstance(text, str) or not text:
                raise ValueError("This request does not accept a text answer.")
            result = text[:2000]
        else:
            if type(index) is not int or not 0 <= index < len(request["answers"]):
                raise ValueError("Invalid choice.")
            result = request["answers"][index]
        request["future"].set_result(result)

    async def permission(self, sid, request, invocation):
        from copilot.rpc import PermissionDecisionApproveOnce, PermissionDecisionReject

        managed = invocation.get("managed_settings_enabled", False) or getattr(
            request, "managed_approval_required", False
        )
        detail = json.dumps(request.to_dict(), indent=2)
        choices = ["Reject"] if managed else ["Reject", "Allow once"]
        if managed:
            detail += "\nManaged policy requires approval on the laptop."
        answer = await self.ask(sid, "permission", detail, choices)
        if answer == "Allow once" and not managed:
            return PermissionDecisionApproveOnce()
        return PermissionDecisionReject(feedback="Rejected or expired on Copilot Minis")

    async def question(self, sid, request, invocation):
        choices = request.get("choices") or []
        answer = await self.ask(
            sid, "question", request.get("question", "Choose an option"), choices
        )
        return {
            "answer": answer or "No answer available; stop and wait for the user.",
            "wasFreeform": answer not in choices,
        }

    def event(self, sid, event):
        kind = event.type.value if hasattr(event.type, "value") else str(event.type)
        data = event.data
        if kind in ("assistant.message", "user.message"):
            self.change(sid, message=getattr(data, "content", ""))
            if kind == "assistant.message":
                print(f"\n[{sid[:8]}] {getattr(data, 'content', '')}", flush=True)
        elif kind in ("assistant.turn_start", "tool.execution_start"):
            if not self.threads[sid]["pending"]:
                self.change(sid, "running")
        elif kind == "session.idle":
            if not self.threads[sid]["pending"]:
                self.change(sid, "idle")
        elif kind == "session.error":
            self.change(sid, "error", getattr(data, "message", "Copilot runtime error"))
        elif kind in ("session.shutdown", "abort", "agent.interrupted"):
            self.change(sid, "stopped")

    async def attach(self, title, resume=None):
        sid = resume or str(uuid.uuid4())
        if sid in self.threads:
            return sid
        self.add(sid, title)
        try:
            options = {
                "on_permission_request": lambda req, inv: self.permission(sid, req, inv),
                "on_user_input_request": lambda req, inv: self.question(sid, req, inv),
                "on_event": lambda event: self.event(sid, event),
                "streaming": True,
            }
            if resume:
                session = await self.client.resume_session(
                    sid, **options, continue_pending_work=False
                )
            else:
                session = await self.client.create_session(session_id=sid, **options)
            self.sessions[sid] = session
            if resume:
                for event in (await session.get_events())[-100:]:
                    kind = event.type.value if hasattr(event.type, "value") else str(event.type)
                    if kind in ("assistant.message", "user.message"):
                        self.change(sid, message=getattr(event.data, "content", ""))
                self.change(sid, "idle")
            return sid
        except Exception:
            self.threads.pop(sid, None)
            raise

    async def send(self, sid, text):
        if sid not in self.threads or sid not in self.sessions:
            raise ValueError("Session is not managed by this bridge.")
        if self.threads[sid]["pending"]:
            raise ValueError("Answer the pending request first.")
        self.change(sid, "running")
        try:
            await self.sessions[sid].send(text)
        except Exception as error:
            self.change(sid, "error", str(error))
            raise

    async def command(self, payload):
        sid = payload.get("session")
        action = payload.get("action")
        if sid not in self.threads:
            raise ValueError("Unknown session.")
        if action == "answer":
            self.answer(sid, payload.get("request"), payload.get("choice"))
        elif action == "stop":
            self.change(sid, "stopped")
            for rid in list(self.threads[sid]["pending"]):
                future = self.pending[rid]["future"]
                if not future.done():
                    future.set_result(None)
            if not self.demo:
                await self.sessions[sid].abort()
        elif action in ("continue", "status"):
            if self.threads[sid]["status"] == "running" and action == "continue":
                raise ValueError("Agent is already running.")
            if self.demo:
                if self.threads[sid]["pending"]:
                    raise ValueError("Answer the pending request first.")
                self.spawn(self.demo_continue(sid))
            else:
                text = (
                    "Continue the task."
                    if action == "continue"
                    else "Give me a brief status update."
                )
                await self.send(sid, text)
        else:
            raise ValueError("Unknown action.")

    async def demo_continue(self, sid):
        self.change(sid, "running", "Demo agent resumed.")
        await asyncio.sleep(2)
        if self.threads[sid]["status"] == "running":
            self.change(sid, "idle", "Demo task finished. Ready for your next instruction.")

    async def seed_demo(self):
        self.add("demo-build", "Build conference app")
        self.add("demo-review", "Review pull request")
        self.add("demo-tests", "Run test suite")
        self.change("demo-tests", "idle", "DEMO: 24 tests passed. Agent has finished.")
        self.change(
            "demo-review", "running", "DEMO: Reviewing changes, then asking which area to inspect."
        )

        async def request(sid, kind, detail, choices):
            answer = await self.ask(sid, kind, detail, choices)
            if self.threads[sid]["status"] != "stopped":
                self.change(sid, "idle", "DEMO reply: " + str(answer))

        self.spawn(
            request(
                "demo-build",
                "permission",
                "DEMO: Run shell command:\nuv run pytest\n\nAllow this command once?",
                ["Reject", "Allow once"],
            )
        )
        self.spawn(
            request(
                "demo-review",
                "question",
                "DEMO: Which area should I review next?",
                ["Button controls", "Network reconnect", "Text wrapping"],
            )
        )

    async def handle(self, reader, writer):
        try:
            line = await asyncio.wait_for(reader.readline(), 10)
            hello = json.loads(line)
            token = hello.get("token") if isinstance(hello, dict) else None
            if not isinstance(token, str) or not hmac.compare_digest(token, self.token):
                writer.write(b'{"type":"error","message":"Pairing failed"}\n')
                await writer.drain()
                return
            while not self.closed:
                writer.write((json.dumps(self.snapshot()) + "\n").encode())
                await asyncio.wait_for(writer.drain(), 5)
                try:
                    line = await asyncio.wait_for(reader.readline(), 1)
                except asyncio.TimeoutError:
                    continue
                if not line:
                    break
                try:
                    command = json.loads(line)
                    if not isinstance(command, dict):
                        raise ValueError("Expected a command object.")
                    await self.command(command)
                    reply = {"type": "ack", "message": "Sent"}
                except Exception as error:
                    reply = {"type": "error", "message": str(error)[:160]}
                writer.write((json.dumps(reply) + "\n").encode())
                await asyncio.wait_for(writer.drain(), 5)
        except (ConnectionError, OSError, ValueError, asyncio.TimeoutError, json.JSONDecodeError):
            pass
        finally:
            writer.close()
            with contextlib.suppress(ConnectionError, OSError):
                await writer.wait_closed()

    async def close(self):
        self.closed = True
        for item in self.pending.values():
            if not item["future"].done():
                item["future"].set_result(None)
        for task in list(self.tasks):
            task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)


def pairing(path, host, port):
    if path.exists():
        config = json.loads(path.read_text())
        token = config["token"]
        if not isinstance(token, str) or len(token) < 32:
            raise ValueError("Invalid pairing token.")
    else:
        token = secrets.token_hex(24)
    config = {"host": host, "port": port, "token": token}
    path.parent.mkdir(parents=True, exist_ok=True)
    # Open with owner-only permissions before writing the token.
    import os

    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    os.fchmod(fd, 0o600)
    with os.fdopen(fd, "w") as output:
        json.dump(config, output)
    return config


async def console(bridge):
    current = next(iter(bridge.threads), None)
    print(
        "Commands: /new NAME | PROMPT, /saved, /resume ID, /send ID | PROMPT, /list, /answer ID | TEXT, /quit",
        flush=True,
    )
    while True:
        try:
            text = await asyncio.to_thread(input, "minis> ")
        except EOFError:
            return
        try:
            if text == "/quit":
                return
            if text == "/list":
                for item in bridge.threads.values():
                    print(item["id"], item["status"], item["title"])
            elif text == "/saved" and bridge.client:
                for item in (await bridge.client.list_sessions())[:30]:
                    print(item.session_id, item.summary or "Untitled")
            elif text.startswith("/resume ") and bridge.client:
                current = await bridge.attach("Resumed chat", resume=text[8:].strip())
            elif text.startswith("/new ") and bridge.client:
                title, prompt = text[5:].split("|", 1)
                current = await bridge.attach(title.strip())
                await bridge.send(current, prompt.strip())
            elif text.startswith("/send ") and bridge.client:
                sid, prompt = text[6:].split("|", 1)
                current = sid.strip()
                await bridge.send(current, prompt.strip())
            elif text.startswith("/answer "):
                rid, answer = text[8:].split("|", 1)
                request = bridge.pending.get(rid.strip())
                if not request:
                    raise ValueError("No such pending request.")
                bridge.answer(request["session"], rid.strip(), text=answer.strip())
            elif text.strip() and current and bridge.client:
                await bridge.send(current, text)
        except Exception as error:
            print("Error:", str(error), flush=True)


async def main(args):
    config = pairing(args.pairing, args.badge_host, args.port)
    client = None
    if not args.demo:
        from copilot import CopilotClient, RuntimeConnection

        binary = shutil.which("copilot")
        if not binary:
            raise ValueError("Install and log in to Copilot CLI first.")
        client = CopilotClient(
            connection=RuntimeConnection.for_stdio(path=binary),
            working_directory=str(args.cwd.resolve()),
        )
        await client.start()
    bridge = Bridge(config["token"], client, args.demo)
    try:
        if args.demo:
            await bridge.seed_demo()
        server = await asyncio.start_server(bridge.handle, args.host, args.port, limit=MAX_FRAME)
        print(
            f"Copilot Minis {'DEMO' if args.demo else 'LIVE'} on {args.host}:{args.port}",
            flush=True,
        )
        print(f"Private badge config: {args.pairing}", flush=True)
        async with server:
            await console(bridge)
    finally:
        await bridge.close()
        if client:
            await client.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--badge-host", default="127.0.0.1", help="Laptop's LAN IPv4 address")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--pairing", type=Path, default=ROOT / ".badge-local/copilot-minis.json")
    parser.add_argument("--cwd", type=Path, default=Path.cwd())
    try:
        asyncio.run(main(parser.parse_args()))
    except KeyboardInterrupt:
        pass

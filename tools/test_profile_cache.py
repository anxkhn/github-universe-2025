"""Check atomic profile downloads without importing the badge graphics runtime."""

import ast
import json
import os
import time
import tempfile
from pathlib import Path
from types import SimpleNamespace

source = Path(__file__).resolve().parents[1] / "badge25/apps/badge/__init__.py"
tree = ast.parse(source.read_text())
function = next(
    node
    for node in tree.body
    if isinstance(node, ast.FunctionDef) and node.name == "async_fetch_to_disk"
)
module = ast.Module(body=[function], type_ignores=[])


class Response:
    def __init__(self, content):
        self.content = content
        self.closed = False

    def readinto(self, buffer):
        chunk, self.content = self.content[: len(buffer)], self.content[len(buffer) :]
        buffer[: len(chunk)] = chunk
        return len(chunk)

    def close(self):
        self.closed = True


responses = []


def urlopen(url, headers):
    return responses.pop(0)


namespace = {
    "os": os,
    "json": json,
    "io": SimpleNamespace(ticks=0),
    "file_exists": os.path.isfile,
    "urlopen": urlopen,
    "GITHUB_TOKEN": None,
    "message": lambda text: None,
    "time": SimpleNamespace(
        ticks_ms=lambda: int(time.monotonic() * 1000), ticks_diff=lambda a, b: a - b
    ),
    "FetchTimeout": type("FetchTimeout", (OSError,), {}),
}
exec(compile(module, str(source), "exec"), namespace)
fetch = namespace["async_fetch_to_disk"]
with tempfile.TemporaryDirectory() as directory:
    cache = Path(directory) / "contrib_data.json"
    cache.write_text("")
    good = Response(b'{"total_contributions":3038,"weeks":[]}')
    responses.append(good)
    task = fetch("https://github.com/test.contribs", str(cache))
    next(task)
    assert cache.read_text() == "", "Partial download replaced cache"
    list(task)
    assert json.loads(cache.read_text())["total_contributions"] == 3038
    assert good.closed
    original = cache.read_bytes()
    for content in (b"", b"not json"):
        response = Response(content)
        responses.append(response)
        try:
            list(fetch("https://github.com/test.contribs", str(cache), True))
        except RuntimeError:
            pass
        else:
            raise AssertionError("Invalid download accepted")
        assert cache.read_bytes() == original
        assert response.closed
    contrib_function = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "get_contrib_data"
    )
    namespace.update(
        {
            "CONTRIB_URL": "https://github.com/{user}.contribs",
            "User": SimpleNamespace(levels=range(5)),
            "gc": SimpleNamespace(collect=lambda: None),
        }
    )
    exec(
        compile(ast.Module(body=[contrib_function], type_ignores=[]), str(source), "exec"),
        namespace,
    )
    real_open = open
    namespace["open"] = lambda path, *args: real_open(
        cache if path == "/contrib_data.json" else path, *args
    )

    def failed_fetch(*args, **kwargs):
        raise RuntimeError("offline")
        yield

    namespace["async_fetch_to_disk"] = failed_fetch
    user = SimpleNamespace(handle="test")
    list(namespace["get_contrib_data"](user, True))
    assert user.contribs == 3038, "Failed refresh discarded valid cached total"
print("Empty cache recovery, atomic writes, invalid JSON preservation, and response cleanup passed")

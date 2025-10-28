import json
from pathlib import Path
import shutil
import subprocess

from pdoc import search

here = Path(__file__).parent


def test_node_executable(monkeypatch):
    monkeypatch.setattr(
        shutil, "which", lambda x: "/usr/bin/nodejs" if x == "nodejs" else None
    )
    search.node_executable.cache_clear()
    assert search.node_executable() == "nodejs"

    monkeypatch.setattr(
        shutil, "which", lambda x: "/usr/bin/node" if x == "node" else None
    )
    search.node_executable.cache_clear()
    assert search.node_executable() == "node"

    monkeypatch.setattr(shutil, "which", lambda _: None)
    search.node_executable.cache_clear()
    assert search.node_executable() is None


def test_precompile_index(monkeypatch, capsys):
    docs = [
        {
            "fullname": "test.Test",
            "modulename": "test",
            "qualname": "Test",
            "type": "class",
            "doc": "a" * 3 * 1024 * 1024,  # we only warn if index size is meaningful.
        }
    ]
    raw = json.dumps(docs)
    compile_js = here / ".." / "pdoc" / "templates" / "build-search-index.js"

    monkeypatch.setattr(subprocess, "check_output", lambda *_, **__: '{"foo": 42}')
    monkeypatch.setattr(search, "node_executable", lambda: "nodejs")
    assert (
        search.precompile_index(docs, compile_js)
        == '{"foo": 42, "_isPrebuiltIndex": true}'
    )

    monkeypatch.setattr(search, "node_executable", lambda: None)
    assert search.precompile_index(docs, compile_js) == raw

    def _raise(*_, **__):
        raise subprocess.CalledProcessError(-1, ["cmd"], b"nodejs error")

    monkeypatch.setattr(search, "node_executable", lambda: "node")
    monkeypatch.setattr(subprocess, "check_output", _raise)
    assert search.precompile_index(docs, compile_js) == raw
    out = capsys.readouterr().out
    assert "pdoc failed to precompile the search index" in out
    assert "Node.js Output" in out

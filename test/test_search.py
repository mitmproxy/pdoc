import json
import shutil
import subprocess
from pathlib import Path

from pdoc import search

here = Path(__file__).parent


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
    compile_js = here / ".." / "pdoc" / "templates" / "build-search-index.js"

    monkeypatch.setattr(subprocess, "check_output", lambda *_, **__: '{"foo": 42}')
    assert (
        search.precompile_index(docs, compile_js)
        == '{"foo": 42, "_isPrebuiltIndex": true}'
    )

    monkeypatch.setattr(shutil, "which", lambda _: "C:\\nodejs.exe")
    assert (
        search.precompile_index(docs, compile_js)
        == '{"foo": 42, "_isPrebuiltIndex": true}'
    )
    monkeypatch.setattr(shutil, "which", lambda _: None)
    assert (
        search.precompile_index(docs, compile_js)
        == '{"foo": 42, "_isPrebuiltIndex": true}'
    )

    def _raise(*_, **__):
        raise subprocess.CalledProcessError(-1, ["cmd"], b"nodejs error")

    monkeypatch.setattr(subprocess, "check_output", _raise)
    assert search.precompile_index(docs, compile_js) == json.dumps(docs)
    assert "pdoc failed to precompile the search index" in capsys.readouterr().out

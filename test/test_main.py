from pathlib import Path
from unittest.mock import patch, call

import pytest

from pdoc import pdoc
from pdoc.__main__ import cli

here = Path(__file__).parent


def test_cli(tmp_path):
    cli(args=[
        str(here / "snapshots" / "demo.py"),
        "-o", str(tmp_path)
    ])
    assert (tmp_path / "demo.html").read_text().startswith("<!doctype html>")
    assert (tmp_path / "index.html").read_text().startswith("<!doctype html>")


def test_cli_web(monkeypatch):
    with patch("pdoc.web.open_browser") as open_browser:
        with patch("pdoc.web.DocServer.serve_forever", side_effect=KeyboardInterrupt) as serve_forever:
            with pytest.raises(KeyboardInterrupt):
                cli(args=[str(here / "snapshots" / "demo.py")])
            assert open_browser.call_args == call("http://localhost:8080/demo")
            assert serve_forever.call_args == call()


def test_api(tmp_path):
    assert pdoc(
        here / "snapshots" / "demo.py"
    ).startswith("<!doctype html>")
    with pytest.raises(ValueError, match="Invalid rendering format"):
        assert pdoc(
            here / "snapshots" / "demo.py",
            format="invalid"
        )
    with pytest.raises(ValueError, match="No valid module specifications"):
        assert pdoc(
            here / "notfound.py",
        )
    with pytest.warns(RuntimeWarning, match="Error importing syntax_err.syntax_err"):
        pdoc(
            here / "syntax_err",
            output_directory=tmp_path
        )

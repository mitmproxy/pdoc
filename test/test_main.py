import warnings

import pytest
from pathlib import Path
from unittest.mock import call, patch

from pdoc import pdoc
from pdoc.__main__ import cli, _nicer_showwarning

here = Path(__file__).parent


def test_cli(capsys, tmp_path):
    cli([str(here / "testdata" / "demo_long.py"), "-o", str(tmp_path)])
    assert (tmp_path / "demo_long.html").read_text().startswith("<!doctype html>")
    assert (tmp_path / "index.html").read_text().startswith("<!doctype html>")

    with pytest.raises(SystemExit, match="1"):
        cli([])
    assert capsys.readouterr().out.startswith("usage:")


def test_cli_version(capsys):
    cli(["--version"])
    assert "pdoc:" in capsys.readouterr().out


def test_cli_web(capsys):
    with patch("pdoc.web.open_browser") as open_browser:
        with patch(
            "pdoc.web.DocServer.serve_forever", side_effect=KeyboardInterrupt
        ) as serve_forever:
            cli([str(here / "testdata" / "demopackage" / "_child_d.py")])
    assert open_browser.call_args[0][0].startswith("http://localhost")
    assert serve_forever.call_args == call()
    assert capsys.readouterr().out.startswith("pdoc server ready")


def test_cli_web_port_used(capsys):
    with patch("pdoc.web.DocServer", side_effect=OSError):
        with pytest.raises(SystemExit, match="1"):
            cli(["dataclasses"])
    assert "Cannot start web server" in capsys.readouterr().out


def test_api(tmp_path):
    assert pdoc(here / "testdata" / "demo_long.py").startswith("<!doctype html>")
    with pytest.raises(ValueError, match="Invalid rendering format"):
        assert pdoc(here / "testdata" / "demo_long.py", format="invalid")

    with pytest.raises(ValueError, match="No modules found matching spec"):
        with pytest.warns(UserWarning, match="Cannot find spec"):
            pdoc(here / "notfound.py")

    with pytest.raises(RuntimeError, match="Unable to import any modules."):
        with pytest.warns(UserWarning, match="Error importing"):
            pdoc(here / "testdata" / "import_err_simple.py")

    # temporarily insert syntax error - we don't leave it permanently to not confuse mypy, flake8 and black.
    f = here / "syntax_err" / "syntax_err.py"
    f.write_bytes(b"class")
    try:
        with pytest.warns(UserWarning, match="Error importing"):
            pdoc(here / "syntax_err", output_directory=tmp_path)
    finally:
        f.write_bytes(b"# syntax error will be inserted by test here\n")


def test_patch_showwarnings(capsys, monkeypatch):
    monkeypatch.setattr(warnings, "showwarning", _nicer_showwarning)

    warnings.warn("test")
    assert capsys.readouterr().err.startswith("Warn: test (")

    warnings.warn("test", RuntimeWarning)
    assert capsys.readouterr().err == "Warn: test\n"

    warnings.warn("test", SyntaxWarning)
    assert capsys.readouterr().err.startswith("SyntaxWarning: test (")

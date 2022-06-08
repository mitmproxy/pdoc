import importlib
import pytest
import sys
from pathlib import Path

from pdoc.extract import invalidate_caches, module_mtime, parse_spec, walk_specs

here = Path(__file__).parent


def test_walk_specs():
    assert walk_specs(["dataclasses"]) == ["dataclasses"]
    assert walk_specs(
        [
            here / "testdata" / "demopackage",
            "!demopackage",
            "demopackage.child_b",
        ]
    ) == ["demopackage.child_b"]

    assert walk_specs(["demopackage", "!demopackage.child_excluded"]) == [
        "demopackage",
        "demopackage._child_e",
        "demopackage.child_b",
        "demopackage.child_c",
    ]
    with pytest.raises(ValueError, match="No modules found matching spec: unknown"):
        with pytest.warns(UserWarning, match="Cannot find spec for unknown"):
            assert walk_specs(["unknown"])
    with pytest.warns(UserWarning, match="Cannot find spec for unknown"):
        assert walk_specs(["dataclasses", "unknown"]) == ["dataclasses"]

    with pytest.warns(UserWarning, match="Error loading test.import_err.err"):
        assert walk_specs([here / "import_err"]) == [
            "test.import_err",
            "test.import_err.err",
        ]
    with pytest.raises(ValueError, match="No modules found matching spec: "):
        assert walk_specs([])

    with pytest.warns(
        UserWarning,
        match="The module specification 'dataclasses' adds a module named dataclasses, "
        "but a module with this name has already been added.",
    ):
        assert walk_specs(["dataclasses", "dataclasses"]) == ["dataclasses"]


def test_parse_spec(monkeypatch):
    p = sys.path

    assert parse_spec("dataclasses") == "dataclasses"
    assert sys.path == p

    monkeypatch.chdir(here)
    assert parse_spec("import_err")
    assert sys.path == p

    assert parse_spec(here / "testdata" / "demo.py") == "demo"
    assert str(here / "testdata") in sys.path
    sys.path = p

    assert (
        parse_spec(here / "testdata" / "demopackage" / "_child.py")
        == "demopackage._child"
    )
    assert str(here / "testdata") in sys.path
    sys.path = p


def test_parse_spec_mod_and_dir(tmp_path, monkeypatch):
    """Test that we display a warning when both a module and a local directory exist with the provided name."""
    (tmp_path / "dataclasses").mkdir()
    (tmp_path / "dataclasses" / "__init__.py").touch()
    (tmp_path / "pdoc").mkdir()
    (tmp_path / "pdoc" / "__init__.py").touch()
    monkeypatch.chdir(tmp_path)

    with pytest.warns(
        RuntimeWarning,
        match="'dataclasses' may refer to either the installed Python module or the local file/directory",
    ):
        assert parse_spec("dataclasses") == "dataclasses"

    with pytest.warns(
        RuntimeWarning,
        match="pdoc cannot load 'pdoc' because a module with the same name is already imported",
    ):
        assert parse_spec("./pdoc") == "pdoc"

    monkeypatch.chdir(here / "testdata")
    assert parse_spec("demo.py") == "demo"


def test_module_mtime():
    assert module_mtime("dataclasses")
    assert module_mtime("unknown") is None
    assert module_mtime("dataclasses.abc") is None


def test_invalidate_caches(monkeypatch):
    def raise_(*_):
        raise RuntimeError

    monkeypatch.setattr(importlib, "reload", raise_)
    with pytest.warns(UserWarning, match="Error reloading"):
        invalidate_caches("pdoc.render_helpers")

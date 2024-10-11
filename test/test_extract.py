import importlib
from pathlib import Path
import sys

import pytest

from pdoc.extract import invalidate_caches
from pdoc.extract import mock_some_common_side_effects
from pdoc.extract import module_mtime
from pdoc.extract import parse_spec
from pdoc.extract import walk_specs

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
        "demopackage.child_f",
        "demopackage.subpackage",
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

    assert walk_specs([here / "mod_with_main"]) == [
        "test.mod_with_main",
        "test.mod_with_main.foo",
    ]
    assert walk_specs([here / "mod_with_main", here / "mod_with_main/__main__.py"]) == [
        "test.mod_with_main",
        "test.mod_with_main.foo",
        "test.mod_with_main.__main__",
    ]

    assert walk_specs(["pdoc_pyo3_sample_library"]) == [
        "pdoc_pyo3_sample_library",
        "pdoc_pyo3_sample_library.submodule",
        "pdoc_pyo3_sample_library.submodule.subsubmodule",
        "pdoc_pyo3_sample_library.explicit_submodule",
        "pdoc_pyo3_sample_library.correct_name_submodule",
    ]

    assert walk_specs([here / "boguous_dir"]) == ["test.boguous_dir"]


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

    assert (
        parse_spec(here / "testdata" / "demopackage" / "__init__.py") == "demopackage"
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


def test_mock_sideeffects():
    """https://github.com/mitmproxy/pdoc/issues/745"""
    with mock_some_common_side_effects():
        import sys

        sys.stdout.reconfigure(encoding="utf-8")

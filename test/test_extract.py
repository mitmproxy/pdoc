import pytest

import pdoc.extract

import tutils


@pytest.mark.parametrize(
    "input,expected",
    [
        ("foo", ("", "foo")),
        ("foo.bar", ("", "foo.bar")),
        ("foo/bar.py", ("foo", "bar")),
        ("./bar.py", (".", "bar")),
        ("./bar.foo", None),
        ("", None),
    ]
)
def test_split_module_spec(input, expected):
    if expected is None:
        with pytest.raises(pdoc.extract.ExtractError):
            pdoc.extract.split_module_spec(input)
    else:
        assert pdoc.extract.split_module_spec(input) == expected


@pytest.mark.parametrize(
    "path,mod,expected,match",
    [
        ("./modules", "one", False, None),
        ("./modules", "dirmod", True, None),
        ("", "email", True, None),
        ("", "csv", False, None),
        ("", "html.parser", False, None),
        ("", "packages.simple", False, None),

        ("./modules", "nonexistent", False, "not found"),
        ("./modules/nonexistent", "foo", False, "not found"),
        ("", "nonexistent.module", False, "not found"),
        ("./modules/malformed", "syntax", False, "Error importing"),
        ("", "packages.malformed_syntax", False, "Error importing"),
    ]
)
def test_load_module(path, mod, expected, match):
    with tutils.tdir():
        if match:
            with pytest.raises(pdoc.extract.ExtractError, match=match):
                pdoc.extract.load_module(path, mod)
        else:
            _, ispkg = pdoc.extract.load_module(path, mod)
            assert ispkg == expected


def test_extract_module():
    with tutils.tdir():
        with pytest.raises(pdoc.extract.ExtractError, match="not found"):
            pdoc.extract.extract_module("./modules/nonexistent.py")
        with pytest.raises(pdoc.extract.ExtractError, match="not found"):
            pdoc.extract.extract_module("./modules/nonexistent/foo")
        with pytest.raises(pdoc.extract.ExtractError, match="Invalid module name"):
            pdoc.extract.extract_module("./modules/one.two")
        with pytest.raises(pdoc.extract.ExtractError, match="Module not found"):
            pdoc.extract.extract_module("nonexistent.module")
        with pytest.raises(pdoc.extract.ExtractError, match="Error importing"):
            pdoc.extract.extract_module("./modules/malformed/syntax.py")
        with pytest.raises(pdoc.extract.ExtractError, match="Error importing"):
            pdoc.extract.extract_module("packages/malformed_syntax")

        assert pdoc.extract.extract_module("./modules/one.py")
        assert pdoc.extract.extract_module("./modules/one")
        assert pdoc.extract.extract_module("./modules/dirmod")
        assert pdoc.extract.extract_module("./modules/submods")
        assert pdoc.extract.extract_module("csv")
        assert pdoc.extract.extract_module("html.parser")
        assert pdoc.extract.extract_module("packages.simple")


@pytest.mark.parametrize(
    "path,modname,expected",
    [
        ("./modules", "one", []),
        ("./modules", "dirmod", []),
        ("./modules", "submods", ["submods.three", "submods.two"]),
        ("./modules", "malformed", ["malformed.syntax"]),
    ]
)
def test_submodules(path, modname, expected):
    with tutils.tdir():
        ret = pdoc.extract.submodules(path, modname)
        assert ret == expected
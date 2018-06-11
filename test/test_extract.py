import pytest

import pdoc.extract

import tutils


def test_extract_module():
    with tutils.tdir():
        with pytest.raises(pdoc.extract.ExtractError, match="File not found"):
            pdoc.extract.extract_module("./modules/nonexistent.py")
        with pytest.raises(pdoc.extract.ExtractError, match="Module not found"):
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
        assert pdoc.extract.extract_module("csv")
        assert pdoc.extract.extract_module("html.parser")
        assert pdoc.extract.extract_module("packages.simple")



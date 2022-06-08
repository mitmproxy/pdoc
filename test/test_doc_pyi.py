import pytest
import types
from pathlib import Path

from pdoc import doc, doc_pyi

here = Path(__file__).parent.absolute()


def test_type_stub_mismatch():
    def foo_func():
        """I'm a func"""

    class foo_cls:
        """I'm a cls"""

    target = types.ModuleType("test")
    target.__dict__["foo"] = foo_func
    target.__dict__["__all__"] = ["foo"]

    stub = types.ModuleType("test")
    stub.__dict__["foo"] = foo_cls
    stub.__dict__["__all__"] = ["foo"]

    with pytest.warns(UserWarning, match="Error processing type stub"):
        doc_pyi._patch_doc(doc.Module(target), doc.Module(stub))


def test_invalid_stub_file(monkeypatch):
    monkeypatch.setattr(
        doc_pyi, "find_stub_file", lambda m: here / "import_err/err/__init__.py"
    )
    with pytest.warns(
        UserWarning, match=r"Error parsing type stubs[\s\S]+RuntimeError"
    ):
        _ = doc.Module(doc).members

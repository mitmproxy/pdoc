from pdoc import _pydantic
import pdoc.doc


def test_no_pydantic(monkeypatch):
    monkeypatch.setattr(_pydantic, "pydantic", None)

    assert not _pydantic.is_pydantic_model(pdoc.doc.Module)
    assert _pydantic.get_field_docstring(pdoc.doc.Module, "kind") is None
    assert _pydantic.default_value(pdoc.doc.Module, "kind", "module") == "module"

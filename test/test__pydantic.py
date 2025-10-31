import pydantic
from functools import cached_property

from pdoc import _pydantic
import pdoc.doc


def test_no_pydantic(monkeypatch):
    monkeypatch.setattr(_pydantic, "pydantic", None)

    assert not _pydantic.is_pydantic_model(pdoc.doc.Module)
    assert _pydantic.get_field_docstring(pdoc.doc.Module, "kind") is None
    assert _pydantic.default_value(pdoc.doc.Module, "kind", "module") == "module"


class ExampleModel(pydantic.BaseModel):
    id: int
    name: str = pydantic.Field(description="desc", default="Jane Doe")

    @pydantic.computed_field(description="computed")
    @property
    def computed(self) -> str:
        return "computed_value"

    @pydantic.computed_field(description="cached")
    @cached_property
    def cached(self) -> str:
        return "computed_value"


def test_with_pydantic(monkeypatch):
    assert _pydantic.is_pydantic_model(ExampleModel)
    assert _pydantic.get_field_docstring(ExampleModel, "name") == "desc"
    assert _pydantic.get_field_docstring(ExampleModel, "computed") == "computed"
    assert _pydantic.get_field_docstring(ExampleModel, "cached") == "cached"
    assert _pydantic.default_value(ExampleModel, "name", None) == "Jane Doe"

    assert not _pydantic.is_pydantic_model(pdoc.doc.Module)
    assert _pydantic.get_field_docstring(pdoc.doc.Module, "kind") is None
    assert _pydantic.default_value(pdoc.doc.Module, "kind", "module") == "module"

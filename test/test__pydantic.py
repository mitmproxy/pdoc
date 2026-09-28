from functools import cached_property

import pydantic
import pydantic.v1 as pydantic_v1

from pdoc import _pydantic
from pdoc import extract
import pdoc.doc


def test_no_pydantic(monkeypatch):
    monkeypatch.setattr(_pydantic, "pydantic", None)

    assert not _pydantic.is_pydantic_model(pdoc.doc.Module)
    assert _pydantic.get_field_docstring(pdoc.doc.Module, "kind") is None
    assert _pydantic.default_value(pdoc.doc.Module, "kind", "module") == "module"


class ExampleModel(pydantic.BaseModel):
    id: int
    name: str = pydantic.Field(description="desc", default="Jane Doe")

    @pydantic.computed_field(description="computed")  # type: ignore[misc]
    @property
    def computed(self) -> str:
        return "computed_value"

    @pydantic.computed_field(description="cached")  # type: ignore[misc]
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


def test_with_pydantic_v1(monkeypatch, tmp_path):
    monkeypatch.setattr(_pydantic, "pydantic", pydantic_v1)

    class LegacyModel(pydantic_v1.BaseModel):
        name: str = pydantic_v1.Field(
            default="Jane Doe", description="legacy description"
        )

    assert _pydantic.is_pydantic_model(LegacyModel)
    assert _pydantic.get_field_docstring(LegacyModel, "name") == "legacy description"
    assert _pydantic.get_field_docstring(LegacyModel, "unknown") is None
    assert _pydantic.default_value(LegacyModel, "name", None) == "Jane Doe"
    assert _pydantic.default_value(LegacyModel, "unknown", "fallback") == "fallback"

    module_file = tmp_path / "legacy_model.py"
    module_file.write_text(
        "from pydantic.v1 import BaseModel, Field\n"
        "class LegacyModel(BaseModel):\n"
        "    name: str = Field(default='Jane Doe', description='legacy description')\n"
    )
    module = extract.load_module(extract.parse_spec(module_file))
    assert "LegacyModel" in pdoc.doc.Module(module).members
    assert "legacy description" in pdoc.pdoc(str(module_file))

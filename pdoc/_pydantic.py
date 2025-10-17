"""Work with Pydantic models."""

from importlib import import_module
from types import ModuleType
from typing import TYPE_CHECKING
from typing import Any
from typing import Final
from typing import Optional
from typing import TypeVar
from typing import cast

from pdoc.docstrings import AnyException

if TYPE_CHECKING:
    import pydantic
else:  # pragma: no cover
    pydantic: Optional[ModuleType]
    try:
        pydantic = import_module("pydantic")
    except AnyException:
        pydantic = None


_IGNORED_FIELDS: Final[list[str]] = [
    "__fields__",
] + list(pydantic.BaseModel.__dict__.keys()) if pydantic is not None else []
"""Fields to ignore when generating docs, e.g. those that emit deprecation
warnings or that are not relevant to users of BaseModel-derived classes."""

T = TypeVar("T")


def is_pydantic_model(obj: Any) -> bool:
    """Returns whether an object is a Pydantic model.

    Raises:
        ModuleNotFoundError: when function is called but Pydantic is not on the PYTHONPATH.

    """
    if pydantic is None:  # pragma: no cover
        raise ModuleNotFoundError(
            "_pydantic.is_pydantic_model() needs Pydantic installed"
        )

    return pydantic.BaseModel in obj.__bases__


def default_value(parent: Any, name: str, obj: T) -> T:
    """Determine the default value of obj.

    If pydantic is not installed or the parent type is not a Pydantic model,
    simply returns obj.

    """
    if (
        pydantic is not None
        and isinstance(parent, type)
        and issubclass(parent, pydantic.BaseModel)
    ):
        _parent = cast(pydantic.BaseModel, parent)
        pydantic_fields = _parent.__pydantic_fields__
        return pydantic_fields[name].default if name in pydantic_fields else obj

    return obj


def get_field_docstring(parent: type, field_name: str) -> Optional[str]:
    if pydantic is not None and issubclass(parent, pydantic.BaseModel):
        pydantic_fields = parent.__pydantic_fields__
        return (
            pydantic_fields[field_name].description
            if field_name in pydantic_fields
            else None
        )

    return None

"""Work with Pydantic models."""

from __future__ import annotations

from typing import Any
from typing import Optional
from typing import TypeGuard
from typing import TypeVar

_HAVE_PYDANTIC: bool = False
try:
    import pydantic

    _HAVE_PYDANTIC = True
except ImportError:  # pragma: no cover
    _HAVE_PYDANTIC = False

_IGNORED_FIELDS: frozenset[str] = frozenset(
    [
        "__fields__",
    ]
    + list(pydantic.BaseModel.__dict__.keys())
    if _HAVE_PYDANTIC
    else []
)
"""Fields to ignore when generating docs, e.g. those that emit deprecation
warnings or that are not relevant to users of BaseModel-derived classes."""

T = TypeVar("T")


def is_pydantic_model(obj: type) -> TypeGuard[pydantic.BaseModel]:
    """Returns whether an object is a Pydantic model.

    If Pydantic is not installed, returns False unconditionally.

    """
    if not _HAVE_PYDANTIC:  # pragma: no cover
        return False

    return isinstance(obj, type) and issubclass(obj, pydantic.BaseModel)


def default_value(parent: Any, name: str, obj: T) -> T:
    """Determine the default value of obj.

    If pydantic is not installed or the parent type is not a Pydantic model,
    simply returns obj.

    """
    if is_pydantic_model(parent):
        pydantic_fields = parent.__pydantic_fields__
        return pydantic_fields[name].default if name in pydantic_fields else obj

    return obj


def get_field_docstring(parent: type, field_name: str) -> Optional[str]:
    if is_pydantic_model(parent):
        pydantic_fields = parent.__pydantic_fields__
        return (
            pydantic_fields[field_name].description
            if field_name in pydantic_fields
            else None
        )

    return None

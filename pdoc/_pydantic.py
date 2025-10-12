"""Work with Pydantic models."""

from typing import Any
from typing import Final
from typing import TypeVar

from pdoc.docstrings import AnyException

try:
    import pydantic
except AnyException:
    pydantic = None

_IGNORED_FIELDS: Final[list[str]] = ["__fields__"]
"""Fields to ignore when generating docs, e.g. those that emit deprecation warnings."""

T = TypeVar("T")


def is_pydantic_model(obj) -> bool:
    return pydantic.BaseModel in obj.__bases__


def default_value(parent, name: str, obj: T) -> T:
    """Determine the default value of obj.

    If pydantic is not installed or the parent type is not a Pydantic model,
    simply returns obj.

    """
    if (
        pydantic is not None
        and isinstance(parent, type)
        and issubclass(parent, pydantic.BaseModel)
    ):
        pydantic_fields = parent.__pydantic_fields__
        return pydantic_fields[name].default if name in pydantic_fields else obj

    return obj


def get_field_docstring(parent, field_name: str) -> str | None:
    if (
        pydantic is not None
        and isinstance(parent, type)
        and issubclass(parent, pydantic.BaseModel)
    ):
        pydantic_fields = parent.__pydantic_fields__
        return (
            pydantic_fields[field_name].description
            if field_name in pydantic_fields
            else None
        )

    return None


def skip_field(
    *,
    parent_kind: str,
    parent_obj: Any,
    name: str,
    taken_from: tuple[str, str],
) -> bool:
    """For Pydantic models, filter out all methods on the BaseModel
    class, as they are almost never relevant to the consumers of the
    inheriting model itself.
    """

    return (
        pydantic is not None
        and parent_kind == "class"
        and is_pydantic_model(parent_obj)
        and (name in _IGNORED_FIELDS or taken_from[0].startswith("pydantic"))
    )

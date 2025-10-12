"""Work with Pydantic models."""

import importlib.util
from typing import Any, Final

_PYDANTIC_ENABLED: Final[bool] = importlib.util.find_spec("pydantic") is not None
"""True when pydantic is found on the PYTHONPATH."""

if _PYDANTIC_ENABLED:
    import pydantic

_IGNORED_FIELDS: Final[list[str]] = ["__fields__"]
"""Fields to ignore when generating docs, e.g. those that emit deprecation warnings."""


def is_pydantic_model(obj):
    return pydantic.BaseModel in obj.__bases__


def default_value(parent, name, obj):
    if (
        _PYDANTIC_ENABLED
        and isinstance(parent, type)
        and issubclass(parent, pydantic.BaseModel)
    ):
        pydantic_fields = parent.__pydantic_fields__
        return pydantic_fields[name].default if name in pydantic_fields else obj

    return obj


def get_field_docstring(parent, field_name) -> str:
    if (
        _PYDANTIC_ENABLED
        and isinstance(parent, type)
        and issubclass(parent, pydantic.BaseModel)
    ):
        pydantic_fields = parent.__pydantic_fields__
        return (
            pydantic_fields[field_name].description
            if field_name in pydantic_fields
            else ""
        )

    return ""


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
        _PYDANTIC_ENABLED
        and parent_kind == "class"
        and is_pydantic_model(parent_obj)
        and (name in _IGNORED_FIELDS or taken_from[0].startswith("pydantic"))
    )

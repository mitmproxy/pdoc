"""Work with Pydantic models."""

import importlib.util
from typing import Final

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

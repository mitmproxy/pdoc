"""Work with Pydantic models."""

_PYDANTIC_ENABLED: bool

try:  # pragma: no cover
    import pydantic
except ImportError:  # pragma: no cover
    _PYDANTIC_ENABLED = False
finally:  # pragma: no cover
    _PYDANTIC_ENABLED = True


_IGNORED_FIELDS = ["__fields__"]


def default_value(parent, name, obj):
    if (
        _PYDANTIC_ENABLED
        and isinstance(parent, type)
        and issubclass(parent, pydantic.BaseModel)
    ):
        pydantic_fields = parent.__pydantic_fields__
        return pydantic_fields[name].default if name in pydantic_fields else obj

    return obj

# fmt: off
import sys

if sys.version_info >= (3, 12):
    from ast import TypeAlias as ast_TypeAlias
else:  # pragma: no cover
    class ast_TypeAlias:
        pass

if sys.version_info >= (3, 12):
    from typing import TypeAliasType
else:  # pragma: no cover
    class TypeAliasType:
        """Placeholder class for TypeAliasType"""

if sys.version_info >= (3, 10):
    from typing import TypeAlias
else:  # pragma: no cover
    class TypeAlias:
        pass

if sys.version_info >= (3, 10):
    from types import UnionType  # type: ignore
else:  # pragma: no cover
    class UnionType:
        pass


if (3, 9) <= sys.version_info < (3, 9, 8) or (3, 10) <= sys.version_info < (3, 10, 1):  # pragma: no cover
    import inspect
    import types

    def formatannotation(annotation) -> str:
        """
        https://github.com/python/cpython/pull/29212
        """
        if isinstance(annotation, types.GenericAlias):
            return str(annotation)
        return inspect.formatannotation(annotation)
else:
    from inspect import formatannotation

if sys.version_info >= (3, 10):
    from typing import is_typeddict
else:  # pragma: no cover
    def is_typeddict(tp):
        try:
            return tp.__orig_bases__[-1].__name__ == "TypedDict"
        except Exception:
            return False


__all__ = [
    "ast_TypeAlias",
    "TypeAliasType",
    "TypeAlias",
    "UnionType",
    "formatannotation",
    "is_typeddict",
]

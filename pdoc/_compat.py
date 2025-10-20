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

if (3, 10) <= sys.version_info < (3, 10, 1):  # pragma: no cover
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


__all__ = [
    "ast_TypeAlias",
    "TypeAliasType",
    "formatannotation",
]

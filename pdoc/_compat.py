# fmt: off
import sys

if sys.version_info >= (3, 9):
    from functools import cache
else:  # pragma: no cover
    from functools import lru_cache

    cache = lru_cache(maxsize=None)

if sys.version_info >= (3, 9):
    from ast import unparse as ast_unparse
else:  # pragma: no cover
    from astunparse import unparse as _unparse

    def ast_unparse(t):  # type: ignore
        return _unparse(t).strip("\t\n \"'")

if sys.version_info >= (3, 9):
    from types import GenericAlias
else:  # pragma: no cover
    from typing import _GenericAlias as GenericAlias

if sys.version_info >= (3, 10):
    from types import UnionType  # type: ignore
else:  # pragma: no cover
    class UnionType:
        pass

if sys.version_info >= (3, 9):
    removesuffix = str.removesuffix
else:  # pragma: no cover
    def removesuffix(x: str, suffix: str):
        if x.endswith(suffix):
            x = x[: -len(suffix)]
        return x

if sys.version_info >= (3, 9):
    removeprefix = str.removeprefix
else:  # pragma: no cover
    def removeprefix(x: str, prefix: str):
        if x.startswith(prefix):
            x = x[len(prefix):]
        return x


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

if sys.version_info >= (3, 9):
    from argparse import BooleanOptionalAction
else:  # pragma: no cover
    # https://github.com/python/cpython/pull/27672
    from argparse import Action

    class BooleanOptionalAction(Action):  # pragma: no cover
        def __init__(self,
                     option_strings,
                     dest,
                     default=None,
                     type=None,
                     choices=None,
                     required=False,
                     help=None,
                     metavar=None):

            _option_strings = []
            for option_string in option_strings:
                _option_strings.append(option_string)

                if option_string.startswith('--'):
                    option_string = '--no-' + option_string[2:]
                    _option_strings.append(option_string)

            if help is not None and default is not None:
                help += " (default: %(default)s)"

            super().__init__(
                option_strings=_option_strings,
                dest=dest,
                nargs=0,
                default=default,
                type=type,
                choices=choices,
                required=required,
                help=help,
                metavar=metavar)

        def __call__(self, parser, namespace, values, option_string=None):
            if option_string in self.option_strings:
                setattr(namespace, self.dest, not option_string.startswith('--no-'))

        def format_usage(self):
            return ' | '.join(self.option_strings)


__all__ = [
    "cache",
    "ast_unparse",
    "GenericAlias",
    "UnionType",
    "removesuffix",
    "formatannotation",
    "BooleanOptionalAction",
]

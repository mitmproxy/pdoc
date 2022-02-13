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

if sys.version_info >= (3, 8):
    from functools import cached_property
else:  # pragma: no cover
    from threading import RLock

    # https://github.com/python/cpython/blob/863eb7170b3017399fb2b786a1e3feb6457e54c2/Lib/functools.py#L930-L980
    # ✂ start ✂
    _NOT_FOUND = object()

    class cached_property:  # type: ignore
        def __init__(self, func):
            self.func = func
            self.attrname = None
            self.__doc__ = func.__doc__
            self.lock = RLock()

        def __set_name__(self, owner, name):
            if self.attrname is None:
                self.attrname = name
            elif name != self.attrname:
                raise TypeError(
                    "Cannot assign the same cached_property to two different names "
                    f"({self.attrname!r} and {name!r})."
                )

        def __get__(self, instance, owner=None):
            if instance is None:
                return self
            if self.attrname is None:
                raise TypeError(
                    "Cannot use cached_property instance without calling __set_name__ on it.")
            try:
                cache = instance.__dict__
            except AttributeError:  # not all objects have __dict__ (e.g. class defines slots)
                msg = (
                    f"No '__dict__' attribute on {type(instance).__name__!r} "
                    f"instance to cache {self.attrname!r} property."
                )
                raise TypeError(msg) from None
            val = cache.get(self.attrname, _NOT_FOUND)
            if val is _NOT_FOUND:
                with self.lock:
                    # check if another thread filled cache while we awaited lock
                    val = cache.get(self.attrname, _NOT_FOUND)
                    if val is _NOT_FOUND:
                        val = self.func(instance)
                        try:
                            cache[self.attrname] = val
                        except TypeError:
                            msg = (
                                f"The '__dict__' attribute on {type(instance).__name__!r} instance "
                                f"does not support item assignment for caching {self.attrname!r} property."
                            )
                            raise TypeError(msg) from None
            return val

        __class_getitem__ = classmethod(GenericAlias)
    # ✂ end ✂

if sys.version_info >= (3, 8):
    from typing import Literal, get_origin
else:  # pragma: no cover
    from typing import Generic

    # There is no Literal on 3.7, so we just make one up. It should not be used anyways!

    class Literal:
        pass

    # get_origin is adapted from
    # https://github.com/python/cpython/blob/863eb7170b3017399fb2b786a1e3feb6457e54c2/Lib/typing.py#L1474-L1515
    # with Annotations removed (not present in 3.7)
    def get_origin(tp):  # type: ignore
        if isinstance(tp, GenericAlias):
            return tp.__origin__
        if tp is Generic:
            return Generic
        return None

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

if True:
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
    "cached_property",
    "get_origin",
    "Literal",
    "formatannotation",
    "BooleanOptionalAction",
]

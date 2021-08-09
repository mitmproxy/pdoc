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
    from typing import _GenericAlias as GenericAlias  # type: ignore

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

if sys.version_info >= (3, 9):
    from typing import ForwardRef
else:  # pragma: no cover
    from typing import _Final, _type_check, _GenericAlias

    # https://github.com/python/cpython/blob/4db8988420e0a122d617df741381b0c385af032c/Lib/typing.py#L298-L314
    # ✂ start ✂
    def _eval_type(t, globalns, localns, recursive_guard=frozenset()):
        """Evaluate all forward references in the given type t.
        For use of globalns and localns see the docstring for get_type_hints().
        recursive_guard is used to prevent prevent infinite recursion
        with recursive ForwardRef.
        """
        if isinstance(t, ForwardRef):
            return t._evaluate(globalns, localns, recursive_guard)
        if isinstance(t, (_GenericAlias, GenericAlias)):
            ev_args = tuple(_eval_type(a, globalns, localns, recursive_guard) for a in t.__args__)
            if ev_args == t.__args__:
                return t
            if isinstance(t, GenericAlias):
                return GenericAlias(t.__origin__, ev_args)
            else:
                return t.copy_with(ev_args)
        return t
    # ✂ end ✂

    # https://github.com/python/cpython/blob/4db8988420e0a122d617df741381b0c385af032c/Lib/typing.py#L569-L629
    # ✂ start ✂
    class ForwardRef(_Final, _root=True):
        """Internal wrapper to hold a forward reference."""

        __slots__ = ('__forward_arg__', '__forward_code__',
                     '__forward_evaluated__', '__forward_value__',
                     '__forward_is_argument__')

        def __init__(self, arg, is_argument=True):
            if not isinstance(arg, str):
                raise TypeError(f"Forward reference must be a string -- got {arg!r}")

            # Double-stringified forward references is a result of activating
            # the 'annotations' future by default. This way, we eliminate them in
            # the runtime.
            if arg.startswith(("'", '\"')) and arg.endswith(("'", '"')):
                arg = arg[1:-1]

            try:
                code = compile(arg, '<string>', 'eval')
            except SyntaxError:
                raise SyntaxError(f"Forward reference must be an expression -- got {arg!r}")
            self.__forward_arg__ = arg
            self.__forward_code__ = code
            self.__forward_evaluated__ = False
            self.__forward_value__ = None
            self.__forward_is_argument__ = is_argument

        def _evaluate(self, globalns, localns, recursive_guard):
            if self.__forward_arg__ in recursive_guard:
                return self
            if not self.__forward_evaluated__ or localns is not globalns:
                if globalns is None and localns is None:
                    globalns = localns = {}
                elif globalns is None:
                    globalns = localns
                elif localns is None:
                    localns = globalns
                type_ = _type_check(
                    eval(self.__forward_code__, globalns, localns),
                    "Forward references must evaluate to types.",
                    is_argument=self.__forward_is_argument__,
                )
                self.__forward_value__ = _eval_type(
                    type_, globalns, localns, recursive_guard | {self.__forward_arg__}
                )
                self.__forward_evaluated__ = True
            return self.__forward_value__

        def __eq__(self, other):
            if not isinstance(other, ForwardRef):
                return NotImplemented
            if self.__forward_evaluated__ and other.__forward_evaluated__:
                return (self.__forward_arg__ == other.__forward_arg__ and
                        self.__forward_value__ == other.__forward_value__)
            return self.__forward_arg__ == other.__forward_arg__

        def __hash__(self):
            return hash(self.__forward_arg__)

        def __repr__(self):
            return f'ForwardRef({self.__forward_arg__!r})'
    # ✂ end ✂


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
    from typing import get_origin, get_args, Literal
else:  # pragma: no cover
    from typing import Generic
    import collections.abc
    from unittest import mock
    # There is no Literal on 3.7, so we just make one up. It should not be used anyways!
    Literal = mock.MagicMock()

    # get_origin and get_args are adapted from
    # https://github.com/python/cpython/blob/863eb7170b3017399fb2b786a1e3feb6457e54c2/Lib/typing.py#L1474-L1515
    # with Annotations removed (not present in 3.7)
    def get_origin(tp):  # type: ignore
        if isinstance(tp, GenericAlias):
            return tp.__origin__
        if tp is Generic:
            return Generic
        return None

    def get_args(tp):  # type: ignore
        if isinstance(tp, _GenericAlias):
            res = tp.__args__
            if tp.__origin__ is collections.abc.Callable and res[0] is not Ellipsis:
                res = (list(res[:-1]), res[-1])
            return res
        if isinstance(tp, GenericAlias):
            return tp.__args__
        return ()


if sys.version_info >= (3, 8):
    from collections import _tuplegetter  # type: ignore
else:  # pragma: no cover
    from operator import itemgetter as _tuplegetter


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
    "removesuffix",
    "ForwardRef",
    "cached_property",
    "get_origin",
    "get_args",
    "Literal",
    "_tuplegetter",
]

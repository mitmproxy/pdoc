# fmt: off
import sys

try:
    from functools import cache
except ImportError:  # pragma: no cover
    from functools import lru_cache

    cache = lru_cache(maxsize=None)

try:
    from ast import unparse as ast_unparse
except ImportError:  # pragma: no cover
    from astunparse import unparse as _unparse

    def ast_unparse(t):  # type: ignore
        return _unparse(t).strip("\t\n \"'")

try:
    from types import GenericAlias
except ImportError:  # pragma: no cover
    from typing import _GenericAlias as GenericAlias  # type: ignore


def removesuffix(x: str, suffix: str):
    try:
        return x.removesuffix(suffix)
    except AttributeError:  # pragma: no cover
        if x.endswith(suffix):
            x = x[: -len(suffix)]
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

__all__ = [
    "cache",
    "ast_unparse",
    "GenericAlias",
    "removesuffix",
    "ForwardRef",
]

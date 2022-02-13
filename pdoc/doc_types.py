"""
This module handles all interpretation of type annotations in pdoc.

In particular, it provides functionality to resolve
[typing.ForwardRef](https://docs.python.org/3/library/typing.html#typing.ForwardRef) objects without raising an
exception.
"""
from __future__ import annotations

import functools
import inspect
import operator
import sys
import types
import typing
import warnings
from types import BuiltinFunctionType, ModuleType
from typing import _GenericAlias  # type: ignore
from typing import TYPE_CHECKING, Any

from . import extract
from ._compat import GenericAlias, Literal, UnionType, get_origin
from .doc_ast import type_checking_sections

if TYPE_CHECKING:

    class empty:
        pass


empty = inspect.Signature.empty  # type: ignore  # noqa
"""
A "special" object signaling the absence of a type annotation. 
This is useful to distinguish it from an actual annotation with `None`.
This value is an alias of `inspect.Signature.empty`.
"""

# adapted from
# https://github.com/python/cpython/blob/9feae41c4f04ca27fd2c865807a5caeb50bf4fc4/Lib/inspect.py#L1740-L1747
# ✂ start ✂
_WrapperDescriptor = type(type.__call__)
_MethodWrapper = type(all.__call__)  # type: ignore
_ClassMethodWrapper = type(int.__dict__["from_bytes"])

NonUserDefinedCallables = (
    _WrapperDescriptor,
    _MethodWrapper,
    _ClassMethodWrapper,
    BuiltinFunctionType,
)


# ✂ end ✂


def resolve_annotations(
    annotations: dict[str, Any],
    module: ModuleType | None,
    fullname: str,
) -> dict[str, Any]:
    """
    Given an `annotations` dictionary with type annotations (for example, `cls.__annotations__`),
    this function tries to resolve all types using `pdoc.doc_types.safe_eval_type`.

    Returns: A dictionary with the evaluated types.
    """
    ns = getattr(module, "__dict__", {})

    resolved = {}
    for name, value in annotations.items():
        resolved[name] = safe_eval_type(value, ns, module, f"{fullname}.{name}")

    return resolved


def safe_eval_type(
    t: Any,
    globalns,
    module: types.ModuleType | None,
    fullname: str,
) -> Any:
    """
    This method wraps `typing._eval_type`, but doesn't raise on errors.
    It is used to evaluate a type annotation, which might already be
    a proper type (in which case no action is required), or a forward reference string,
    which needs to be resolved.

    If _eval_type fails, we try some heuristics to import a missing module.
    If that still fails, a warning is emitted and `t` is returned as-is.
    """
    try:
        return _eval_type(t, globalns, None)
    except AttributeError as e:
        err = str(e)
        _, obj, _, attr, _ = err.split("'")
        mod = f"{obj}.{attr}"
    except NameError as e:
        err = str(e)
        _, mod, _ = err.split("'")
    except Exception as e:
        if "unsupported operand type(s) for |" in str(e) and sys.version_info < (3, 10):
            py_ver = ".".join(str(x) for x in sys.version_info[:3])
            warnings.warn(
                f"Error parsing type annotation {t} for {fullname}: {e}. "
                f"You are likely attempting to use Python 3.10 syntax (PEP 604 union types) with an older Python "
                f"release. `X | Y`-style type annotations are invalid syntax on Python {py_ver}, which is what your "
                f"pdoc instance is using. `from future import __annotations__` (PEP 563) postpones evaluation of "
                f"annotations, which is why your program won't crash right away. However, pdoc needs to evaluate your "
                f"type annotations and is unable to do so on Python {py_ver}. To fix this issue, either invoke pdoc "
                f"from Python 3.10+, or switch to `typing.Union[]` syntax."
            )
        else:
            warnings.warn(f"Error parsing type annotation {t} for {fullname}: {e}")
        return t

    # Simple _eval_type has failed. We now execute all TYPE_CHECKING sections in the module and try again.
    if module:
        try:
            code = compile(type_checking_sections(module), "<string>", "exec")
            eval(code, globalns, globalns)
        except Exception as e:
            warnings.warn(
                f"Failed to run TYPE_CHECKING code while parsing {t} type annotation for {fullname}: {e}"
            )
        try:
            return _eval_type(t, globalns, None)
        except (AttributeError, NameError):
            pass  # still not found
        except Exception as e:
            warnings.warn(
                f"Error parsing type annotation {t} for {fullname} after evaluating TYPE_CHECKING blocks: {e}"
            )
            return t

    try:
        val = extract.load_module(mod)
    except Exception:
        warnings.warn(
            f"Error parsing type annotation {t} for {fullname}. Import of {mod} failed: {err}"
        )
        return t
    return safe_eval_type(t, {mod: val, **globalns}, module, fullname)


def _eval_type(t, globalns, localns, recursive_guard=frozenset()):
    # Adapted from typing._eval_type.
    # Added type coercion originally found in get_type_hints, but removed NoneType check because that was distracting.
    # Added a special check for typing.Literal, whose literal strings would otherwise be evaluated.

    if isinstance(t, str):
        if sys.version_info < (3, 9):  # pragma: no cover
            t = t.strip("\"'")
        t = typing.ForwardRef(t)

    if get_origin(t) is Literal:
        return t

    if isinstance(t, typing.ForwardRef):
        # inlined from
        # https://github.com/python/cpython/blob/4f51fa9e2d3ea9316e674fb9a9f3e3112e83661c/Lib/typing.py#L684-L707
        if t.__forward_arg__ in recursive_guard:  # pragma: no cover
            return t
        if not t.__forward_evaluated__ or localns is not globalns:
            if globalns is None and localns is None:  # pragma: no cover
                globalns = localns = {}
            elif globalns is None:  # pragma: no cover
                globalns = localns
            elif localns is None:  # pragma: no cover
                localns = globalns
            __forward_module__ = getattr(t, "__forward_module__", None)
            if __forward_module__ is not None:
                globalns = getattr(
                    sys.modules.get(__forward_module__, None), "__dict__", globalns
                )
            (type_,) = (eval(t.__forward_code__, globalns, localns),)
            t.__forward_value__ = _eval_type(
                type_, globalns, localns, recursive_guard | {t.__forward_arg__}
            )
            t.__forward_evaluated__ = True
        return t.__forward_value__

    # https://github.com/python/cpython/blob/main/Lib/typing.py#L333-L343
    # fmt: off
    # ✂ start ✂
    if isinstance(t, (_GenericAlias, GenericAlias, UnionType)):
        ev_args = tuple(_eval_type(a, globalns, localns, recursive_guard) for a in t.__args__)
        if ev_args == t.__args__:
            return t
        if isinstance(t, GenericAlias):
            return GenericAlias(t.__origin__, ev_args)
        if isinstance(t, UnionType):
            return functools.reduce(operator.or_, ev_args)
        else:
            return t.copy_with(ev_args)
    return t
    # ✂ end ✂

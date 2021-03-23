"""
This module handles all interpretation of type annotations in pdoc.

In particular, it provides functionality to resolve
[typing.ForwardRef](https://docs.python.org/3/library/typing.html#typing.ForwardRef) objects without raising an
exception.
"""
from __future__ import annotations

import inspect
import sys
import typing
import warnings
from types import BuiltinFunctionType, ModuleType
from typing import (  # type: ignore
    Any,
    Optional,
    TYPE_CHECKING,
    _GenericAlias,
)

from . import extract
from ._compat import ForwardRef, GenericAlias, Literal, get_args, get_origin

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


def formatannotation(annotation: Any) -> str:
    """
    Like `inspect.formatannotation()`, but with a small bugfix for Python 3.9's GenericAlias annotations.
    """
    # a small inconsistency in Python 3.9,
    # formatannotation(list[str]) returns "list".
    if isinstance(annotation, type) and get_args(annotation):
        return repr(annotation)
    return inspect.formatannotation(annotation)


def resolve_annotations(
    annotations: dict[str, Any],
    module: Optional[ModuleType],
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
        resolved[name] = safe_eval_type(value, ns, fullname)

    return resolved


def safe_eval_type(
    t: Any,
    globalns,
    fullname: str,
    last_err: Optional[str] = None,
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
        err = last_err = str(e)
        mod = ""  # make type checker happy
    if err == last_err:
        warnings.warn(f"Error parsing type annotation for {fullname}: {err}")
        return t
    try:
        val = extract.load_module(mod)
    except Exception:
        warnings.warn(
            f"Error parsing type annotation for {fullname}. Import of {mod} failed: {err}"
        )
        return t
    return safe_eval_type(t, {mod: val, **globalns}, fullname, err)


def _eval_type(t, globalns, localns, recursive_guard=frozenset()):
    # Adapted from typing._eval_type.
    # Added type coercion originally found in get_type_hints, but removed NoneType check because that was distracting.
    # Added a special check for typing.Literal, whose literal strings would otherwise be evaluated.

    if isinstance(t, str):
        if sys.version_info < (3, 9):  # pragma: no cover
            t = t.strip("\"'")
        t = ForwardRef(t, is_argument=False)

    if get_origin(t) is Literal:
        return t

    if sys.version_info < (3, 9) and isinstance(
        t, (typing.ForwardRef, ForwardRef)
    ):  # pragma: no cover
        # we do a very happy dance here for Python 3.8, where things are a bit crazy.
        # In a nutshell, we convert Python 3.8's ForwardRef to our vendored ForwardRef,
        # and then eval on the whole thing recursively.
        if isinstance(t, typing.ForwardRef):
            t = ForwardRef(t.__forward_arg__, is_argument=False)
        return _eval_type(
            t._evaluate(globalns, localns, recursive_guard),
            globalns,
            localns,
            recursive_guard,
        )

    # https://github.com/python/cpython/blob/4db8988420e0a122d617df741381b0c385af032c/Lib/typing.py#L299-L314
    # fmt: off
    # ✂ start ✂
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

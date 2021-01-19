"""
This module handles all interpretation of the *Abstract Syntax Tree (AST)* in pdoc.

Parsing the AST is done to extract docstrings, type annotations, and variable declarations from `__init__`.
"""
from __future__ import annotations

import ast
import inspect
import types
from dataclasses import dataclass
from itertools import zip_longest, tee
from typing import Union, Iterable, TypeVar, Iterator, Any, overload, TYPE_CHECKING

from ._compat import cache, ast_unparse


@cache
def get_source(obj: Any) -> str:
    """
    Returns the source code of the Python object `obj` as a str.
    This tries to first unwrap the method if it is wrapped and then calls `inspect.getsource`.

    If this fails, an empty string is returned.
    """
    try:
        obj = inspect.unwrap(obj)
        return inspect.getsource(obj)
    except Exception:
        return ""


@overload
def parse(obj: types.ModuleType) -> ast.Module:
    ...


@overload
def parse(obj: types.FunctionType) -> Union[ast.FunctionDef, ast.AsyncFunctionDef]:
    ...


@overload
def parse(obj: type) -> ast.ClassDef:
    ...


def parse(
    obj: Union[type, types.ModuleType, types.FunctionType]
) -> Union[ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef]:
    """
    Parse a module, class or function and return the (unwrapped) AST node.
    If an object's source code cannot be found, this function returns an empty ast node stub
    which can still be walked.
    """
    src = get_source(obj)
    if isinstance(obj, types.ModuleType):
        return _parse_module(src)
    elif isinstance(obj, type):
        return _parse_class(src)
    else:
        return _parse_function(src)


if not TYPE_CHECKING:
    # we're running into a weird mypy bug here, @overload and @cache don't like each other
    parse = cache(parse)


@cache
def unparse(tree: ast.AST):
    """`ast.unparse`, but cached."""
    return ast_unparse(tree)


@dataclass
class AstInfo:
    """The information extracted from walking the syntax tree."""

    docstrings: dict[str, str]
    """A qualname -> docstring mapping."""
    annotations: dict[str, str]
    """A qualname -> annotation mapping.
    
    Annotations are not evaluated by this module and only returned as strings."""


@cache
def walk_tree(obj: Union[types.ModuleType, type]) -> AstInfo:
    """
    Walks the abstract syntax tree for `obj` and returns the extracted information.
    """
    tree = parse(obj)
    docstrings = {}
    annotations = {}
    for a, b in _pairwise_longest(_nodes(tree)):
        if isinstance(a, ast.AnnAssign) and isinstance(a.target, ast.Name) and a.simple:
            name = a.target.id
            annotations[name] = unparse(a.annotation)
        elif (
            isinstance(a, ast.Assign)
            and len(a.targets) == 1
            and isinstance(a.targets[0], ast.Name)
        ):
            name = a.targets[0].id
        else:
            continue
        if (
            isinstance(b, ast.Expr)
            and isinstance(b.value, ast.Constant)
            and isinstance(b.value.value, str)
        ):
            docstrings[name] = inspect.cleandoc(b.value.value).strip()
    return AstInfo(
        docstrings,
        annotations,
    )


T = TypeVar("T")


def sort_by_source(
    obj: Union[types.ModuleType, type], sorted: dict[str, T], unsorted: dict[str, T]
) -> tuple[dict[str, T], dict[str, T]]:
    """
    Takes items from `unsorted` and inserts them into `sorted` in order of appearance in the source code of `obj`.
    The only exception to this rule is `__init__`, which (if present) is always inserted first.

    Some items may not be found, for example because they've been inherited from a superclass. The are returned as-is.

    Returns a `(sorted, not found)` tuple.
    """
    tree = parse(obj)

    if "__init__" in unsorted:
        sorted["__init__"] = unsorted.pop("__init__")

    for a in _nodes(tree):
        if (
            isinstance(a, ast.Assign)
            and len(a.targets) == 1
            and isinstance(a.targets[0], ast.Name)
        ):
            name = a.targets[0].id
        elif (
            isinstance(a, ast.AnnAssign) and isinstance(a.target, ast.Name) and a.simple
        ):
            name = a.target.id
        elif isinstance(a, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            name = a.name
        else:
            continue

        if name in unsorted:
            sorted[name] = unsorted.pop(name)
    return sorted, unsorted


@cache
def _parse_module(source: str) -> ast.Module:
    """
    Parse the AST for the source code of a module and return the ast.Module.

    Returns an empty ast.Module if source is empty.
    """
    return ast.parse(source)


@cache
def _parse_class(source: str) -> ast.ClassDef:
    """
    Parse the AST for the source code of a class and return the ast.ClassDef.

    Returns an empty ast.ClassDef if source is empty.
    """
    tree = ast.parse(_dedent(source))
    assert len(tree.body) <= 1
    if tree.body:
        t = tree.body[0]
        assert isinstance(t, ast.ClassDef)
        return t
    return ast.ClassDef(body=[], decorator_list=[])


@cache
def _parse_function(source: str) -> Union[ast.FunctionDef, ast.AsyncFunctionDef]:
    """
    Parse the AST for the source code of a (async) function and return the matching AST node.

    Returns an empty ast.FunctionDef if source is empty.
    """
    tree = ast.parse(_dedent(source))
    assert len(tree.body) <= 1
    if tree.body:
        t = tree.body[0]
        if isinstance(t, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return t
        else:
            # we have a lambda function,
            # to simplify the API return the ast.FunctionDef stub.
            pass
    return ast.FunctionDef(body=[], decorator_list=[])


@cache
def _dedent(source: str) -> str:
    """
    Dedent the head of a function or class definition so that it can be parsed by `ast.parse`.
    This is an alternative to `textwrap.dedent`, which does not dedent if there are docstrings
    without indentation. For example, this is valid Python code but would not be dedented with `textwrap.dedent`:

    class Foo:
        def bar(self):
           '''
    this is a docstring
           '''
    """
    if not source or source[0] not in (" ", "\t"):
        return source
    source = source.lstrip()
    if source[0] in ("@", "#"):
        first_line, rest = source.split("\n", 1)
        return first_line + "\n" + _dedent(rest)
    else:
        return source


@cache
def _nodes(tree: Union[ast.Module, ast.ClassDef]) -> list[ast.AST]:
    """
    Returns the list of all nodes in tree's body, but also inlines the body of __init__.

    This is useful to detect all declared variables in a class, even if they only appear in the constructor.
    """
    return list(_nodes_iter(tree))


def _nodes_iter(tree: Union[ast.Module, ast.ClassDef]) -> Iterator[ast.AST]:
    for a in tree.body:
        yield a
        if isinstance(a, ast.FunctionDef) and a.name == "__init__":
            yield from _init_nodes(a)


def _init_nodes(tree: ast.FunctionDef) -> Iterator[ast.AST]:
    """
    Transform attribute assignments like "self.foo = 42" to name assignments like "foo = 42",
    keep all constant expressions, and no-op everything else.
    This essentially allows us to inline __init__ when parsing a class definition.
    """
    for a in tree.body:
        if (
            isinstance(a, ast.AnnAssign)
            and isinstance(a.target, ast.Attribute)
            and isinstance(a.target.value, ast.Name)
            and a.target.value.id == "self"
        ):
            yield ast.AnnAssign(
                ast.Name(a.target.attr), a.annotation, a.value, simple=1
            )
        elif (
            isinstance(a, ast.Assign)
            and len(a.targets) == 1
            and isinstance(a.targets[0], ast.Attribute)
            and isinstance(a.targets[0].value, ast.Name)
            and a.targets[0].value.id == "self"
        ):
            yield ast.Assign(
                [ast.Name(a.targets[0].attr)],
                value=a.value,
                type_comment=a.type_comment,
            )
        elif (
            isinstance(a, ast.Expr)
            and isinstance(a.value, ast.Constant)
            and isinstance(a.value.value, str)
        ):
            yield a
        else:
            yield ast.Pass()


def _pairwise_longest(iterable: Iterable[T]) -> Iterable[tuple[T, T]]:
    """s -> (s0,s1), (s1,s2), (s2, s3),  ..., (sN, None)"""
    a, b = tee(iterable)
    next(b, None)
    return zip_longest(a, b)

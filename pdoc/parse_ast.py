import ast
import inspect
import textwrap
from dataclasses import dataclass
from functools import cache
from itertools import zip_longest, tee
from typing import Union, Iterable, TypeVar, Iterator, Any


@cache
def get_source(obj: Any) -> str:
    """
    Returns the source code of the Python object `obj` as a str.
    This tries to extract the source from the special
    `__wrapped__` attribute if it exists. Otherwise, it falls back
    to `inspect.getsource`.

    If neither works, an empty string is returned.
    """
    while hasattr(obj, "__wrapped__"):
        obj = obj.__wrapped__
    try:
        return inspect.getsource(obj)
    except Exception:
        return ""


@cache
def parse_module(source: str) -> ast.Module:
    """
    Parse the AST for the source code of a module and return the ast.Module.

    Returns an empty ast.Module if source is empty.
    """
    return ast.parse(source)


@cache
def parse_class(source: str) -> ast.ClassDef:
    """
    Parse the AST for the source code of a class and return the ast.ClassDef.

    Returns an empty ast.ClassDef if source is empty.
    """
    tree = ast.parse(textwrap.dedent(source))
    assert len(tree.body) <= 1
    if tree.body:
        t = tree.body[0]
        assert isinstance(t, ast.ClassDef)
        return t
    return ast.ClassDef(body=[], decorator_list=[])


@cache
def parse_function(source: str) -> Union[ast.FunctionDef, ast.AsyncFunctionDef]:
    """
    Parse the AST for the source code of a (async) function and return the matching AST node.

    Returns an empty ast.FunctionDef if source is empty.
    """
    tree = ast.parse(textwrap.dedent(source))
    assert len(tree.body) <= 1
    if tree.body:
        t = tree.body[0]
        assert isinstance(t, (ast.FunctionDef, ast.AsyncFunctionDef))
        return t
    return ast.FunctionDef(body=[], decorator_list=[])


T = TypeVar("T")


def _pairwise_longest(iterable: Iterable[T]) -> Iterable[tuple[T, T]]:
    """s -> (s0,s1), (s1,s2), (s2, s3),  ..., (sN, None)"""
    a, b = tee(iterable)
    next(b, None)
    return zip_longest(a, b)


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


def __nodes(tree: Union[ast.Module, ast.ClassDef]) -> Iterator[ast.AST]:
    for a in tree.body:
        yield a
        if isinstance(a, ast.FunctionDef) and a.name == "__init__":
            yield from _init_nodes(a)


@cache
def _nodes(tree: Union[ast.Module, ast.ClassDef]) -> list[ast.AST]:
    return list(__nodes(tree))


@dataclass
class AstInfo:
    docstrings: dict[str, str]
    annotations: dict[str, str]


@cache
def walk_tree(tree: Union[ast.Module, ast.ClassDef]) -> AstInfo:
    """Returns (docstrings, annotations) extracted from AST"""
    docstrings = {}
    annotations = {}
    for a, b in _pairwise_longest(_nodes(tree)):
        if isinstance(a, ast.AnnAssign) and isinstance(a.target, ast.Name) and a.simple:
            name = a.target.id
            annotations[name] = ast.unparse(a.annotation)
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
    return AstInfo(docstrings, annotations)


def sort_by_source(
        tree: Union[ast.Module, ast.ClassDef], sorted: dict[str, T], unsorted: dict[str, T]
) -> tuple[dict[str, T], dict[str, T]]:
    """Returns (sorted, not found)"""

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

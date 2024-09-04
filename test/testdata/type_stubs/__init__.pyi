from typing import Any
from typing import Iterable
from typing import overload

from ._utils import ImportedClass

def func(x: str, y: Any, z: "Iterable[str]") -> int: ...

var: list[str]
"""Docstring override from the .pyi file."""

class Class:
    attr: int

    def meth(self, y: bool) -> bool: ...

    class Subclass:
        attr: str

        def meth(self, y: bool) -> bool: ...

    @overload
    def overloaded(self, x: int) -> int: ...
    @overload
    def overloaded(self, x: str) -> str: ...

__all__ = [
    "func",
    "var",
    "Class",
    "ImportedClass",
]

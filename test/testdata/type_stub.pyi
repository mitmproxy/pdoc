from typing import Any
from typing import Iterable
from typing import overload

def func(x: str, y: Any, z: "Iterable[str]") -> int: ...

var: list[str]
"""Docstring override from the .pyi file."""

class Class:
    attr: int

    @overload
    def __init__(self, x: int): ...
    @overload
    def __init__(self, x: str): ...
    def meth(self, y: bool) -> bool: ...

    class Subclass:
        attr: str

        def meth(self, y: bool) -> bool: ...

    @overload
    def overloaded(self, x: int) -> int: ...
    @overload
    def overloaded(self, x: str) -> str: ...

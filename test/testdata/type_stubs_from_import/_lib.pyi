from typing import overload

def foo(x: int, y: str, z: bool) -> None:
    """docstring in stub file"""

def bar(x: float, y: float, z: float) -> int: ...

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

from typing import Any
from typing import Iterable

def func(x: str, y: Any, z: "Iterable[str]") -> int: ...

var: list[str]

class Class:
    attr: int

    def meth(self, y: bool) -> bool: ...

    class Subclass:
        attr: str

        def meth(self, y: bool) -> bool: ...

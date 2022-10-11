# no from __future__ import annotations!
from typing import List
from typing import Literal
from typing import Union


def foo(x: Literal["r", "w"]) -> Union[str, int]:
    pass


def bar(x: list["int"], /) -> List["int"]:
    pass

# no from __future__ import annotations!
from typing import Literal, Union, List


def foo(x: Literal["r", "w"]) -> Union[str, int]:
    pass


def bar(x: list["int"], /) -> List["int"]:
    pass

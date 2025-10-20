# no from __future__ import annotations!
from typing import List
from typing import Literal


def foo(x: Literal["r", "w"]) -> str | int:
    raise NotImplementedError


def bar(x: list["int"], /) -> List["int"]:
    raise NotImplementedError

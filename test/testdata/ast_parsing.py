from typing import TypeVar

T = TypeVar("T")


def first(l: list[T]) -> T:
    return l[0]


class Foo:
    def __init__(self):
        self.no_docstring = 42

        self.with_docstring = 43
        """This is an attribute docstring."""

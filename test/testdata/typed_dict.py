from typing import TypedDict
from typing import Optional

class Foo(TypedDict):
    a: Optional[int]
    """First attribute."""


class Bar(Foo, total=False):
    """A TypedDict subclass. Before 3.12, TypedDict botches __mro__."""

    b: int
    """Second attribute."""
    c: str
    # undocumented attribute


class Baz(Bar):
    """A TypedDict subsubclass."""

    d: bool
    """new attribute"""

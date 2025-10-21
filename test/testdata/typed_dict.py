from typing import TypedDict


class Foo(TypedDict):
    a: int | None
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

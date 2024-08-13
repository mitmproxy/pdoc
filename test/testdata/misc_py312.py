# mypy: ignore-errors
# https://github.com/python/mypy/issues/16607
"""
Testing features that either are 3.12+ only or render slightly different on 3.12.
"""

from __future__ import annotations

import typing
from typing import NamedTuple
from typing import Optional
from typing import TypedDict

# Testing the new Python 3.12 `type` statement.
type MyType = int
"""A custom Python 3.12 type."""

foo: MyType
"""A custom type instance."""


type MyTypeWithoutDocstring = int

MyTypeClassic: typing.TypeAlias = int
"""A "classic" typing.TypeAlias."""

# Testing a typing.NamedTuple
# we do not care very much about collections.namedtuple,
# the typing version is superior for documentation and a drop-in replacement.


class NamedTupleExample(NamedTuple):
    """
    An example for a typing.NamedTuple.
    """

    name: str
    """Name of our example tuple."""
    id: int = 3


# Testing some edge cases in our inlined implementation of ForwardRef._evaluate in _eval_type.
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

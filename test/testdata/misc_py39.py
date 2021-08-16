"""
Testing features that either are 3.9+ only or render slightly different on 3.9.
"""
from __future__ import annotations
from typing import NamedTuple, Optional, TypedDict


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


class Bar(Foo, total=False):
    b: int

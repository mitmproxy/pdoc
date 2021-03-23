"""
Testing features that either are 3.9+ only or render slightly different on 3.9.
"""
from typing import NamedTuple


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

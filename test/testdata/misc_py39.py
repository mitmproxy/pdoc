"""
Testing features that either are 3.9+ only or render slightly different on 3.9.
"""
from __future__ import annotations

import functools
from typing import NamedTuple
from typing import Optional
from typing import TypedDict
from typing import Union


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
    """A TypedDict subclass. TypedDict botches the MRO, so things aren't perfect here."""

    b: int
    """Second attribute."""
    c: str
    # undocumented attribute


class BarWorkaround(Foo, TypedDict, total=False):
    """
    A TypedDict subclass with the workaround to also inherit from TypedDict.

    See https://github.com/sphinx-doc/sphinx/pull/10806.
    """

    b: int
    """Second attribute."""
    c: str
    # undocumented attribute


class SingleDispatchMethodExample:
    @functools.singledispatchmethod
    def fancymethod(self, str_or_int: Union[str, int]):
        """A fancy method which is capable of handling either `str` or `int`.

        :param str_or_int: string or integer to handle
        """
        raise NotImplementedError(f"{type(str_or_int)=} not implemented!")

    @fancymethod.register
    def fancymethod_handle_str(self, str_to_handle: str):
        """Fancy method handles a string.

        :param str_to_handle: string which will be handled
        """
        print(f"{type(str_to_handle)} = '{str_to_handle}")

    @fancymethod.register
    def _fancymethod_handle_int(self, int_to_handle: int):
        """Fancy method handles int (not shown in doc).

        :param int_to_handle: int which will be handled
        """
        print(f"{type(int_to_handle)} = '{int_to_handle:x}'")

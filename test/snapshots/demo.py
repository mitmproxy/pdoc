"""

# Test Module

This is a demo module to show what's possible!

## Subheading

- A list
- with items
- and *more* markdown!
- `demo.Foo.do_foo`
- `typing.Type`

wtf lol
"""
import os
from dataclasses import dataclass, field
from typing import TypeVar

CONST_A: int = 42
"""A happy constant"""

T = TypeVar('T')


def foo(a: str, b: "Foo", *, c: T = False) -> T:
    """Do foo, but do it quickly."""
    return 42


CONST_B = "yes"
"""A non-annotated constant"""

CONST_C: float
"""An unset constant"""

CONST_D: "Foo"


class Foo:
    """Doing foo all day long"""
    foo = "lots of foo!"
    '''The fooest of all attributes.'''

    def __init__(self):
        """Let's make a foo!"""
        self.a: int = 42
        """I am defined in the constructor only"""

    def do_foo(self) -> "Foo":
        """You can actually do foo, too!"""
        return self

    async def i_am_async(self) -> int:
        pass


class Bar(Foo):
    bar: str
    """I sneaked in. :)"""

    class Baz:
        baz = True

        def wat(self) -> None:
            """bar baz wat?"""


def wat(x: Bar.Baz = "a test", t: os.environ = os.environ) -> int:
    return False


class DoubleInherit(Foo, Bar.Baz):
    """I am rich."""


@dataclass
class DataDemo:
    a: int
    b: str
    """I am documented!"""
    c: bool = field(repr=False)

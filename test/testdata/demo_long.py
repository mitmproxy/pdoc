"""

# Test Module

This is a test module demonstrating pdoc's parsing capabilities.

- All docstrings support plain markdown.
- Including code!

  ```python
  print("hello world")
  ```
- You can link to classes or modules by putting them between backticks: `demo.Dog.bark`
  - The only requirement is that you must specify the full qualified path for external modules.
- Module members appear in the order they are listed in the source code.
  If you do not like the order in pdoc, you should probably have a different order in your source file as well.

# A Second Section

You can have multiple sections in your module docstring,
which will also show up in the navigation.
"""
from __future__ import annotations

import abc
from dataclasses import dataclass
from dataclasses import field
import enum
from functools import cached_property
import os
from typing import ClassVar
from typing import List
from typing import Optional
from typing import Sequence
from typing import TypeVar
from typing import Union

from pdoc._compat import cache

FOO_CONSTANT: int = 42
"""
A happy constant. ✨  
pdoc documents constants with their type annotation and default value.
"""

FOO_SINGLETON: "Foo"
"""
This variable is annotated with a type only, but not assigned to a value.
We also haven't defined the associated type (`Foo`) yet, 
so the type annotation in the code in the source code is actually a string literal:

```python
FOO_SINGLETON: "Foo"
```

Similar to mypy, pdoc resolves
[string forward references](https://mypy.readthedocs.io/en/stable/kinds_of_types.html#class-name-forward-references)
automatically.
"""

NO_DOCSTRING: int
# this variable has a type annotation but not docstring.


def a_simple_function(a: str) -> str:
    """
    This is a basic module-level function.

    For a more complex example, take a look at `a_complex_function`!
    """
    return a.upper()


T = TypeVar("T")


def a_complex_function(
    a: str, b: Union["Foo", str], *, c: Optional[T] = None
) -> Optional[T]:
    """
    This is a function with a fairly complex signature,
    involving type annotations with `typing.Union`, a `typing.TypeVar` (~T),
    as well as a keyword-only arguments (*).
    """
    return None


class Foo:
    """
    `Foo` is a basic class without any parent classes (except for the implicit `object` class).

    You will see in the definition of `Bar` that docstrings are inherited by default.

    Functions in the current scope can be referenced without prefix: `a_regular_function()`.
    """

    an_attribute: Union[str, List["int"]]
    """A regular attribute with type annotations"""

    a_class_attribute: ClassVar[str] = "lots of foo!"
    """An attribute with a ClassVar annotation."""

    def __init__(self) -> None:
        """
        The constructor is currently always listed first as this feels most natural."""
        self.a_constructor_only_attribute: int = 42
        """This attribute is defined in the constructor only, but still picked up by pdoc's AST traversal."""

        self.undocumented_constructor_attribute = 42
        a_complex_function("a", "Foo")

    def a_regular_function(self) -> "Foo":
        """This is a regular method, returning the object itself."""
        return self

    @property
    def a_property(self) -> str:
        """This is a `@property` attribute. pdoc will display it as a variable."""
        return "true foo"

    @cached_property
    def a_cached_property(self) -> str:
        """This is a `@functools.cached_property` attribute. pdoc will display it as a variable as well."""
        return "true foo"

    @cache
    def a_cached_function(self) -> str:
        """This is method with `@cache` decoration."""
        return "true foo"

    @classmethod
    def a_class_method(cls) -> int:
        """This is what a `@classmethod` looks like."""
        return 24

    @classmethod  # type: ignore
    @property
    def a_class_property(cls) -> int:
        """This is what a `@classmethod @property` looks like."""
        return 24

    @staticmethod
    def a_static_method():
        """This is what a `@staticmethod` looks like."""
        print("Hello World")


class Bar(Foo):
    bar: str
    """A new attribute defined on this subclass."""

    class Baz:
        """
        This class is an attribute of `Bar`.
        To not create overwhelmingly complex trees, pdoc flattens the class hierarchy in the documentation
        (but not in the navigation).

        It should be noted that inner classes are a pattern you most often want to avoid in Python.
        Think about moving stuff in a new package instead!

        This class has no __init__ method defined, so pdoc will not show a constructor.
        """

        def wat(self):
            """A regular method. Above, you see what happens if a class has no constructor defined and
            no constructor docstring."""


async def i_am_async(self) -> int:
    """
    This is an example of an async function.

    - Knock, knock
    - An async function
    - Who's there?
    """
    raise NotImplementedError


@cache
def fib(n):
    """
    This is an example of decorated function. Decorators are included in the documentation as well.
    This is often useful when documenting web APIs, for example.
    """
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)


def security(test=os.environ):
    """
    Default values are generally rendered using repr(),
    but some special cases -- like os.environ -- are overridden to avoid leaking sensitive data.
    """
    return False


class DoubleInherit(Foo, Bar.Baz, abc.ABC):
    """This is an example of a class that inherits from multiple parent classes."""


CONST_B = "yes"
"""A constant without type annotation"""

CONST_NO_DOC = "SHOULD NOT APPEAR"


@dataclass
class DataDemo:
    """
    This is an example for a dataclass.

    As usual, you can link to individual properties: `DataDemo.a`.
    """

    a: int
    """Again, we can document individual properties with docstrings."""
    a2: Sequence[str]
    # This property has a type annotation but is not documented.
    a3 = "a3"
    # This property has a default value but is not documented.
    a4: str = "a4"
    # This property has a type annotation and a default value but is not documented.
    b: bool = field(repr=False, default=True)
    """This property is assigned to `dataclasses.field()`, which works just as well."""


@dataclass
class DataDemoExtended(DataDemo):
    c: str = "42"
    """A new attribute."""


class EnumDemo(enum.Enum):
    """
    This is an example of an Enum.

    As usual, you can link to individual properties: `GREEN`.
    """

    RED = 1
    """I am the red."""
    GREEN = 2
    """I am green."""
    BLUE = enum.auto()


def embed_image():
    """
    This docstring includes an embedded image:

    ```
    ![pdoc logo](../docs/logo.png)
    ```

    ![pdoc logo](../../docs/logo.png)
    """


def admonitions():
    """
    pdoc also supports basic reStructuredText admonitions:

    ```
    .. note/warning/danger:: Optional title
       Body text
    ```

    .. note::
       Hi there!

    .. warning:: Be Careful!
       This warning has both a title and content.

    .. danger::
       Danger ahead.

    """

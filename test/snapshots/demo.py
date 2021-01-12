"""

# Test Module

This is a test module demonstrating pdoc's parsing capabilities!

- All docstrings support plain markdown.
- Including code!

  ```python
  print("hello world")
  ```
- You can link to classes or modules: demo.do_foo
  - The only requirement is that you must specify the full qualified path.
  - You can still put it in backticks for a monospace font: `demo.do_foo`
- Module members appear in the order they are listed in the source code.
  If you do not like the order in pdoc, you should probably have a different order in your source file as well.

# More Documentation

You can have multiple section in your module docstring,
which will all show up in the navigation on the left.
"""
import os
from dataclasses import dataclass, field
from functools import cache, cached_property
from typing import TypeVar, Union, ClassVar, Optional

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


def a_simple_function(a: str) -> str:
    """
    This is a basic module-level function.

    For a more complex example, take a look at `demo.a_complex_function`!
    """
    return a.upper()


T = TypeVar('T')


def a_complex_function(a: str, b: Union["Foo", str], *, c: Optional[T] = None) -> Optional[T]:
    """
    This is a function with a fairly complex signature,
    involving type annotations with `typing.Union`, a `typing.TypeVar` (~T),
    as well as a keyword-only arguments (*).
    """
    return 42


class Foo:
    """
    `demo.Foo` is a basic class without any parent classes (except for the implict `object` class).

    You will see in the definition of `demo.Bar` that docstrings are inherited by default.
    """

    an_attribute: Union[str, list[int]]
    """A regular attribute with type annotations"""

    a_class_attribute: ClassVar[str] = "lots of foo!"
    '''An attribute with a ClassVar annotation.'''

    def __init__(self):
        """
        The constructor is currently always listed first as this feels most natural."""
        self.a_constructor_only_attribute: int = 42
        """This attribute is defined in the constructor only, but still picked up by pdoc's AST traversal."""

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

    @classmethod
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

        Below, you see what happens if a class has no constructor defined (and hence no constructor docstring).
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


@cache
def fib(n):
    """
    This is an example of decorated function. Decorators are included in the documentation as well.
    This is often useful when documenting web APIs, for example.
    """
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)


def special_cases(test: os.environ = os.environ):
    """Default values are generally rendered using repr(), but some special cases -- like os.environ -- are overriden to avoid
    leaking sensitive data."""
    return False


class DoubleInherit(Foo, Bar.Baz):
    """This is an example of a class that inherits from multiple parent classes."""


CONST_B = "yes"
"""A constant without type annotation"""

CONST_NO_DOC = "WTF"


@dataclass
class DataDemo:
    """
    This is an example for a dataclass.
    Dataclasses generate a relatively pointless docstring by default,
    but you can override it by providing your own (like here!).
    """
    a: int
    """Again, we can document indivial properties with docstrings."""
    b: str
    c: bool = field(repr=False, default=True)
    """This property is assigned to `field()`, which works just as well."""

import abc
from functools import lru_cache
from typing import Generic
from typing import TypeVar

from pdoc._compat import cached_property


# https://github.com/mitmproxy/pdoc/issues/226


class Descriptor:
    def __init__(self, func):
        self.__doc__ = func.__doc__

    def __get__(self, instance, owner):
        return self if instance is None else getattr(instance, "_x", 0)

    def __set__(self, instance, value):
        instance._x = value


class Issue226:
    @Descriptor
    def size(self):
        """This is the size"""


# Testing function and object default values

def default_func():
    pass


default_obj = object()

var_with_default_obj = default_obj
"""this shouldn't render the object address"""
var_with_default_func = default_func
"""this just renders like a normal function"""


def func_with_defaults(
    a=default_obj,
    b=default_func
):
    """this shouldn't render object or function addresses"""
    pass


# Testing classmethod links in code
class ClassmethodLink:
    """
    You can either do

    >>> ClassmethodLink.bar()
    42

    or

    ```python
    ClassmethodLink.bar()
    ```

    neither will be linked.
    """

    @classmethod
    def bar(cls):
        return 42


# Testing generic bases

T = TypeVar("T")


class GenericParent(Generic[T]):
    pass


class NonGenericChild(GenericParent[str]):
    pass


# Testing docstring inheritance

class Base:
    def __init__(self):
        """init"""
        super().__init__()

    def foo(self):
        """foo"""
        pass

    @classmethod
    def bar(cls):
        """bar"""
        pass

    @staticmethod
    def baz():
        """baz"""
        pass

    @property
    def qux(self):
        """qux"""
        return

    # This is not supported by inspect.getdoc yet.
    @cached_property
    def quux(self):
        """quux"""
        return

    quuux: int = 42
    """quuux"""


class Child(Base):
    def __init__(self):
        super().__init__()

    def foo(self):
        pass

    @classmethod
    def bar(cls):
        pass

    @staticmethod
    def baz():
        pass

    @property
    def qux(self):
        return

    @cached_property
    def quux(self):
        return

    quuux: int = 42


# Testing that an attribute that is only annotated does not trigger a "submodule not found" warning.

only_annotated: int


# Testing that Exceptions render properly


class CustomException(RuntimeError):
    """custom exception type"""


# Testing that a private class in __all__ is displayed


class _Private:
    """private class"""

    pass

    def _do(self):
        """private method"""


# Testing a class attribute that is a lambda (which generates quirky sources)


class LambdaAttr:
    # not really supported, but also shouldn't crash.
    attr = lambda x: 42  # noqa


# Testing different docstring annotations
# fmt: off


def foo():
    """no indents"""


def bar():
    """no
indents"""


def baz():
    """one
    indent"""


def qux():
    """
    two
    indents
    """


class Indented:
    def foo(self):
        """no indents"""

    def bar(self):
        """no
indents"""

    def baz(self):
        """one
        indent"""

    def qux(self):
        """
        two
        indents
        """

    @lru_cache()
    def foo_decorated(self):
        """no indents"""

    @lru_cache()
    # comment
    def foo_commented(self):
        """no indents"""

    @lru_cache()
    def bar_decorated(self):
        """no
indents"""

    @lru_cache()
    def baz_decorated(self):
        """one
        indent"""

    @lru_cache()
    def qux_decorated(self):
        """
        two
        indents
        """

    @lru_cache(
        maxsize=42
    )
    def quux_decorated(self):
        """multi-line decorator, https://github.com/mitmproxy/pdoc/issues/246"""


def _protected_decorator(f):
    return f


@_protected_decorator
def fun_with_protected_decorator():
    """This function has a protected decorator (name starting with a single `_`)."""


class UnhashableDataDescriptor:
    def __get__(self):
        pass
    __hash__ = None  # type: ignore


unhashable = UnhashableDataDescriptor()


class AbstractClass(metaclass=abc.ABCMeta):
    """This class shouldn't show a constructor as it's abstract."""
    @abc.abstractmethod
    def foo(self):
        pass


# Adapted from https://github.com/mitmproxy/pdoc/issues/320

def make_adder(a: int):
    def add_func(b: int) -> int:
        """This function adds two numbers."""
        return a + b
    return add_func


add_four = make_adder(4)
add_five = make_adder(5)
"""This function adds five."""
add_six = make_adder(6)
add_six.__doc__ = "This function adds six."


# Adapted from https://github.com/mitmproxy/pdoc/issues/335
def linkify_links():
    """
    This docstring contains links that are also identifiers:

    - [`linkify_links`](https://example.com/)
    - [misc.linkify_links](https://example.com/)
    - [`linkify_links()`](https://example.com/)
    - [misc.linkify_links()](https://example.com/)
    - [link in target](https://example.com/misc.linkify_links)
    - [explicit linking](#AbstractClass.foo)
    """


class Issue352aMeta(type):
    def __call__(cls, *args, **kwargs):
        """Meta.__call__"""


class Issue352a(metaclass=Issue352aMeta):
    def __init__(self):
        """Issue352.__init__ should be preferred over Meta.__call__."""


class Issue352bMeta(type):
    def __call__(cls, *args, **kwargs):
        pass


class Issue352b(metaclass=Issue352bMeta):
    """No docstrings for the constructor here."""


class CustomCallMeta(type):
    def __call__(cls, *args, **kwargs):
        """Custom docstring in metaclass.`__call__`"""


class CustomCall(metaclass=CustomCallMeta):
    """A class where the constructor is defined by its metaclass."""


class Headings:
    """
    # Heading 1

    Here is some text.

    ## Heading 2

    Here is some text.

    ### Heading 3

    Here is some text.

    #### Heading 4

    Here is some text.

    ##### Heading 5

    Here is some text.

    ###### Heading 6

    Here is some text.

    """


class CustomRepr:
    def __repr__(self):
        return "°<script>alert(1)</script>"


def repr_not_syntax_highlightable(x=CustomRepr()):
    """The default value for x fails to highlight with pygments."""


__all__ = [
    "Issue226",
    "var_with_default_obj",
    "var_with_default_func",
    "func_with_defaults",
    "ClassmethodLink",
    "GenericParent",
    "NonGenericChild",
    "Child",
    "only_annotated",
    "CustomException",
    "_Private",
    "LambdaAttr",
    "foo",
    "bar",
    "baz",
    "qux",
    "Indented",
    "fun_with_protected_decorator",
    "unhashable",
    "AbstractClass",
    "add_four",
    "add_five",
    "add_six",
    "linkify_links",
    "Issue352a",
    "Issue352b",
    "CustomCall",
    "Headings",
    "repr_not_syntax_highlightable",
]

from functools import lru_cache

import demo_long

# Testing a proper __module__, but no useful __qualname__ attribute.

bad_qualname = demo_long.DataDemo.__init__

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

    @lru_cache
    def foo_decorated(self):
        """no indents"""

    @lru_cache
    # comment
    def foo_commented(self):
        """no indents"""

    @lru_cache
    def bar_decorated(self):
        """no
indents"""

    @lru_cache
    def baz_decorated(self):
        """one
        indent"""

    @lru_cache
    def qux_decorated(self):
        """
        two
        indents
        """


__all__ = [  # noqa
    "bad_qualname",
    "only_annotated",
    "CustomException",
    "_Private",
    "LambdaAttr",
    "foo",
    "bar",
    "baz",
    "qux",
    "Indented",
]

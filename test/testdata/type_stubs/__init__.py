"""
This module has an accompanying .pyi file with type stubs.
"""

from ._utils import ImportedClass


def func(x, y):
    """A simple function."""


var = []
"""A simple variable."""


class Class:
    attr = 42
    """An attribute"""

    def meth(self, y):
        """A simple method."""

    class Subclass:
        attr = "42"
        """An attribute"""

        def meth(self, y):
            """A simple method."""

    def no_type_annotation(self, z):
        """A method not present in the .pyi file."""

    def overloaded(self, x):
        """An overloaded method."""


__all__ = [
    "func",
    "var",
    "Class",
    "ImportedClass",
]

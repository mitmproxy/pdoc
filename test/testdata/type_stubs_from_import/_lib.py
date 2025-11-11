def foo(x, y, z): ...


def bar(x, y, z):
    """docstring in py file"""
    ...


def not_in_pyi(x: int) -> str: ...


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

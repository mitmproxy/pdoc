from functools import cache


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

    @cache
    def foo_decorated(self):
        """no indents"""

    @cache
    def bar_decorated(self):
        """no
indents"""

    @cache
    def baz_decorated(self):
        """one
        indent"""

    @cache
    def qux_decorated(self):
        """
        two
        indents
        """

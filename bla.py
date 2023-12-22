from functools import cached_property


class A:
    """An example class to be documented by pdoc."""

    @property
    def la(self):
        """Print la."""
        print("la")

    @cached_property
    def li(self):
        """Print li."""
        print("li")

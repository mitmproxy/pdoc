"""
Example where double-underscore method should be rendered.
"""


class HasDunderMethods:
    def __eq__(self, other):
        # Not documented because no docstring.
        pass

    def __lt__(self, other):
        """Documented because it has docstring."""


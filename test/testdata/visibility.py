"""
Example where no children should be rendered.
"""


class Undocumented:
    # Not shown because no docstring.
    pass


def my_func():
    """
    This is a public method that's not shown because it's marked as @private.
    """

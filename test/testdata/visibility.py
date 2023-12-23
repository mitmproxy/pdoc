"""
Example where only the children `__private_func` and  `__private_func_explicitly_public` should be rendered.
"""


class Undocumented:
    # Not shown because no docstring.
    pass


def my_func():
    """
    This is a public method that's not shown because it's marked as @private.
    """


def __protected_func():
    """
    This is a protected method that's not shown because its name starts with _.
    """


def __private_func():
    """
    This is a private method that's not shown because its name starts with __.
    """


def __private_func_explicitly_public():
    """
    This is a private method that's shown because it is explicitly marked
    as public.
    @public"""


def my_other_func():
    """
    This is another public method that's shown. It should show without additional
    whitespace above.
    """

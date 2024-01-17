"""
Example where only the these children should be rendered:
    * `__private_func_explicitly_public`,
    * `my_other_func` and
    * `yet_another_func` should be rendered.
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
    """@public
    This is a private method that's shown because it is explicitly marked
    as public.
    """


def public_func():
    """
    This is another public method that's shown. It should show without additional
    whitespace above.
    """


def yet_another_func():
    """
    This is yet another public method to give a gauge for the expected amount of
    whitespace between too methods.
    """

from warnings import deprecated


class MyDict(dict):
    pass


class CustomException(RuntimeError):
    """custom exception type"""


@deprecated("Do not use this anymore")
def deprecated_func():
    pass

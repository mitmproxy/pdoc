from warnings import deprecated


class MyDict(dict):
    pass


@deprecated("Do not use this anymore")
def deprecated_func():
    pass

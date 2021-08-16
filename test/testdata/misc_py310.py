import demo_long

# Testing a proper __module__, but no useful __qualname__ attribute.

bad_qualname = demo_long.DataDemo.__init__


def new_union(a: int | dict[str, "Foo"]) -> bool | None:
    """Testing Python 3.10's new type union syntax."""""


class Foo:
    pass

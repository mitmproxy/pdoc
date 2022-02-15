class Foo:
    class FooSub:
        pass


class Bar(Foo):
    pass


def baz(f: Foo) -> Foo.FooSub:
    pass

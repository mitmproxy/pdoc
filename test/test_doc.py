import tutils

import pdoc.doc
import pdoc.extract


def test_simple():
    with tutils.tdir():
        m = pdoc.extract.extract_module("./modules/one.py")
        assert m


class Parent:
    @staticmethod
    def bar():
        pass

    def baz(self):
        pass


class Child(Parent):
    @staticmethod
    def baz():
        pass


def test_is_static():
    assert pdoc.doc._is_static(Parent, "bar")
    assert not pdoc.doc._is_static(Parent, "baz")
    assert pdoc.doc._is_static(Child, "bar")
    assert pdoc.doc._is_static(Child, "baz")

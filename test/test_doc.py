import tutils

import pdoc.doc
import pdoc.extract


def test_simple():
    with tutils.tdir():
        m = pdoc.extract.extract_module("./modules/one.py")
        assert m


class Dummy:
    def method(self):
        pass

    @classmethod
    def class_method(cls):
        pass

    @staticmethod
    def static_method():
        pass


class DummyChild(Dummy):
    def class_method(self):
        pass


def test_is_static():
    assert pdoc.doc._is_method(Dummy, "method")
    assert not pdoc.doc._is_method(Dummy, "class_method")
    assert not pdoc.doc._is_method(Dummy, "static_method")

    assert pdoc.doc._is_method(DummyChild, "method")
    assert pdoc.doc._is_method(DummyChild, "class_method")
    assert not pdoc.doc._is_method(Dummy, "static_method")

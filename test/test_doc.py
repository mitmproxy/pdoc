import types

import builtins
import dataclasses
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from pdoc import extract
from pdoc.doc import Class, Module, Variable
from pdoc.doc_types import empty

here = Path(__file__).parent


def test_repr_tb(monkeypatch):
    m = Module(dataclasses)
    with patch("pdoc.doc._docstr", side_effect=ValueError):
        with pytest.raises(RuntimeError, match="Error in dataclasses's repr!"):
            repr(m)


def test_order():
    m = Module(dataclasses)
    m2 = Module(pytest)
    assert m < m2


def test_attrs():
    mod = extract.load_module(extract.parse_spec(here / "testdata" / "demo_long.py"))

    m = Module(mod)
    assert m.variables
    assert m.classes
    assert m.functions
    assert m.source_lines

    c = m.members["Foo"]
    assert isinstance(c, Class)
    assert c.class_variables
    assert c.instance_variables
    assert c.classmethods
    assert c.staticmethods
    assert c.methods


def test_all_with_import_err():
    mod = extract.load_module(extract.parse_spec(here / "import_err"))
    m = Module(mod)
    with pytest.warns(
        UserWarning,
        match="Found 'err' in test.import_err.__all__, but it does not resolve: Error importing test.import_err",
    ):
        assert m.members


def test_all_with_objects_instead_of_strings():
    class Foo:
        pass

    mod = types.ModuleType("mod")
    mod.__dict__["Foo"] = Foo
    mod.__dict__["__all__"] = [Foo]  # should be ["Foo"]

    m = Module(mod)
    assert m.members


def test_var_with_raising_repr():
    class Raising:
        def __repr__(self):
            raise RuntimeError

    v = Variable(
        "module",
        "var",
        taken_from=("module", "var"),
        docstring="",
        annotation=empty,
        default_value=Raising(),
    )
    assert v.default_value_str == " = <unable to get value representation>"


def test_class_with_raising_getattr():
    class _Raise(type):
        def __getattribute__(cls, key):
            if key == "__annotations__":
                raise RuntimeError
            return super().__getattribute__(key)

    class RaisingGetAttr(metaclass=_Raise):
        pass

    c = Class("test", "Raising", RaisingGetAttr, ("test", "Raising"))
    with pytest.warns(UserWarning, match="getattr.+raised an exception"):
        assert c.members


def test_builtin_source():
    m = Module(builtins)
    assert m.source_file is None
    assert m.source_lines is None


@pytest.mark.skipif(sys.version_info < (3, 9), reason="3.9+ only")
def test_raising_getdoc():
    class Foo:
        @classmethod
        @property
        def __doc__(self):
            raise RuntimeError

    x = Class(Foo.__module__, Foo.__qualname__, Foo, (Foo.__module__, Foo.__qualname__))
    with pytest.warns(UserWarning, match="inspect.getdoc(.+) raised an exception"):
        assert x.docstring == ""

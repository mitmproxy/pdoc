import sys
import types
import typing

import pytest

from pdoc import doc_ast
from pdoc.doc_types import safe_eval_type


@pytest.mark.parametrize(
    "typestr", ["totally_unknown_module", "!!!!", "html.unknown_attr"]
)
def test_eval_fail(typestr):
    a = types.ModuleType("a")
    with pytest.warns(UserWarning, match="Error parsing type annotation"):
        assert safe_eval_type(typestr, a.__dict__, None, a, "a") == typestr


def test_eval_fail2(monkeypatch):
    monkeypatch.setattr(
        doc_ast,
        "get_source",
        lambda _: "import typing\nif typing.TYPE_CHECKING:\n\traise RuntimeError()",
    )
    a = types.ModuleType("a")
    with pytest.warns(UserWarning, match="Failed to run TYPE_CHECKING code"):
        assert safe_eval_type("xyz", a.__dict__, None, a, "a") == "xyz"


def test_eval_fail3(monkeypatch):
    monkeypatch.setattr(
        doc_ast,
        "get_source",
        lambda _: "import typing\nif typing.TYPE_CHECKING:\n\tFooFn = typing.Callable[[],int]",
    )
    a = types.ModuleType("a")
    a.__dict__["typing"] = typing
    with pytest.warns(
        UserWarning,
        match="Error parsing type annotation .+ after evaluating TYPE_CHECKING blocks",
    ):
        assert safe_eval_type("FooFn[int]", a.__dict__, None, a, "a") == "FooFn[int]"


def test_eval_fail_import_nonexistent(monkeypatch):
    monkeypatch.setattr(
        doc_ast,
        "get_source",
        lambda _: "import typing\nif typing.TYPE_CHECKING:\n\timport nonexistent_module",
    )
    a = types.ModuleType("a")
    with pytest.warns(
        UserWarning, match="No module named 'nonexistent_module'|Import of xyz failed"
    ):
        assert safe_eval_type("xyz", a.__dict__, None, a, "a") == "xyz"


def test_eval_union_types_on_old_python(monkeypatch):
    monkeypatch.setattr(sys, "version_info", (3, 9, 0))
    with pytest.warns(
        UserWarning,
        match=r"You are likely attempting to use Python 3.10 syntax \(PEP 604 union types\) "
        r"with an older Python release.",
    ):
        # str never implements `|`, so we can use that to trigger the error on newer versions.
        safe_eval_type('"foo" | "bar"', {}, None, None, "example")


def test_recurse(monkeypatch):
    def get_source(mod):
        if mod == a:
            return "import typing\nif typing.TYPE_CHECKING:\n\tfrom b import Foo"
        else:
            return "import typing\nif typing.TYPE_CHECKING:\n\tfrom a import Foo"

    a = types.ModuleType("a")
    b = types.ModuleType("b")

    monkeypatch.setattr(doc_ast, "get_source", get_source)
    monkeypatch.setitem(sys.modules, "a", a)
    monkeypatch.setitem(sys.modules, "b", b)

    with pytest.warns(
        UserWarning, match="Recursion error when importing a|Import of xyz failed"
    ):
        assert safe_eval_type("xyz", a.__dict__, None, a, "a") == "xyz"

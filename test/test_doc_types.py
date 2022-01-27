import inspect
import typing

import pytest
import sys
import types

from pdoc import doc_ast
from pdoc.doc_types import formatannotation, safe_eval_type


@pytest.mark.skipif(sys.version_info < (3, 9), reason="3.9+ only")
def test_formatannotation_still_unfixed():
    """when this tests starts to fail, we can remove the workaround in our formatannotation wrapper"""
    assert formatannotation(list[str]) == "list[str]"
    assert inspect.formatannotation(list[str]) == "list"


@pytest.mark.parametrize(
    "typestr", ["totally_unknown_module", "!!!!", "html.unknown_attr"]
)
def test_eval_fail(typestr):
    with pytest.warns(UserWarning, match="Error parsing type annotation"):
        assert safe_eval_type(typestr, {}, types.ModuleType("a"), "a") == typestr


def test_eval_fail2(monkeypatch):
    monkeypatch.setattr(
        doc_ast,
        "get_source",
        lambda _: "import typing\nif typing.TYPE_CHECKING:\n\traise RuntimeError()",
    )
    with pytest.warns(UserWarning, match="Failed to run TYPE_CHECKING code"):
        assert safe_eval_type("xyz", {}, types.ModuleType("a"), "a") == "xyz"


def test_eval_fail3(monkeypatch):
    monkeypatch.setattr(
        doc_ast,
        "get_source",
        lambda _: "import typing\nif typing.TYPE_CHECKING:\n\tFooFn = typing.Callable[[],int]",
    )
    with pytest.warns(
        UserWarning,
        match="Error parsing type annotation .+ after evaluating TYPE_CHECKING blocks",
    ):
        assert (
            safe_eval_type("FooFn[int]", {"typing": typing}, types.ModuleType("a"), "a")
            == "FooFn[int]"
        )


def test_eval_union_types_on_old_python(monkeypatch):
    monkeypatch.setattr(sys, "version_info", (3, 9, 0))
    with pytest.warns(
        UserWarning,
        match=r"You are likely attempting to use Python 3.10 syntax \(PEP 604 union types\) "
        r"with an older Python release.",
    ):
        # str never implements `|`, so we can use that to trigger the error on newer versions.
        safe_eval_type('"foo" | "bar"', {}, None, "example")

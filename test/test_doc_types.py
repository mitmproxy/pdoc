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

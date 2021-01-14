import inspect

import pytest

from pdoc.doc_types import formatannotation, safe_eval_type


def test_formatannotation_still_unfixed():
    """when this tests starts to fail, we can remove the workaround in our formatannotation wrapper"""
    assert formatannotation(list[str]) == "list[str]"
    assert inspect.formatannotation(list[str]) == "list"


@pytest.mark.parametrize("typestr", ["html", "totally_unknown_module", "!!!!", "html.unknown_attr"])
def test_eval_fail(typestr):
    with pytest.warns(UserWarning, match="Error parsing type annotation"):
        assert safe_eval_type(typestr, {}, "test_eval_fail") == typestr

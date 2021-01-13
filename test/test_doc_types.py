import inspect

from pdoc.doc_types import formatannotation


def test_formatannotation_still_unfixed():
    """when this tests starts to fail, we can remove the workaround in our formatannotation wrapper"""
    assert formatannotation(list[str]) == "list[str]"
    assert inspect.formatannotation(list[str]) == "list"

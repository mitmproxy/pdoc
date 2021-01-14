from __future__ import annotations

from collections.abc import Mapping
from typing import Optional

import pytest

from pdoc.render_helpers import relative_link, edit_url, split_identifier


@pytest.mark.parametrize(
    "current,target,relative",
    [
        ("foo", "foo", ""),
        ("foo", "bar", "bar.html"),
        ("foo.foo", "bar", "../bar.html"),
        ("foo.bar", "foo.bar.baz", "bar/baz.html"),
        ("foo.bar.baz", "foo.qux.quux", "../qux/quux.html"),
    ],
)
def test_relative_link(current, target, relative):
    assert relative_link(current, target) == relative


@pytest.mark.parametrize(
    "modulename,is_package,mapping,result",
    [
        ["demo", False, {"dem": "abc"}, None],
        [
            "demo",
            False,
            {"demo": "https://github.com/mhils/pdoc/blob/master/test/snapshots/demo"},
            "https://github.com/mhils/pdoc/blob/master/test/snapshots/demo.py",
        ],
        [
            "demo",
            True,
            {"demo": "https://github.com/mhils/pdoc/blob/master/test/snapshots/demo/"},
            "https://github.com/mhils/pdoc/blob/master/test/snapshots/demo/__init__.py",
        ],
    ],
)
def test_edit_url(
    modulename: str, is_package: bool, mapping: Mapping[str, str], result: Optional[str]
):
    assert edit_url(modulename, is_package, mapping) == result


@pytest.mark.parametrize(
    "all_modules,fullname,result",
    [
        [["a", "a.b", "c"], "a.b.c.d", ("a.b", "c.d")],
        [["a", "a.b", "c"], "a.c.b.d", ("a", "c.b.d")],
    ],
)
def test_split_identifier(all_modules, fullname, result):
    assert split_identifier(all_modules, fullname) == result

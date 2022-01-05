import pytest
from hypothesis import given
from hypothesis.strategies import text

from pdoc import docstrings


# The important tests are in test_snapshot.py (and, by extension, testdata/)
# only some fuzzing here.


@given(text())
def test_google(s):
    ret = docstrings.google(s)
    assert not s or ret


@given(text())
def test_numpy(s):
    ret = docstrings.numpy(s)
    assert not s or ret


@given(text())
def test_rst(s):
    ret = docstrings.rst(s, None)
    assert not s or ret


def test_rst_include_nonexistent():
    with pytest.warns(UserWarning, match="Cannot include 'nonexistent.txt'"):
        docstrings.rst(".. include:: nonexistent.txt", None)

from pathlib import Path

from hypothesis import given
from hypothesis.strategies import text
import pytest

from pdoc import docstrings

# The important tests are in test_snapshot.py (and, by extension, testdata/)
# mostly some fuzzing here.


here = Path(__file__).parent.absolute()


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


@given(text())
def test_rst_extract_options_fuzz(s):
    content, options = docstrings._rst_extract_options(s)
    assert not s or content or options


def test_google_fenced_code_block():
    """Google section headers inside a fenced code block are left alone (#775)."""
    s = "Lorem dolor sit amet.\n\n```\nABC:\n    DEF\nGHI\n```\n"
    assert docstrings.google(s) == s

    s = "Args:\n    x: foo\n\n~~~\nABC:\n    DEF\n~~~\n\nReturns:\n    bar\n"
    ret = docstrings.google(s)
    assert "~~~\nABC:\n    DEF\n~~~" in ret
    assert "###### Arguments:" in ret
    assert "###### Returns:" in ret

    # a longer fence is only closed by a fence of at least the same length
    s = "````md\n```\nx\n```\nABC:\n    DEF\n````\n"
    assert docstrings.google(s) == s

    # unterminated fences are treated as regular text
    s = "```\nArgs:\n    x: foo\n"
    assert "###### Arguments:" in docstrings.google(s)


def test_convert_exception(monkeypatch):
    def raise_(*_):
        raise Exception

    monkeypatch.setattr(docstrings, "rst", raise_)
    with pytest.raises(RuntimeError, match="Docstring processing failed"):
        docstrings.convert(
            "Valid minimal docstring without in- or output.",
            "numpy",
            None,
        )


def test_rst_extract_options():
    content = (
        ":alpha: beta\n"
        ":charlie:delta:foxtrot\n"
        "rest of content\n"
        ":option ignored: as follows content\n"
    )
    content, options = docstrings._rst_extract_options(content)
    assert options == {
        "alpha": "beta",
        "charlie": "delta:foxtrot",
    }
    assert content == ("\nrest of content\n:option ignored: as follows content\n")


def test_rst_include_trim_lines():
    content = "alpha\nbeta\ncharlie\ndelta\necho"
    trimmed = docstrings._rst_include_trim(
        content, {"start-line": "2", "end-line": "4"}
    )
    assert trimmed == "charlie\ndelta"


def test_rst_include_trim_pattern():
    content = "alpha\nbeta\ncharlie\ndelta\necho"
    trimmed = docstrings._rst_include_trim(
        content, {"start-after": "beta", "end-before": "echo"}
    )
    assert trimmed == "\ncharlie\ndelta\n"


def test_rst_include_trim_start_after_applied_first():
    content = 'alpha\n"""\nbeta\ncharlie\ndelta\n"""\necho'
    trimmed = docstrings._rst_include_trim(
        content, {"start-after": '"""\n', "end-before": '"""'}
    )
    assert trimmed == "beta\ncharlie\ndelta\n"


def test_rst_include_trim_mixture():
    content = "alpha\nbeta\ncharlie\ndelta\necho"
    trimmed = docstrings._rst_include_trim(
        content, {"start-after": "beta", "end-line": "4"}
    )
    assert trimmed == "\ncharlie\ndelta"


def test_rst_include_nonexistent():
    with pytest.warns(UserWarning, match="Cannot include 'nonexistent.txt'"):
        docstrings.rst(".. include:: nonexistent.txt", None)


def test_rst_include_invalid_options():
    with pytest.warns(UserWarning, match="Failed to process include options"):
        docstrings.rst(
            ".. include:: ../README.md\n   :start-line: invalid",
            here / "test_docstrings.py",
        )

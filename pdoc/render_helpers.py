import os
import re
from contextlib import contextmanager
from functools import cache
from typing import Optional, Mapping, Container
from unittest.mock import patch

import markdown2
import pygments.formatters.html
import pygments.lexers.python
import pytest
from jinja2 import contextfilter
from jinja2.runtime import Context
from markupsafe import Markup

import pdoc

lexer = pygments.lexers.python.PythonLexer()
formatter = pygments.formatters.html.HtmlFormatter(cssclass="codehilite")


@cache
def highlight(code: str) -> str:
    return Markup(pygments.highlight(code, lexer, formatter))


@cache
def markdown(code: str) -> str:
    return markdown2.markdown(
        code,
        extras=[
            "fenced-code-blocks",
            "header-ids",
            "toc",
            "tables",
            "code-friendly",
        ],
    )


def split_identifier(all_modules: Container[str], fullname: str) -> tuple[str, str]:
    if not fullname:
        raise ValueError("Invalid identifier.")
    if fullname in all_modules:
        return fullname, ""
    else:
        parent, _, name = fullname.rpartition(".")
        modulename, qualname = split_identifier(all_modules, parent)
        if qualname:
            return modulename, f"{qualname}.{name}"
        else:
            return modulename, name


def _relative_link(current: list[str], target: list[str]) -> str:
    if target[: len(current)] == current:
        return "/".join(target[len(current):]) + ".html"
    else:
        return "../" + _relative_link(current[:-1], target)


@cache
def relative_link(current_module: str, target_module: str) -> str:
    if current_module == target_module:
        return ""
    return _relative_link(
        current_module.split(".")[:-1],
        target_module.split("."),
    )


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


@contextfilter
def linkify(context: Context, code: str) -> str:
    def linkify_repl(m: re.Match):
        fullname = m.group(0)
        try:
            module, qualname = split_identifier(context["all_modules"], fullname)
        except ValueError:
            return fullname
        else:
            return f'<a href="{relative_link(context["module"].modulename, module)}#{qualname}">{fullname}</a>'

    return Markup(
        re.sub(
            r"(?<![/a-zA-Z_0-9])(?!\d)[a-zA-Z_0-9]+\.[a-zA-Z_0-9.]+", linkify_repl, code
        )
    )


@contextfilter
def link(context: Context, spec: tuple[str, str], text: Optional[str] = None) -> str:
    modulename, qualname = spec
    fullname = f"{modulename}.{qualname}".rstrip(".")
    if modulename in context["all_modules"]:
        return Markup(
            f'<a href="{relative_link(context["module"].modulename, modulename)}#{qualname}">{text or fullname}</a>'
        )
    return text or fullname


def edit_url(mod: pdoc.doc.Module, mapping: Mapping[str, str]) -> Optional[str]:
    for m, prefix in mapping.items():
        if mod.modulename.startswith(m):
            filename = mod.modulename[len(m) + 1:].replace(".", "/")
            if mod.is_package:
                filename = f"{filename}/__init__.py".removeprefix("/")
            else:
                filename += ".py"
            return f"{prefix}{filename}".replace("//", "/")
    return None


@contextmanager
def defuse_unsafe_reprs():
    with (patch.object(os._Environ, "__repr__", lambda self: "os.environ")):
        yield

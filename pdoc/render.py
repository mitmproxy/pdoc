import base64
import os
import re
from contextlib import contextmanager
from functools import cache
from pathlib import Path
from typing import Optional
from unittest.mock import patch

import markdown2
import pygments.formatters.html
import pygments.lexers.python
import pygments.token
import pytest
from jinja2 import FileSystemLoader, Environment
from markupsafe import Markup

import pdoc.doc
from pdoc import extract

default_templates = Path(__file__).parent / "templates"

lexer = pygments.lexers.python.PythonLexer()
formatter = pygments.formatters.html.HtmlFormatter(cssclass="codehilite")
formatter.get_style_defs()

roots: list[str] = []
sort: bool = False
github_sources: dict[str, str] = {}


@cache
def highlight(code: str) -> str:
    return Markup(pygments.highlight(code, lexer, formatter))


@cache
def markdown(code: str) -> str:
    return markdown2.markdown(code, extras=[
        "fenced-code-blocks",
        "header-ids",
        "toc",
        "tables",
    ])


@cache
def split_identifier(refname: str) -> tuple[str, str]:
    if extract.module_exists(refname):
        return refname, ""
    else:
        parent, name = refname.rsplit(".", maxsplit=1)
        module_name, qualname = split_identifier(parent)
        return module_name, f"{qualname}.{name}".lstrip(".")


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


@cache
def linkify(code: str, current: str) -> str:
    def repl(m: re.Match):
        refname = m.group(0)
        if any(refname == root or refname.startswith(f"{root}.") for root in roots):
            module, qualname = split_identifier(refname)
            return (
                f'<a href="{relative_link(current, module)}#{qualname}">{refname}</a>'
            )
        return refname

    return Markup(re.sub(r"(?<![/a-zA-Z_0-9])(?!\d)[a-zA-Z_0-9]+\.[a-zA-Z_0-9.]+", repl, code))


@cache
def link(spec, current: str, text=None) -> str:
    module_name, qualname = spec
    refname = f"{module_name}.{qualname}".rstrip(".")
    if any(refname == root or refname.startswith(f"{root}.") for root in roots):
        return Markup(
            f'<a href="{relative_link(current, module_name)}#{qualname}">{text or refname}</a>'
        )
    return text or refname


def safe_repr(val):
    """Some values may raise in their __repr__"""
    try:
        return repr(val)
    except Exception:
        try:
            return str(val)
        except Exception:
            return "<unable to get value representation>"


@cache
def github_url(mod: pdoc.doc.Module) -> Optional[str]:
    for m, prefix in github_sources.items():
        if mod.module_name.startswith(m):
            filename = mod.module_name[len(m) + 1:].replace(".", "/")
            if mod.is_package:
                filename = f"{filename}/__init__.py".removeprefix("/")
            else:
                filename += ".py"
            return f"{prefix}{filename}".replace("//", "/")
    return None


env = Environment(
    loader=FileSystemLoader([default_templates]),
    autoescape=True,
)
env.filters["markdown"] = markdown
env.filters["highlight"] = highlight
env.filters["linkify"] = linkify
env.filters["link"] = link
env.filters["repr"] = safe_repr
env.filters["base64encode"] = lambda x: base64.b64encode(x.encode())
env.globals["github_url"] = github_url


def html_index() -> str:
    return env.get_template("html_index.jinja2").render(pdoc=pdoc)


def html_error(error: str, details: str = "") -> str:
    return env.get_template("html_error.jinja2").render(error=error, details=details, pdoc=pdoc)


def html_module(module: pdoc.doc.Module, mtime: Optional[str] = None) -> str:
    with mock_unsafe_reprs():
        return env.get_template("html_module.jinja2").render(
            module=module,
            pdoc=pdoc,
            mtime=mtime,
            show_module_list_link=len(roots) > 1,
        )


@contextmanager
def mock_unsafe_reprs():
    with (
            patch.object(os._Environ, "__repr__", lambda self: "os.environ")
    ):
        yield

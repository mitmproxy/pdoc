from __future__ import annotations

import os
import re
from contextlib import contextmanager
from typing import Optional, Mapping, Container
from unittest.mock import patch

import markdown2
import pygments.formatters.html
import pygments.lexers.python
from jinja2 import contextfilter
from jinja2.runtime import Context
from markupsafe import Markup

from ._compat import cache

lexer = pygments.lexers.python.PythonLexer()
"""
The pygments lexer used for pdoc.render_helpers.highlight.
Overwrite this to configure pygments lexing.
"""
formatter = pygments.formatters.html.HtmlFormatter(cssclass="codehilite")
"""
The pygments formatter used for pdoc.render_helpers.highlight. 
Overwrite this to configure pygments highlighting.
"""

markdown_extensions = [
    "fenced-code-blocks",
    "header-ids",
    "toc",
    "tables",
    "code-friendly",
    "footnotes",
]
"""
The default extensions loaded for markdown2."""


@cache
def highlight(code: str) -> str:
    """Highlight a piece of Python code using pygments."""
    return Markup(pygments.highlight(code, lexer, formatter))


@cache
def markdown(code: str) -> str:
    """Convert markdown to HTML using markdown2."""
    return markdown2.markdown(code, extras=markdown_extensions)


def split_identifier(all_modules: Container[str], fullname: str) -> tuple[str, str]:
    """
    Split an identifier into a `(modulename, qualname)` tuple. For example, `pdoc.render_helpers.split_identifier`
    would be split into `("pdoc.render_helpers","split_identifier")`. This is necessary to generate links to the
    correct module.
    """
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
    if target == current:
        return f"../{target[-1]}.html"
    elif target[: len(current)] == current:
        return "/".join(target[len(current) :]) + ".html"
    else:
        return "../" + _relative_link(current[:-1], target)


@cache
def relative_link(current_module: str, target_module: str) -> str:
    """Compute the relative link to another module's HTML file."""
    if current_module == target_module:
        return ""
    return _relative_link(
        current_module.split(".")[:-1],
        target_module.split("."),
    )


@contextfilter
def linkify(context: Context, code: str) -> str:
    """
    Link all identifiers in a block of text. Identifiers referencing unknown modules or modules that
    are not rendered at the moment will be ignored.
    A piece of text is considered to be an identifier if it either contains a `.` or is surrounded by `<code>` tags.
    """

    def linkify_repl(m: re.Match):
        fullname = m.group(0)
        try:
            module, qualname = split_identifier(context["all_modules"], fullname)
        except ValueError:
            return fullname
        else:
            if qualname:
                qualname = f"#{qualname}"
            return f'<a href="{relative_link(context["module"].modulename, module)}{qualname}">{fullname}</a>'

    return Markup(
        re.sub(
            r"""
            (?<!/)(?!\d)[a-zA-Z_0-9]+(?:\.(?!\d)[a-zA-Z_0-9]+)+  # foo.bar
            |
            (?<=<code>)(?!\d)[a-zA-Z_0-9]+(?=</code>)  # `foo`
            """,
            linkify_repl,
            code,
            flags=re.VERBOSE,
        )
    )


@contextfilter
def link(context: Context, spec: tuple[str, str], text: Optional[str] = None) -> str:
    """Create a link for a specific `(modulename, qualname)` tuple."""
    modulename, qualname = spec
    fullname = f"{modulename}.{qualname}".rstrip(".")
    if qualname:
        qualname = f"#{qualname}"
    if modulename in context["all_modules"]:
        return Markup(
            f'<a href="{relative_link(context["module"].modulename, modulename)}{qualname}">{text or fullname}</a>'
        )
    return text or fullname


def edit_url(
    modulename: str, is_package: bool, mapping: Mapping[str, str]
) -> Optional[str]:
    """Create a link to edit a particular file in the used version control system."""
    for m, prefix in mapping.items():
        if m == modulename or modulename.startswith(f"{m}."):
            filename = modulename[len(m) + 1 :].replace(".", "/")
            if is_package:
                filename = f"{filename}/__init__.py".lstrip("/")
            else:
                filename += ".py"
            return f"{prefix}{filename}"
    return None


@contextmanager
def defuse_unsafe_reprs():
    """This decorator is applied by pdoc before calling an object's repr().
    It applys some heuristics to patch our sensitive information.
    For example, `os.environ`'s default `__repr__` implementation exposes all
    local secrets.
    """
    with (patch.object(os._Environ, "__repr__", lambda self: "os.environ")):
        yield

import importlib.util
import re
from pathlib import Path

import markdown2
import pygments.formatters.html
import pygments.lexers.python
import pygments.token
import pytest
from jinja2 import FileSystemLoader, Environment
from markupsafe import Markup

import pdoc.doc

default_templates = Path(__file__).parent / "templates"
lexer = pygments.lexers.python.PythonLexer()
formatter = pygments.formatters.html.HtmlFormatter(cssclass="codehilite")
formatter.get_style_defs()

roots: list[str] = []
sort: bool = False


def highlight(code: str) -> str:
    return Markup(pygments.highlight(code, lexer, formatter))


def markdown(code: str) -> str:
    return Markup(markdown2.markdown(code, extras=["fenced-code-blocks"]))


def split_identifier(identifier: str) -> tuple[str, str]:
    try:
        ok = importlib.util.find_spec(identifier)
        if ok is None:
            raise ModuleNotFoundError()
    except Exception:
        parent, name = identifier.rsplit(".", maxsplit=1)
        module_name, qualname = split_identifier(parent)
        return module_name, f"{qualname}.{name}".lstrip(".")
    else:
        return identifier, ""


def _relative_link(current: list[str], target: list[str]) -> str:
    if target[: len(current)] == current:
        return "/".join(target[len(current):]) + ".html"
    else:
        return "../" + _relative_link(current[:-1], target)


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


def linkify(code: str, current: str) -> str:
    def repl(m: re.Match):
        refname = m.group(0)
        if any(refname == root or refname.startswith(f"{root}.") for root in roots):
            module, qualname = split_identifier(refname)
            return (
                f'<a href="{relative_link(current, module)}#{qualname}">{refname}</a>'
            )
        return refname

    return Markup(re.sub("[a-zA-Z_][a-zA-Z_0-9]*\.[a-zA-Z_0-9.]+", repl, code))


def link(spec, current: str, text=None) -> str:
    module_name, qualname = spec
    refname = f"{module_name}.{qualname}".rstrip(".")
    if any(refname == root or refname.startswith(f"{root}.") for root in roots):
        return Markup(
            f'<a href="{relative_link(current, module_name)}#{qualname}">{text or refname}</a>'
        )
    return refname


def safe_repr(val):
    """Some values may raise in their __repr__"""
    try:
        return repr(val)
    except Exception:
        try:
            return str(val)
        except Exception:
            return "<unable to get value representation>"


env = Environment(
    loader=FileSystemLoader([default_templates]),
    autoescape=True,
)
env.filters["markdown"] = markdown
env.filters["highlight"] = highlight
env.filters["linkify"] = linkify
env.filters["link"] = link
env.filters["repr"] = safe_repr


def html_index(module: pdoc.doc.Module) -> str:
    return env.get_template("html_index.jinja2").render(module=module, pdoc=pdoc)


def html_module(
        module: pdoc.doc.Module,
) -> str:
    return env.get_template("html_module.jinja2").render(module=module, pdoc=pdoc)

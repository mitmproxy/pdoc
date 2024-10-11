from __future__ import annotations

from collections.abc import Collection
from collections.abc import Iterable
from collections.abc import Mapping
from contextlib import contextmanager
from functools import cache
import html
import inspect
import os
import re
from unittest.mock import patch
import warnings

from jinja2 import ext
from jinja2 import nodes
import pygments.formatters
import pygments.lexers

try:
    # Jinja2 >= 3.0
    from jinja2 import pass_context  # type: ignore
except ImportError:  # pragma: no cover
    from jinja2 import contextfilter as pass_context  # type: ignore

from jinja2.runtime import Context
from markupsafe import Markup

import pdoc.markdown2

from . import docstrings

lexer = pygments.lexers.PythonLexer()
"""
The pygments lexer used for pdoc.render_helpers.highlight.
Overwrite this to configure pygments lexing.
"""

formatter = pygments.formatters.HtmlFormatter(
    cssclass="pdoc-code codehilite",
    linenos="inline",
    anchorlinenos=True,
)
"""
The pygments formatter used for pdoc.render_helpers.highlight.
Overwrite this to configure pygments highlighting of code blocks.

The usage of the `.codehilite` CSS selector in custom templates is deprecated since pdoc 10, use `.pdoc-code` instead.
"""

signature_formatter = pygments.formatters.HtmlFormatter(nowrap=True)
"""
The pygments formatter used for pdoc.render_helpers.format_signature.
Overwrite this to configure pygments highlighting of signatures.
"""

# Keep in sync with the documentation in pdoc/__init__.py!
markdown_extensions = {
    "alerts": None,
    "code-friendly": None,
    "cuddled-lists": None,
    "fenced-code-blocks": {"cssclass": formatter.cssclass},
    "footnotes": None,
    "header-ids": None,
    "link-patterns": None,
    "markdown-in-html": None,
    "mermaid": None,
    "pyshell": None,
    "strike": None,
    "tables": None,
    "task_list": None,
    "toc": {"depth": 2},
}
"""
The default extensions loaded for `markdown2`.
Overwrite this to configure Markdown rendering.
"""
markdown_link_patterns = [
    (
        re.compile(
            r"""
            \b
            (
                (?:https?://|(?<!//)www\.)    # prefix - https:// or www.
                \w[\w_\-]*(?:\.\w[\w_\-]*)*   # host
                [^<>\s"']*                    # rest of url
                (?<![?!.,:*_~);])             # exclude trailing punctuation
                (?=[?!.,:*_~);]?(?:[<\s]|$))  # make sure that we're not followed by " or ', i.e. we're outside of href="...".
            )
        """,
            re.X,
        ),
        r"\1",
    )
]
"""
Link pattern used for markdown2's [`link-patterns` extra](https://github.com/trentm/python-markdown2/wiki/link-patterns).
"""


@cache
def highlight(doc: pdoc.doc.Doc) -> str:
    """Highlight the source code of a documentation object using pygments."""
    if isinstance(doc, str):  # pragma: no cover
        warnings.warn(
            "Passing a string to the `highlight` render helper is deprecated, pass a pdoc.doc.Doc object instead.",
            DeprecationWarning,
        )
        return Markup(pygments.highlight(doc, lexer, formatter))

    # set up correct line numbers and anchors
    formatter.linespans = doc.qualname or "L"
    formatter.linenostart = doc.source_lines[0] + 1 if doc.source_lines else 1
    return Markup(pygments.highlight(doc.source, lexer, formatter))


def format_signature(sig: inspect.Signature, colon: bool) -> str:
    """Format and highlight a function signature using pygments. Returns HTML."""
    # First get a list with all params as strings.
    result = pdoc.doc._PrettySignature._params(sig)  # type: ignore
    return_annot = pdoc.doc._PrettySignature._return_annotation_str(sig)  # type: ignore

    multiline = (
        sum(len(x) + 2 for x in result) + len(return_annot)
        > pdoc.doc._PrettySignature.MULTILINE_CUTOFF
    )

    def _try_highlight(code: str) -> str:
        """Try to highlight a piece of code using pygments, but return the input as-is if pygments detects errors."""
        pretty = pygments.highlight(code, lexer, signature_formatter).strip()
        if '<span class="err">' not in pretty:
            return pretty
        else:
            return html.escape(code)

    # Next, individually highlight each parameter using pygments and wrap it in a span.param.
    # This later allows us to properly control line breaks.
    pretty_result = []
    for i, param in enumerate(result):
        pretty = _try_highlight(param)
        if multiline:
            pretty = f"""<span class="param">\t{pretty},</span>"""
        else:
            pretty = f"""<span class="param">{pretty}, </span>"""
        pretty_result.append(pretty)

    # remove last comma.
    if pretty_result:
        pretty_result[-1] = pretty_result[-1].rpartition(",")[0] + "</span>"

    # Add return annotation.
    anno = ")"
    if return_annot:
        anno += f" -> {_try_highlight(return_annot)}"
    if colon:
        anno += ":"
    if return_annot or colon:
        anno = f'<span class="return-annotation">{anno}</span>'

    rendered = "(" + "".join(pretty_result) + anno

    if multiline:
        rendered = f'<span class="signature pdoc-code multiline">{rendered}</span>'
    else:
        rendered = f'<span class="signature pdoc-code condensed">{rendered}</span>'

    return Markup(rendered)


@cache
def to_html(docstring: str) -> str:
    """
    Convert `docstring` from Markdown to HTML.
    """
    # careful: markdown2 returns a subclass of str with an extra
    # .toc_html attribute. don't further process the result,
    # otherwise this attribute will be lost.
    return pdoc.markdown2.markdown(  # type: ignore
        docstring,
        extras=markdown_extensions,
        link_patterns=markdown_link_patterns,
    )


@pass_context
def to_markdown_with_context(context: Context, docstring: str) -> str:
    """
    Converts `docstring` from a custom docformat to Markdown (if necessary), and then from Markdown to HTML.
    """
    module: pdoc.doc.Module = context["module"]
    docformat: str = context["docformat"]
    return to_markdown(docstring, module, docformat)


def to_markdown(docstring: str, module: pdoc.doc.Module, default_docformat: str) -> str:
    docformat = getattr(module.obj, "__docformat__", default_docformat) or ""
    return docstrings.convert(docstring, docformat, module.source_file)


def possible_sources(
    all_modules: Collection[str], identifier: str
) -> Iterable[tuple[str, str]]:
    """
    For a given identifier, return all possible sources where it could originate from.
    For example, assume `examplepkg._internal.Foo` with all_modules=["examplepkg"].
    This could be a Foo class in _internal.py, or a nested `class _internal: class Foo` in examplepkg.
    We return both candidates as we don't know if _internal.py exists.
    It may not be in all_modules because it's been excluded by `__all__`.
    However, if `examplepkg._internal` is in all_modules we know that it can only be that option.

    >>> possible_sources(["examplepkg"], "examplepkg.Foo.bar")
    examplepkg.Foo, bar
    examplepkg, Foo.bar
    """
    if identifier in all_modules:
        yield identifier, ""
        return

    modulename = identifier
    qualname = None
    while modulename:
        modulename, _, add = modulename.rpartition(".")
        qualname = f"{add}.{qualname}" if qualname else add
        yield modulename, qualname
        if modulename in all_modules:
            return
    raise ValueError(f"Invalid identifier: {identifier}")


def split_identifier(all_modules: Collection[str], fullname: str) -> tuple[str, str]:
    """
    Split an identifier into a `(modulename, qualname)` tuple. For example, `pdoc.render_helpers.split_identifier`
    would be split into `("pdoc.render_helpers","split_identifier")`. This is necessary to generate links to the
    correct module.
    """
    warnings.warn(
        "pdoc.render_helpers.split_identifier is deprecated and will be removed in a future release. "
        "Use pdoc.render_helpers.possible_sources instead.",
        DeprecationWarning,
    )
    *_, last = possible_sources(all_modules, fullname)
    return last


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


def qualname_candidates(identifier: str, context_qualname: str) -> list[str]:
    """
    Given an identifier in a current namespace, return all possible qualnames in the current module.
    For example, if we are in Foo's subclass Bar and `baz()` is the identifier,
    return `Foo.Bar.baz()`, `Foo.baz()`, and `baz()`.
    """
    end = len(context_qualname)
    ret = []
    while end > 0:
        ret.append(f"{context_qualname[:end]}.{identifier}")
        end = context_qualname.rfind(".", 0, end)
    ret.append(identifier)
    return ret


def module_candidates(identifier: str, current_module: str) -> Iterable[str]:
    """
    Given an identifier and the current module name, return the module names we should look at
    to find where the target object is exposed. Module names are ordered by preferences, i.e.
    we always prefer the current module and then top-level modules over their children.

    >>> module_candidates("foo.bar.baz", "qux")
    qux
    foo
    foo.bar
    foo.bar.baz
    >>> module_candidates("foo.bar.baz", "foo.bar")
    foo.bar
    foo
    foo.bar.baz
    """
    yield current_module

    end = identifier.find(".")
    while end > 0:
        if (name := identifier[:end]) != current_module:
            yield name
        end = identifier.find(".", end + 1)

    if identifier != current_module:
        yield identifier


@pass_context
def linkify(
    context: Context, code: str, namespace: str = "", shorten: bool = True
) -> str:
    """
    Link all identifiers in a block of text. Identifiers referencing unknown modules or modules that
    are not rendered at the moment will be ignored.
    A piece of text is considered to be an identifier if it either contains a `.` or is surrounded by `<code>` tags.

    If `shorten` is True, replace identifiers with short forms where possible.
    For example, replace "current_module.Foo" with "Foo". This is useful for annotations
    (which are verbose), but undesired for docstrings (where we want to preserve intent).
    """

    def linkify_repl(m: re.Match):
        """
        Resolve `text` to the most suitable documentation object.
        """
        text = m.group(0)
        plain_text = text.replace(
            '</span><span class="o">.</span><span class="n">', "."
        )
        identifier = plain_text.removesuffix("()")
        mod: pdoc.doc.Module = context["module"]

        # Check if this is a relative reference. These cannot be local and need to be resolved.
        if identifier.startswith("."):
            taken_from_mod = mod
            if namespace and (ns := mod.get(namespace)):
                # Imported from somewhere else, so the relative reference should be from the original module.
                taken_from_mod = context["all_modules"].get(ns.taken_from[0], mod)
            if taken_from_mod.is_package:
                # If we are in __init__.py, we want `.foo` to refer to a child module.
                parent_module = taken_from_mod.modulename
            else:
                # If we are in a leaf module, we want `.foo` to refer to the adjacent module.
                parent_module = taken_from_mod.modulename.rpartition(".")[0]
            while identifier.startswith(".."):
                identifier = identifier[1:]
                parent_module = parent_module.rpartition(".")[0]
            identifier = parent_module + identifier
        else:
            # Is this a local reference within this module?
            for qualname in qualname_candidates(identifier, namespace):
                doc = mod.get(qualname)
                if doc and context["is_public"](doc).strip():
                    return f'<a href="#{qualname}">{plain_text}</a>'

        # Is this a reference pointing straight at a module?
        if identifier in context["all_modules"]:
            return f'<a href="{relative_link(context["module"].modulename, identifier)}">{identifier}</a>'

        try:
            sources = list(possible_sources(context["all_modules"], identifier))
        except ValueError:
            # possible_sources did not find a parent module.
            return text

        # Try to find the actual target object so that we can then later verify
        # that objects exposed at a parent module with the same name point to it.
        target_object = None
        for module_name, qualname in sources:
            if doc := context["all_modules"].get(module_name, {}).get(qualname):
                target_object = doc.obj
                break

        # Look at the different modules where our target object may be exposed.
        for module_name in module_candidates(identifier, mod.modulename):
            module: pdoc.doc.Module | None = context["all_modules"].get(module_name)
            if not module:
                continue

            for _, qualname in sources:
                doc = module.get(qualname)
                # Check if they have an object with the same name,
                # and verify that it's pointing to the right thing and is public.
                if (
                    doc
                    and (target_object is doc.obj or target_object is None)
                    and context["is_public"](doc).strip()
                ):
                    if shorten:
                        if module == mod:
                            url_text = qualname
                        else:
                            url_text = doc.fullname
                        if plain_text.endswith("()"):
                            url_text += "()"
                    else:
                        url_text = plain_text
                    return f'<a href="{relative_link(context["module"].modulename, doc.modulename)}#{qualname}">{url_text}</a>'

        # No matches found.
        return text

    return Markup(
        re.sub(
            r"""
            # Part 1: foo.bar or foo.bar() (without backticks)
            (?<![/=?#&\.])  # heuristic: not part of a URL
            # First part of the identifier (e.g. "foo") - this is optional for relative references.
            (?:
                \b
                (?!\d)[a-zA-Z0-9_]+
                |
                \.*  # We may also start with multiple dots.
            )
            # Rest of the identifier (e.g. ".bar" or "..bar")
            (?:
                # A single dot or a dot surrounded with pygments highlighting.
                (?:\.|</span><span\ class="o">\.</span><span\ class="n">)
                (?!\d)[a-zA-Z0-9_]+
            )+
            (?:\(\)|\b(?!\(\)))  # we either end on () or on a word boundary.
            (?!</a>)  # not an existing link
            (?![/#])  # heuristic: not part of a URL

            | # Part 2: `foo` or `foo()`. `foo.bar` is already covered with part 1.
            (?<=<code>)
                 (?!\d)[a-zA-Z0-9_]+
            (?:\(\))?
            (?=</code>(?!</a>))
            """,
            linkify_repl,
            code,
            flags=re.VERBOSE,
        )
    )


@pass_context
def link(context: Context, spec: tuple[str, str], text: str | None = None) -> str:
    """Create a link for a specific `(modulename, qualname)` tuple."""
    mod: pdoc.doc.Module = context["module"]
    modulename, qualname = spec

    # Check if the object we are interested is also imported and re-exposed in the current namespace.
    # https://github.com/mitmproxy/pdoc/issues/490: We need to do this for every level, not just the tail.
    doc: pdoc.doc.Doc | None = mod
    for part in qualname.split("."):
        doc = doc.get(part) if isinstance(doc, pdoc.doc.Namespace) else None
        if not (
            doc
            and doc.taken_from[0] == modulename
            and context["is_public"](doc).strip()
        ):
            break
    else:
        # everything down to the tail is imported and re-exposed.
        if text:
            text = text.replace(f"{modulename}.", f"{mod.modulename}.")
        modulename = mod.modulename

    if mod.modulename == modulename:
        fullname = qualname
    else:
        fullname = f"{modulename}.{qualname}".removesuffix(".")

    if qualname:
        qualname = f"#{qualname}"
    if modulename in context["all_modules"]:
        return Markup(
            f'<a href="{relative_link(context["module"].modulename, modulename)}{qualname}">{text or fullname}</a>'
        )
    return text or fullname


def edit_url(
    modulename: str, is_package: bool, mapping: Mapping[str, str]
) -> str | None:
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


def root_module_name(all_modules: Mapping[str, pdoc.doc.Module]) -> str | None:
    """
    Return the name of the (unique) top-level module, or `None`
    if no such module exists.

    For example, assuming `foo`, `foo.bar`, and `foo.baz` are documented,
    this function will return `foo`. If `foo` and `bar` are documented,
    this function will return `None` as there is no unique top-level module.
    """
    shortest_name = min(all_modules, key=len, default=None)
    prefix = f"{shortest_name}."
    all_others_are_submodules = all(
        x.startswith(prefix) or x == shortest_name for x in all_modules
    )
    if all_others_are_submodules:
        return shortest_name
    else:
        return None


def minify_css(css: str) -> str:
    """Do some very basic CSS minification."""
    css = re.sub(r"[ ]{4}|\n|(?<=[:{}]) | (?=[{}])", "", css)
    css = re.sub(
        r"/\*.+?\*/", lambda m: m.group(0) if m.group(0).startswith("/*!") else "", css
    )
    return Markup(css.replace("<style", "\n<style"))


@contextmanager
def defuse_unsafe_reprs():
    """This decorator is applied by pdoc before calling an object's repr().
    It applies some heuristics to patch our sensitive information.
    For example, `os.environ`'s default `__repr__` implementation exposes all
    local secrets.
    """
    with patch.object(os._Environ, "__repr__", lambda self: "os.environ"):
        yield


class DefaultMacroExtension(ext.Extension):
    """
    This extension provides a new `{% defaultmacro %}` statement, which defines a macro only if it does not exist.

    For example,

    ```html+jinja
    {% defaultmacro example() %}
        test 123
    {% enddefaultmacro %}
    ```

    is equivalent to

    ```html+jinja
    {% macro default_example() %}
    test 123
    {% endmacro %}
    {% if not example %}
        {% macro example() %}
            test 123
        {% endmacro %}
    {% endif %}
    ```

    Additionally, the default implementation is also available as `default_$macroname`, which makes it possible
    to reference it in the override.
    """

    tags = {"defaultmacro"}

    def parse(self, parser):
        m = nodes.Macro(lineno=next(parser.stream).lineno)
        name = parser.parse_assign_target(name_only=True).name
        m.name = f"default_{name}"
        parser.parse_signature(m)
        m.body = parser.parse_statements(("name:enddefaultmacro",), drop_needle=True)

        if_stmt = nodes.If(
            nodes.Not(nodes.Name(name, "load")),
            [nodes.Macro(name, m.args, m.defaults, m.body)],
            [],
            [],
        )
        return [m, if_stmt]

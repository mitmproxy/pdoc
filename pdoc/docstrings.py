"""
This module handles the conversion of docstring flavors to Markdown.

The conversion from docstring flavors to Markdown is mostly done with regular expressions.
This is not particularly beautiful, but good enough for our purposes.
The alternative would be to depend on <https://github.com/rr-/docstring_parser> or a similar project,
but that introduces more complexity than we are comfortable with.

If you miss a particular feature for your favorite flavor, contributions are welcome.
That being said, please keep the complexity low and make sure that changes are
accompanied by matching snapshot tests in `test/testdata/`.
"""
from __future__ import annotations

import inspect
import re
import warnings
from pathlib import Path
from textwrap import dedent, indent

from ._compat import cache


@cache
def convert(docstring: str, docformat: str, source_file: Path | None) -> str:
    """
    Convert `docstring` from `docformat` to Markdown.
    """
    docformat = docformat.lower()

    if any(x in docformat for x in ["google", "numpy", "restructuredtext"]):
        docstring = rst(docstring, source_file)

    if "google" in docformat:
        docstring = google(docstring)

    if "numpy" in docformat:
        docstring = numpy(docstring)

    return docstring


def google(docstring: str) -> str:
    """Convert Google-style docstring sections into Markdown."""
    return re.sub(
        r"""
        ^(?P<name>[A-Z][A-Z a-z]+):\n
        (?P<contents>(
            \n        # empty lines
            |         # or
            [ \t]+.+  # lines with indentation
        )+)$
        """,
        _google_section,
        docstring,
        flags=re.VERBOSE | re.MULTILINE,
    )


GOOGLE_LIST_SECTIONS = ["Args", "Raises", "Attributes"]


def _google_section(m: re.Match[str]) -> str:
    name = m.group("name")
    contents = dedent(m.group("contents"))
    if name in GOOGLE_LIST_SECTIONS:
        items = _indented_list(contents)
        contents = ""
        for item in items:
            try:
                # first ":" on the first line
                _, attr, desc = re.split(r"^(.+?:)", item, maxsplit=1)
            except ValueError:
                contents += " - " + indent(item, "   ")[3:]
            else:
                contents += f" - **{attr}** " + indent(desc, "   ")[3:]
            contents += "\n"
    else:
        contents = indent(contents, "> ", lambda line: True)

    return f"\n###### {name}\n{contents}\n"


def _indented_list(contents: str) -> list[str]:
    """
    Convert a list string into individual (dedented) elements. For example,

    foo:
        desc
    bar: int
        more desc
    baz:
        desc
            indented

    returns [
        "foo:\ndesc",
        "bar: int\nmore desc",
        "baz:\ndesc\n    indented",
    ]
    """
    # we expect this to be through cleandoc() already.
    assert not contents.startswith(" ")
    assert not contents.startswith("\n")
    assert "\t" not in contents

    ret: list[str] = []
    for line in contents.splitlines(keepends=True):
        empty = not line.strip()
        indented = line.startswith(" ")
        if not (empty or indented):
            # new section
            ret.append(line)
        else:
            # append to current section
            ret[-1] += line

    return [inspect.cleandoc(x) for x in ret]


def numpy(docstring: str) -> str:
    """Convert NumPy-style docstring sections into Markdown.

    See <https://numpydoc.readthedocs.io/en/latest/format.html> for details.
    """
    sections = re.split(
        r"""
        ^([A-Z][A-Za-z ]+)\n  # a heading
        ---+\n+              # followed by a dashed line
        """,
        docstring,
        flags=re.VERBOSE | re.MULTILINE,
    )
    contents = sections[0]
    for heading, content in zip(sections[1::2], sections[2::2]):
        if content.startswith(" "):
            # If the first line of section content is indented, we consider the section to be finished
            # on the first non-indented line. We take out the rest - the tail - here.
            content, tail = re.split(r"\n(?![ \n])", content, maxsplit=1)
        else:
            tail = ""

        if heading in (
            "Parameters",
            "Returns",
            "Yields",
            "Receives",
            "Other Parameters",
            "Raises",
            "Warns",
            "Attributes",
        ):
            contents += f"###### {heading}\n{_numpy_parameters(content)}"
        elif heading == "See Also":
            contents += f"###### {heading}\n{_numpy_seealso(content)}"
        else:
            contents += f"###### {heading}\n{dedent(content)}"
        contents += tail
    return contents


def _numpy_seealso(content: str) -> str:
    """Convert a NumPy-style "See Also" section into Markdown"""
    contents = ""
    for item in _indented_list(content):
        if ":" in item:
            funcstr, desc = item.split(":", maxsplit=1)
            desc = f": {desc}"
        else:
            funcstr, desc = item, ""

        funclist = [f.strip() for f in funcstr.split(" ")]
        funcs = ", ".join(f"`{f}`" for f in funclist if f)
        contents += f"{funcs}{desc}  \n"
    return contents


def _numpy_parameters(content: str) -> str:
    """Convert a NumPy-style parameter section into Markdown"""
    contents = ""
    for item in _indented_list(content):
        m = re.match(r"^(.+):(.+)([\s\S]*)", item)
        if m:
            contents += (
                f" - **{m.group(1).strip()}** ({m.group(2).strip()}):\n"
                f"{indent(m.group(3).strip(), '   ')}\n"
            )
        else:
            if "\n" in item:
                name, desc = item.split("\n", maxsplit=1)
                name = name.strip()
                desc = desc.strip()
            else:
                name, desc = item.strip(), ""

            if desc:
                contents += f" - **{name}**: {desc}\n"
            else:
                contents += f" - **{name}**\n"
    return f"{contents}\n"


def rst(contents: str, source_file: Path | None) -> str:
    """
    Convert reStructuredText elements to Markdown.
    We support the most common elements, but we do not aim to mirror the full complexity of the spec here.
    """
    contents = _rst_admonitions(contents, source_file)
    contents = _rst_links(contents)

    # Code References: :obj:`foo` -> `foo`
    contents = re.sub(
        r"(:py)?:(mod|func|data|const|class|meth|attr|exc|obj):", "", contents
    )

    # Math: :math:`foo` -> \\( foo \\)
    # We don't use $ as that's not enabled by MathJax by default.
    contents = re.sub(r":math:`(.+?)`", r"\\\\( \1 \\\\)", contents)

    contents = _rst_footnotes(contents)

    contents = _rst_fields(contents)

    return contents


def _rst_footnotes(contents: str) -> str:
    """Convert reStructuredText footnotes"""
    footnotes: set[str] = set()
    autonum: int

    def register_footnote(m: re.Match[str]) -> str:
        nonlocal autonum
        fn_id = m.group("id")
        if fn_id in "*#":
            fn_id = f"fn-{autonum}"
            autonum += 1
        fn_id = fn_id.lstrip("#*")
        footnotes.add(fn_id)
        content = indent(m.group("content"), "   ").lstrip()
        return f"{m.group('indent')}[^{fn_id}]: {content}"

    # Register footnotes
    autonum = 1
    contents = re.sub(
        r"""
            ^(?P<indent>[ ]*)\.\.[ ]+\[(?P<id>\d+|[#*]\w*)](?P<content>.*
            (
                \n                 # empty lines
                |                  # or
                (?P=indent)[ ]+.+  # lines with indentation
            )*)$
            """,
        register_footnote,
        contents,
        flags=re.MULTILINE | re.VERBOSE,
    )

    def replace_references(m: re.Match[str]) -> str:
        nonlocal autonum
        fn_id = m.group("id")
        if fn_id in "*#":
            fn_id = f"fn-{autonum}"
            autonum += 1
        fn_id = fn_id.lstrip("#*")
        if fn_id in footnotes:
            return f"[^{fn_id}]"
        else:
            return m.group(0)

    autonum = 1
    contents = re.sub(r"\[(?P<id>\d+|[#*]\w*)]_", replace_references, contents)
    return contents


def _rst_links(contents: str) -> str:
    """Convert reStructuredText hyperlinks"""
    links = {}

    def register_link(m: re.Match[str]) -> str:
        refid = re.sub(r"\s", "", m.group("id").lower())
        links[refid] = m.group("url")
        return ""

    def replace_link(m: re.Match[str]) -> str:
        text = m.group("id")
        refid = re.sub(r"[\s`]", "", text.lower())
        try:
            return f"[{text.strip('`')}]({links[refid]})"
        except KeyError:
            return m.group(0)

    # Embedded URIs
    contents = re.sub(
        r"`(?P<text>[^`]+)<(?P<url>.+?)>`_", r"[\g<text>](\g<url>)", contents
    )
    # External Hyperlink Targets
    contents = re.sub(
        r"^\s*..\s+_(?P<id>[^\n:]+):\s*(?P<url>http\S+)",
        register_link,
        contents,
        flags=re.MULTILINE,
    )
    contents = re.sub(r"(?P<id>[A-Za-z0-9_\-.:+]|`[^`]+`)_", replace_link, contents)
    return contents


def _rst_admonitions(contents: str, source_file: Path | None) -> str:
    """
    Convert reStructuredText admonitions - a bit tricky because they may already be indented themselves.
    <https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html>
    """

    def _rst_admonition(m: re.Match[str]) -> str:
        ind = m.group("indent")
        type = m.group("type")
        val = m.group("val").strip()
        contents = dedent(m.group("contents")).strip()

        if type == "include":
            loc = source_file or Path(".")
            try:
                included = (loc.parent / val).read_text("utf8", "replace")
            except OSError as e:
                warnings.warn(f"Cannot include {val!r}: {e}")
                included = "\n"
            included = _rst_admonitions(included, loc.parent / val)
            return indent(included, ind)
        if type == "math":
            return f"{ind}$${val}{contents}$$\n"
        if type in ("note", "warning", "danger"):
            if val:
                heading = f"{ind}###### {val}\n"
            else:
                heading = ""
            return (
                f'{ind}<div class="pdoc-alert pdoc-alert-{type}" markdown="1">\n'
                f"{heading}"
                f"{indent(contents, ind)}\n"
                f"{ind}</div>\n"
            )
        elif type == "versionadded":
            text = f"New in version {val}"
        elif type == "versionchanged":
            text = f"Changed in version {val}"
        elif type == "deprecated":
            text = f"Deprecated since version {val}"
        else:
            text = f"{type} {val}".strip()

        if contents:
            text = f"{ind}*{text}:*\n{indent(contents, ind)}\n\n"
        else:
            text = f"{ind}*{text}.*\n"

        return text

    admonition = "note|warning|danger|versionadded|versionchanged|deprecated|seealso|math|include"
    return re.sub(
        rf"""
            ^(?P<indent>[ ]*)\.\.[ ]+(?P<type>{admonition})::(?P<val>.*)
            (?P<contents>(
                \n                 # empty lines
                |                  # or
                (?P=indent)[ ]+.+  # lines with indentation
            )*)$
        """,
        _rst_admonition,
        contents,
        flags=re.MULTILINE | re.VERBOSE,
    )


def _rst_fields(contents: str) -> str:
    """
    Convert reStructuredText fields to Markdown.
    <https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html#rst-field-lists>
    """

    _has_parameter_section = False
    _has_raises_section = False

    def _rst_field(m: re.Match[str]) -> str:
        type = m["type"]
        body = m["body"]

        if m["name"]:
            name = f"**{m['name'].strip()}**: "
        else:
            name = ""

        if type == "param":
            nonlocal _has_parameter_section
            text = f" - {name}{body}"
            if not _has_parameter_section:
                _has_parameter_section = True
                text = "\n###### Parameters\n" + text
            return text
        elif type == "type":
            return ""  # we expect users to use modern type annotations.
        elif type == "return":
            body = indent(body, "> ", lambda line: True)
            return f"\n###### Returns\n{body}"
        elif type == "rtype":
            return ""  # we expect users to use modern type annotations.
        elif type == "raises":
            nonlocal _has_raises_section
            text = f" - {name}{body}"
            if not _has_raises_section:
                _has_raises_section = True
                text = "\n###### Raises\n" + text
            return text
        else:  # pragma: no cover
            raise AssertionError("unreachable")

    field = "param|type|return|rtype|raises"
    return re.sub(
        rf"""
            ^:(?P<type>{field})(?:[ ]+(?P<name>.+))?:
            (?P<body>.*(
                (?:\n[ ]*)*  # maybe some empty lines followed by
                [ ]+.+       # lines with indentation
            )*(?:\n|$))
        """,
        _rst_field,
        contents,
        flags=re.MULTILINE | re.VERBOSE,
    )

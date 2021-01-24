"""
This module handles the conversion of docstring flavors to Markdown.

The conversion from docstring flavors to Markdown is mostly done with regular expressions.
This is not particularly beautiful, but good enough for our purposes.
The alternative would be to depend on <https://github.com/rr-/docstring_parser> or a similar project,
but that introduces more complexity than we are comfortable with.

If you miss a particular feature for your favorite flavor, contributions are welcome.
That being said, please keep the complexity low and make sure that changes are
accompanied by matching snapshot tests in test/testdata/.
"""
from __future__ import annotations

import re
from textwrap import indent, dedent

from ._compat import cache


@cache
def convert(docstring: str, docformat: str) -> str:
    """
    Convert `docstring` from `docformat` to Markdown.
    """
    docformat = docformat.lower()

    if any(x in docformat for x in ["google", "numpy", "restructuredtext"]):
        docstring = rst(docstring)

    if "google" in docformat:
        docstring = google(docstring)

    if "numpy" in docformat:
        docstring = numpy(docstring)

    return docstring


def google(docstring: str) -> str:
    """Convert Google-style docstring sections into Markdown."""
    return re.sub(
        r"""
        ^(?P<name>[A-Z][A-Za-z]+):\n
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


def _google_section(m: re.Match[str]) -> str:
    name = m.group("name")
    contents = dedent(m.group("contents"))
    if name in ("Args", "Raises", "Attributes"):
        items = _indented_list(contents)
        contents = ""
        for item in items:
            try:
                # last ":" on the first line
                _, attr, desc = re.split(r"^(.+:)", item, maxsplit=1)
            except ValueError:
                contents += " - " + indent(item, "   ")[3:]
            else:
                contents += f" - **{attr}** " + indent(desc, "   ")[3:]
    else:
        contents = indent(contents, "> ")

    return f"\n###### {name}\n{contents}\n"


def _indented_list(contents: str) -> list[str]:
    """
    Convert a list string into individual (dedented) elements. For example,

    foo:
        desc
    bar: int
        more desc

    returns [
        "foo:\ndesc",
        "bar: int\nmore desc",
    ]
    """
    # we expect this to be through cleandoc() already.
    assert not contents.startswith(" ")
    assert "\t" not in contents

    ret: list[str] = []
    for line in contents.splitlines(keepends=True):
        if not line.strip():
            ret[-1] += line
        elif not line.startswith(" "):
            # new section
            ret.append(line)
        else:
            ret[-1] += line.lstrip()
    return ret


def numpy(docstring: str) -> str:
    """Convert Numpy-style docstring sections into Markdown. """
    sections = re.split(
        r"""
        ^([A-Z][A-Za-z]+)\n  # a heading
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
            "Warnings",
            "Attributes",
        ):
            contents += f"###### {heading}\n" f"{_numpy_parameters(content)}"
        else:
            contents += f"###### {heading}\n" f"{dedent(content)}"
        contents += tail
    return contents


def _numpy_parameters(content: str) -> str:
    """Convert a numpy parameter section into Markdown"""
    contents = ""
    for item in _indented_list(content):
        if m := re.match(r"^(.+):(.+)([\s\S]*)", item):
            contents += (
                f" - **{m.group(1).strip()}** ({m.group(2).strip()}):\n"
                f"{indent(m.group(3).strip(), '   ')}\n"
            )
        else:
            x = item.split("\n", maxsplit=1)
            if len(x) == 1:
                contents += f" - **{x[0].strip()}**\n"
            else:
                contents += f" - **{x[0].strip()}**: {x[1].strip()}\n"
    return f"{contents}\n"


def rst(contents: str) -> str:
    """
    Convert reStructuredText elements to Markdown.
    We support the most common elements, but we do not aim to mirror the full complexity of the spec here.
    """
    contents = _rst_links(contents)

    # Code References: :obj:`foo` -> `foo`
    contents = re.sub(
        r"(:py)?:(mod|func|data|const|class|meth|attr|exc|obj):", "", contents
    )

    contents = _rst_admonitions(contents)

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
            return text

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


def _rst_admonitions(contents: str) -> str:
    """
    Convert reStructuredText admonitions - a bit tricky because they may already be indented themselves.
    https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html
    """
    admonition = "note|warning|versionadded|versionchanged|deprecated|seealso"
    return re.sub(
        rf"""
            ^(?P<indent>[ ]*)..[ ]+(?P<type>{admonition})::(?P<val>.*)
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


def _rst_admonition(m: re.Match[str]) -> str:
    ind = m.group("indent")
    type = m.group("type")
    val = m.group("val").strip()
    contents = dedent(m.group("contents")).strip()

    if type == "note":
        text = val or "Note"
    elif type == "warning":
        text = val or "Warning"
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

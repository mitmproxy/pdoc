import os
from pathlib import Path
from typing import Optional, Collection, Mapping, Literal

from jinja2 import FileSystemLoader, Environment

import pdoc.doc
from pdoc.render_helpers import (
    highlight,
    linkify,
    link,
    defuse_unsafe_reprs,
    edit_url,
    formatter,
    render_docstring,
)


def configure(
    *,
    template_directory: Optional[Path] = None,
    docformat: Optional[Literal["google", "numpy", "restructuredtext"]] = None,
    edit_url_map: Optional[Mapping[str, str]] = None,
):
    """
    Configure the rendering output.

    - `template_directory` can be used to set an additional (preferred) directory
      for templates. You can find an example in the main documentation of `pdoc`
      or in `test/customtemplate`.
    - `docformat` is the docstring flavor in use.
      pdoc prefers plain Markdown (the default), but also supports other formats.
    - `edit_url_map` is a mapping from module names to URL prefixes. For example,

        ```json
        {
            "pdoc": "https://github.com/mitmproxy/pdoc/blob/main/pdoc/"
        }
        ```

        renders the "Edit on GitHub" button on this page. The URL prefix can be modified to pin a particular version.
    """
    searchpath = _default_searchpath
    if template_directory:
        searchpath = [template_directory] + searchpath
    env.loader = FileSystemLoader(searchpath)

    env.globals["edit_url_map"] = edit_url_map or {}
    env.globals["docformat"] = docformat


def html_module(
    module: pdoc.doc.Module,
    all_modules: Collection[str],
    mtime: Optional[str] = None,
) -> str:
    """
    Renders the documentation for a `pdoc.doc.Module`.

    - `all_modules` is a list of all modules that are rendered in this invocation.
      This is used to determine which identifiers should be linked and which should not.
    - If `mtime` is given, include additional JavaScript on the page for live-reloading.
      This is only passed by `pdoc.web`.
    """
    with defuse_unsafe_reprs():
        return env.select_template(
            ["module.html.jinja2", "default/module.html.jinja2"]
        ).render(
            module=module,
            all_modules=all_modules,
            mtime=mtime,
            edit_url=edit_url(
                module.modulename, module.is_package, env.globals["edit_url_map"]
            ),
            pygments_css=formatter.get_style_defs(),
        )


def html_index(all_modules: Collection[str]) -> str:
    """Renders the module index."""
    return env.select_template(
        ["index.html.jinja2", "default/index.html.jinja2"]
    ).render(
        all_modules=[m for m in all_modules if "._" not in m],
    )


def html_error(error: str, details: str = "") -> str:
    """Renders an error message."""
    return env.select_template(
        ["index.html.jinja2", "default/error.html.jinja2"]
    ).render(
        error=error,
        details=details,
    )


@defuse_unsafe_reprs()
def repr_module(module: pdoc.doc.Module) -> str:
    """Renders `repr(pdoc.doc.Module)`, primarily used for tests and debugging."""
    with defuse_unsafe_reprs():
        return repr(module)


_default_searchpath = [
    Path(os.environ.get("XDG_CONFIG_HOME", "~/.config")).expanduser() / "pdoc",
    Path(__file__).parent / "templates",
]

env = Environment(
    loader=FileSystemLoader(_default_searchpath),
    autoescape=True,
    trim_blocks=True,
    lstrip_blocks=True,
)
"""
The Jinja2 environment used to render all templates.
You can modify this object to add custom filters and globals.
Examples can be found in this module's source code.
"""
env.filters["render_docstring"] = render_docstring
env.filters["highlight"] = highlight
env.filters["linkify"] = linkify
env.filters["link"] = link
env.globals["__version__"] = pdoc.__version__
env.globals["edit_url_map"] = {}
env.globals["docformat"] = ""

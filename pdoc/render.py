from __future__ import annotations

import os
import types
import warnings
from pathlib import Path
from typing import cast, Mapping

import jinja2
from jinja2 import Environment, FileSystemLoader

import pdoc.doc
import pdoc.docstrings
from pdoc._compat import Literal
from pdoc.render_helpers import (
    DefaultMacroExtension,
    defuse_unsafe_reprs,
    edit_url,
    highlight,
    link,
    linkify,
    minify_css,
    root_module_name,
    to_html,
    to_markdown_with_context,
)
from pdoc.search import make_index, precompile_index


def configure(
    *,
    docformat: Literal["markdown", "google", "numpy", "restructuredtext"] = "restructuredtext",
    edit_url_map: Mapping[str, str] | None = None,
    favicon: str | None = None,
    footer_text: str = "",
    logo: str | None = None,
    logo_link: str | None = None,
    math: bool = False,
    search: bool = True,
    show_source: bool = True,
    template_directory: Path | None = None,
):
    """
    Configure the rendering output.

    - `docformat` is the docstring flavor in use.
      pdoc prefers plain Markdown (the default), but also supports other formats.
    - `edit_url_map` is a mapping from module names to URL prefixes. For example,

        ```json
        {"pdoc": "https://github.com/mitmproxy/pdoc/blob/main/pdoc/"}
        ```

      renders the "Edit on GitHub" button on this page. The URL prefix can be modified to pin a particular version.
    - `favicon` is an optional path/URL for a favicon image
    - `footer_text` is additional text that should appear in the navigation footer.
    - `logo` is an optional URL to the project's logo image
    - `logo_link` is an optional URL the logo should point to
    - `math` enables math rendering by including MathJax into the rendered documentation.
    - `search` controls whether search functionality is enabled and a search index is built.
    - `show_source` controls whether a "View Source" button should be included in the output.
    - `template_directory` can be used to set an additional (preferred) directory
      for templates. You can find an example in the main documentation of `pdoc`
      or in `examples/custom-template`.
    """
    searchpath = _default_searchpath
    if template_directory:
        searchpath = [template_directory] + searchpath
    env.loader = FileSystemLoader(searchpath)

    env.globals["edit_url_map"] = edit_url_map or {}
    env.globals["docformat"] = docformat
    env.globals["math"] = math
    env.globals["show_source"] = show_source
    env.globals["favicon"] = favicon
    env.globals["logo"] = logo
    env.globals["logo_link"] = logo_link
    env.globals["footer_text"] = footer_text
    env.globals["search"] = search


@defuse_unsafe_reprs()
def html_module(
    module: pdoc.doc.Module,
    all_modules: Mapping[str, pdoc.doc.Module],
    mtime: str | None = None,
) -> str:
    """
    Renders the documentation for a `pdoc.doc.Module`.

    - `all_modules` contains all modules that are rendered in this invocation.
      This is used to determine which identifiers should be linked and which should not.
    - If `mtime` is given, include additional JavaScript on the page for live-reloading.
      This is only passed by `pdoc.web`.
    """
    return env.get_template("module.html.jinja2").render(
        module=module,
        all_modules=all_modules,
        root_module_name=root_module_name(all_modules),
        edit_url=edit_url(
            module.modulename,
            module.is_package,
            cast(Mapping[str, str], env.globals["edit_url_map"]),
        ),
        mtime=mtime,
    )


@defuse_unsafe_reprs()
def html_index(all_modules: Mapping[str, pdoc.doc.Module]) -> str:
    """Renders the module index."""
    return env.get_template("index.html.jinja2").render(
        all_modules=all_modules,
        root_module_name=root_module_name(all_modules),
    )


@defuse_unsafe_reprs()
def html_error(error: str, details: str = "") -> str:
    """Renders an error message."""
    return env.get_template("error.html.jinja2").render(
        error=error,
        details=details,
    )


@defuse_unsafe_reprs()
def search_index(all_modules: Mapping[str, pdoc.doc.Module]) -> str:
    """Renders the Elasticlunr.js search index."""
    if not env.globals["search"]:
        return ""
    # This is a rather terrible hack to determine if a given object is public and should be included in the index.
    module_template: jinja2.Template = env.get_template("module.html.jinja2")
    ctx: jinja2.runtime.Context = module_template.new_context(
        {"module": pdoc.doc.Module(types.ModuleType("")), "all_modules": all_modules}
    )
    for _ in module_template.root_render_func(ctx):  # type: ignore
        pass

    def is_public(x: pdoc.doc.Doc) -> bool:
        return bool(ctx["is_public"](x).strip())

    index = make_index(
        all_modules,
        is_public,
        cast(str, env.globals["docformat"]),
    )

    compile_js = Path(env.get_template("build-search-index.js").filename)  # type: ignore
    return env.get_template("search.js.jinja2").render(
        search_index=precompile_index(index, compile_js)
    )


@defuse_unsafe_reprs()
def repr_module(module: pdoc.doc.Module) -> str:
    """Renders `repr(pdoc.doc.Module)`, primarily used for tests and debugging."""
    return repr(module)


_default_searchpath = [
    Path(os.environ.get("XDG_CONFIG_HOME", "~/.config")).expanduser() / "pdoc",
    Path(__file__).parent / "templates",
    Path(__file__).parent / "templates" / "default",
    Path(__file__).parent / "templates" / "deprecated",
]

env = Environment(
    loader=FileSystemLoader(_default_searchpath),
    extensions=[DefaultMacroExtension],
    autoescape=True,
    trim_blocks=True,
    lstrip_blocks=True,
)
"""
The Jinja2 environment used to render all templates.
You can modify this object to add custom filters and globals.
"""
env.filters["to_markdown"] = to_markdown_with_context
env.filters["to_html"] = to_html
env.filters["highlight"] = highlight
env.filters["linkify"] = linkify
env.filters["link"] = link
env.filters["minify_css"] = minify_css
env.globals["__version__"] = pdoc.__version__
env.globals["env"] = os.environ
env.globals["warn"] = warnings.warn
configure()  # add default globals

import os
from pathlib import Path
from typing import Optional, Collection, Mapping

from jinja2 import FileSystemLoader, Environment

import pdoc.doc
from pdoc.render_helpers import (
    markdown,
    highlight,
    linkify,
    link,
    defuse_unsafe_reprs,
    edit_url,
    formatter,
)

_default_searchpath = [
    Path(os.environ.get("XDG_CONFIG_HOME", "~/.config")).expanduser() / "pdoc",
    Path(__file__).parent / "templates"
]

env = Environment(
    loader=FileSystemLoader(_default_searchpath),
    autoescape=True,
)
env.filters["markdown"] = markdown
env.filters["highlight"] = highlight
env.filters["linkify"] = linkify
env.filters["link"] = link
env.globals["__version__"] = pdoc.__version__
env.globals["edit_url_map"] = {}


def configure(
    *,
    template_directory: Optional[Path] = None,
    edit_url_map: Optional[Mapping[str, str]] = None,
):
    searchpath = _default_searchpath
    if template_directory:
        searchpath = [template_directory] + searchpath
    env.loader = FileSystemLoader(searchpath)

    env.globals["edit_url_map"] = edit_url_map or {}


def html_index(all_modules: Collection[str]) -> str:
    return env.select_template(["custom-index.html.jinja2", "index.html.jinja2"]).render(
        all_modules=[m for m in all_modules if "._" not in m],
    )


def html_error(error: str, details: str = "") -> str:
    return env.select_template(["custom-error.html.jinja2", "error.html.jinja2"]).render(
        error=error,
        details=details,
    )


@defuse_unsafe_reprs()
def html_module(
    module: pdoc.doc.Module,
    all_modules: Collection[str],
    mtime: Optional[str] = None,
) -> str:
    return env.select_template(["custom-module.html.jinja2", "module.html.jinja2"]).render(
        module=module,
        all_modules=all_modules,
        mtime=mtime,
        show_module_list_link=len(all_modules) > 1,
        edit_url=edit_url(module.modulename, module.is_package, env.globals["edit_url_map"]),
        pygments_css=formatter.get_style_defs(),
    )


@defuse_unsafe_reprs()
def repr_module(module: pdoc.doc.Module) -> str:
    return repr(module)

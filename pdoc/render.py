from pathlib import Path
from typing import Optional, Collection, Mapping

from jinja2 import FileSystemLoader, Environment

import pdoc
import pdoc.doc
from pdoc.render_helpers import markdown, highlight, linkify, link, defuse_unsafe_reprs, edit_url, formatter

env = Environment(
    loader=FileSystemLoader(Path(__file__).parent / "templates"),
    autoescape=True,
)
env.filters["markdown"] = markdown
env.filters["highlight"] = highlight
env.filters["linkify"] = linkify
env.filters["link"] = link


def html_index(all_modules: Collection[str]) -> str:
    return env.get_template("html_index.jinja2").render(
        all_modules=[m for m in all_modules if "._" not in m],
        __version__=pdoc.__version__,
    )


def html_error(error: str, details: str = "") -> str:
    return env.get_template("html_error.jinja2").render(
        error=error,
        details=details,
        __version__=pdoc.__version__,
    )


@defuse_unsafe_reprs()
def html_module(
    module: pdoc.doc.Module,
    all_modules: Collection[str],
    edit_url_map: Mapping[str, str],
    mtime: Optional[str] = None,
) -> str:
    return env.get_template("html_module.jinja2").render(
        module=module,
        all_modules=all_modules,
        mtime=mtime,
        show_module_list_link=len(all_modules) > 1,
        edit_url=edit_url(module, edit_url_map),
        pygments_css=formatter.get_style_defs(),
        __version__=pdoc.__version__,
    )

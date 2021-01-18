#!/usr/bin/env python3
import shutil
from pathlib import Path

import pygments.formatters.html
import pygments.lexers.python
from jinja2 import Environment, FileSystemLoader
from markupsafe import Markup

import pdoc.render_helpers

here = Path(__file__).parent

if __name__ == "__main__":
    demo = here / ".." / "test" / "snapshots" / "demo.py"
    env = Environment(loader=FileSystemLoader([here, here / ".." / "pdoc" / "templates"]), autoescape=True)

    lexer = pygments.lexers.python.PythonLexer()
    formatter = pygments.formatters.html.HtmlFormatter(style="friendly")
    pygments_css = formatter.get_style_defs()
    example_html = Markup(pygments.highlight(demo.read_text("utf8"), lexer, formatter))

    (here / "index.html").write_text(
        env.get_template("index.html.jinja2").render(
            example_html=example_html,
            pygments_css=pygments_css,
            __version__=pdoc.__version__
        ), "utf8"
    )

    if (here / "docs").is_dir():
        shutil.rmtree(here / "docs")
    pdoc.pdoc(
        "pdoc",
        demo,
        here / ".." / "test" / "snapshots" / "demo_long.py",
        output_directory=here / "docs",
    )

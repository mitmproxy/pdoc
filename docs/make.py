#!/usr/bin/env python3
import shutil
from pathlib import Path

import pygments.formatters.html
import pygments.lexers.python
from jinja2 import Environment, FileSystemLoader
from markupsafe import Markup

import pdoc.render

here = Path(__file__).parent

if __name__ == "__main__":
    demo = here / ".." / "test" / "testdata" / "demo.py"
    env = Environment(loader=FileSystemLoader([here, here / ".." / "pdoc" / "templates"]), autoescape=True)

    lexer = pygments.lexers.python.PythonLexer()
    formatter = pygments.formatters.html.HtmlFormatter(style="friendly")
    pygments_css = formatter.get_style_defs()
    example_html = Markup(pygments.highlight(demo.read_text("utf8"), lexer, formatter))

    (here / "index.html").write_bytes(
        env.get_template("index.html.jinja2").render(
            example_html=example_html,
            pygments_css=pygments_css,
            __version__=pdoc.__version__
        ).encode()
    )

    if (here / "docs").is_dir():
        shutil.rmtree(here / "docs")

    pdoc.render.configure(
        edit_url_map={
            "pdoc": "https://github.com/mitmproxy/pdoc/blob/main/pdoc/",
        }
    )

    pdoc.pdoc(
        "pdoc",
        demo,
        here / ".." / "test" / "testdata" / "demo_long.py",
        output_directory=here / "docs",
    )

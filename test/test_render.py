import pdoc.extract
import pdoc.render
import pdoc.doc
import pdoc.markup

import tutils


def test_html_module():
    with tutils.tdir():
        markup = pdoc.markup.Markdown()
        m = pdoc.extract.extract_module("./modules/one")
        assert pdoc.render.html_module(m, False, '/', False, markup)


def test_html_module_index():
    with tutils.tdir():
        roots = [
            pdoc.extract.extract_module("./modules/one"),
            pdoc.extract.extract_module("./modules/submods")
        ]
        markup = pdoc.markup.Markdown()
        assert pdoc.render.html_index(roots, markup)
import pdoc.extract
import pdoc.render_old
import pdoc.doc

import tutils


def test_html_module():
    with tutils.tdir():
        m = pdoc.extract.load_module("./modules/one")
        assert pdoc.render_old.html_module(m)


def test_html_module_index():
    with tutils.tdir():
        roots = [
            pdoc.extract.load_module("./modules/one"),
            pdoc.extract.load_module("./modules/submods"),
        ]
        assert pdoc.render_old.html_index(roots)

import pdoc.extract
import pdoc.render
import pdoc.doc

import tutils


def test_html_module():
    with tutils.tdir():
        m = pdoc.extract.extract_module("./modules/one")
        assert pdoc.render.html_module(m)


def test_html_module_index():
    with tutils.tdir():
        roots = [
            pdoc.extract.extract_module("./modules/one"),
            pdoc.extract.extract_module("./modules/submods")
        ]
        assert pdoc.render.html_index(roots)

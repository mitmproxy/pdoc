import pdoc.extract
import pdoc.render
import pdoc.doc

import tutils


def test_html_module():
    with tutils.tdir():
        m = pdoc.extract.extract_module("./modules/one")
        assert pdoc.render.html_module(pdoc.doc.Module(m))


def test_html_module_index():
    with tutils.tdir():
        assert pdoc.render.html_index(
            modules = [
                ("name", "desc"),
                ("name2", "desc2"),
            ]
        )
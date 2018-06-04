import pdoc.extract
import pdoc.render
import pdoc.doc

import tutils


def test_html():
    with tutils.tdir():
        m = pdoc.extract.extract_module("./modules/one")
        assert pdoc.render.html(pdoc.doc.Module(m))
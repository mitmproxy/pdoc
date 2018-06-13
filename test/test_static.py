import tutils

import pdoc.extract
import pdoc.static


def test_static_single(tmpdir):
    with tutils.tdir():
        m = pdoc.extract.extract_module("./modules/one")
        pdoc.static.html_out(tmpdir, m)
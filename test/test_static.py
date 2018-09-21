import pytest
import tutils
import pathlib

import pdoc.extract
import pdoc.static


@pytest.mark.parametrize(
    "modspec,ident,path",
    [
        ("./modules/one", "one", "one.html"),
        ("./modules/dirmod", "dirmod", "dirmod.html"),
        ("./modules/submods", "submods", "submods/index.html"),
        ("./modules/submods", "submods.two", "submods/two.html"),
        ("./modules/submods", "submods.three", "submods/three.html"),
        ("./modules/index", "index", "index/index.html"),
        ("./modules/index", "index.index", "index/index.m.html"),
    ]
)
def test_module_path(modspec, ident, path):
    with tutils.tdir():
        root = pdoc.extract.extract_module(modspec)
        submod = root.find_ident(ident)

        mp = pdoc.static.module_to_path(submod)
        assert mp == pathlib.Path(path)


def test_static(tmpdir):
    dst = pathlib.Path(str(tmpdir))
    with tutils.tdir():
        one = pdoc.extract.extract_module("./modules/one")
        two = pdoc.extract.extract_module("./modules/submods")
        assert not pdoc.static.would_overwrite(dst, [one])
        assert not pdoc.static.would_overwrite(dst, [one, two])
        pdoc.static.html_out(dst, [one])
        assert pdoc.static.would_overwrite(dst, [one])
        assert pdoc.static.would_overwrite(dst, [one, two])
        pdoc.static.html_out(dst, [one, two])
        assert pdoc.static.would_overwrite(dst, [one])
        assert pdoc.static.would_overwrite(dst, [one, two])

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
        assert mp == pathlib.PosixPath(path)

        retmod = pdoc.static.path_to_module(root, mp)
        assert retmod.name == submod.name

        retmod = pdoc.static.path_to_module(root, mp.with_suffix(""))
        assert retmod.name == submod.name


def test_path_to_module():
    with tutils.tdir():
        root = pdoc.extract.extract_module("./modules/submods")
        with pytest.raises(pdoc.static.StaticError):
            pdoc.static.path_to_module(root, pathlib.Path("nonexistent"))


def test_static_single(tmpdir):
    dst = pathlib.Path(tmpdir)
    with tutils.tdir():
        m = pdoc.extract.extract_module("./modules/one")
        assert not pdoc.static.would_overwrite(dst, m)
        pdoc.static.html_out(dst, m)
        assert pdoc.static.would_overwrite(dst, m)
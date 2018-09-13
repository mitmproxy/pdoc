import pathlib
import typing

import pdoc.render
import pdoc.doc


class StaticError(Exception):
    pass


def module_to_path(m: pdoc.doc.Module) -> pathlib.Path:
    """
        Calculates the filesystem path for the static output of a given module.
    """
    p = pathlib.Path(*m.name.split("."))
    if m.submodules:
        p /= "index.html"
    else:
        if p.stem == "index":
            p = p.with_suffix(".m.html")
        else:
            p = p.with_suffix(".html")
    return p


def path_to_module(
    roots: typing.Sequence[pdoc.doc.Module], path: pathlib.Path
) -> pdoc.doc.Module:
    """
        Retrieves the matching module for a given path from a module tree.
    """
    if path.suffix == ".html":
        path = path.with_suffix("")
    parts = list(path.parts)
    if parts[-1] == "index":
        parts = parts[:-1]
    elif parts[-1] == "index.m":
        parts[-1] = "index"
    for root in roots:
        mod = root.find_ident(".".join(parts))
        if isinstance(mod, pdoc.doc.Module):
            return mod
    raise StaticError("No matching module for {path}".format(path=path))


def would_overwrite(dst: pathlib.Path, roots: typing.Sequence[pdoc.doc.Module]) -> bool:
    """
        Would rendering root to dst overwrite any file?
    """
    if len(roots) > 1:
        p = dst / "index.html"
        if p.exists():
            return True
    for root in roots:
        for m in root.allmodules():
            p = dst.joinpath(module_to_path(m))
            if p.exists():
                return True
    return False


def html_out(
    dst: pathlib.Path,
    roots: typing.Sequence[pdoc.doc.Module],
    external_links: bool = True,
    link_prefix: str = "",
    source: bool = False,
):
    if len(roots) > 1:
        p = dst / "index.html"
        idx = pdoc.render.html_index(roots, link_prefix=link_prefix)
        p.write_text(idx, encoding="utf-8")
    for root in roots:
        for m in root.allmodules():
            p = dst.joinpath(module_to_path(m))
            p.parent.mkdir(parents=True, exist_ok=True)
            out = pdoc.render.html_module(
                m, external_links=external_links, link_prefix=link_prefix, source=source
            )
            p.write_text(out, encoding="utf-8")

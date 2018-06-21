import pathlib

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


def path_to_module(root: pdoc.doc.Module, path: pathlib.Path) -> pdoc.doc.Module:
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
    mod = root.find_ident(".".join(parts))
    if not isinstance(mod, pdoc.doc.Module):
        raise StaticError(f"No matching module for {path}")
    return mod


def would_overwrite(dst: pathlib.Path, root: pdoc.doc.Module) -> bool:
    """
        Would rendering root to dst overwrite any file?
    """
    for m in root.allmodules():
        p = dst.joinpath(module_to_path(m))
        if p.exists():
            return True
    return False


def html_out(
    dst: pathlib.Path,
    root: pdoc.doc.Module,
    external_links: bool = True,
    link_prefix: str = "",
    source: bool = False,
):
    for m in root.allmodules():
        p = dst.joinpath(module_to_path(m))
        p.parent.mkdir(parents=True, exist_ok=True)
        out = pdoc.render.html_module(
            m, external_links=external_links, link_prefix=link_prefix, source=source
        )
        p.write_text(out, encoding="utf-8")

import importlib
import importlib.util
import os
import pkgutil
from typing import Any, Sequence, Optional

import pdoc.doc


class ExtractError(Exception):
    pass


def split_module_spec(spec: str) -> tuple[str, str]:
    """
    Splits a module specification into a base path (which may be empty), and a module name.

    Raises ExtactError if the spec is invalid.
    """
    if not spec:
        raise ExtractError("Empty module spec.")
    if (os.sep in spec) or (os.altsep and os.altsep in spec):
        dirname, filename = os.path.split(spec)
        if filename.endswith(".py"):
            mname, _ = os.path.splitext(filename)
            return dirname, mname
        else:
            if "." in filename:
                raise ExtractError(
                    f"Invalid module name {filename}. Mixing path and module specifications is not supported."
                )
            return dirname, filename
    else:
        return "", spec


def load_module(basedir: str, module: str) -> tuple[Any, bool]:
    """
    Returns a module object, and whether the module is a package or not.
    """
    ispackage = False
    if basedir:
        mods = module.split(".")
        dirname = os.path.join(basedir, *mods[:-1])
        modname = mods[-1]

        pkgloc = os.path.join(dirname, modname, "__init__.py")
        fileloc = os.path.join(dirname, modname + ".py")

        if os.path.exists(pkgloc):
            location, ispackage = pkgloc, True
        elif os.path.exists(fileloc):
            location, ispackage = fileloc, False
        else:
            raise ExtractError(f"Module {module} not found in {basedir}")

        ispec = importlib.util.spec_from_file_location(modname, location)
        mobj = importlib.util.module_from_spec(ispec)
        try:
            # This can literally raise anything
            ispec.loader.exec_module(mobj)  # type: ignore
        except Exception as e:
            raise ExtractError(f"Error importing {location}: {e}")
        return mobj, ispackage
    else:
        try:
            # This can literally raise anything
            m = importlib.import_module(module)
        except ImportError:
            raise ExtractError(f"Module not found: {module}")
        except Exception as e:
            raise ExtractError(f"Error importing {module}: {e}")
        # This is the only case where we actually have to test whether we're a package
        if getattr(m, "__package__", False) and getattr(m, "__path__", False):
            ispackage = True
        return m, ispackage


def submodules(dname: str, mname: str) -> Sequence[str]:
    """
    Returns a list of fully qualified submodules within a package, given a
    base directory and a fully qualified module name.
    """
    loc = os.path.join(dname, *mname.split("."))
    ret = []
    for mi in pkgutil.iter_modules([loc], prefix=mname + "."):
        ret.append(mi.name)
    ret.sort()
    return ret


def _extract_module(
    dname: str, mname: str, parent: Optional[pdoc.doc.Module] = None
) -> pdoc.doc.Module:
    m, pkg = load_module(dname, mname)
    mod = pdoc.doc.Module(mname, m, parent)
    #if pkg:
    #    for i in submodules(dname, mname):
    #        mod.submodules.append(_extract_module(dname, i, parent=mod))
    return mod


def extract_module(spec: str) -> pdoc.doc.Module:
    """
    Extracts and returns a module object. The spec argument can have the
    following forms:

    Simple module: "foo.bar"
    Module path: "./path/to/module"
    File path: "./path/to/file.py"

    This function always invalidates caches to enable hot load and reload.

    May raise ExtactError.
    """
    importlib.invalidate_caches()
    dname, mname = split_module_spec(spec)
    return _extract_module(dname, mname)

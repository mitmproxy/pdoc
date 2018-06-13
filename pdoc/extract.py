import os
import typing
import importlib

import pdoc.doc


class ExtractError(Exception):
    pass


def _load_module(spec: str) -> (typing.Any, bool):
    """
        Returns a module object, and whether the module is a package or not.
    """
    ispackage = False
    if (os.sep in spec) or (os.altsep and os.altsep in spec):
        if spec.endswith(".py"):
            mname = os.path.splitext(os.path.basename(spec))[0]
            location = spec
            if not os.path.isfile(location):
                raise ExtractError("File not found: %s" % location)
            ispackage = False
        else:
            mname = os.path.basename(spec)
            if "." in mname:
                raise ExtractError(
                    f"Invalid module name {mname}. "
                    "Mixing path and module specifications is not supported."
                )
            if os.path.isfile(spec + ".py"):
                location = spec + ".py"
                ispackage = False
            elif os.path.isfile(os.path.join(spec, "__init__.py")):
                location = os.path.join(spec, "__init__.py")
                ispackage = True
            else:
                raise ExtractError(f"Module not found: {spec}")
        ispec = importlib.util.spec_from_file_location(mname, location)
        module = importlib.util.module_from_spec(ispec)
        # This can literally raise anything
        try:
            ispec.loader.exec_module(module)
        except Exception as e:
            raise ExtractError(f"Error importing {spec}: {e}")
        return module, ispackage
    else:
        try:
            m = importlib.import_module(spec)
        except ModuleNotFoundError:
            raise ExtractError(f"Module not found: {spec}")
        # This is the only case where we actually have to test whether we're a package
        return m, ispackage


def extract_module(spec: str):
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
    m, _ = _load_module(spec)
    return pdoc.doc.Module(m)

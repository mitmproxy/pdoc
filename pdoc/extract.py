import os
import importlib


class ExtractError(Exception):
    pass


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
    if (os.sep in spec) or (os.altsep and os.altsep in spec):
        if spec.endswith(".py"):
            mname = os.path.splitext(os.path.basename(spec))[0]
            location = spec
            if not os.path.isfile(location):
                raise ExtractError("File not found: %s" % location)
        else:
            mname = os.path.basename(spec)
            if "." in mname:
                raise ExtractError(
                    f"Invalid module name {mname}. "
                    "Mixing path and module specifications is not supported."
                )
            if os.path.isfile(spec + ".py"):
                location = spec + ".py"
            elif os.path.isfile(os.path.join(spec, "__init__.py")):
                location = os.path.join(spec, "__init__.py")
            else:
                raise ExtractError(f"Module not found: {spec}")
        ispec = importlib.util.spec_from_file_location(mname, location)
        module = importlib.util.module_from_spec(ispec)
        # This can literally raise anything
        try:
            ispec.loader.exec_module(module)
        except Exception as e:
            raise ExtractError(f"Error importing {spec}: {e}")
        return module
    else:
        try:
            return importlib.import_module(spec)
        except ModuleNotFoundError:
            raise ExtractError(f"Module not found: {spec}")

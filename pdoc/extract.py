"""
This module handles the interaction with Python's module system,
that is it loads the correct module based on whatever the user specified,
and provides the rest of pdoc with some additional module metadata.
"""
import importlib
import importlib.util
import io
import linecache
import os
import pkgutil
import platform
import subprocess
import sys
import sysconfig
import types
import warnings
from contextlib import contextmanager
from functools import partial
from pathlib import Path
from typing import Union, Optional, Iterable, Literal, Collection
from unittest.mock import patch


@contextmanager
def mock_some_common_side_effects():
    """
    This context manager is applied when importing modules. It mocks some common side effects that may happen upon
    module import. For example, importing the builtin `antigravity` module normally causes a webbrowser to open,
    which we want to suppress. Note that this function must not be used for security purposes, it's easily bypassable.
    """
    _popen = subprocess.Popen

    if platform.system() == "Windows":
        noop = "echo.exe"
    else:
        noop = "echo"

    with (
        patch(
            "subprocess.Popen", new_callable=lambda: partial(_popen, executable=noop)
        ),
        patch("sys.stdout", new_callable=lambda: io.StringIO()),
        patch("sys.stderr", new_callable=lambda: io.StringIO()),
        patch("sys.stdin", new_callable=lambda: io.StringIO()),
    ):
        yield


@mock_some_common_side_effects()
def parse_specs(modules: Iterable[Union[Path, str]]) -> dict[str, Literal[None]]:
    """
    This function processes a list of module specifications and returns a list of module names
    that should be included in the module index.

    FIXME: more doc
    """
    module_index = {}
    if modules:
        for spec in modules:
            modname = parse_spec(spec)
            module_index[modname] = True

            # try to get all submodules
            try:
                path = importlib.util.find_spec(modname).submodule_search_locations
                if path is None:  # not a package
                    continue
            except Exception:
                warnings.warn(f"Cannot find spec for {modname} (from {spec})")
            else:
                submodules = pkgutil.walk_packages(path, f"{modname}.")
                while True:
                    try:
                        module_index[next(submodules).name] = None
                    except StopIteration:
                        break
                    except Exception as e:
                        warnings.warn(f"Error importing subpackage: {e!r}")
    else:
        stdlib = sysconfig.get_path("stdlib")
        platstdlib = sysconfig.get_path("platstdlib")
        for m in pkgutil.iter_modules():
            if m.name.startswith("_"):
                continue
            if m.module_finder.path in (stdlib, platstdlib):
                continue
            module_index[m.name] = None

    if not module_index:
        raise ValueError("No valid module specifications found.")

    return module_index


def parse_spec(spec: Union[Path, str]) -> str:
    """
    This functions parses a user's module specification into a module identifier that can be imported.
    A module specification can either be the name of an installed module, or the path to a specific file or package.
    For example, the following strings are valid module specifications:

     - typing
     - collections.abc
     - ./test/snapshots/demo.py
     - ./test/snapshots/demopackage

    *This function has side-effects:* `sys.path` will be amended if the specification is a path.
    If this side-effect is undesired, pass a module name instead.
    """
    # isinstance check is required as Path is not iterable.
    if not isinstance(spec, Path) and (
        os.sep in spec or (os.altsep and os.altsep in spec)
    ):
        spec = Path(spec)

    if isinstance(spec, Path):
        if str(spec.parent) not in sys.path:
            sys.path.insert(0, str(spec.parent))
        return spec.name.removesuffix(".py")
    else:
        return spec


@mock_some_common_side_effects()
def load_module(module: str) -> types.ModuleType:
    """Try to import a module without side-effects. If import fails, a RuntimeError is raised.

    Returns: The module."""
    try:
        return importlib.import_module(module)
    except BaseException as e:
        raise RuntimeError(f"Error importing {module}.") from e


def module_exists(modulename: str) -> bool:
    """Returns `True` if the specified module exists, `False` otherwise."""
    try:
        spec = importlib.util.find_spec(modulename)
    except Exception:
        return False
    else:
        return spec is not None


def module_mtime(modulename: str) -> Optional[float]:
    """Returns the time the specified module file was last modified, or `None` if this cannot be determined.
    The primary use of this is live-reloading modules on modification."""
    try:
        spec = importlib.util.find_spec(modulename)
        if spec is not None and spec.origin is not None:
            return Path(spec.origin).stat().st_mtime
    except Exception:
        pass
    return None


def invalidate_caches(modules: Collection[str]) -> None:
    """
    Invalidate all module caches to allow live-reloading of modules.
    Getting this right is tricky – we remove a bunch of stuff from `sys.modules`, which sometimes causes surprising
    side-effects.
    """
    importlib.invalidate_caches()
    linecache.clearcache()
    sys.modules = {
        name: mod
        for name, mod in sys.modules.items()
        if not name in modules
    }

import importlib
import importlib.util
import io
import os
import subprocess
import sys
import types
from contextlib import contextmanager
from functools import cache, partial
from pathlib import Path
from typing import Union, Optional, Iterable
from unittest.mock import patch

import pdoc.doc


@cache
def parse_spec(spec: Union[Path, str]) -> str:
    """
    Splits a module specification into a base path (which may be empty), and a module name.
    """
    if os.sep in spec or (os.altsep and os.altsep in spec):
        spec = Path(spec)

    if isinstance(spec, Path):
        if str(spec.parent) not in sys.path:
            sys.path.insert(0, str(spec.parent))
        return spec.name.removesuffix(".py")
    else:
        return spec


@contextmanager
def mock_some_common_side_effects():
    _popen = subprocess.Popen

    with (
            patch("subprocess.Popen", new_callable=lambda: partial(_popen, executable="echo.exe")),
            patch("sys.stdout", new_callable=lambda: io.StringIO()),
            patch("sys.stderr", new_callable=lambda: io.StringIO()),
            patch("sys.stdin", new_callable=lambda: io.StringIO()),
            patch.object(os._Environ, "__repr__", lambda self: "os.environ")
    ):
        yield


def _import_module(module: str) -> types.ModuleType:
    """
    Returns a module object, and whether the module is a package or not.
    """

    try:
        with mock_some_common_side_effects():
            return importlib.import_module(module)
    except BaseException as e:
        raise RuntimeError(f"Error importing {module}.") from e


def extract_module(module: str) -> pdoc.doc.Module:
    module = _import_module(module)
    return pdoc.doc.Module(module)


@cache
def module_exists(module_name: str) -> bool:
    try:
        spec = importlib.util.find_spec(module_name)
    except Exception:
        return False
    else:
        return spec is not None


def module_mtime(module_name: str) -> Optional[float]:
    try:
        spec = importlib.util.find_spec(module_name)
        if spec is not None and spec.origin is not None:
            return Path(spec.origin).stat().st_mtime
    except Exception:
        pass
    return None


def invalidate_caches(roots) -> None:
    pass
    # importlib.invalidate_caches()
    # sys.modules = {
    #    name: mod
    #    for name, mod in sys.modules.items()
    #    if not any(name.startswith(root) for root in roots)
    # }


def all_submodules(module_name: str) -> Iterable[str]:
    pass

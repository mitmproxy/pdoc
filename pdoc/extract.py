import importlib
import importlib.util
import io
import linecache
import os
import platform
import subprocess
import sys
import types
from contextlib import contextmanager
from functools import cache, partial
from pathlib import Path
from typing import Union, Optional
from unittest.mock import patch


@cache
def parse_spec(spec: Union[Path, str]) -> str:
    """
    Splits a module specification into a base path (which may be empty), and a module name.
    """
    # first check required as Path is not iterable.
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


@contextmanager
def mock_some_common_side_effects():
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


def load_module(module: str) -> types.ModuleType:
    try:
        with mock_some_common_side_effects():
            return importlib.import_module(module)
    except BaseException as e:
        raise RuntimeError(f"Error importing {module}.") from e


def module_exists(modulename: str) -> bool:
    try:
        spec = importlib.util.find_spec(modulename)
    except Exception:
        return False
    else:
        return spec is not None


def module_mtime(modulename: str) -> Optional[float]:
    try:
        spec = importlib.util.find_spec(modulename)
        if spec is not None and spec.origin is not None:
            return Path(spec.origin).stat().st_mtime
    except Exception:
        pass
    return None


def invalidate_caches(roots: list[str]) -> None:
    importlib.invalidate_caches()
    linecache.clearcache()
    sys.modules = {
        name: mod
        for name, mod in sys.modules.items()
        if not any(name.startswith(root) for root in roots)
    }

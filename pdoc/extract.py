"""
This module handles the interaction with Python's module system,
that is it loads the correct module based on whatever the user specified,
and provides the rest of pdoc with some additional module metadata.
"""
from __future__ import annotations

import importlib
import importlib.util
import io
import linecache
import os
import pkgutil
import platform
import subprocess
import sys
import traceback
import types
import warnings
from contextlib import contextmanager
from functools import partial
from pathlib import Path
from typing import Callable, Iterable, Iterator, Optional, Sequence, Union
from unittest.mock import patch

from . import doc_ast

AnyException = (SystemExit, GeneratorExit, Exception)
"""BaseException, but excluding KeyboardInterrupt.

Modules may raise SystemExit on import (which we want to catch),
but we don't want to catch a user's KeyboardInterrupt.
"""


@contextmanager
def mock_some_common_side_effects():
    """
    This context manager is applied when importing modules. It mocks some common side effects that may happen upon
    module import. For example, importing the builtin `antigravity` module normally causes a webbrowser to open,
    which we want to suppress. Note that this function must not be used for security purposes, it's easily bypassable.
    """
    _popen = subprocess.Popen

    if platform.system() == "Windows":  # pragma: no cover
        noop_exe = "echo.exe"
    else:  # pragma: no cover
        noop_exe = "echo"

    def noop(*args, **kwargs):
        pass

    with patch("subprocess.Popen", new=partial(_popen, executable=noop_exe)), patch(
        "os.startfile", new=noop, create=True
    ), patch("sys.stdout", new=io.StringIO()), patch(
        "sys.stderr", new=io.StringIO()
    ), patch(
        "sys.stdin", new=io.StringIO()
    ):
        yield


def parse_specs(modules: Sequence[Union[Path, str]]) -> dict[str, None]:
    """
    This function processes a list of module specifications and returns the list of module names, including all
    submodules, that should be processed by pdoc.
    """
    module_index: dict[str, None] = {}
    for spec in modules:
        modname = parse_spec(spec)

        try:
            with mock_some_common_side_effects():
                modspec = importlib.util.find_spec(modname)
                if modspec is None:
                    raise ModuleNotFoundError(modname)
        except AnyException:
            warnings.warn(
                f"Cannot find spec for {modname} (from {spec}):\n{traceback.format_exc()}",
                RuntimeWarning,
                stacklevel=2,
            )
        else:
            mod_info = pkgutil.ModuleInfo(
                None,  # type: ignore
                name=modname,
                ispkg=bool(modspec.submodule_search_locations),
            )
            for m in walk_packages2([mod_info]):
                module_index[m.name] = None

    if not module_index:
        raise ValueError(f"Module not found: {', '.join(str(x) for x in modules)}.")

    return module_index


def _all_submodules(modulename: str) -> bool:
    return True


def walk_packages2(
    modules: Iterable[pkgutil.ModuleInfo],
    module_filter: Callable[[str], bool] = _all_submodules,
) -> Iterator[pkgutil.ModuleInfo]:
    """
    For a given list of modules, recursively yield their names and all their submodules' names.

    This function is similar to pkgutil.walk_packages, but respects a package's __all__ attribute if specified.
    If __all__ is defined, submodules not listed in __all__ are excluded.
    """

    # noinspection PyDefaultArgument
    def seen(p, m={}):  # pragma: no cover
        if p in m:
            return True
        m[p] = True

    for mod in modules:
        # is __all__ defined and the module not in __all__?
        if not module_filter(mod.name.rpartition(".")[2]):
            continue

        yield mod

        if mod.ispkg:
            try:
                module = load_module(mod.name)
            except RuntimeError:
                warnings.warn(
                    f"Error loading {mod.name}:\n{traceback.format_exc()}",
                    RuntimeWarning,
                )
                continue

            mod_all: list[str] = getattr(module, "__all__", None)
            if mod_all is not None:
                filt = mod_all.__contains__
            else:
                filt = _all_submodules

            # don't traverse path items we've seen before
            path = [p for p in (getattr(module, "__path__", None) or []) if not seen(p)]

            yield from walk_packages2(pkgutil.iter_modules(path, f"{mod.name}."), filt)


def parse_spec(spec: Union[Path, str]) -> str:
    """
    This functions parses a user's module specification into a module identifier that can be imported.
    A module specification can either be the name of an installed module, or the path to a specific file or package.
    For example, the following strings are valid module specifications:

     - typing
     - collections.abc
     - ./test/testdata/demo_long.py
     - ./test/testdata/demopackage

    *This function has side-effects:* `sys.path` will be amended if the specification is a path.
    If this side-effect is undesired, pass a module name instead.
    """
    # isinstance check is required as Path is not iterable.
    if not isinstance(spec, Path) and (
        os.sep in spec or (os.altsep and os.altsep in spec)
    ):
        spec = Path(spec)

    if isinstance(spec, Path):
        if (spec.parent / "__init__.py").exists():
            return parse_spec(spec.parent) + f".{spec.stem}"
        if str(spec.parent) not in sys.path:
            sys.path.insert(0, str(spec.parent))
        return spec.stem
    else:
        return spec


@mock_some_common_side_effects()
def load_module(module: str) -> types.ModuleType:
    """Try to import a module. If import fails, a RuntimeError is raised.

    Returns the imported module."""
    try:
        return importlib.import_module(module)
    except AnyException as e:
        raise RuntimeError(f"Error importing {module}") from e


@mock_some_common_side_effects()
def module_mtime(modulename: str) -> Optional[float]:
    """Returns the time the specified module file was last modified, or `None` if this cannot be determined.
    The primary use of this is live-reloading modules on modification."""
    try:
        spec = importlib.util.find_spec(modulename)
    except AnyException:
        pass
    else:
        if spec is not None and spec.origin is not None:
            return Path(spec.origin).stat().st_mtime
    return None


def invalidate_caches(module_name: str) -> None:
    """
    Invalidate module cache to allow live-reloading of modules.
    """
    # Getting this right is tricky – reloading modules causes a bunch of surprising side-effects.
    # Our current best effort is to call `importlib.reload` on all modules that start with module_name.
    # We also exclude our own dependencies, which cause fun errors otherwise.
    if module_name not in sys.modules:
        return
    if any(
        module_name.startswith(f"{x}.") or x == module_name
        for x in ("jinja2", "markupsafe", "markdown2", "pygments")
    ):
        return

    # a more extreme alternative:
    # filename = sys.modules[module_name].__file__
    # if (
    #    filename.startswith(sysconfig.get_path("platstdlib"))
    #    or filename.startswith(sysconfig.get_path("stdlib"))
    # ):
    #     return

    importlib.invalidate_caches()
    linecache.clearcache()
    doc_ast.get_source.cache_clear()

    prefix = f"{module_name}."
    mods = sorted(
        mod for mod in sys.modules if module_name == mod or mod.startswith(prefix)
    )
    for modname in mods:
        if modname == "pdoc.render":
            # pdoc.render is stateful after configure(), so we don't want to reload it.
            continue
        try:
            if not isinstance(sys.modules[modname], types.ModuleType):
                continue  # some funky stuff going on - one example is typing.io, which is a class.
            with mock_some_common_side_effects():
                importlib.reload(sys.modules[modname])
        except AnyException:
            warnings.warn(
                f"Error reloading {modname}:\n{traceback.format_exc()}",
                RuntimeWarning,
                stacklevel=2,
            )

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
import re
import shutil
import subprocess
import sys
import traceback
import types
import warnings
from collections.abc import Callable, Iterable, Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

import pdoc
import pdoc.doc_ast
import pdoc.docstrings


def walk_specs(specs: Sequence[Path | str]) -> list[str]:
    """
    This function processes a list of module specifications and returns a collection of module names, including all
    submodules, that should be processed by pdoc.

    A module specification can either be the name of an installed module, or the path to a specific file or package.
    For example, the following strings are valid module specifications:

     - `typing`
     - `collections.abc`
     - `./test/testdata/demo_long.py`
     - `./test/testdata/demopackage`

    *This function has side effects:* See `parse_spec`.
    """
    all_modules: dict[str, None] = {}
    for spec in specs:

        if isinstance(spec, str) and spec.startswith("!"):
            ignore_pattern = re.compile(spec[1:])
            all_modules = {
                k: v for k, v in all_modules.items() if not ignore_pattern.match(k)
            }
            continue

        modname = parse_spec(spec)

        try:
            with mock_some_common_side_effects():
                modspec = importlib.util.find_spec(modname)
                if modspec is None:
                    raise ModuleNotFoundError(modname)
        except AnyException:
            warnings.warn(
                f"Cannot find spec for {modname} (from {spec}):\n{traceback.format_exc()}",
                stacklevel=2,
            )
        else:
            mod_info = pkgutil.ModuleInfo(
                None,  # type: ignore
                name=modname,
                ispkg=bool(modspec.submodule_search_locations),
            )
            for m in walk_packages2([mod_info]):
                if m.name in all_modules:
                    warnings.warn(
                        f"The module specification {spec!r} adds a module named {m.name}, but a module with this name "
                        f"has already been added. You may have accidentally repeated a module spec, or you are trying "
                        f"to document two modules with the same filename from two different directories, which does "
                        f"not work. Only one documentation page will be generated."
                    )
                all_modules[m.name] = None

    if not all_modules:
        raise ValueError(
            f"No modules found matching spec: {', '.join(str(x) for x in specs)}"
        )

    return list(all_modules)


def parse_spec(spec: Path | str) -> str:
    """
    This functions parses a user's module specification into a module identifier that can be imported.
    If both a local file/directory and an importable module with the same name exist, a warning will be printed.

    *This function has side effects:* `sys.path` will be amended if the specification is a path.
    If this side effect is undesired, pass a module name instead.
    """
    pspec = Path(spec)
    if isinstance(spec, str) and (os.sep in spec or (os.altsep and os.altsep in spec)):
        # We have a path separator, so it's definitely a filepath.
        spec = pspec

    if isinstance(spec, str) and (pspec.is_file() or (pspec / "__init__.py").is_file()):
        # We have a local file with this name, but is there also a module with the same name?
        try:
            with mock_some_common_side_effects():
                modspec = importlib.util.find_spec(spec)
                if modspec is None:
                    raise ModuleNotFoundError
        except AnyException:
            # Module does not exist, use local file.
            spec = pspec
        else:
            # Module does exist. We now check if the local file/directory is the same (e.g. after pip install -e),
            # and emit a warning if that's not the case.
            origin = (
                Path(modspec.origin).absolute() if modspec.origin else Path("unknown")
            )
            local_dir = Path(spec).absolute()
            if local_dir not in (origin, origin.parent):
                warnings.warn(
                    f"{spec!r} may refer to either the installed Python module or the local file/directory with the "
                    f"same name. pdoc will document the installed module, prepend './' to force documentation of the "
                    f"local file/directory.\n"
                    f" - Module location: {origin}\n"
                    f" - Local file/directory: {local_dir}",
                    RuntimeWarning,
                )

    if isinstance(spec, Path):
        if (spec.parent / "__init__.py").exists():
            return parse_spec(spec.resolve().parent) + f".{spec.stem}"
        parent_dir = str(spec.parent)
        sys.path = [parent_dir] + [x for x in sys.path if x != parent_dir]
        if spec.stem in sys.modules and sys.modules[spec.stem].__file__:
            local_dir = spec.resolve()
            file = sys.modules[spec.stem].__file__
            assert file is not None  # make mypy happy
            origin = Path(file).resolve()
            if local_dir not in (origin, origin.parent, origin.with_suffix("")):
                warnings.warn(
                    f"pdoc cannot load {spec.stem!r} because a module with the same name is already imported in pdoc's "
                    f"Python process. pdoc will document the loaded module from {origin} instead.",
                    RuntimeWarning,
                )
        return spec.stem
    else:
        return spec


def _noop(*args, **kwargs):
    pass


class PdocDefusedPopen(subprocess.Popen):
    if platform.system() == "Windows":  # pragma: no cover
        _noop_exe = "echo.exe"
    else:  # pragma: no cover
        _noop_exe = "echo"

    def __init__(self, *args, **kwargs):  # pragma: no cover
        command_allowed = (
            args
            and args[0]
            and args[0][0]
            in (
                # these invocations may all come from https://github.com/python/cpython/blob/main/Lib/ctypes/util.py,
                # which we want to keep working.
                "/sbin/ldconfig",
                "ld",
                shutil.which("gcc") or shutil.which("cc"),
                shutil.which("objdump"),
            )
        )
        if not command_allowed:
            kwargs["executable"] = self._noop_exe
        super().__init__(*args, **kwargs)


@contextmanager
def mock_some_common_side_effects():
    """
    This context manager is applied when importing modules. It mocks some common side effects that may happen upon
    module import. For example, `import antigravity` normally causes a web browser to open, which we want to suppress.

    Note that this function must not be used for security purposes, it's easily bypassable.
    """
    with patch("subprocess.Popen", new=PdocDefusedPopen), patch(
        "os.startfile", new=_noop, create=True
    ), patch("sys.stdout", new=io.StringIO()), patch(
        "sys.stderr", new=io.StringIO()
    ), patch(
        "sys.stdin", new=io.StringIO()
    ):
        yield


@mock_some_common_side_effects()
def load_module(module: str) -> types.ModuleType:
    """Try to import a module. If import fails, a RuntimeError is raised.

    Returns the imported module."""
    try:
        return importlib.import_module(module)
    except AnyException as e:
        raise RuntimeError(f"Error importing {module}") from e


AnyException = (SystemExit, GeneratorExit, Exception)
"""BaseException, but excluding KeyboardInterrupt.

Modules may raise SystemExit on import (which we want to catch),
but we don't want to catch a user's KeyboardInterrupt.
"""


def _all_submodules(modulename: str) -> bool:
    return True


def walk_packages2(
    modules: Iterable[pkgutil.ModuleInfo],
    module_filter: Callable[[str], bool] = _all_submodules,
) -> Iterator[pkgutil.ModuleInfo]:
    """
    For a given list of modules, recursively yield their names and all their submodules' names.

    This function is similar to `pkgutil.walk_packages`, but respects a package's `__all__` attribute if specified.
    If `__all__` is defined, submodules not listed in `__all__` are excluded.
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
                warnings.warn(f"Error loading {mod.name}:\n{traceback.format_exc()}")
                continue

            mod_all = getattr(module, "__all__", None)
            if mod_all is not None:
                filt = mod_all.__contains__
            else:
                filt = _all_submodules

            # don't traverse path items we've seen before
            path = [p for p in (getattr(module, "__path__", None) or []) if not seen(p)]

            yield from walk_packages2(pkgutil.iter_modules(path, f"{mod.name}."), filt)


def module_mtime(modulename: str) -> float | None:
    """Returns the time the specified module file was last modified, or `None` if this cannot be determined.
    The primary use of this is live-reloading modules on modification."""
    try:
        with mock_some_common_side_effects():
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
    # Getting this right is tricky – reloading modules causes a bunch of surprising side effects.
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
    pdoc.doc.Module.from_name.cache_clear()
    pdoc.doc_ast._get_source.cache_clear()
    pdoc.docstrings.convert.cache_clear()

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
                stacklevel=2,
            )

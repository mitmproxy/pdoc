"""
This module handles the interaction with Python's module system,
that is it loads the correct module based on whatever the user specified,
and provides the rest of pdoc with some additional module metadata.
"""

from __future__ import annotations

from collections.abc import Iterable
from collections.abc import Iterator
from collections.abc import Sequence
from contextlib import contextmanager
import importlib.util
import io
import linecache
import os
from pathlib import Path
import pkgutil
import platform
import re
import shutil
import subprocess
import sys
import traceback
import types
from unittest.mock import patch
import warnings

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
        if spec.name == "__init__.py":
            spec = spec.parent
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


class _PdocDefusedPopen(subprocess.Popen):
    """A small wrapper around subprocess.Popen that converts most executions into no-ops."""

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
                # https://github.com/mitmproxy/pdoc/issues/430: GitPython invokes git commands, which is also fine.
                "git",
            )
        )
        if not command_allowed and os.environ.get("PDOC_ALLOW_EXEC", "") == "":
            # sys.stderr is patched, so we need to unpatch it for printing a warning.
            with patch("sys.stderr", new=sys.__stderr__):
                warnings.warn(
                    f"Suppressed execution of {args[0]!r} during import. "
                    f"Set PDOC_ALLOW_EXEC=1 as an environment variable to allow subprocess execution.",
                    stacklevel=2,
                )
            kwargs["executable"] = self._noop_exe
        super().__init__(*args, **kwargs)


@contextmanager
def mock_some_common_side_effects():
    """
    This context manager is applied when importing modules. It mocks some common side effects that may happen upon
    module import. For example, `import antigravity` normally causes a web browser to open, which we want to suppress.

    Note that this function must not be used for security purposes, it's easily bypassable.
    """
    with (
        patch("subprocess.Popen", new=_PdocDefusedPopen),
        patch("os.startfile", new=_noop, create=True),
        patch("sys.stdout", new=io.TextIOWrapper(io.BytesIO())),
        patch("sys.stderr", new=io.TextIOWrapper(io.BytesIO())),
        patch("sys.stdin", new=io.TextIOWrapper(io.BytesIO())),
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


def iter_modules2(module: types.ModuleType) -> dict[str, pkgutil.ModuleInfo]:
    """
    Returns all direct child modules of a given module.
    This function is similar to `pkgutil.iter_modules`, but

      1. Respects a package's `__all__` attribute if specified.
         If `__all__` is defined, submodules not listed in `__all__` are excluded.
      2. It will try to detect submodules that are not findable with iter_modules,
         but are present in the module object.
    """
    mod_all = getattr(module, "__all__", None)

    submodules = {}

    for submodule in pkgutil.iter_modules(
        getattr(module, "__path__", []), f"{module.__name__}."
    ):
        name = submodule.name.rpartition(".")[2]
        if mod_all is None or name in mod_all:
            submodules[name] = submodule

    # 2023-12: PyO3 and pybind11 submodules are not detected by pkgutil
    # This is a hacky workaround to register them.
    members = dir(module) if mod_all is None else mod_all
    for name in members:
        if name in submodules or name == "__main__" or not isinstance(name, str):
            continue
        member = getattr(module, name, None)
        is_wild_child_module = (
            isinstance(member, types.ModuleType)
            # the name is either just "bar", but can also be "foo.bar",
            # see https://github.com/PyO3/pyo3/issues/759#issuecomment-1811992321
            and (
                member.__name__ == f"{module.__name__}.{name}"
                or (
                    member.__name__ == name
                    and sys.modules.get(member.__name__, None) is not member
                )
            )
        )
        if is_wild_child_module:
            # fixup the module name so that the rest of pdoc does not break
            assert member
            member.__name__ = f"{module.__name__}.{name}"
            sys.modules[f"{module.__name__}.{name}"] = member
            submodules[name] = pkgutil.ModuleInfo(
                None,  # type: ignore
                name=f"{module.__name__}.{name}",
                ispkg=True,
            )

    submodules.pop("__main__", None)  # https://github.com/mitmproxy/pdoc/issues/438

    return submodules


def walk_packages2(
    modules: Iterable[pkgutil.ModuleInfo],
) -> Iterator[pkgutil.ModuleInfo]:
    """
    For a given list of modules, recursively yield their names and all their submodules' names.

    This function is similar to `pkgutil.walk_packages`, but based on `iter_modules2`.
    """
    # the original walk_packages implementation has a recursion check for path, but that does not seem to be needed?
    for mod in modules:
        yield mod

        if mod.ispkg:
            try:
                module = load_module(mod.name)
            except RuntimeError:
                warnings.warn(f"Error loading {mod.name}:\n{traceback.format_exc()}")
                continue

            submodules = iter_modules2(module)
            yield from walk_packages2(submodules.values())


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

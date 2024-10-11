"""
This module is responsible for patching `pdoc.doc.Doc` objects with type annotations found
in `.pyi` type stub files ([PEP 561](https://peps.python.org/pep-0561/)).
This makes it possible to add type hints for native modules such as modules written using [PyO3](https://pyo3.rs/).
"""

from __future__ import annotations

from functools import cache
import importlib.util
from pathlib import Path
import sys
import traceback
import types
import typing
from unittest import mock
import warnings

from pdoc import doc

overload_docstr = typing.overload(lambda: None).__doc__


@cache
def find_stub_file(module_name: str) -> Path | None:
    """Try to find a .pyi file with type stubs for the given module name."""
    module_path = module_name.replace(".", "/")

    # Find .pyi-file in a PEP 0561 compatible stub-package
    module_part_name = module_name.split(".")
    module_part_name[0] = f"{module_part_name[0]}-stubs"
    module_stub_path = "/".join(module_part_name)

    for search_dir in sys.path:
        file_candidates = [
            Path(search_dir) / (module_path + ".pyi"),
            Path(search_dir) / (module_path + "/__init__.pyi"),
            Path(search_dir) / (module_stub_path + ".pyi"),
            Path(search_dir) / (module_stub_path + "/__init__.pyi"),
        ]
        for f in file_candidates:
            if f.exists():
                return f
    return None


def _import_stub_file(module_name: str, stub_file: Path) -> types.ModuleType:
    """
    Import the type stub outside of the normal import machinery.

    Note that currently, for objects imported by the stub file, the _original_ module
    is used and not the corresponding stub file.
    """
    sys.path_hooks.append(
        importlib.machinery.FileFinder.path_hook(
            (importlib.machinery.SourceFileLoader, [".pyi"])
        )
    )
    try:
        loader = importlib.machinery.SourceFileLoader(module_name, str(stub_file))
        spec = importlib.util.spec_from_file_location(
            module_name, stub_file, loader=loader
        )
        assert spec is not None
        m = importlib.util.module_from_spec(spec)
        loader.exec_module(m)
        return m
    finally:
        sys.path_hooks.pop()


def _prepare_module(ns: doc.Namespace) -> None:
    """
    Touch all lazy properties that are accessed in `_patch_doc` to make sure that they are precomputed.
    We want to do this in advance while sys.modules is not monkeypatched yet.
    """

    # at the moment, .members is the only lazy property that is accessed.
    for member in ns.members.values():
        if isinstance(member, doc.Class):
            _prepare_module(member)


def _patch_doc(target_doc: doc.Doc, stub_mod: doc.Module) -> None:
    """
    Patch the target doc (a "real" Python module, e.g. a ".py" file)
    with the type information from stub_mod (a ".pyi" file).
    """
    if target_doc.qualname:
        stub_doc = stub_mod.get(target_doc.qualname)
        if stub_doc is None:
            return
    else:
        stub_doc = stub_mod

    if isinstance(target_doc, doc.Function) and isinstance(stub_doc, doc.Function):
        # pyi files have functions where all defs have @overload.
        # We don't want to pick up the docstring from the typing helper.
        if stub_doc.docstring == overload_docstr:
            stub_doc.docstring = ""

        target_doc.signature = stub_doc.signature
        target_doc.funcdef = stub_doc.funcdef
        target_doc.docstring = stub_doc.docstring or target_doc.docstring
    elif isinstance(target_doc, doc.Variable) and isinstance(stub_doc, doc.Variable):
        target_doc.annotation = stub_doc.annotation
        target_doc.docstring = stub_doc.docstring or target_doc.docstring
    elif isinstance(target_doc, doc.Namespace) and isinstance(stub_doc, doc.Namespace):
        target_doc.docstring = stub_doc.docstring or target_doc.docstring
        for m in target_doc.members.values():
            _patch_doc(m, stub_mod)
    else:
        warnings.warn(
            f"Error processing type stub for {target_doc.fullname}: "
            f"Stub is a {stub_doc.kind}, but target is a {target_doc.kind}."
        )


def include_typeinfo_from_stub_files(module: doc.Module) -> None:
    """Patch the provided module with type information from a matching .pyi file."""
    # Check if module is a stub module itself - we don't want to recurse!
    module_file = str(
        doc._safe_getattr(sys.modules.get(module.modulename), "__file__", "")
    )
    if module_file.endswith(".pyi"):
        return

    stub_file = find_stub_file(module.modulename)
    if not stub_file:
        return

    try:
        imported_stub = _import_stub_file(module.modulename, stub_file)
    except Exception:
        warnings.warn(
            f"Error parsing type stubs for {module.modulename}:\n{traceback.format_exc()}"
        )
        return

    _prepare_module(module)

    stub_mod = doc.Module(imported_stub)
    with mock.patch.dict("sys.modules", {module.modulename: imported_stub}):
        _patch_doc(module, stub_mod)

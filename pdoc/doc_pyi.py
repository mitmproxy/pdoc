"""
This module is responsible for patching `pdoc.doc.Doc` objects with type annotations found
in `.pyi` type stub files ([PEP 561](https://peps.python.org/pep-0561/)).
This makes it possible to add type hints for native modules such as modules written using [PyO3](https://pyo3.rs/).
"""
from __future__ import annotations

from unittest import mock

import sys
import traceback
import types
import warnings
from pathlib import Path

from pdoc import doc
from ._compat import cache


@cache
def find_stub_file(module_name: str) -> Path | None:
    """Try to find a .pyi file with type stubs for the given module name."""
    module_path = module_name.replace(".", "/")

    for dir in sys.path:
        file_candidates = [
            Path(dir) / (module_path + ".pyi"),
            Path(dir) / (module_path + "/__init__.pyi"),
        ]
        for f in file_candidates:
            if f.exists():
                return f
    return None


def _import_stub_file(module_name: str, stub_file: Path) -> types.ModuleType:
    """Import the type stub outside of the normal import machinery."""
    code = compile(stub_file.read_text(), str(stub_file), "exec")
    m = types.ModuleType(module_name)
    m.__file__ = str(stub_file)
    eval(code, m.__dict__, m.__dict__)

    return m


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
        target_doc.signature = stub_doc.signature
        target_doc.funcdef = stub_doc.funcdef
    elif isinstance(target_doc, doc.Variable) and isinstance(stub_doc, doc.Variable):
        target_doc.annotation = stub_doc.annotation
    elif isinstance(target_doc, doc.Namespace) and isinstance(stub_doc, doc.Namespace):
        # pdoc currently does not include variables without docstring in .members (not ideal),
        # so the regular patching won't work. We manually copy over type annotations instead.
        for (k, v) in stub_doc._var_annotations.items():
            var = target_doc.members.get(k, None)
            if isinstance(var, doc.Variable):
                var.annotation = v

        for m in target_doc.members.values():
            _patch_doc(m, stub_mod)
    else:
        warnings.warn(
            f"Error processing type stub for {target_doc.fullname}: "
            f"Stub is a {stub_doc.type}, but target is a {target_doc.type}."
        )


def include_typeinfo_from_stub_files(module: doc.Module) -> None:
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

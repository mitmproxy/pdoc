import importlib
import importlib.util
import os
import sys
import types
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

import pdoc.doc


class ExtractError(Exception):
    pass


@dataclass
class Spec:
    path: Optional[Path]
    name: str


def parse_spec(val: Union[Path, str]) -> Spec:
    """
    Splits a module specification into a base path (which may be empty), and a module name.
    """
    if not isinstance(val, Path) and (
        os.sep in val or (os.altsep and os.altsep in val)
    ):
        val = Path(val)

    if isinstance(val, Path):
        return Spec(val.parent, val.name.removesuffix(".py"))
    else:
        return Spec(None, val)


def _import_module(spec: Spec) -> types.ModuleType:
    """
    Returns a module object, and whether the module is a package or not.
    """
    if str(spec.path) not in sys.path:
        sys.path.insert(0, str(spec.path))

    try:
        return importlib.import_module(spec.name)
    except Exception as e:
        raise ExtractError(f"Error importing {spec.name}: {e}")


def extract_module(spec: Spec) -> pdoc.doc.Module:
    module = _import_module(spec)
    return pdoc.doc.Module(module)

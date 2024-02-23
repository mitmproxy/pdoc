"""A test package with a sub-package at `.subpackage`."""
import demopackage2

from . import _child_e
from . import child_b
from ._child_d import Test
from .child_b import B
from .child_c import C
from .child_f import F

if demopackage2:
    pass

__all__ = [
    "Test",
    "B",
    "C",
    "child_b",
    "child_c",
    "demopackage2",
    "_child_e",
    "child_excluded",
    "subpackage",
    "F"
]

"""A test package"""

from . import child_b, _child_e
from ._child_d import Test

import demopackage2

__all__ = [
    "Test",
    "child_b",
    "child_c",
    "demopackage2",
    "_child_e",
]

"""A test package"""

from . import child_b, _child_e
from ._child_d import Test

import misc

__all__ = [
    "Test",
    "child_b",
    "child_c",
    "misc",
    "_child_e",
]

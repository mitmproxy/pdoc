"""A test package"""

from . import child_b
from ._child_d import Test

import misc

__all__ = [
    "Test",
    "child_b",
    "child_c",
    "misc",
]

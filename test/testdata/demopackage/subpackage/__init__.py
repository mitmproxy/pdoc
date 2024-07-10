"""
A sub-package.

It imports and re-exposes ..child_b.B, and links to `..C` .

It also exposes .child_g.G. These links should all point to the local instance:

- demopackage.G
- demopackage.subpackage.G
- demopackage.subpackage.child_g.G
"""

from ..child_b import B
from .child_g import G

__all__ = ["B", "G"]

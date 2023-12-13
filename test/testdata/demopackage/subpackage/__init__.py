"""
A sub-package.

It imports and re-exposes ..child_b.B, and links to `..C` .
"""

from ..child_b import B

__all__ = ["B"]

"""child_b docstr"""
from __future__ import annotations

import typing


class B:
    """This class is defined in .child_b."""

    b_type: typing.Type[B]
    """we have a self-referential attribute here"""

    def b(self):
        return 1

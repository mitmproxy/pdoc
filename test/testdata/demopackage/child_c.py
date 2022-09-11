"""child_c docstr"""
from . import child_b


class C(child_b.B):
    """This class is defined in .child_c and inherits from .child_b.B"""

    def c(self):
        return 2

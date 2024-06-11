"""child_f docstr"""

from .subpackage import G


class F:
    """This class is defined in .child_f links to demopackage.subpackage.G."""

    def g(self) -> G:
        return G()

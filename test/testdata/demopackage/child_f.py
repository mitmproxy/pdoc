"""child_f docstr"""

from . import subpackage


class F:
    """
    This class defined in .child_f links to subpackage's G which is re-exposed as `G` directly in demopackage.

    We want to make sure that these links render:

    - demopackage.G
    - demopackage.subpackage.G
    - demopackage.subpackage.child_g.G
    """

    def g(self) -> subpackage.G:
        return subpackage.G()

    G = subpackage.G

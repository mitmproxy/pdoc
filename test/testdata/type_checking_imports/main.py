from __future__ import annotations

import typing
from typing import TYPE_CHECKING

from . import cached_submodule

if typing.TYPE_CHECKING:
    from typing import Sequence

if TYPE_CHECKING:
    from typing import Dict

    from .cached_submodule import StrOrInt
    from .uncached_submodule import StrOrBool

assert cached_submodule


def foo(a: Sequence[str], b: Dict[str, str]):
    """A method with TYPE_CHECKING type annotations."""


var: Sequence[int] = (1, 2, 3)
"""A variable with TYPE_CHECKING type annotations."""


imported_from_cached_module: StrOrInt = 42
"""
A variable with a type annotation that's imported from another file's TYPE_CHECKING block.

https://github.com/mitmproxy/pdoc/issues/648
"""

imported_from_uncached_module: StrOrBool = True
"""
A variable with a type annotation that's imported from another file's TYPE_CHECKING block.

In this case, the module is not in sys.modules outside of TYPE_CHECKING.
"""

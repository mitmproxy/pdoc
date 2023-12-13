from __future__ import annotations

import typing

from . import cached_subsubmodule

assert cached_subsubmodule

if typing.TYPE_CHECKING:
    from .cached_subsubmodule import StrOrInt

    assert StrOrInt

from __future__ import annotations

import typing
from typing import TYPE_CHECKING

if typing.TYPE_CHECKING:
    from typing import Sequence

if TYPE_CHECKING:
    from typing import Dict


def foo(a: Sequence[str], b: Dict[str, str]):
    pass


var: Sequence[int] = (1, 2, 3)

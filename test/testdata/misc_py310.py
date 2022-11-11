from typing import Dict


def new_union(a: int | dict[str, "Foo"]) -> bool | None:
    """Testing Python 3.10's new type union syntax."""


class Foo:
    pass


NewStyleDict = dict[str, str]
"""New-style dict."""

OldStyleDict = Dict[str, str]
"""Old-style dict."""

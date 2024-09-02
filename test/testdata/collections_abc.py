"""Test that we remove 'collections.abc' from type signatures."""
from collections.abc import Awaitable, Container


def func(
    bar: Awaitable[None]
) -> Awaitable[None]:
  return bar

class Class(Container[str]):
  """
  For subclasses, we currently display the full classname.
  Mostly because it's easier, but it also makes a bit more sense here.
  """
  def __contains__(self, item):
    return item == "Bar"

var: Container[str] = "baz"

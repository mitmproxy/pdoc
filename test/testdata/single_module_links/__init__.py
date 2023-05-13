from .helpers import something
from .types import BigThing


def abc():
    '''
    Test that submodules are linked to when documenting a single module.

    Do `helpers.something` with a `types.BigThing`
    '''
    something()
    BigThing()

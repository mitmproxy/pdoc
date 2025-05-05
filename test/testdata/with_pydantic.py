"""
A small example with Pydantic entities.
"""

import pydantic


class Foo(pydantic.BaseModel):
    a: int = pydantic.Field(default=1, description="Docstring for a")

    b: int = 2
    """Docstring for b."""

import pydantic
from pydantic.dataclasses import dataclass


class Foo(pydantic.BaseModel):
    a: int = pydantic.Field(default=1, description="Docstring for a")

    b: int = 2
    """Docstring for b."""


@dataclass
class PydanticStyleDataclass:
    a: int = 1

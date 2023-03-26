"""
A small `pdoc` example using Mermaid diagrams.

The relationship for Pet and Dog follows the UML diagram:

```mermaid
classDiagram
    class Dog~Pet~{
        -__init__(str name) None
        +bark(bool loud) None
    }
    Dog <|-- Pet
    Pet : +str name
    Pet : +List[Pet] friends
```
"""


class Pet:
    name: str
    """The name of our pet."""
    friends: list["Pet"]
    """The friends of our pet."""

    def __init__(self, name: str):
        """Make a Pet without any friends (yet)."""
        self.name = name
        self.friends = []


class Dog(Pet):
    """🐕"""

    def bark(self, loud: bool = True):
        """*woof*"""

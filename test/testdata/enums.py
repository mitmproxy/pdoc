import enum


class EnumDemo(enum.Enum):
    """
    This is an example of an Enum.

    As usual, you can link to individual properties: `GREEN`.
    """

    RED = 1
    """I am the red."""
    GREEN = 2
    """I am green."""
    BLUE = enum.auto()


class EnumWithoutDocstrings(enum.Enum):
    FOO = enum.auto()
    BAR = enum.auto()


class IntEnum(enum.IntEnum):
    FOO = enum.auto()
    BAR = enum.auto()


class StrEnum(enum.StrEnum):
    FOO = enum.auto()
    BAR = enum.auto()

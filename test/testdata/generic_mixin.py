from abc import ABC
from typing import Generic
from typing import TypeVar

T = TypeVar("T")


class GenericBase(ABC, Generic[T]):
    def generic_method(self):
        pass


class PlainBase(ABC):
    def plain_method(self):
        pass


class Mixed(GenericBase[T], PlainBase):
    def generic_method(self):
        """generic_method implementation docstring"""

    def plain_method(self):
        """plain_method implementation docstring"""

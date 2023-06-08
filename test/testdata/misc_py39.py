"""
Testing features that either are 3.9+ only or render slightly different on 3.9.
"""
from __future__ import annotations

import functools
from typing import Union


class SingleDispatchMethodExample:
    @functools.singledispatchmethod
    def fancymethod(self, str_or_int: Union[str, int]):
        """A fancy method which is capable of handling either `str` or `int`.

        :param str_or_int: string or integer to handle
        """
        raise NotImplementedError(f"{type(str_or_int)=} not implemented!")

    @fancymethod.register
    def fancymethod_handle_str(self, str_to_handle: str):
        """Fancy method handles a string.

        :param str_to_handle: string which will be handled
        """
        print(f"{type(str_to_handle)} = '{str_to_handle}")

    @fancymethod.register
    def _fancymethod_handle_int(self, int_to_handle: int):
        """Fancy method handles int (not shown in doc).

        :param int_to_handle: int which will be handled
        """
        print(f"{type(int_to_handle)} = '{int_to_handle:x}'")

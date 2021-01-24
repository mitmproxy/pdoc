__docformat__ = "restructuredtext"


def links():
    """
    For type hints, read `PEP 484`_.
    See the `Python home page <http://www.python.org>`_ for info.

    .. _PEP 484:
        https://www.python.org/dev/peps/pep-0484/

    """


def refs():
    """This is similar to :py:obj:`links` and :func:`links`."""


def admonitions():
    """

    .. note::

       This function is not suitable for sending spam e-mails.

    .. warning::
       This function is not suitable for sending spam e-mails.

    .. versionadded:: 2.5
       The *spam* parameter.

    .. versionchanged:: 2.5
       The *spam* parameter.

    .. deprecated:: 3.1
       Use :func:`spam` instead.

    .. deprecated:: 3.1

    This text is not part of the deprecation notice.
    """


def seealso():
    # this is not properly supported yet
    """
    .. seealso::

       Module :py:mod:`zipfile`
          Documentation of the :py:mod:`zipfile` standard module.

       `GNU tar manual, Basic Tar Format <http://link>`_
          Documentation for tar archive files, including GNU tar extensions.
    """


def seealso_short():
    # this is not properly supported yet
    """
    .. seealso:: modules :py:mod:`zipfile`, :py:mod:`tarfile`
    """


def tables():
    """
    | Header 1 | *Header* 2 |
    | -------- | -------- |
    | `Cell 1` | [Cell 2](http://example.com) link |
    | Cell 3 | **Cell 4** |
    """

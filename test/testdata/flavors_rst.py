__docformat__ = "restructuredtext"


def links():
    """
    For type hints, read `PEP 484`_.
    See the `Python home page <http://www.python.org>`_ for info.

    .. _PEP 484:
        https://www.python.org/dev/peps/pep-0484/

    """


def refs():
    """Here we have refs to :py:obj:`links` and :func:`admonitions`."""


def admonitions():
    """

    .. note::

       This function is not suitable for sending spam e-mails.

    .. warning::
       This function is not suitable for sending spam e-mails.

    .. danger::
       This function is not suitable for sending **spam** e-mails.

    .. warning::  Be Careful!
       This warning has both a title and content.

    .. warning::  This warning has a title only.

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


def footnote1():
    """
    Cite the relevant literature, e.g. [1]_.  You may also cite these
    references in the notes section above.

    .. [1] O. McNoleg, "The integration of GIS, remote sensing,
       expert systems and adaptive co-kriging for environmental habitat
       modelling of the Highland Haggis using object-oriented, fuzzy-logic
       and neural-network techniques," Computers & Geosciences, vol. 22,
       pp. 585-588, 1996.
    """


def footnote2():
    """
    Autonumbered footnotes are
    possible, like using [#]_ and [#]_.

    .. [#] This is the first one.
    .. [#] This is the second one.

    They may be assigned 'autonumber
    labels' - for instance,
    [#fourth]_ and [#third]_.

    .. [#third] a.k.a. third_

    .. [#fourth] a.k.a. fourth_
    """


def footnote3():
    """
    Auto-symbol footnotes are also
    possible, like this: [*]_ and [*]_.

    .. [*] This is the first one.
    .. [*] This is the second one.
    """


def footnote4():
    """
    There is no footnote for this reference [#]_.
    """


def include():
    """
    Included from another file:

    .. include:: flavors_rst_include/include.rst
    """


def fields(foo: str = "foo", bar: bool = True) -> str:
    """This method has field descriptions.

    :param foo: A string,
        defaults to None
    :type foo: string, optional
    :param bar: Another
     boolean.
    :return: Another string,
        or maybe `None`.
    :rtype: A string.
    """
    raise NotImplementedError


def fields_text_after_param(foo):
    """This method has text after the `:param` fields.

    :param foo: Some text.

    Here's some more text.
    """


def fields_invalid(foo: str = "foo") -> str:
    """This method has invalid `:param` definitions.

    :param: What is this for?

    :unknown: This is an unknown field name.
    """
    raise NotImplementedError


def fields_exception():
    """
    :raises RuntimeError: Some multi-line
        exception description.
    """

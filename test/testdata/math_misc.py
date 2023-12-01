def test_stars():
    r"""
    Markdown emphasis tokens (*) should be rendered correctly.
    https://github.com/mitmproxy/pdoc/issues/639

    Currently broken:

    $$
    \begin{align*}
    f(x) &= x^2\\
         &= x \cdot x
    \end{align*}
    $$

    Workaround:

    $$
    \begin{align\*}
    f(x) &= x^2\\
         &= x \cdot x
    \end{align\*}
    $$
    """


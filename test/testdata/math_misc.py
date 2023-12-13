"""
Markdown should ignore tokens within inline `$...$` and displaymath `$$...$$`.
https://github.com/mitmproxy/pdoc/issues/639
"""


def test_stars():
    r"""
    Markdown emphasis tokens (`*`) should not be captured in math mode.

    Currently broken: $*xyz*$

    Workaround (escaping `*`): $\*xyz\*$

    Workaround (extra whitespace): $* xyz *$

    """


def test_math_newline():
    r"""
    Markdown should not consume double backslashes (math newlines) in math mode.

    Currently broken:

    $$
    \begin{align\*}
    f(x) &= x^2\\
         &= x \cdot x
    \end{align\*}
    $$

    Workaround (escaping `\\`):

    $$
    \begin{align\*}
    f(x) &= x^2\\\\
         &= x \cdot x
    \end{align\*}
    $$
    """


def test_markdown_newline():
    r"""
    Markdown newlines (`\n\n`) should not emit a paragraph break in math mode.

    Currently broken:

    $$
    x + y

    = z
    $$

    Workaround (no empty lines in math mode):

    $$
    x + y
    % comment
    = z
    $$
    """


def test_macros():
    r"""
    Markdown should not capture headings (`#`) in math mode.
    Currently broken:

    $$
    \newcommand{\define}[2]
    {
    #1 \quad \text{#2}
    }
    \define{e^{i\pi}+1=0}{Euler's identity}
    $$


    Workaround (no lines with leading `#`):

    $$
    \newcommand{\define}[2]{#1 \quad \text{#2}}
    \define{e^{i\pi}+1=0}{Euler's identity}
    $$
    """

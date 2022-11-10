r'''
This is a small demo module showing how pdoc renders $\LaTeX$ when invoked as `pdoc --math`!

# Using Math in Docstrings

Note that docstrings work like regular strings, so backslashes are treated as escape characters.
You can either escape a backslash with a second backslash:


```python
def foo():
    """docstring with $\\frac{x}{y}$."""
```

or prefix your docstring with an "r" so that you have a
[raw string](https://docs.python.org/3/reference/lexical_analysis.html#string-and-bytes-literals)
where backslashes are not processed:

```python

def foo():
    r"""raw docstring with $\frac{x}{y}$."""
```

# Advanced Usage

pdoc uses MathJax's MathJax's in-browser renderer by default. Please note that while pdoc
generally strives to be self-contained, these resources are included from MathJax's CDN.
You can create a `math.html.jinja2` file in your pdoc template directory to override the
[default implementation](https://github.com/mitmproxy/pdoc/blob/main/pdoc/templates/math.html.jinja2).

# Example
'''
import math


def binom_coef(n: int, k: int) -> int:
    """
    Return the number of ways to choose $k$ items from $n$ items without repetition and without order.

    Evaluates to $n! / (k! * (n - k)!)$ when $k <= n$ and evaluates to zero when $k > n$.
    """
    return math.comb(n, k)


def long_formula():
    r"""
    $$
        \Delta =
        \Delta_\text{this} +
        \Delta_\text{is} +
        \Delta_\text{a} +
        \Delta_\text{very} +
        \Delta_\text{long} +
        \Delta_\text{formula} +
        \Delta_\text{that} +
        \Delta_\text{does} +
        \Delta_\text{not} +
        \Delta_\text{fully} +
        \Delta_\text{fit} +
        \Delta_\text{on} +
        \Delta_\text{the} +
        \Delta_\text{screen}
    $$
    """

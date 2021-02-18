r'''
This is a small demo module showing how pdoc renders $\LaTeX$!

Note that docstrings work like regular strings, so backslashes are treated as escape characters.  
You can either escape a backslash with a second backslash:


```python
def foo():
    """docstring with $\\frac{x}{y}$."""
```

or prefix your docstring with an "r" so that you have a [raw string](https://docs.python.org/3/reference/lexical_analysis.html#string-and-bytes-literals)
where backslashes are not processed:

```python

def foo():
    r"""raw docstring with $\frac{x}{y}$."""
```

Example: $\frac{x}{y}$

'''
import math

def binom_coef(n: int, k: int) -> int:
    """
    Return the number of ways to choose $k$ items from $n$ items without repetition and without order.

    Evaluates to $n! / (k! * (n - k)!)$ when $k <= n$ and evaluates to zero when $k > n$.
    """
    return math.comb(n, k)

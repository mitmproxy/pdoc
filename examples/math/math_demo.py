"""
This is a small demo module showing how pdoc renders $\LaTeX$!
"""
import math

def binom_coef(n: int, k: int):
	"""
	Return the number of ways to choose $k$ items from $n$ items without repetition and without order.

	Evaluates to $n! / (k! * (n - k)!)$ when $k <= n$ and evaluates to zero when $k > n$.
	"""
	return math.comb(n, k)

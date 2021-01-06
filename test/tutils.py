import contextlib
import os


@contextlib.contextmanager
def tdir():
    """
    A small helper to place us within the test directory.
    """
    old_dir = os.getcwd()
    os.chdir(os.path.dirname(__file__))
    yield
    os.chdir(old_dir)

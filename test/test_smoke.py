import importlib
import pkgutil

import pytest

import pdoc

# idlelib: starts IDLE, hard to avoid...
# test: runs too slow
# py: https://bugs.python.org/issue35791
modules = [
    m.name
    for m in pkgutil.iter_modules()
    if not m.name.startswith("_") and m.name not in ("test", "idlelib", "py")
] + ["unittest.mock"]


@pytest.mark.slow
@pytest.mark.filterwarnings("ignore")
@pytest.mark.parametrize("module", modules)
def test_smoke(module):
    try:
        with pdoc.extract.mock_some_common_side_effects():
            importlib.import_module(module)
    except pdoc.docstrings.AnyException:
        pass
    else:
        try:
            pdoc.pdoc(module)
        except RuntimeError as e:
            assert "Error importing" in str(e)

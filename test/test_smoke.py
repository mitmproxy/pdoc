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
]


@pytest.mark.slow
@pytest.mark.filterwarnings("ignore")
@pytest.mark.parametrize("module", modules)
def test_smoke(module):
    try:
        with pdoc.extract.mock_some_common_side_effects():
            importlib.import_module(module)
    except pdoc.extract.AnyException:
        pass
    else:
        # noinspection PyTypeChecker
        pdoc.pdoc(module, format="repr")
        pdoc.pdoc(module, format="html")

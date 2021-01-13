import importlib
import pkgutil

import pytest

import pdoc

modules = [
    m.name
    for m in pkgutil.iter_modules()
    if not m.name.startswith("_") and m.name not in ("test", "idlelib")
]

@pytest.mark.slow
@pytest.mark.filterwarnings("ignore")
@pytest.mark.parametrize("module", modules)
def test_smoke(module):
    print(f"{module=}")
    try:
        with pdoc.extract.mock_some_common_side_effects():
            importlib.import_module(module)
    except BaseException:
        pass
    else:
        # noinspection PyTypeChecker
        pdoc.pdoc(module, format="repr")
        pdoc.pdoc(module, format="html")

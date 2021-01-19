import sys
from pathlib import Path
from typing import Union

import pytest

import pdoc

snapshot_dir = (Path(__file__).parent / "snapshots").absolute()

snapshots = [
    snapshot_dir / "demo.py",
    snapshot_dir / "demo_long.py",
    snapshot_dir / "demo_eager.py",
    snapshot_dir / "demopackage",
    snapshot_dir / "misc.py",
]


def make_html_snapshot(module: Union[str, Path]) -> str:
    return pdoc.pdoc(module, format="html")


def make_repr_snapshot(module: Union[str, Path]) -> str:
    # noinspection PyTypeChecker
    return pdoc.pdoc(module, format="repr")  # type: ignore


@pytest.mark.parametrize("module", snapshots)
def test_html_snapshots(module: Path):
    if sys.version_info < (3, 9) and module.name in (
        "demo.py",
        "demo_long.py",
        "demo_eager.py",
    ):
        pytest.skip("minor rendering differences on Python 3.8")
    expected = module.with_suffix(".html").read_text("utf8")
    actual = make_html_snapshot(module)
    assert actual == expected


@pytest.mark.parametrize("module", snapshots)
def test_repr_snapshots(module: Path):
    if sys.version_info < (3, 9) and module.name in (
        "demo.py",
        "demo_long.py",
        "demo_eager.py",
    ):
        pytest.skip("minor rendering differences on Python 3.8")
    expected = module.with_suffix(".txt").read_text("utf8")
    actual = make_repr_snapshot(module)
    assert actual == expected


if __name__ == "__main__":
    if sys.version_info < (3, 9):  # pragma: no cover
        raise RuntimeError("Snapshots need to be generated on Python 3.9+")
    for module in snapshots:
        print(f"Rendering {module}...")
        rendered = make_html_snapshot(module)
        module.with_suffix(".html").write_bytes(rendered.encode())
        rendered = make_repr_snapshot(module)
        module.with_suffix(".txt").write_bytes(rendered.encode())
    print("All snapshots rendered!")

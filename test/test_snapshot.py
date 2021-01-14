import platform
from pathlib import Path
from typing import Union

import pytest

import pdoc

snapshot_dir = (Path(__file__).parent / "snapshots").absolute()

snapshots = [
    str(snapshot_dir / "demo.py"),
    str(snapshot_dir / "demopackage"),
    str(snapshot_dir / "indent.py"),
    str(snapshot_dir / "submodules_in_all.py"),
]


def make_html_snapshot(module: Union[str, Path]) -> str:
    return pdoc.pdoc(module, format="html")


def make_repr_snapshot(module: Union[str, Path]) -> str:
    # noinspection PyTypeChecker
    return pdoc.pdoc(module, format="repr")  # type: ignore


@pytest.mark.parametrize("module", snapshots)
def test_html_snapshots(module):
    try:
        expected = (snapshot_dir / f"{module}-{platform.python_version()}.html").read_text(
            "utf8"
        )
    except FileNotFoundError:
        pytest.xfail("no snapshot found. generate by running python test_snapshot.py.")
        assert False
    actual = make_html_snapshot(module)
    assert actual == expected


@pytest.mark.parametrize("module", snapshots)
def test_repr_snapshots(module):
    try:
        expected = (snapshot_dir / f"{module}-{platform.python_version()}.txt").read_text(
            "utf8"
        )
    except FileNotFoundError:
        pytest.xfail("no snapshot found. generate by running python test_snapshot.py.")
        assert False
    actual = make_repr_snapshot(module)
    assert actual == expected


if __name__ == "__main__":
    for module in snapshots:
        print(f"Rendering {module}...")
        rendered = make_html_snapshot(module)
        (snapshot_dir / f"{module}-{platform.python_version()}.html").write_text(
            rendered, "utf8"
        )
        rendered = make_repr_snapshot(module)
        (snapshot_dir / f"{module}-{platform.python_version()}.txt").write_text(
            rendered, "utf8"
        )
    print("All snapshots rendered!")

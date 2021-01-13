from pathlib import Path

import pytest

import pdoc

snapshot_dir = (Path(__file__).parent / "snapshots").absolute()

snapshots = [
    (snapshot_dir / "demo.py"),
    (snapshot_dir / "demopackage"),
]


def make_html_snapshot(module: str) -> str:
    return pdoc.pdoc(module, format="html")


def make_repr_snapshot(module: str) -> str:
    # noinspection PyTypeChecker
    return pdoc.pdoc(module, format="repr")


@pytest.mark.parametrize("module", snapshots)
def test_html_snapshots(module):
    expected = (snapshot_dir / f"{module}.html").read_text("utf8")
    actual = make_html_snapshot(module)
    assert actual == expected


@pytest.mark.parametrize("module", snapshots)
def test_repr_snapshots(module):
    expected = (snapshot_dir / f"{module}.txt").read_text("utf8")
    actual = make_repr_snapshot(module)
    assert actual == expected


if __name__ == "__main__":
    for module in snapshots:
        print(f"Rendering {module}...")
        rendered = make_html_snapshot(module)
        (snapshot_dir / f"{module}.html").write_text(rendered, "utf8")
        rendered = make_repr_snapshot(module)
        (snapshot_dir / f"{module}.txt").write_text(rendered, "utf8")
    print("All snapshots rendered!")

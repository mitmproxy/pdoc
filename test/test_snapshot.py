#!/usr/bin/env python3
import sys
from pathlib import Path
from typing import Optional

import pytest

import pdoc
from pdoc import render

here = Path(__file__).parent.absolute()

snapshot_dir = here / "testdata"


class Snapshot:
    id: str
    path: Path
    render_options: dict
    extra: Optional[Path]

    def __init__(
        self,
        id: str,
        filename: Optional[str] = None,
        render_options: Optional[dict] = None,
        extra: Optional[Path] = None,
    ):
        self.id = id
        self.extra = extra
        self.path = snapshot_dir / (filename or f"{id}.py")
        self.render_options = render_options or {}

    def __str__(self):
        return f"Snapshot({self.id})"

    def make(self, format: str) -> str:
        render.configure(**self.render_options)
        paths = [self.path]
        if self.extra:
            paths.append(self.extra)
        # noinspection PyTypeChecker
        rendered = pdoc.pdoc(*paths, format=format)  # type: ignore
        render.configure()
        return rendered

    def outfile(self, format: str) -> Path:
        return (snapshot_dir / self.id).with_suffix(
            {
                "html": ".html",
                "repr": ".txt",
            }[format]
        )


snapshots = [
    Snapshot("demo"),
    Snapshot("flavors_google"),
    Snapshot("flavors_numpy"),
    Snapshot("flavors_rst"),
    Snapshot(
        "demo_customtemplate",
        "demo.py",
        {"template_directory": here / ".." / "examples" / "custom-template"},
    ),
    Snapshot("demo_long", extra=snapshot_dir / "demo.py"),
    Snapshot("demo_eager"),
    Snapshot("demopackage"),
    Snapshot("misc"),
]


@pytest.mark.parametrize("snapshot", snapshots)
@pytest.mark.parametrize("format", ["html", "repr"])
def test_snapshots(snapshot: Snapshot, format: str):
    """
    Compare pdoc's rendered output against stored snapshots.
    """
    if sys.version_info < (3, 9) and snapshot.id in (
        "demo",
        "demo_customtemplate",
        "demo_long",
        "demo_eager",
    ):
        pytest.skip("minor rendering differences on Python <=3.8")
    expected = snapshot.outfile(format).read_text("utf8")
    actual = snapshot.make(format)
    assert actual == expected, (
        f"Rendered output does not match for snapshot {snapshot.id}. "
        "Run `python3 ./test/test_snapshot.py` to update snapshots."
    )


if __name__ == "__main__":
    if sys.version_info < (3, 9):  # pragma: no cover
        raise RuntimeError("Snapshots need to be generated on Python 3.9+")
    for snapshot in snapshots:
        for format in ["html", "repr"]:
            print(f"Rendering {snapshot} to {format}...")
            rendered = snapshot.make(format)
            snapshot.outfile(format).write_bytes(rendered.encode())
    print("All snapshots rendered!")

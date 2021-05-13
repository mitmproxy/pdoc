#!/usr/bin/env python3
import sys
import tempfile
from pathlib import Path
from typing import Optional

import pytest

import pdoc
import pdoc.render

here = Path(__file__).parent.absolute()

snapshot_dir = here / "testdata"


class Snapshot:
    id: str
    path: Path
    render_options: dict
    with_output_directory: bool

    def __init__(
        self,
        id: str,
        filename: Optional[str] = None,
        render_options: Optional[dict] = None,
        with_output_directory: bool = False,
    ):
        self.id = id
        self.path = snapshot_dir / (filename or f"{id}.py")
        self.render_options = render_options or {}
        self.with_output_directory = with_output_directory

    def __repr__(self):
        return f"Snapshot({self.id})"

    def make(self, format: str) -> str:
        pdoc.render.configure(**self.render_options)
        pdoc.render.env.globals["__version__"] = "$VERSION"
        if self.with_output_directory:
            with tempfile.TemporaryDirectory() as tmpdirname:
                tmpdir = Path(tmpdirname)
                # noinspection PyTypeChecker
                pdoc.pdoc(self.path, format=format, output_directory=Path(tmpdir))  # type: ignore

                rendered = '<style>iframe {width: 100%; min-height: 50vh}</style>\n'
                for f in sorted(tmpdir.glob("**/*"), reverse=True):
                    if not f.is_file():
                        continue
                    rendered += (
                        f'<h3>{f.relative_to(tmpdir).as_posix()}</h3>\n' +
                        '<iframe srcdoc="\n' +
                        f.read_text("utf8").replace("&", "&amp;").replace(""" " """.strip(), "&quot;") +
                        '\n"></iframe>\n\n'
                    )

        else:
            # noinspection PyTypeChecker
            rendered = pdoc.pdoc(self.path, format=format)  # type: ignore
        pdoc.render.configure()
        pdoc.render.env.globals["__version__"] = pdoc.__version__
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
    Snapshot("demo_long"),
    Snapshot("demo_eager"),
    Snapshot("demopackage", "demopackage"),
    Snapshot("demopackage_dir", "demopackage", with_output_directory=True),
    Snapshot("misc"),
    Snapshot("misc_py39"),
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
        "misc_py39",
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

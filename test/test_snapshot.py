#!/usr/bin/env python3
from __future__ import annotations
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
    min_version: tuple[int, int]

    def __init__(
        self,
        id: str,
        filename: Optional[str] = None,
        render_options: Optional[dict] = None,
        with_output_directory: bool = False,
        min_version: tuple[int, int] = (3, 7),
    ):
        self.id = id
        self.path = snapshot_dir / (filename or f"{id}.py")
        self.render_options = render_options or {}
        self.with_output_directory = with_output_directory
        self.min_version = min_version

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

                rendered = "<style>iframe {width: 100%; min-height: 50vh}</style>\n"
                for f in sorted(tmpdir.glob("**/*"), reverse=True):
                    if not f.is_file():
                        continue
                    rendered += (
                        f"<h3>{f.relative_to(tmpdir).as_posix()}</h3>\n"
                        + '<iframe srcdoc="\n'
                        + f.read_text("utf8")
                        .replace("&", "&amp;")
                        .replace(""" " """.strip(), "&quot;")
                        + '\n"></iframe>\n\n'
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
    Snapshot("demo", min_version=(3, 9)),
    Snapshot("flavors_google"),
    Snapshot("flavors_numpy"),
    Snapshot("flavors_rst"),
    Snapshot(
        "example_customtemplate",
        "demo.py",
        {"template_directory": here / ".." / "examples" / "custom-template"},
        min_version=(3, 9),
    ),
    Snapshot(
        "example_darkmode",
        "demo.py",
        {"template_directory": here / ".." / "examples" / "dark-mode"},
        min_version=(3, 9),
    ),
    Snapshot(
        "example_mkdocs",
        "demo.py",
        {"template_directory": here / ".." / "examples" / "mkdocs" / "pdoc-template"},
        min_version=(3, 9),
    ),
    Snapshot("demo_long", min_version=(3, 9)),
    Snapshot("demo_eager", min_version=(3, 9)),
    Snapshot("demopackage", "demopackage"),
    Snapshot("demopackage_dir", "demopackage", with_output_directory=True),
    Snapshot("misc"),
    Snapshot("misc_py39", min_version=(3, 9)),
    Snapshot("misc_py310", min_version=(3, 10)),
    Snapshot("math_demo", render_options={"math": True}),
    Snapshot("render_options", render_options={
        "show_source": False,
        "logo": "https://placedog.net/500?random",
        "logo_link": "https://example.com/",
        "footer_text": "custom footer text"
    }),
    Snapshot("type_checking_imports"),
]


@pytest.mark.parametrize("snapshot", snapshots)
@pytest.mark.parametrize("format", ["html", "repr"])
def test_snapshots(snapshot: Snapshot, format: str):
    """
    Compare pdoc's rendered output against stored snapshots.
    """
    if sys.version_info < snapshot.min_version:
        pytest.skip(
            f"Snapshot only works on Python {'.'.join(str(x) for x in snapshot.min_version)} and above."
        )
    expected = snapshot.outfile(format).read_text("utf8")
    actual = snapshot.make(format)
    assert actual == expected, (
        f"Rendered output does not match for snapshot {snapshot.id}. "
        "Run `python3 ./test/test_snapshot.py` to update snapshots."
    )


if __name__ == "__main__":
    if sys.version_info < (3, 10):  # pragma: no cover
        raise RuntimeError("Snapshots need to be generated on Python 3.10+")
    for snapshot in snapshots:
        for format in ["html", "repr"]:
            print(f"Rendering {snapshot} to {format}...")
            rendered = snapshot.make(format)
            snapshot.outfile(format).write_bytes(rendered.encode())
    print("All snapshots rendered!")

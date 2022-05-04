#!/usr/bin/env python3
from __future__ import annotations

import os
import shutil
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
    specs: list[str]
    render_options: dict
    with_output_directory: bool
    min_version: tuple[int, int]

    def __init__(
        self,
        id: str,
        filenames: Optional[list[str]] = None,
        render_options: Optional[dict] = None,
        with_output_directory: bool = False,
        min_version: tuple[int, int] = (3, 7),
    ):
        self.id = id
        self.specs = filenames or [f"{id}.py"]
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
                pdoc.pdoc(*self.specs, format=format, output_directory=Path(tmpdir))  # type: ignore

                if format == "html":
                    rendered = "<style>iframe {width: 100%; min-height: 50vh}</style>\n"
                else:
                    rendered = ""
                for f in sorted(tmpdir.glob("**/*"), reverse=True):
                    if not f.is_file():
                        continue
                    if format == "html":
                        rendered += (
                            f"<h3>{f.relative_to(tmpdir).as_posix()}</h3>\n"
                            + '<iframe srcdoc="\n'
                            + f.read_text("utf8")
                            .replace("&", "&amp;")
                            .replace('"', "&quot;")
                            + '\n"></iframe>\n\n'
                        )
                    else:
                        rendered += (
                            f"# {f.relative_to(tmpdir).as_posix()}\n"
                            f"{f.read_text('utf8')}\n"
                        )

        else:
            # noinspection PyTypeChecker
            rendered = pdoc.pdoc(*self.specs, format=format)  # type: ignore
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
        ["demo.py"],
        {"template_directory": here / ".." / "examples" / "custom-template"},
        min_version=(3, 9),
    ),
    Snapshot(
        "example_darkmode",
        ["demo.py"],
        {"template_directory": here / ".." / "examples" / "dark-mode"},
        min_version=(3, 9),
    ),
    Snapshot(
        "example_mkdocs",
        ["demo.py"],
        {"template_directory": here / ".." / "examples" / "mkdocs" / "pdoc-template"},
        min_version=(3, 9),
    ),
    Snapshot("demo_long", min_version=(3, 9)),
    Snapshot("demo_eager", min_version=(3, 9)),
    Snapshot("demopackage", ["demopackage", "!demopackage.child_excluded"]),
    Snapshot(
        "demopackage_dir",
        ["demopackage", "demopackage2", "!demopackage.child_excluded"],
        render_options={
            "edit_url_map": {
                "demopackage.child_b": "https://gitlab.example.com/foo/bar/-/blob/main/demopackage/child_b",
                "demopackage.child_c": "https://custom.example.com/demopackage/child_c",
                "demopackage": "https://github.com/mitmproxy/pdoc/tree/main/test/testdata/demopackage/",
            }
        },
        with_output_directory=True,
    ),
    Snapshot("misc"),
    Snapshot("misc_py39", min_version=(3, 9)),
    Snapshot("misc_py310", min_version=(3, 10)),
    Snapshot("math_demo", render_options={"math": True}),
    Snapshot(
        "render_options",
        ["render_options", "math_demo"],
        render_options={
            "show_source": False,
            "logo": "https://placedog.net/500?random",
            "logo_link": "https://example.com/",
            "footer_text": "custom footer text",
            "search": False,
            "favicon": "https://pdoc.dev/favicon.svg",
        },
        with_output_directory=True,
    ),
    Snapshot("top_level_reimports", ["top_level_reimports"]),
    Snapshot("type_checking_imports"),
    Snapshot("type_stub", min_version=(3, 10)),
]


@pytest.mark.parametrize("snapshot", snapshots, ids=[x.id for x in snapshots])
@pytest.mark.parametrize("format", ["html", "repr"])
def test_snapshots(snapshot: Snapshot, format: str, monkeypatch):
    """
    Compare pdoc's rendered output against stored snapshots.
    """
    monkeypatch.chdir(snapshot_dir)
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
    if not shutil.which("nodejs") and not shutil.which("node"):
        print(
            "Snapshots include precompiled search indices, "
            "but this system does not have Node.js installed to render them. Aborting."
        )
        sys.exit(1)
    os.chdir(snapshot_dir)
    skipped_some = False
    for snapshot in snapshots:
        if sys.version_info < snapshot.min_version:
            print(
                f"Skipping {snapshot} as it requires a more recent version of Python."
            )
            skipped_some = True
            continue
        if len(sys.argv) > 1 and snapshot.id not in sys.argv:
            continue
        for format in ["html", "repr"]:
            print(f"Rendering {snapshot} to {format}...")
            rendered = snapshot.make(format)
            snapshot.outfile(format).write_bytes(rendered.encode())
    print("All snapshots rendered!")
    sys.exit(int(skipped_some))

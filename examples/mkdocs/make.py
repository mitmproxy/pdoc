#!/usr/bin/env python3
import shutil
from pathlib import Path

from pdoc import pdoc
from pdoc import render

here = Path(__file__).parent
out = here / "docs" / "api"
if out.exists():
    shutil.rmtree(out)

# Render parts of pdoc's documentation into docs/api...
render.configure(template_directory=here / "pdoc-template")
pdoc("pdoc", "!pdoc.", "pdoc.doc", output_directory=out)

# ...and rename the .html files to .md so that mkdocs picks them up!
for f in out.glob("**/*.html"):
    f.rename(f.with_suffix(".md"))

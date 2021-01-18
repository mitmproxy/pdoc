from pathlib import Path

from pdoc import render, doc

here = Path(__file__).parent


def test_render_custom_template():
    mod = doc.Module(doc)
    assert "View Source" in render.html_module(mod, ["pdoc.doc"])
    render.configure(template_directory=here / "customtemplate")

    try:
        assert "View Source" not in render.html_module(mod, ["pdoc.doc"])
    finally:
        render.configure()

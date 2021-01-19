from pathlib import Path

from pdoc import render, doc

here = Path(__file__).parent


def test_render_custom_template():
    mod = doc.Module(doc)
    assert "View Source" in render.html_module(mod, ["pdoc.doc"])
    render.configure(template_directory=here / "customtemplate")

    try:
        html = render.html_module(mod, ["pdoc.doc"])
        assert "View Source" not in html
        assert "wat" in html
    finally:
        render.configure()

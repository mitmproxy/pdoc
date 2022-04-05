"""
pdoc has a search box which allows users to quickly find relevant parts in the documentation.
This feature is implemented entirely client-side so that pdoc can still be hosted statically,
and works without any third-party services in a privacy-preserving way. When a user focuses the
search box for the first time, pdoc will fetch the search index (`search.js`) and use that to
answer all upcoming queries.

##### Search Coverage

The search functionality covers all documented elements and their docstrings.
You may find documentation objects using their name, arguments, or type annotations; the source code is not considered.

##### Search Performance

pdoc uses [Elasticlunr.js](https://github.com/weixsong/elasticlunr.js) to implement search. To improve end user
performance, pdoc will attempt to precompile the search index when building the documentation. This only works if
`nodejs` is available, and pdoc gracefully falls back to client-side index building if this is not the case.

If your search index reaches a size where compilation times are meaningful and `nodejs` cannot be invoked,
pdoc will let you know and print a notice when building your documentation. In this case it should be enough to install
a recent version of [Node.js](https://nodejs.org/) on your system and make a `nodejs` or `node` available on your PATH.
There are no other additional dependencies. pdoc only uses `node` to interpret a local JS file, it does not download any
additional packages.

You can test if your search index is precompiled by clicking the search box (so that the search index is fetched) and
then checking your browser's developer console.

##### Search Index Size

The search index can be relatively large as it includes all docstrings. For larger projects, you should make sure that
you have [HTTP compression](https://en.wikipedia.org/wiki/HTTP_compression) and caching enabled. `search.js` usually
compresses to about 10% of its original size. For example, pdoc's own precompiled search index compresses from 312kB
to 27kB.

##### Disabling Search

If you wish to hide the search box, you can add
```html+jinja
{% block search %}{% endblock %}
{% block search_js %}{% endblock %}
```
in your [`module.html.jinja2` template](../pdoc.html#edit-pdocs-html-template).
"""
from __future__ import annotations

import json
import shutil
import subprocess
import textwrap
from collections.abc import Callable, Mapping
from pathlib import Path

import pdoc.doc
from pdoc.render_helpers import to_html, to_markdown


def make_index(
    all_modules: Mapping[str, pdoc.doc.Module],
    is_public: Callable[[pdoc.doc.Doc], bool],
    default_docformat: str,
) -> list[dict]:
    """
    This method compiles all currently documented modules into a pile of documentation JSON objects,
    which can then be ingested by Elasticlunr.js.
    """

    documents = []
    for modname, module in all_modules.items():

        def make_item(doc: pdoc.doc.Doc, **kwargs) -> dict[str, str]:
            # TODO: We could be extra fancy here and split `doc.docstring` by toc sections.
            ret = {
                "fullname": doc.fullname,
                "modulename": doc.modulename,
                "qualname": doc.qualname,
                "type": doc.type,
                "doc": to_html(to_markdown(doc.docstring, module, default_docformat)),
                **kwargs,
            }
            return {k: v for k, v in ret.items() if v}

        # TODO: Instead of building our own JSON objects here we could also use module.html.jinja2's member()
        #  implementation to render HTML for each documentation object and then implement a elasticlunr tokenizer that
        #  removes HTML. It wouldn't be great for search index size, but the rendered search entries would be fully
        #  consistent.
        def make_index(mod: pdoc.doc.Namespace, **extra):
            if not is_public(mod):
                return
            yield make_item(mod, **extra)
            for m in mod.own_members:
                if isinstance(m, pdoc.doc.Variable) and is_public(m):
                    yield make_item(
                        m,
                        annotation=m.annotation_str,
                        default_value=m.default_value_str,
                    )
                elif isinstance(m, pdoc.doc.Function) and is_public(m):
                    yield make_item(
                        m,
                        signature=str(m.signature),
                        funcdef=m.funcdef,
                    )
                elif isinstance(m, pdoc.doc.Class):
                    yield from make_index(
                        m,
                        bases=", ".join(x[2] for x in m.bases),
                    )
                else:
                    pass

        documents.extend(make_index(module))

    return documents


def precompile_index(documents: list[dict], compile_js: Path) -> str:
    """
    This method tries to precompile the Elasticlunr.js search index by invoking `nodejs` or `node`.
    If that fails, an unprocessed index will be returned (which will be compiled locally on the client side).
    If this happens and the index is rather large (>3MB), a warning with precompile instructions is printed.

    We currently require nodejs, but we'd welcome PRs that support other JavaScript runtimes or
    – even better – a Python-based search index generation similar to
    [elasticlunr-rs](https://github.com/mattico/elasticlunr-rs) that could be shipped as part of pdoc.
    """
    raw = json.dumps(documents)
    try:
        if shutil.which("nodejs"):
            executable = "nodejs"
        else:
            executable = "node"
        out = subprocess.check_output(
            [executable, compile_js],
            input=raw.encode(),
            cwd=Path(__file__).parent / "templates",
            stderr=subprocess.STDOUT,
        )
        index = json.loads(out)
        index["_isPrebuiltIndex"] = True
    except Exception as e:
        if len(raw) > 3 * 1024 * 1024:
            print(
                f"pdoc failed to precompile the search index: {e}\n"
                f"Search will work, but may be slower. "
                f"This error may only show up now because your index has reached a certain size. "
                f"See https://pdoc.dev/docs/pdoc/search.html for details."
            )
            if isinstance(e, subprocess.CalledProcessError):
                print(f"{' Node.js Output ':=^80}")
                print(
                    textwrap.indent(e.output.decode("utf8", "replace"), "    ").rstrip()
                )
                print("=" * 80)
        return raw
    else:
        return json.dumps(index)

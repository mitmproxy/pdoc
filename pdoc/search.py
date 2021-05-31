"""
pdoc has a search box which allows users to quickly find relevant parts in the documentation.
This feature is implemented entirely client-side so that pdoc can still be hosted statically,
and works without any third-party services in a privacy-preserving way. When a user focuses the
search box for the first time, pdoc will fetch the search index (`search.json`) and use that to
answer all upcoming queries.

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
you have [HTTP compression](https://en.wikipedia.org/wiki/HTTP_compression) and caching enabled. `search.json` usually
compresses to about 10% of its original size. For example, pdoc's own precompiled search index compresses from 312kB
to 27kB.

##### Disabling Search

If you wish to hide the search box, you can add
```html+jinja
{% block search %}{% endblock %}
{% block search_js %}{% endblock %}
```
in your [`module.html.jinja2` template](../pdoc.html#editing-pdocs-html-template).
"""
from __future__ import annotations

import json
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path

import pdoc.doc
from pdoc.render_helpers import render_docstring


def make_index(
    doc_objects: dict[str, pdoc.doc.Module],
    is_public: Callable[[pdoc.doc.Doc], bool],
    default_docformat: str,
) -> list[dict]:
    """
    This method compiles all currently documented modules into a pile of documentation JSON objects,
    which can then be ingested by Elasticlunr.js.
    """

    documents = []
    for modname, mod in doc_objects.items():

        def make_item(doc: pdoc.doc.Doc, **kwargs) -> dict[str, str]:
            # TODO: We could be extra fancy here and split `doc.docstring` by toc sections.
            return {
                "fullname": doc.fullname,
                "modulename": doc.modulename,
                "qualname": doc.qualname,
                "type": doc.type,
                "doc": render_docstring(doc.docstring, mod, default_docformat),
                **kwargs,
            }

        def make_index(mod: pdoc.doc.Namespace):
            if not is_public(mod):
                return
            yield make_item(mod)
            for m in mod.own_members:
                if isinstance(m, pdoc.doc.Variable) and is_public(m):
                    yield make_item(m)
                elif isinstance(m, pdoc.doc.Function) and is_public(m):
                    yield make_item(
                        m,
                        parameters=list(m.signature.parameters),
                        funcdef=m.funcdef,
                    )
                elif isinstance(m, pdoc.doc.Class):
                    yield from make_index(m)
                else:
                    pass

        documents.extend(make_index(mod))

    return documents


def precompile_index(documents: list[dict], compile_js: Path) -> str:
    """
    This method tries to precompile the Elasticlunr.js search index by invoking `nodejs` or `node`.
    If that fails, an unprocessed index will be returned (which will be compiled locally on the client side).
    If this happens and the index is rather large (>3MB), a warning with precompile instructions is printed.

    We currently require nodejs, but we'd welcome PRs that support other JaveScript runtimes or
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
        )
        index = json.loads(out)
        index["_isPrebuiltIndex"] = True
    except Exception as e:
        if len(raw) > 3 * 1024 * 1024:
            print(
                f"Note: pdoc failed to precompile the search index ({e}). "
                f"To improve search speed, see https://pdoc.dev/docs/pdoc/search.html"
            )
        return raw
    else:
        return json.dumps(index)

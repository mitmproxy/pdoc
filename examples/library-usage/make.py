#!/usr/bin/env python3
import foo

import pdoc

if __name__ == "__main__":
    doc = pdoc.doc.Module(foo)

    # We can override most pdoc doc attributes by just assigning to them.
    doc.get("Foo.A").docstring = "I'm a docstring for Foo.A."

    out = pdoc.render.html_module(module=doc, all_modules={"foo": doc})

    with open("foo.html", "w") as f:
        f.write(out)

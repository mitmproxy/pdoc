r'''
# What is pdoc?

pdoc auto-generates API documentation that follows your project's Python module hierarchy.

pdoc's main feature is a focus on simplicity: pdoc aims to do one thing and do it well.

 - Easy setup, no configuration necessary.
 - Documentation is plain Markdown.
 - First-class support for type annotations.
 - Builtin web server with live reloading.
 - Customizable HTML templates.
 - Understands numpydoc and Google-style docstrings.

# Quickstart

As an example, we want to generate API documentation for `demo.py`.
Our demo module already includes a bunch of docstrings:

```python
"""
A small `pdoc` example.
"""

class Dog:
    """🐕"""
    name: str
    """The name of our dog."""
    friends: list["Dog"]
    """The friends of our dog."""

    def __init__(self, name: str):
        """Make a Dog without any friends (yet)."""
        self.name = name
        self.friends = []

    def bark(self, loud: bool = True):
        """*woof*"""
```

We can invoke pdoc to take our docstrings and render them into a standalone HTML document:

```shell
pdoc ./demo.py  # or: pdoc my_module_name
```

This opens a browser with our module documentation. Here's a copy of what you should see:

<iframe style="
    width: 100%;
    height: 250px;
    border: solid gray 1px;
    display: block;
    margin: 1rem auto;
    border-radius: 5px;"
    title="rendered demo.py documentation"
    src="https://pdoc.dev/docs/demo-standalone.html"></iframe>

If you look closely, you'll notice that docstrings are interpreted as Markdown.
For example, \`pdoc\` is rendered as `pdoc﻿`. Additionally, identifiers such as the type annotation
for `Dog.friends` are automatically linked.

If we edit `demo.py` now, the page will reload automatically.
Once we are happy with everything, we can export the documentation to an HTML file:

```shell
pdoc ./demo.py -o ./docs
```

This will create an HTML file at `docs/demo.html` which contains our module documentation. 🎉

## Customizing pdoc

We can optionally configure pdoc's output via command line flags.
For example, we can add a project logo to the documentation:

```shell
pdoc ./demo.py --logo "https://placedog.net/300?random"
```

To get a list of all available rendering options, run:

```shell
pdoc --help
```

If you need more advanced customization options, see [*How can I edit pdoc's HTML template?*](#edit-pdocs-html-template).


## Deploying to GitHub Pages

*In this example we'll deploy pdoc's documentation to GitHub Pages. Of course, you can distribute
the generated documentation however you want! pdoc's job is to "just" produce self-contained HTML files for you.*

A very simple way to host your API documentation is to set up a continuous integration job which
pushes your documentation to GitHub Pages. This keeps your docs updated automatically.

 1. Enable GitHub Actions and GitHub Pages in your project's settings.
 2. Copy pdoc's GitHub Actions workflow into your own repository and adjust it to how you build your docs:
    [`.github/workflows/docs.yml`](https://github.com/mitmproxy/pdoc/blob/main/.github/workflows/docs.yml)

That's it – no need to fiddle with any secrets or set up any `gh-pages` branches. 🥳

# How can I ... ?

## ...add documentation?

In Python, objects like modules, functions and classes have
a special attribute named `__doc__` which contains that object's
*docstring*.  The docstring comes from a special placement of a string
in your source code.  For example, the following code shows how to
define a function with a docstring and access the contents of that
docstring:

```python
>>> def test():
...     """This is a docstring."""
...     pass
...
>>> test.__doc__
'This is a docstring.'
```

Something similar can be done for classes and modules too. For classes,
the docstring should come on the line immediately following `class
...`. For modules, the docstring should start on the first line of
the file. These docstrings are what you see for each module, class,
function and method listed in the documentation produced by pdoc.

## ...document variables?

Python itself [does not attach docstrings to
variables](https://www.python.org/dev/peps/pep-0224/). For example:

```python
variable = "SomeValue"
"""Docstring for variable."""
```

The resulting `variable` will have no `__doc__` attribute.
To compensate, pdoc will read the abstract syntax tree (an abstract representation of the source code)
and include all assignment statements immediately followed by a docstring. This approach is not formally standardized,
but followed by many tools, including Sphinx's autodoc extension in case you ever decide to migrate off pdoc.
Docstring detection is limited to the current module, docstrings for variables imported from other modules are not
picked up.

Something similar is done for instance variables, which are either type-annotated in the class
or defined in a class's `__init__`. Here is an example showing both conventions detected by pdoc:

```python
class GoldenRetriever(Dog):
    name: str
    """Full Name"""

    def __init__(self):
        self.weight: int = 10
        """Weight in kilograms"""
```


If you would like to distinguish an instance variable from a class variable,
you can use [`typing.ClassVar`](https://docs.python.org/3/library/typing.html#typing.ClassVar):

```python
class GoldenRetriever(Dog):
    breed_code: ClassVar[str] = "GOLD"
    """International breed code (same for all instances)"""
    name: str
    """Full Name (different for each instance)"""
```

## ...control what is documented?

The public interface of a module is determined through one of two
ways.

- If `__all__` is defined in the module, then all identifiers in that list will be considered public.
   No other identifiers will be considered public.
- If `__all__` is not defined, then pdoc will consider all members public that
   1. do not start with an underscore
   2. and are defined in the current module (i.e. they are not imported).

In general, we recommend keeping these conventions:

- If you want to document a private member, consider making it public.
- If you want to hide a public member, consider making it private.
- If you want to document a special `__dunder__` method, the recommended way to do so is
  to not document the dunder method specifically, but to add some usage examples in the class documentation.

As a last resort, you can override pdoc's behavior with a custom module template (see
[*How can I edit pdoc's HTML template?*](#edit-pdocs-html-template)).
You can find an example at
[`examples/custom-template/module.html.jinja2`](https://github.com/mitmproxy/pdoc/blob/main/examples/custom-template/module.html.jinja2).

### ...exclude submodules from being documented?

If you would like to exclude specific submodules from the documentation, the recommended way is to specify `__all__` as
shown in the previous section. Alternatively, you can pass negative regular expression `!patterns` as part of the
module specification. Each pattern removes all previously specified (sub)module names that match. For example, the following
invocation documents `foo` and all submodules of `foo`, but not `foo.bar`:

```
pdoc foo !foo.bar
```

Likewise, `pdoc pdoc !pdoc.` would document the pdoc module itself, but none of its submodules. Patterns are always
matched on the final module name, even if modules are passed as file paths.

## ...link to other identifiers?

In your documentation, you can link to other identifiers by enclosing them in backticks:
<code>\`pdoc\`</code> will link to `pdoc`.
When linking to identifiers in other modules, the identifier name must be fully qualified.
For example, <code>\`pdoc.doc.Doc\`</code> will be automatically linked to `pdoc.doc.Doc`,
while <code>\`Doc\`</code> only works within the `pdoc.doc` module.

pdoc will link all identifiers that are rendered in the current run.
This means that you need to run `pdoc module_a module_b` to have interlinking between module_a and module_b.
If you run `pdoc module_a` followed by `pdoc module_b`, there will be no cross-linking between the two modules.

## ...change the item order?

By default, documentation items are sorted in order of (first) appearance in the source code.
This means that if you want to move a particular function to the beginning of your documentation,
you need to move it there in your source code. This is not only useful to the readers of your documentation,
but also useful to the consumers of your source code.

## ...use numpydoc or Google docstrings?

While pdoc prefers docstrings that are plain Markdown, it also understands numpydoc and Google-style docstrings.
If your documentation follows one of these styles, you can:

1. Run `pdoc --docformat ...` to enable a particular docstring flavor globally, or
2. Add `__docformat__ = "..."` at the top-level of the module you are documenting.

The following values are supported:

- `markdown`: Process Markdown syntax only.
- `restructuredtext`: Process reStructuredText elements, then Markdown (default setting).
- `google`: Process reStructuredText elements, then Google-style syntax, then Markdown.
- `numpy`: Process reStructuredText elements, then Numpydoc syntax, then Markdown.

pdoc only interprets a subset of the reStructuredText specification.
Adding additional syntax elements is usually easy. If you feel that pdoc doesn't parse a docstring element properly,
please amend `pdoc.docstrings` and send us a pull request!


## ...render math formulas?

Run `pdoc --math`, and pdoc will render formulas in your docstrings. See
[`math_demo`](https://pdoc.dev/docs/math/math_demo.html) for details.


## ...add my project's logo?

See [*Configuring pdoc*](#configuring-pdoc).


## ...include Markdown files?

You can include external Markdown files in your documentation by using reStructuredText's
`.. include::` directive. For example, a common pattern is to include your project's README in your top-level `__init__.py` like this:

```python
"""
.. include:: ../README.md
"""
```

Since version 11, pdoc processes such reStructuredText elements by default.


## ...edit pdoc's HTML template?

For more advanced customization, we can edit pdoc's
[default HTML template](https://github.com/mitmproxy/pdoc/blob/main/pdoc/templates/default/module.html.jinja2),
which uses the
[Jinja2](https://jinja.palletsprojects.com/) templating language.

Let's assume you want to replace the logo with a custom button. We first find the right location in the template by searching
for "logo", which shows us that the logo is defined in a Jinja2 block named `nav_title`.
We now extend the default template by creating a file titled `module.html.jinja2` in the current directory
 with the following contents:

```html+jinja
{% extends "default/module.html.jinja2" %}
{% block nav_title %}
<button>Donate dog food</button>
{% endblock %}
```

We then specify our custom template directory when invoking pdoc...

```shell
pdoc -t . ./demo.py
```

...and the updated documentation – with button – renders! 🎉

See [`examples/`](https://github.com/mitmproxy/pdoc/tree/main/examples/)
for more examples.

## ...pass arguments to the Jinja2 template?

If you need to pass additional data to pdoc's Jinja2 templates,
you can use system environment variables.
For example,
[`examples/custom-template/module.html.jinja2`](https://github.com/mitmproxy/pdoc/blob/main/examples/custom-template/module.html.jinja2)
shows how to include a version number in the rendered HTML.


## ...integrate pdoc into other systems?

pdoc's HTML and CSS are written in a way that the default template can be easily adjusted
to produce standalone HTML fragments that can be embedded in other systems.
This makes it possible to integrate pdoc with almost every CMS or static site generator.
The only limitation is that you need to retain pdoc's directory structure
if you would like to link between modules.

To do so, [create a custom `frame.html.jinja2` template](#edit-pdocs-html-template) which only emits CSS and the main
page contents instead of a full standalone HTML document:
```html+jinja
{% block content %}{% endblock %}

{% filter minify_css %}
    {% block style %}
        {# The same CSS files as in pdoc's default template, except for layout.css.
        You may leave out Bootstrap Reboot, which corrects inconsistences across browsers
        but may conflict with you website's stylesheet. #}
        <style>{% include "resources/bootstrap-reboot.min.css" %}</style>
        <style>{% include "syntax-highlighting.css" %}</style>
        <style>{% include "theme.css" %}</style>
        <style>{% include "content.css" %}</style>
    {% endblock %}
{% endfilter %}
```

This should be enough to produce HTML files that can be embedded into other pages.
All CSS selectors are prefixed with `.pdoc` so that pdoc's page style does not interfere with the rest of your website.

You can find a full example for mkdocs in [`examples/mkdocs`](https://github.com/mitmproxy/pdoc/tree/main/examples/mkdocs/).


# Docstring Inheritance

pdoc extends the standard use of docstrings in two important ways:
by introducing variable docstrings (see [*How can I document variables?*](#document-variables)),
and by allowing functions and classes to inherit docstrings and type annotations.

This is useful to not unnecessarily repeat information. Consider this example:

```python
class Dog:
    def bark(self, loud: bool) -> None:
        """
        Make the dog bark. If `loud` is True,
        use full volume. Not supported by all breeds.
        """

class GoldenRetriever(Dog):
    def bark(self, loud: bool) -> None:
        print("Woof Woof")
```

In Python, the docstring for `GoldenRetriever.bark` is empty, even though one was
defined in `Dog.bark`. If pdoc generates documentation for the above
code, then it will automatically attach the docstring for `Dog.bark` to
`GoldenRetriever.bark` if it does not have a docstring.


# Limitations

  - **Scope:** pdoc main use case is API documentation.
    If you have substantially more complex documentation needs, we recommend using [Sphinx](https://www.sphinx-doc.org/)!
  - **Dynamic analysis:** pdoc makes heavy use of dynamic analysis to extract docstrings.
    This means your Python modules will be executed/imported when pdoc runs.
  - **HTML Output:** pdoc only supports HTML as an output format. If you want to use pdoc with a static site
    generator that only accepts Markdown, that may work nonetheless – take a look at
    [integrating pdoc into other systems](https://pdoc.dev/docs/pdoc.html#integrate-pdoc-into-other-systems).


# Using pdoc as a library

pdoc provides the high-level `pdoc.pdoc()` interface explained below. This makes it possible to do custom adjustments
to your Python code before pdoc is used.

It is also possible to create `pdoc.doc.Module` objects directly and modify them before rendering.
You can find an example in [`examples/library-usage`](https://github.com/mitmproxy/pdoc/tree/main/examples/library-usage).
'''
from __future__ import annotations

__docformat__ = "markdown"  # explicitly disable rST processing in the examples above.
__version__ = "11.0.0"  # this is read from setup.py

import traceback
import warnings
from pathlib import Path
from typing import overload

from pdoc import doc, extract, render
from pdoc._compat import Literal


@overload
def pdoc(
    *modules: Path | str,
    output_directory: None = None,
    format: Literal["html"] = "html",
) -> str:
    pass


@overload
def pdoc(
    *modules: Path | str,
    output_directory: Path,
    format: Literal["html"] = "html",
) -> None:
    pass


def pdoc(
    *modules: Path | str,
    output_directory: Path | None = None,
    format: Literal["html"] = "html",
) -> str | None:
    """
    Render the documentation for a list of modules.

     - If `output_directory` is `None`, returns the rendered documentation
       for the first module in the list.
     - If `output_directory` is set, recursively writes the rendered output
       for all specified modules and their submodules to the target destination.

    Rendering options can be configured by calling `pdoc.render.configure` in advance.
    """
    if format not in ("html", "markdown", "repr"):
        raise ValueError(f"Invalid rendering format {format!r}.")
    if format == "markdown":  # pragma: no cover
        raise NotImplementedError(
            "Markdown support is currently unimplemented, but PRs are welcome!"
        )

    all_modules: dict[str, doc.Module] = {}
    for module_name in extract.walk_specs(modules):
        try:
            all_modules[module_name] = doc.Module.from_name(module_name)
        except RuntimeError:
            warnings.warn(f"Error importing {module_name}:\n{traceback.format_exc()}")

    if not all_modules:
        raise RuntimeError("Unable to import any modules.")

    for module in all_modules.values():
        if format == "html":
            out = render.html_module(module, all_modules)
        else:
            out = render.repr_module(module)

        if not output_directory:
            return out
        else:
            outfile = output_directory / f"{module.fullname.replace('.', '/')}.html"
            outfile.parent.mkdir(parents=True, exist_ok=True)
            outfile.write_bytes(out.encode())

    assert output_directory
    if format == "html":
        index = render.html_index(all_modules)
        if index:
            (output_directory / "index.html").write_bytes(index.encode())

        search = render.search_index(all_modules)
        if search:
            (output_directory / "search.js").write_bytes(search.encode())

    return None

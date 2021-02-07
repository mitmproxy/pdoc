# Release History

# 2021-02-07 pdoc 6.1.0

 - Add compatibility for Python 3.7

# 2021-02-07 pdoc 6.0.0

 - Add dark mode theme (@Arkelis)
   pdoc's color scheme can now be customized with CSS variables.
   This may be a minor breaking change for users who have heavily customized their templates.
 - Docs: Add an example how to integrate pdoc with mkdocs.
 - Bugfix: pdoc now retains custom rendering configuration when it renders itself with live-reload.

# 2021-02-05 pdoc 5.0.0

 - Make it easier to embed pdoc into other systems:
   See <https://pdoc.dev/docs/pdoc.html#integrate-pdoc-into-other-systems> for details.
   This change may be a minor breaking change for users using custom templates.
 - Generic class bases are now displayed fully. 
   This may be a minor breaking change for users who customized class base output.
 - Add header anchors to documentation items.
 - Define all Jinja2 macros as `{% defaultmacro %}`, which makes them easier to override.
 - Parsing is not more robust if source code is unavailable.
 - Bugfix: Functions decorated with `@classmethod` now also inherit their docstring.
 - Bugfix: The "View Source" marker is now properly displayed in Firefox.

# 2021-02-01 pdoc 4.0.0

 - Improve how inherited members are detected.
   `Doc.declared_at` is superseded by `Doc.taken_from`,
   which is a relatively minor but breaking change in the Python API.
 - Bugfix: Don't link private members in the same module.
 - Improve error message when module live-reload fails.
 - Smaller favicon, improved CSS minification
 - Improve error message if module is not found.

# 2021-01-26 pdoc 3.0.1

 - Fix usage of `--docformat`.

# 2021-01-24 pdoc 3.0.0

 - Add support for alternative docstring flavors.
   Flavors can be enabled globally using `--docformat` or on a per-module
   basis using `__docformat__ = "..."`.
 - Add support for Google docstrings.
 - Add basic support for Numpydoc and reStructuredText docstrings.
   The most common rST elements are supported, but we do not intend
   to support the full complexity of the spec.
 - Links within the current module now don't require the full qualified path.
 - Live-reloading is now more robust.
 - Improvements to the default theme.

# 2021-01-22: pdoc 2.0.0

 - Make it possible to selectively include private or exclude public members in templates.  
   This comes with a breaking change: `pdoc.doc.Namespace.members` now includes private members.
 - Enhancement: Keep page position when live-reloading.
 - Enhancement: Don't show common server connection errors in the console.

# 2021-01-20: pdoc 1.1.0

 - pdoc now respects `__all__` when listing submodules.

# 2021-01-19: pdoc 1.0.1

 - Test CI processes by shipping a quick patch release.
 - Bugfix: Don't crash on lambdas as class attributes.
 - Bugfix: Don't crash on comments between decorators.
 - Bugfix: Don't crash pdoc if a user's custom __getattr__ implementation is crashing.
 - Bugfix: use `inspect.unwrap` instead of unwrapping manually.

# 2021-01-19: pdoc 1.0.0

This release features a major rewrite of pdoc, dropping compatibility
with Python 2 and focusing on modern Python 3 only.

 - Added: First-class support for type annotations
 - Added: Simpler directory structure
 - Added: New responsive documentation theme
 - Added: New website and documentation
 - Added: 100% test coverage and CI
 - Use Jinja2 instead of mako.
 - Removed: Support for `__pdoc__`, which is rarely required
   when following modern Python standards. This feature may return
   depending on user feedback.
 - Removed: Markdown output. The project now focuses on HTML documentation.
   PRs to re-add markdown support will be gladly accepted.

pdoc is now maintained by [@mhils](https://github.com/mhils) and the rest of the mitmproxy team.


# pdoc 0.3.2

  - Bugfix release.


# pdoc 0.3.1

  - Source code is extracted from __wrapped__ if it exists, and then
    falls back to inspect.getsourcelines. This reverses the behavior
    implemented in #6.
  - Fix Python 2.6 compatibility by requiring Markdown < 2.5 (#19).
    Markdown 2.5 dropped support for Python 2.6.
  - Get rid of tabs that sneaked in from #17.
  - Fix pep8 violations.

# pdoc 0.3.0

  - Major HTML face lift. Kudos to @knadh!
    (PR: https://github.com/mitmproxy/pdoc/pull/17)

# pdoc 0.2.4

  - Fixed bug in HTTP server that was referencing a non-existent
    variable.

# pdoc 0.2.3

  - Fixed #10 (the --template-dir flag now works).

# pdoc 0.2.2

  - Fixes #7 by ignoring module loaders that lack a 'path' attribute.

# pdoc 0.2.1

  - Fixes #5 by trying to find source for decorated functions.
    (@austin1howard)

# pdoc 0.2.0

  - Fix issue #2 by making pdoc a package instead of a module.
    The templates are now included as package_data, which seems
    to be more portable (its final location is more predictable).

# pdoc 0.1.8

  - pdoc now interprets `__pdoc__[key] = None` as an explicit way
    to hide `key` from the public interface of its module.

# pdoc 0.1.7

  - Removed __new__ from the public interface. I think __init__
    is sufficient.

# pdoc 0.1.6

  - Fixed bug #1.

# pdoc 0.1.5

  - Fixed a bug with an improper use of getattr.
  - Made pdoc aware of __slots__. (Every identifier in __slots__
    is automatically interpreted as an instance variable.)

# pdoc 0.1.4

  - Fixed bug where getargspec wasn't being used in Python 2.x.

# pdoc 0.1.3

  - Avoid a FQDN lookup.

# pdoc 0.1.2

  - A few doco touchups.
  - Fixed a bug in Py3K. Use getfullargspec when available.

# pdoc 0.1.1

  - Documentation touch ups.
  - Removed unused command line flags.

# pdoc 0.1.0

First public release.

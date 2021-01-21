# Release History

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

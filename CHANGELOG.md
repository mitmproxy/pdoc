# Release History

# Unreleased: pdoc next

 - The search functionality now also covers function parameters,
   annotated types, default values, and base classes.
 - Work around a Blink renderer bug to make sure that the small "expand" triangle is displayed next to the
   *View Source* button.
 - Add negated module specs to exclude specific (sub)modules.
   For example, `pdoc foo !foo.bar` documents `foo` and all submodules of `foo` except `foo.bar`.
 - Only display headings up to a depth of 2 in the table of contents for module docstrings.

# 2022-01-05: pdoc 8.2.0

 - Improve rendering of warnings emitted by pdoc.
 - Improve search quality by disabling the word stemmer.
 - Fix a bug where the search bar on the index page did not work if only a single module was documented.
 - Add a warning when multiple modules with the same name are added from different paths.

# 2021-12-28: pdoc 8.1.0

 - Add CSS styling for Markdown tables. (@sitic)
 - Prefer epydoc-style docstrings after variable assignments 
   over the variable's `__doc__`.
 - Improve error message on search index compilation failures.

# 2021-10-29: pdoc 8.0.1

 - Fix an edge case where class annotations were not evaluated properly.
 - Improve error messages for invalid type hints.
 - Fix module index when using pdoc's web server.

# 2021-09-19: pdoc 8.0.0

 - `search.json` -> `search.js`: Most of pdoc's search-related JavaScript code is now
   only fetched on demand, which improves page size and performance.
 - pdoc's search now works from `file://` pages.
 - Improve display of (extension module) data descriptors.

# 2021-08-18: pdoc 7.4.0

 - Display error webpage for template errors.
 - When processing type hints, detect imports in 
   [`TYPE_CHECKING`](https://docs.python.org/3/library/typing.html#typing.TYPE_CHECKING) 
   blocks.
 - Add `--no-search` to disable search functionality.

# 2021-08-09: pdoc 7.3.1

 - Fix a bug where an empty footer was incorrectly emitted by the template.

# 2021-08-09: pdoc 7.3.0

 - Full compatibility with Python 3.10.
 - Many template customizations are now directly available as command line switches, for example:
    - `--math`
    - `--logo`
    - `--no-show-source`
    - `--footer-text`

# 2021-07-28: pdoc 7.2.0

 - Don't include variables/attributes that only have a type annotation but no value and no docstring.
   If one wants to document a variable, a docstring should be added.
 - Templating: `render_docstring` is split into `to_markdown` and `to_html` to increase customizability.
 - Fix hot-reloading of included Markdown files.
 - Allow Google docstring section headers to contain spaces.
 - Fix formatting of Google docstrings that have multiple colons.
 - Fix a crash when importing a module from within its directory.

# 2021-06-11: pdoc 7.1.1

 - Do not show constructors for abstract base classes unless they have a custom docstring.
 - Fix math example to render formulae in search results.

# 2021-06-03: pdoc 7.1.0

 - Invoking `pdoc` without any arguments now asks the user to specify module name
   instead of starting pdoc with all available modules. The previous implementation 
   had a poor user experience as building the search index took too long.
 - Improve documentation of `pdoc.extract`. `pdoc.extract.parse_specs` has been renamed to `walk_specs`, 
   the old API now emits a deprecation warning.
 - Add `pdoc.doc.Doc.source_lines` to access where in a file an object is defined.
 - Fix a crash when importing `asyncio` on Windows on Python 3.7. 

# 2021-05-30: pdoc 7.0.3

 - Do not show a search bar on the module page if only one module is documented.
   If the entire documentation is contained on a single HTML page, the browser's search functionality is just as good.
   Users can piggyback on their preexisting knowledge about the search semantics in this case.

# 2021-05-27: pdoc 7.0.2

 - Fix section indentation in Google-style docstrings.

# 2021-05-21: pdoc 7.0.1

 - Fix compatibility with older Jinja2 versions.
 - Fix basic compatibility with Python 3.10b1.

# 2021-05-12: pdoc 7.0.0

 - Add search functionality.
   pdoc now has a search bar which allows users to quickly
   find relevant parts in the documentation.
   See https://pdoc.dev/docs/pdoc/search.html for details.
 - Redesign module list (index.html.jinja2).
 - Update Bootstrap to v5.0.0.
 - Do not fail if `inspect.getdoc()` raises.
 - Fix compatibility with Jinja2 3.0.0.

# 2021-04-30: pdoc 6.6.0

 - Jinja2 templates can now access system environment variables,
   for example to pass version information.

# 2021-04-29: pdoc 6.5.0

 - Add support for `.. include::` directives to include external Markdown files.
 - Add word break points for long module and class names. (@jstriebel)

# 2021-04-21: pdoc 6.4.4

 - Fix a crash when `inspect.signature` returns incomplete source code.
 - Fix a crash when inspecting unhashable functions.

# 2021-04-11: pdoc 6.4.3

 - Fix a bug when dedenting multi-line decorators.
 - Make it easier to change the logo on the module index page.

# 2021-03-28: pdoc 6.4.2

 - Minor rendering improvements for enums and typing.NamedTuples.
 - pdoc now emits a warning when directory names conflict with modules
   already loaded by pdoc.
 - If a class is publicly reimported in the current module, pdoc now links to
   the reimported instance instead of the source location.

# 2021-03-19: pdoc 6.4.1

 - Private function decorators (those starting with "\_")
   are now hidden by default. (@zmoon)
 - If pdoc is invoked with a name that is both an installed Python module 
   and a local directory, notify the user that the installed module will be documented.
 - `__doc__` is now not rendered as a variable, even if included in `__all__`.
 - Submodules are now internally assigned a qualname, which fixes broken anchor links.

# 2021-03-10: pdoc 6.4.0

 - Functions in the current scope can now be referenced without specifying
   the full qualified name. For example, one can use `bar()` instead of 
   `Foo.bar()` in the docstring of `Foo`.
 - Numpydoc: *See Also* sections are now parsed properly.
 - reStructuredText: Add support for footnotes and fix minor bugs.

# 2021-02-24: pdoc 6.3.2

 - Bugfix: Docstrings for data descriptors are now captured properly.
 - Add an example for math formula rendering.

# 2021-02-15: pdoc 6.3.1

 - Cosmetic improvements in default value rendering:
   object and function memory addresses are now stripped.
 - Accessibility Improvements

# 2021-02-14: pdoc 6.3.0

 - Respect `__all__` when collecting submodules.
 - Correct wrong links in module index (@fweisser)
 - Emit more detailed error messages on import failure.

# 2021-02-12: pdoc 6.2.0

 - Improvement: Add syntax highlighting in ">>>" code block examples.
 - Bugfix: Module-level comments are not properly live-reloaded.

# 2021-02-12 pdoc 6.1.1

 - Bugfix: Don't eat underscores in numpy/Google-style docstrings.
 - Bugfix: Fix rendering of typing.NamedTuple.

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

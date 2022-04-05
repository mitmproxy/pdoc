# 📑 pdoc templates

This directory contains pdoc's default templates, which you can extend in your own template directory. See
[the documentation](https://pdoc.dev/docs/pdoc.html#edit-pdocs-html-template) for an example.

For customization, the most important files are:

**Main HTML Templates**

 - `default/module.html.jinja2`: Template for documentation pages.
 - `default/index.html.jinja2`: Template for the top-level `index.html`.
 - `default/frame.html.jinja2`: The common page layout for `module.html.jinja2` and `index.html.jinja2`.

**CSS Stylesheets**

 - `custom.css`: Empty be default, add custom additional rules here.
 - `content.css`: All style definitions for documentation contents.
 - `layout.css`: All style definitions for the page layout (navigation, sidebar, ...).
 - `theme.css`: Color definitions (see [`examples/dark-mode`](../../examples/dark-mode)).
 - `syntax-highlighting.css`: Code snippet style, see below.

## Extending templates

pdoc will first check for `$template.jinja2` before checking `default/$template.jinja2`. This allows you to reuse the
macros from the main templates in `default/`. For example, you can create a `module.html.jinja2` file in your custom 
template directory that extends the default template as follows:

```html
{% extends "default/module.html.jinja2" %}
{% block title %}new page title{% endblock %}
```

## Syntax Highlighting

The `syntax-highlighting.css` file contains the CSS styles used for syntax highlighting.
It is generated as follows:

```
pygmentize -f html -a .pdoc-code -S <theme> > default/syntax-highlighting.css
```

The default theme is `default`, with extended padding added to the `.linenos` class.
Alternative color schemes can be tested on [the Pygments website](https://pygments.org/demo/).

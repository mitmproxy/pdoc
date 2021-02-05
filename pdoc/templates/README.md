This directory contains pdoc's default templates, which you can extend in your own code.

## Extending templates

pdoc will first check for `$template.jinja2` before checking `default/$template.jinja2`. For example, you can create
a `module.html.jinja2` file in your custom template directory that extends the default template as follows:

```html
{% extends "default/module.html.jinja2" %}
{% block title %}new page title{% endblock %}
```

## Changing the code highlighting themes

The `code-highlighting.css` file contains the CSS styles used to add code
source highlighting for both light and dark themes. Default color schemes
are `default` (light theme) and `monokai` (dark theme). To change them,
you can generate your own file by running:

```
pygmentize -S <theme> -f html > code-highlighting.css
```

Then, you can add a dark color scheme:

```
echo "\n@media(prefers-color-scheme: dark){ \
      \n$(pygmentize -S <theme> -f html)\n}" >> code-highlighting.css
```

You can test different builtin themes on [the Pygments website](https://pygments.org/demo/).

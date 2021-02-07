This directory contains pdoc's default templates, which you can extend in your own code.

## Extending templates

pdoc will first check for `$template.jinja2` before checking `default/$template.jinja2`. For example, you can create
a `module.html.jinja2` file in your custom template directory that extends the default template as follows:

```html
{% extends "default/module.html.jinja2" %}
{% block title %}new page title{% endblock %}
```

## Syntax Highlighting

The `syntax-highlighting.css` file contains the CSS styles used to add
source code syntax highlighting.
They are generated as follows:

```
pygmentize -f html -a .pdoc -S <theme> > syntax-highlighting.css
```

Optionally, add a dark color scheme:

```
echo -e "\n@media(prefers-color-scheme: dark){ \
      \n$(pygmentize -f html -a .pdoc -S <theme>)\n}" >> syntax-highlighting.css
```

The default color schemes are `default` (light theme) and `monokai` (dark theme). 
You can test different builtin themes on [the Pygments website](https://pygments.org/demo/).

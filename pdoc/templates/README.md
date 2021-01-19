This directory contains pdoc's default templates, which you can extend in your own code.

## Extending templates

pdoc will first check for `$template.jinja2` before checking `default/$template.jinja2`. For example, you can create
a `module.html.jinja2` file in your custom template directory that extends the default template as follows:

```html
{% extends "default/module.html.jinja2" %}
{% block title %}new page title{% endblock %}
```

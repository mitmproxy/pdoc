# Using a Custom Template

This is an example showing how one can customize pdoc's default template.  
The individual changes are explained in the template files themselves.

To use a custom template, run pdoc with the `--template-directory` (short: `-t`) command line argument:

```
pdoc -t ./examples/custom-template pdoc
```

### Additional Resources for Template Development

 - [pdoc's Default Templates](https://github.com/mitmproxy/pdoc/tree/main/pdoc/templates)
 - [Jinja2 Template Designer Documentation](https://jinja.palletsprojects.com/en/2.11.x/templates/)

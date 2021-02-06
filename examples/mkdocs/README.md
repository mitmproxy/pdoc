# mkdocs with pdoc

This is an example showing how to use pdoc with [mkdocs](https://www.mkdocs.org).
Run `./make.py` to generate the API documentation and then `mkdocs serve` to view this website!

## Implementation

The main trick is that we define a custom `frame.html.jinja2` and `module.html.jinja2` to
remove the usual HTML frame and layout. We then invoke pdoc normally and rename the output files to `.md` so 
that they are picked up by mkdocs.

## Limitations

 - If you want to link between different pages in your documentation,
   pdoc requires `use_directory_urls: false` for linking to work.
 - pdoc doesn't populate mkdocs' table of contents as all raw HTML is ignored by mkdocs' Markdown parser.
   You can hide the table of contents with some custom CSS in `frame.html.jinja2`.

A simple program (and library) to auto generate API documentation for Python 
libraries. All documentation text is parsed as Markdown and can be outputted as 
HTML or as plain text for console use. There are no special syntax rules, just 
pure Markdown.

While pdoc tries to stay consistent with documentation practices recommend by 
PEP 8 and PEP 257, pdoc also looks for documentation of representation in some 
places just as epydoc does. Namely, docstrings proceeding module level 
variables, class variables and instance variables in `__init__` methods. This 
is done by traversing the ast of the source text.


"""
Module pdoc provides types and functions for accessing the public
documentation of a Python module. This includes modules (and
sub-modules), functions, classes and module, class and instance
variables.  Docstrings are taken from modules, functions and classes
using the special `__doc__` attribute. Docstrings for variables are
extracted by examining the module's abstract syntax tree.

The public interface of a module is determined through one of two
ways. If `__all__` is defined in the module, then all identifiers in
that list will be considered public. No other identifiers will be
considered as public. Conversely, if `__all__` is not defined, then
`pdoc` will heuristically determine the public interface. There are
three rules that are applied to each identifier in the module:

1. If the name starts with an underscore, it is **not** public.

2. If the name is defined in a different module, it is **not** public.

3. If the name refers to an immediate sub-module, then it is public.

Once documentation for a module is created with `pdoc.Module`, it
can be output as either HTML or plain text using the covenience
functions `pdoc.html` and `pdoc.text`, or the corresponding methods
`pdoc.Module.html` and `pdoc.Module.text`.

Alternatively, you may run an HTTP server with the `pdoc` script
included with this module.


Compatibility
-------------
`pdoc` has been tested on Python 2.6, 2.7 and 3.3. It seems to work
on all three.


Contributing
------------
`pdoc` [is on GitHub](https://github.com/BurntSushi/pdoc). Pull
requests and bug reports are welcome.


Linking to other identifiers
----------------------------
In your documentation, you may link to other identifiers in
your module or submodules. Linking is automatically done for
you whenever you surround an identifier with a back quote
(grave). The identifier name must be fully qualified. For
example, <code>\`pdoc.Doc.docstring\`</code> is correct while
<code>\`Doc.docstring\`</code> is incorrect.

If the `pdoc` script is used to run an HTTP server, then external
linking to other packages installed is possible. No extra work is
necessary; simply use the fully qualified path. For example,
<code>\`nflvid.slice\`</code> will create a link to the `nflvid.slice`
function, which is **not** a part of `pdoc` at all.


Where does pdoc get documentation from?
---------------------------------------
Broadly speaking, `pdoc` gets everything you see from introspecting the
module. This includes words describing a particular module, class,
function or variable. While `pdoc` does some analysis on the source
code of a module, importing the module itself is necessary to use
Python's introspection features.

In Python, objects like modules, functions, classes and methods have
a special attribute named `__doc__` which contains that object's
*docstring*.  The docstring comes from a special placement of a string
in your source code.  For example, the following code shows how to
define a function with a docstring and access the contents of that
docstring:

    #!python
    >>> def test():
    ...     '''This is a docstring.'''
    ...     pass
    ...
    >>> test.__doc__
    'This is a docstring.'

Something similar can be done for classes and modules too. For classes,
the docstring should come on the line immediately following `class
...`. For modules, the docstring should start on the first line of
the file. These docstrings are what you see for each module, class,
function and method listed in the documentation produced by `pdoc`.

The above just about covers *standard* uses of docstrings in Python.
`pdoc` extends the above in a few important ways.


### Special docstring conventions used by `pdoc`

**Firstly**, docstrings can be inherited. Consider the following code
sample:

    #!python
    >>> class A (object):
    ...     def test():
    ...         '''Docstring for A.'''
    ...
    >>> class B (A):
    ...     def test():
    ...         pass
    ...
    >>> print(A.test.__doc__)
    Docstring for A.
    >>> print(B.test.__doc__)
    None

In Python, the docstring for `B.test` is empty, even though one was
defined in `A.test`. If `pdoc` generates documentation for the above
code, then it will automatically attach the docstring for `A.test` to
`B.test` only if `B.test` does not have a docstring. In the default
HTML output, an inherited docstring is grey.

**Secondly**, docstrings can be attached to variables, which includes
module (or global) variables, class variables and instance variables.
Python by itself [does not allow docstrings to be attached to
variables](http://www.python.org/dev/peps/pep-0224). For example:

    #!python
    variable = "SomeValue"
    '''Docstring for variable.'''

The resulting `variable` will have no `__doc__` attribute. To
compensate, `pdoc` will read the source code when it's available to
infer a connection between a variable and a docstring. The connection
is only made when an assignment statement is followed by a docstring.

Something similar is done for instance variables as well. By
convention, instance variables are initialized in a class's `__init__`
method.  Therefore, `pdoc` adheres to that convention and looks for
docstrings of variables like so:

    #!python
    def __init__(self):
        self.variable = "SomeValue"
        '''Docstring for instance variable.'''

Note that `pdoc` only considers attributes defined on `self` as
instance variables.

Class and instance variables can also have inherited docstrings.

**Thirdly and finally**, docstrings can be overridden with a special
`__pdoc__` dictionary that `pdoc` inspects if it exists. The keys of
`__pdoc__` should be identifiers within the scope of the module. (In
the case of an instance variable `self.variable` for class `A`, its
module identifier would be `A.variable`.) The values of `__pdoc__`
should be docstrings.

This particular feature is useful when there's no feasible way of
attaching a docstring to something. A good example of this is a
[namedtuple](http://goo.gl/akfXJ9):

    #!python
    __pdoc__ = {}

    Table = namedtuple('Table', ['types', 'names', 'rows'])
    __pdoc__['Table.types'] = 'Types for each column in the table.'
    __pdoc__['Table.names'] = 'The names of each column in the table.'
    __pdoc__['Table.rows'] = 'Lists corresponding to each row in the table.'

`pdoc` will then show `Table` as a class with documentation for the
`types`, `names` and `rows` members.

Note that assignments to `__pdoc__` need to placed where they'll be
executed when the module is imported. For example, at the top level
of a module or in the definition of a class.

If `__pdoc__[key] = None`, then `key` will not be included in the
public interface of the module.


License
-------
`pdoc` is in the public domain via the
[UNLICENSE](http://unlicense.org).
"""
from __future__ import absolute_import, division, print_function
import ast
import imp
import inspect
import os
import os.path as path
import pkgutil
import re
import sys

from mako.lookup import TemplateLookup
from mako.exceptions import TopLevelLookupException

__version__ = '0.3.2'
"""
The current version of pdoc. This value is read from `setup.py`.
"""

html_module_suffix = '.m.html'
"""
The suffix to use for module HTML files. By default, this is set to
`.m.html`, where the extra `.m` is used to differentiate a package's
`index.html` from a submodule called `index`.
"""

html_package_name = 'index.html'
"""
The file name to use for a package's `__init__.py` module.
"""

import_path = sys.path[:]
"""
A list of paths to restrict imports to. Any module that cannot be
found in `import_path` will not be imported. By default, it is set to a
copy of `sys.path` at initialization.
"""

_template_path = [
    path.join(path.dirname(__file__), 'templates'),
]
"""
A list of paths to search for Mako templates used to produce the
plain text and HTML output. Each path is tried until a template is
found.
"""
if os.getenv('XDG_CONFIG_HOME'):
    _template_path.insert(0, path.join(os.getenv('XDG_CONFIG_HOME'), 'pdoc'))

__pdoc__ = {}
tpl_lookup = TemplateLookup(directories=_template_path,
                            cache_args={'cached': True,
                                        'cache_type': 'memory'})
"""
A `mako.lookup.TemplateLookup` object that knows how to load templates
from the file system. You may add additional paths by modifying the
object's `directories` attribute.
"""


def html(module_name, docfilter=None, allsubmodules=False,
         external_links=False, link_prefix='', source=True):
    """
    Returns the documentation for the module `module_name` in HTML
    format. The module must be importable.

    `docfilter` is an optional predicate that controls which
    documentation objects are shown in the output. It is a single
    argument function that takes a documentation object and returns
    `True` or `False`. If `False`, that object will not be included in
    the output.

    If `allsubmodules` is `True`, then every submodule of this module
    that can be found will be included in the documentation, regardless
    of whether `__all__` contains it.

    If `external_links` is `True`, then identifiers to external modules
    are always turned into links.

    If `link_prefix` is `True`, then all links will have that prefix.
    Otherwise, links are always relative.

    If `source` is `True`, then source code will be retrieved for
    every Python object whenever possible. This can dramatically
    decrease performance when documenting large modules.
    """
    mod = Module(import_module(module_name),
                 docfilter=docfilter,
                 allsubmodules=allsubmodules)
    return mod.html(external_links=external_links,
                    link_prefix=link_prefix, source=source)


def text(module_name, docfilter=None, allsubmodules=False):
    """
    Returns the documentation for the module `module_name` in plain
    text format. The module must be importable.

    `docfilter` is an optional predicate that controls which
    documentation objects are shown in the output. It is a single
    argument function that takes a documentation object and returns
    True of False. If False, that object will not be included in the
    output.

    If `allsubmodules` is `True`, then every submodule of this module
    that can be found will be included in the documentation, regardless
    of whether `__all__` contains it.
    """
    mod = Module(import_module(module_name),
                 docfilter=docfilter,
                 allsubmodules=allsubmodules)
    return mod.text()


def import_module(module_name):
    """
    Imports a module. A single point of truth for importing modules to
    be documented by `pdoc`. In particular, it makes sure that the top
    module in `module_name` can be imported by using only the paths in
    `pdoc.import_path`.

    If a module has already been imported, then its corresponding entry
    in `sys.modules` is returned. This means that modules that have
    changed on disk cannot be re-imported in the same process and have
    its documentation updated.
    """
    if import_path != sys.path:
        # Such a kludge. Only restrict imports if the `import_path` has
        # been changed. We don't want to always restrict imports, since
        # providing a path to `imp.find_module` stops it from searching
        # in special locations for built ins or frozen modules.
        #
        # The problem here is that this relies on the `sys.path` not being
        # independently changed since the initialization of this module.
        # If it is changed, then some packages may fail.
        #
        # Any other options available?

        # Raises an exception if the parent module cannot be imported.
        # This hopefully ensures that we only explicitly import modules
        # contained in `pdoc.import_path`.
        imp.find_module(module_name.split('.')[0], import_path)

    if module_name in sys.modules:
        return sys.modules[module_name]
    else:
        __import__(module_name)
        return sys.modules[module_name]


def _source(obj):
    """
    Returns the source code of the Python object `obj` as a list of
    lines. This tries to extract the source from the special
    `__wrapped__` attribute if it exists. Otherwise, it falls back
    to `inspect.getsourcelines`.

    If neither works, then the empty list is returned.
    """
    try:
        return inspect.getsourcelines(obj.__wrapped__)[0]
    except:
        pass
    try:
        return inspect.getsourcelines(obj)[0]
    except:
        return []


def _get_tpl(name):
    """
    Returns the Mako template with the given name.  If the template
    cannot be found, a nicer error message is displayed.
    """
    try:
        t = tpl_lookup.get_template(name)
    except TopLevelLookupException:
        locs = [path.join(p, name.lstrip('/')) for p in _template_path]
        raise IOError(2, 'No template at any of: %s' % ', '.join(locs))
    return t


def _eprint(*args, **kwargs):
    """Print to stderr."""
    kwargs['file'] = sys.stderr
    print(*args, **kwargs)


def _safe_import(module_name):
    """
    A function for safely importing `module_name`, where errors are
    suppressed and `stdout` and `stderr` are redirected to a null
    device. The obligation is on the caller to close `stdin` in order
    to avoid impolite modules from blocking on `stdin` when imported.
    """
    class _Null (object):
        def write(self, *_):
            pass

    sout, serr = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = _Null(), _Null()
    try:
        m = import_module(module_name)
    except:
        m = None
    sys.stdout, sys.stderr = sout, serr
    return m


def _var_docstrings(tree, module, cls=None, init=False):
    """
    Extracts variable docstrings given `tree` as the abstract syntax,
    `module` as a `pdoc.Module` containing `tree` and an option `cls`
    as a `pdoc.Class` corresponding to the tree. In particular, `cls`
    should be specified when extracting docstrings from a class or an
    `__init__` method. Finally, `init` should be `True` when searching
    the AST of an `__init__` method so that `_var_docstrings` will only
    accept variables starting with `self.` as instance variables.

    A dictionary mapping variable name to a `pdoc.Variable` object is
    returned.
    """
    vs = {}
    children = list(ast.iter_child_nodes(tree))
    for i, child in enumerate(children):
        if isinstance(child, ast.Assign) and len(child.targets) == 1:
            if not init and isinstance(child.targets[0], ast.Name):
                name = child.targets[0].id
            elif (isinstance(child.targets[0], ast.Attribute)
                    and isinstance(child.targets[0].value, ast.Name)
                    and child.targets[0].value.id == 'self'):
                name = child.targets[0].attr
            else:
                continue
            if not _is_exported(name) \
                    and name not in getattr(module, '__all__', []):
                continue

            docstring = ''
            if (i+1 < len(children)
                    and isinstance(children[i+1], ast.Expr)
                    and isinstance(children[i+1].value, ast.Str)):
                docstring = children[i+1].value.s

            vs[name] = Variable(name, module, docstring, cls=cls)
    return vs


def _is_exported(ident_name):
    """
    Returns `True` if `ident_name` matches the export criteria for an
    identifier name.

    This should not be used by clients. Instead, use
    `pdoc.Module.is_public`.
    """
    return not ident_name.startswith('_')


class Doc (object):
    """
    A base class for all documentation objects.

    A documentation object corresponds to *something* in a Python module
    that has a docstring associated with it. Typically, this only includes
    modules, classes, functions and methods. However, `pdoc` adds support
    for extracting docstrings from the abstract syntax tree, which means
    that variables (module, class or instance) are supported too.

    A special type of documentation object `pdoc.External` is used to
    represent identifiers that are not part of the public interface of
    a module. (The name "External" is a bit of a misnomer, since it can
    also correspond to unexported members of the module, particularly in
    a class's ancestor list.)
    """
    def __init__(self, name, module, docstring):
        """
        Initializes a documentation object, where `name` is the public
        identifier name, `module` is a `pdoc.Module` object, and
        `docstring` is a string containing the docstring for `name`.
        """
        self.module = module
        """
        The module documentation object that this object was defined
        in.
        """

        self.name = name
        """
        The identifier name for this object.
        """

        self.docstring = inspect.cleandoc(docstring or '')
        """
        The docstring for this object. It has already been cleaned
        by `inspect.cleandoc`.
        """

    @property
    def source(self):
        """
        Returns the source code of the Python object `obj` as a list of
        lines. This tries to extract the source from the special
        `__wrapped__` attribute if it exists. Otherwise, it falls back
        to `inspect.getsourcelines`.

        If neither works, then the empty list is returned.
        """
        assert False, 'subclass responsibility'

    @property
    def refname(self):
        """
        Returns an appropriate reference name for this documentation
        object. Usually this is its fully qualified path. Every
        documentation object must provide this property.

        e.g., The refname for this property is
        <code>pdoc.Doc.refname</code>.
        """
        assert False, 'subclass responsibility'

    def __lt__(self, other):
        return self.name < other.name

    def is_empty(self):
        """
        Returns true if the docstring for this object is empty.
        """
        return len(self.docstring.strip()) == 0


class Module (Doc):
    """
    Representation of a module's documentation.
    """

    __pdoc__['Module.module'] = 'The Python module object.'
    __pdoc__['Module.name'] = \
        """
        The name of this module with respect to the context in which
        it was imported. It is always an absolute import path.
        """

    def __init__(self, module, docfilter=None, allsubmodules=False):
        """
        Creates a `Module` documentation object given the actual
        module Python object.

        `docfilter` is an optional predicate that controls which
        documentation objects are returned in the following
        methods: `pdoc.Module.classes`, `pdoc.Module.functions`,
        `pdoc.Module.variables` and `pdoc.Module.submodules`. The
        filter is propagated to the analogous methods on a `pdoc.Class`
        object.

        If `allsubmodules` is `True`, then every submodule of this
        module that can be found will be included in the
        documentation, regardless of whether `__all__` contains it.
        """
        name = getattr(module, '__pdoc_module_name', module.__name__)
        super(Module, self).__init__(name, module, inspect.getdoc(module))

        self._filtering = docfilter is not None
        self._docfilter = (lambda _: True) if docfilter is None else docfilter
        self._allsubmodules = allsubmodules

        self.doc = {}
        """A mapping from identifier name to a documentation object."""

        self.refdoc = {}
        """
        The same as `pdoc.Module.doc`, but maps fully qualified
        identifier names to documentation objects.
        """

        vardocs = {}
        try:
            tree = ast.parse(inspect.getsource(self.module))
            vardocs = _var_docstrings(tree, self, cls=None)
        except:
            pass
        self._declared_variables = vardocs.keys()

        public = self.__public_objs()
        for name, obj in public.items():
            # Skip any identifiers that already have doco.
            if name in self.doc and not self.doc[name].is_empty():
                continue

            # Functions and some weird builtins?, plus methods, classes,
            # modules and module level variables.
            if inspect.isfunction(obj) or inspect.isbuiltin(obj):
                self.doc[name] = Function(name, self, obj)
            elif inspect.ismethod(obj):
                self.doc[name] = Function(name, self, obj)
            elif inspect.isclass(obj):
                self.doc[name] = Class(name, self, obj)
            elif inspect.ismodule(obj):
                # Only document modules that are submodules or are forcefully
                # exported by __all__.
                if obj is not self.module and \
                        (self.__is_exported(name, obj)
                         or self.is_submodule(obj.__name__)):
                    self.doc[name] = self.__new_submodule(name, obj)
            elif name in vardocs:
                self.doc[name] = vardocs[name]
            else:
                # Catch all for variables.
                self.doc[name] = Variable(name, self, '', cls=None)

        # Now scan the directory if this is a package for all modules.
        if not hasattr(self.module, '__path__') \
                and not hasattr(self.module, '__file__'):
            pkgdir = []
        else:
            pkgdir = getattr(self.module, '__path__',
                             [path.dirname(self.module.__file__)])
        if self.is_package():
            for (_, root, _) in pkgutil.iter_modules(pkgdir):
                # Ignore if this module was already doc'd.
                if root in self.doc:
                    continue

                # Ignore if it isn't exported, unless we've specifically
                # requested to document all submodules.
                if not self._allsubmodules \
                        and not self.__is_exported(root, self.module):
                    continue

                fullname = '%s.%s' % (self.name, root)
                m = _safe_import(fullname)
                if m is None:
                    continue
                self.doc[root] = self.__new_submodule(root, m)

        # Now see if we can grab inheritance relationships between classes.
        for docobj in self.doc.values():
            if isinstance(docobj, Class):
                docobj._fill_inheritance()

        # Build the reference name dictionary.
        for basename, docobj in self.doc.items():
            self.refdoc[docobj.refname] = docobj
            if isinstance(docobj, Class):
                for v in docobj.class_variables():
                    self.refdoc[v.refname] = v
                for v in docobj.instance_variables():
                    self.refdoc[v.refname] = v
                for f in docobj.methods():
                    self.refdoc[f.refname] = f
                for f in docobj.functions():
                    self.refdoc[f.refname] = f

        # Finally look for more docstrings in the __pdoc__ override.
        for name, docstring in getattr(self.module, '__pdoc__', {}).items():
            refname = '%s.%s' % (self.refname, name)
            if docstring is None:
                self.doc.pop(name, None)
                self.refdoc.pop(refname, None)
                continue

            dobj = self.find_ident(refname)
            if isinstance(dobj, External):
                continue
            dobj.docstring = inspect.cleandoc(docstring)

    def text(self):
        """
        Returns the documentation for this module as plain text.
        """
        t = _get_tpl('/text.mako')
        text, _ = re.subn('\n\n\n+', '\n\n', t.render(module=self).strip())
        return text

    def html(self, external_links=False, link_prefix='',
             source=True, **kwargs):
        """
        Returns the documentation for this module as
        self-contained HTML.

        If `external_links` is `True`, then identifiers to external
        modules are always turned into links.

        If `link_prefix` is `True`, then all links will have that
        prefix. Otherwise, links are always relative.

        If `source` is `True`, then source code will be retrieved for
        every Python object whenever possible. This can dramatically
        decrease performance when documenting large modules.

        `kwargs` is passed to the `mako` render function.
        """
        t = _get_tpl('/html.mako')
        t = t.render(module=self,
                     external_links=external_links,
                     link_prefix=link_prefix,
                     show_source_code=source,
                     **kwargs)
        return t.strip()

    def is_package(self):
        """
        Returns `True` if this module is a package.

        Works by checking if `__package__` is not `None` and whether it
        has the `__path__` attribute.
        """
        return hasattr(self.module, '__path__')

    @property
    def source(self):
        return _source(self.module)

    @property
    def refname(self):
        return self.name

    def mro(self, cls):
        """
        Returns a method resolution list of documentation objects
        for `cls`, which must be a documentation object.

        The list will contain objects belonging to `pdoc.Class` or
        `pdoc.External`. Objects belonging to the former are exported
        classes either in this module or in one of its sub-modules.
        """
        ups = inspect.getmro(cls.cls)
        return list(map(lambda c: self.find_class(c), ups))

    def descendents(self, cls):
        """
        Returns a descendent list of documentation objects for `cls`,
        which must be a documentation object.

        The list will contain objects belonging to `pdoc.Class` or
        `pdoc.External`. Objects belonging to the former are exported
        classes either in this module or in one of its sub-modules.
        """
        if cls.cls == type or not hasattr(cls.cls, '__subclasses__'):
            # Is this right?
            return []

        downs = cls.cls.__subclasses__()
        return list(map(lambda c: self.find_class(c), downs))

    def is_public(self, name):
        """
        Returns `True` if and only if an identifier with name `name` is
        part of the public interface of this module. While the names
        of sub-modules are included, identifiers only exported by
        sub-modules are not checked.

        `name` should be a fully qualified name, e.g.,
        <code>pdoc.Module.is_public</code>.
        """
        return name in self.refdoc

    def find_class(self, cls):
        """
        Given a Python `cls` object, try to find it in this module
        or in any of the exported identifiers of the submodules.
        """
        for doc_cls in self.classes():
            if cls is doc_cls.cls:
                return doc_cls
        for module in self.submodules():
            doc_cls = module.find_class(cls)
            if not isinstance(doc_cls, External):
                return doc_cls
        return External('%s.%s' % (cls.__module__, cls.__name__))

    def find_ident(self, name):
        """
        Searches this module and **all** of its sub-modules for an
        identifier with name `name` in its list of exported
        identifiers according to `pdoc`. Note that unexported
        sub-modules are searched.

        A bare identifier (without `.` separators) will only be checked
        for in this module.

        The documentation object corresponding to the identifier is
        returned. If one cannot be found, then an instance of
        `External` is returned populated with the given identifier.
        """
        if name in self.refdoc:
            return self.refdoc[name]
        for module in self.submodules():
            o = module.find_ident(name)
            if not isinstance(o, External):
                return o
        return External(name)

    def variables(self):
        """
        Returns all documented module level variables in the module
        sorted alphabetically as a list of `pdoc.Variable`.
        """
        p = lambda o: isinstance(o, Variable) and self._docfilter(o)
        return sorted(filter(p, self.doc.values()))

    def classes(self):
        """
        Returns all documented module level classes in the module
        sorted alphabetically as a list of `pdoc.Class`.
        """
        p = lambda o: isinstance(o, Class) and self._docfilter(o)
        return sorted(filter(p, self.doc.values()))

    def functions(self):
        """
        Returns all documented module level functions in the module
        sorted alphabetically as a list of `pdoc.Function`.
        """
        p = lambda o: isinstance(o, Function) and self._docfilter(o)
        return sorted(filter(p, self.doc.values()))

    def submodules(self):
        """
        Returns all documented sub-modules in the module sorted
        alphabetically as a list of `pdoc.Module`.
        """
        p = lambda o: isinstance(o, Module) and self._docfilter(o)
        return sorted(filter(p, self.doc.values()))

    def is_submodule(self, name):
        """
        Returns `True` if and only if `name` starts with the full
        import path of `self` and has length at least one greater than
        `len(self.name)`.
        """
        return self.name != name and name.startswith(self.name)

    def __is_exported(self, name, module):
        """
        Returns `True` if and only if `pdoc` considers `name` to be
        a public identifier for this module where `name` was defined
        in the Python module `module`.

        If this module has an `__all__` attribute, then `name` is
        considered to be exported if and only if it is a member of
        this module's `__all__` list.

        If `__all__` is not set, then whether `name` is exported or
        not is heuristically determined. Firstly, if `name` starts
        with an underscore, it will not be considered exported.
        Secondly, if `name` was defined in a module other than this
        one, it will not be considered exported. In all other cases,
        `name` will be considered exported.
        """
        if hasattr(self.module, '__all__'):
            return name in self.module.__all__
        if not _is_exported(name):
            return False
        if module is not None and self.module.__name__ != module.__name__:
            return name in self._declared_variables
        return True

    def __public_objs(self):
        """
        Returns a dictionary mapping a public identifier name to a
        Python object.
        """
        members = dict(inspect.getmembers(self.module))
        return dict([(name, obj)
                     for name, obj in members.items()
                     if self.__is_exported(name, inspect.getmodule(obj))])

    def __new_submodule(self, name, obj):
        """
        Create a new submodule documentation object for this `obj`,
        which must by a Python module object and pass along any
        settings in this module.
        """
        # Forcefully set the module name so that it is always the absolute
        # import path. We can't rely on `obj.__name__`, since it doesn't
        # necessarily correspond to the public exported name of the module.
        obj.__dict__['__pdoc_module_name'] = '%s.%s' % (self.refname, name)
        return Module(obj,
                      docfilter=self._docfilter,
                      allsubmodules=self._allsubmodules)


class Class (Doc):
    """
    Representation of a class's documentation.
    """

    def __init__(self, name, module, class_obj):
        """
        Same as `pdoc.Doc.__init__`, except `class_obj` must be a
        Python class object. The docstring is gathered automatically.
        """
        super(Class, self).__init__(name, module, inspect.getdoc(class_obj))

        self.cls = class_obj
        """The class Python object."""

        self.doc = {}
        """A mapping from identifier name to a `pdoc.Doc` objects."""

        self.doc_init = {}
        """
        A special version of `pdoc.Class.doc` that contains
        documentation for instance variables found in the `__init__`
        method.
        """

        public = self.__public_objs()
        try:
            # First try and find docstrings for class variables.
            # Then move on to finding docstrings for instance variables.
            # This must be optional, since not all modules have source
            # code available.
            cls_ast = ast.parse(inspect.getsource(self.cls)).body[0]
            self.doc = _var_docstrings(cls_ast, self.module, cls=self)

            for n in (cls_ast.body if '__init__' in public else []):
                if isinstance(n, ast.FunctionDef) and n.name == '__init__':
                    self.doc_init = _var_docstrings(n, self.module,
                                                    cls=self, init=True)
                    break
        except:
            pass

        # Convert the public Python objects to documentation objects.
        for name, obj in public.items():
            # Skip any identifiers that already have doco.
            if name in self.doc and not self.doc[name].is_empty():
                continue
            if name in self.doc_init:
                # Let instance members override class members.
                continue

            if inspect.ismethod(obj):
                self.doc[name] = Function(name, self.module, obj.__func__,
                                          cls=self, method=True)
            elif inspect.isfunction(obj):
                self.doc[name] = Function(name, self.module, obj,
                                          cls=self, method=False)
            elif isinstance(obj, property):
                docstring = getattr(obj, '__doc__', '')
                self.doc_init[name] = Variable(name, self.module, docstring,
                                               cls=self)
            elif not inspect.isbuiltin(obj) \
                    and not inspect.isroutine(obj):
                if name in getattr(self.cls, '__slots__', []):
                    self.doc_init[name] = Variable(name, self.module,
                                                   '', cls=self)
                else:
                    self.doc[name] = Variable(name, self.module, '', cls=self)

    @property
    def source(self):
        return _source(self.cls)

    @property
    def refname(self):
        return '%s.%s' % (self.module.refname, self.cls.__name__)

    def class_variables(self):
        """
        Returns all documented class variables in the class, sorted
        alphabetically as a list of `pdoc.Variable`.
        """
        p = lambda o: isinstance(o, Variable) and self.module._docfilter(o)
        return sorted(filter(p, self.doc.values()))

    def instance_variables(self):
        """
        Returns all instance variables in the class, sorted
        alphabetically as a list of `pdoc.Variable`. Instance variables
        are attributes of `self` defined in a class's `__init__`
        method.
        """
        p = lambda o: isinstance(o, Variable) and self.module._docfilter(o)
        return sorted(filter(p, self.doc_init.values()))

    def methods(self):
        """
        Returns all documented methods as `pdoc.Function` objects in
        the class, sorted alphabetically with `__init__` always coming
        first.

        Unfortunately, this also includes class methods.
        """
        p = lambda o: (isinstance(o, Function)
                       and o.method
                       and self.module._docfilter(o))
        return sorted(filter(p, self.doc.values()))

    def functions(self):
        """
        Returns all documented static functions as `pdoc.Function`
        objects in the class, sorted alphabetically.
        """
        p = lambda o: (isinstance(o, Function)
                       and not o.method
                       and self.module._docfilter(o))
        return sorted(filter(p, self.doc.values()))

    def _fill_inheritance(self):
        """
        Traverses this class's ancestor list and attempts to fill in
        missing documentation from its ancestor's documentation.

        The first pass connects variables, methods and functions with
        their inherited couterparts. (The templates will decide how to
        display docstrings.) The second pass attempts to add instance
        variables to this class that were only explicitly declared in
        a parent class. This second pass is necessary since instance
        variables are only discoverable by traversing the abstract
        syntax tree.
        """
        mro = filter(lambda c: c != self and isinstance(c, Class),
                     self.module.mro(self))

        def search(d, fdoc):
            for c in mro:
                doc = fdoc(c)
                if d.name in doc and isinstance(d, type(doc[d.name])):
                    return doc[d.name]
            return None
        for fdoc in (lambda c: c.doc_init, lambda c: c.doc):
            for d in fdoc(self).values():
                dinherit = search(d, fdoc)
                if dinherit is not None:
                    d.inherits = dinherit

        # Since instance variables aren't part of a class's members,
        # we need to manually deduce inheritance. Oh lawdy.
        for c in mro:
            for name in filter(lambda n: n not in self.doc_init, c.doc_init):
                d = c.doc_init[name]
                self.doc_init[name] = Variable(d.name, d.module, '', cls=self)
                self.doc_init[name].inherits = d

    def __public_objs(self):
        """
        Returns a dictionary mapping a public identifier name to a
        Python object. This counts the `__init__` method as being
        public.
        """
        _pdoc = getattr(self.module.module, '__pdoc__', {})

        def forced_out(name):
            return _pdoc.get('%s.%s' % (self.name, name), False) is None

        def exported(name):
            exported = name == '__init__' or _is_exported(name)
            return not forced_out(name) and exported

        idents = dict(inspect.getmembers(self.cls))
        return dict([(n, o) for n, o in idents.items() if exported(n)])


class Function (Doc):
    """
    Representation of documentation for a Python function or method.
    """

    def __init__(self, name, module, func_obj, cls=None, method=False):
        """
        Same as `pdoc.Doc.__init__`, except `func_obj` must be a
        Python function object. The docstring is gathered automatically.

        `cls` should be set when this is a method or a static function
        beloing to a class. `cls` should be a `pdoc.Class` object.

        `method` should be `True` when the function is a method. In
        all other cases, it should be `False`.
        """
        super(Function, self).__init__(name, module, inspect.getdoc(func_obj))

        self.func = func_obj
        """The Python function object."""

        self.cls = cls
        """
        The `pdoc.Class` documentation object if this is a method. If
        not, this is None.
        """

        self.method = method
        """
        Whether this function is a method or not.

        In particular, static class methods have this set to False.
        """

    @property
    def source(self):
        return _source(self.func)

    @property
    def refname(self):
        if self.cls is None:
            return '%s.%s' % (self.module.refname, self.name)
        else:
            return '%s.%s' % (self.cls.refname, self.name)

    def spec(self):
        """
        Returns a nicely formatted spec of the function's parameter
        list as a string. This includes argument lists, keyword
        arguments and default values.
        """
        return ', '.join(self.params())

    def params(self):
        """
        Returns a list where each element is a nicely formatted
        parameter of this function. This includes argument lists,
        keyword arguments and default values.
        """
        def fmt_param(el):
            if isinstance(el, str) or isinstance(el, unicode):
                return el
            else:
                return '(%s)' % (', '.join(map(fmt_param, el)))
        try:
            getspec = getattr(inspect, 'getfullargspec', inspect.getargspec)
            s = getspec(self.func)
        except TypeError:
            # I guess this is for C builtin functions?
            return ['...']

        params = []
        for i, param in enumerate(s.args):
            if s.defaults is not None and len(s.args) - i <= len(s.defaults):
                defind = len(s.defaults) - (len(s.args) - i)
                params.append('%s=%s' % (param, repr(s.defaults[defind])))
            else:
                params.append(fmt_param(param))
        if s.varargs is not None:
            params.append('*%s' % s.varargs)

        # TODO: This needs to be adjusted in Python 3. There's more stuff
        #       returned from getfullargspec than what we're looking at here.
        keywords = getattr(s, 'varkw', getattr(s, 'keywords', None))
        if keywords is not None:
            params.append('**%s' % keywords)
        return params

    def __lt__(self, other):
        # Push __init__ to the top.
        if '__init__' in (self.name, other.name):
            return self.name != other.name and self.name == '__init__'
        else:
            return self.name < other.name


class Variable (Doc):
    """
    Representation of a variable's documentation. This includes
    module, class and instance variables.
    """

    def __init__(self, name, module, docstring, cls=None):
        """
        Same as `pdoc.Doc.__init__`, except `cls` should be provided
        as a `pdoc.Class` object when this is a class or instance
        variable.
        """
        super(Variable, self).__init__(name, module, docstring)

        self.cls = cls
        """
        The `podc.Class` object if this is a class or instance
        variable. If not, this is None.
        """

    @property
    def source(self):
        return []

    @property
    def refname(self):
        if self.cls is None:
            return '%s.%s' % (self.module.refname, self.name)
        else:
            return '%s.%s' % (self.cls.refname, self.name)


class External (Doc):
    """
    A representation of an external identifier. The textual
    representation is the same as an internal identifier, but without
    any context. (Usually this makes linking more difficult.)

    External identifiers are also used to represent something that is
    not exported but appears somewhere in the public interface (like
    the ancestor list of a class).
    """

    __pdoc__['External.docstring'] = \
        """
        An empty string. External identifiers do not have
        docstrings.
        """
    __pdoc__['External.module'] = \
        """
        Always `None`. External identifiers have no associated
        `pdoc.Module`.
        """
    __pdoc__['External.name'] = \
        """
        Always equivalent to `pdoc.External.refname` since external
        identifiers are always expressed in their fully qualified
        form.
        """

    def __init__(self, name):
        """
        Initializes an external identifier with `name`, where `name`
        should be a fully qualified name.
        """
        super(External, self).__init__(name, None, '')

    @property
    def source(self):
        return []

    @property
    def refname(self):
        return self.name

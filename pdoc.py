"""
Module pdoc provides types and functions for accessing the public
documentation of a Python module. This includes module level
variables, modules (and sub-modules), functions, classes and class
and instance variables. Docstrings are taken from modules, functions,
and classes using special `__doc__` attribute. Docstrings for any of
the variables are extracted by examining the module's abstract syntax
tree.

The public interface of a module is determined through one of two
ways. If `__all__` is defined in the module, then all identifiers in
that list will be considered public. No other identifiers will be
considered as public. Conversely, if `__all__` is not defined, then
`pdoc` will heuristically determine the public interface. There are two
simple rules that are applied to each identifier in the module:

1. If the name starts with an underscore, it is **not** public.

2. If the name is defined in a different module, it is **not** public.

3. If the name is a direct sub-module, then it is public.

Once documentation for a module is created, it can be outputted
in either HTML or plain text using the covenience functions
`pdoc.html` and `pdoc.text`, or the corresponding methods
`pdoc.Module.html` and `pdoc.Module.text`.
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

template_path = [
    path.join(sys.prefix, 'share', 'pdoc'),
    path.join(path.dirname(__file__), 'templates'),  # For my dev environment.
]
"""
A list of paths to search for Mako templates used to produce the
plain text and HTML output. Each path is tried until a template is
found.
"""
if os.getenv('XDG_CONFIG_HOME'):
    template_path.insert(0, path.join(os.getenv('XDG_CONFIG_HOME'), 'pdoc'))

_tpl_lookup = TemplateLookup(directories=template_path,
                             cache_args={'cached': True,
                                         'cache_type': 'memory'})


def html(module_name,
         docfilter=None, allsubmodules=False,
         external_links=False, link_prefix=''):
    """
    Returns the documentation for the module `module_name` in HTML
    format. The module must be importable.

    `docfilter` is an optional predicate that controls which
    documentation objects are shown in the output. It is a single
    argument function that takes a documentation object and returns
    `True` or `False`. If `False`, that object will not be included in
    the output.

    If `allsubmodules` is True, then every submodule of this
    module that can be found will be included in the
    documentation, regardless of whether `__all__` contains it.

    If `external_links` is True, then identifiers to external modules
    are always turned into links.

    If `link_prefix` is set, then all links will have that prefix.
    Otherwise, links are always relative.
    """
    mod = Module(import_module(module_name),
                 docfilter=docfilter,
                 allsubmodules=allsubmodules)
    return mod.html(external_links=external_links,
                    link_prefix=link_prefix)


def text(module_name,
         docfilter=None, allsubmodules=False):
    """
    Returns the documentation for the module `module_name` in plain
    text format. The module must be importable.

    `docfilter` is an optional predicate that controls which
    documentation objects are shown in the output. It is a single
    argument function that takes a documentation object and returns
    True of False. If False, that object will not be included in
    the output.

    If `allsubmodules` is True, then every submodule of this
    module that can be found will be included in the
    documentation, regardless of whether `__all__` contains it.
    """
    mod = Module(import_module(module_name),
                 docfilter=docfilter,
                 allsubmodules=allsubmodules)
    return mod.text()


def import_module(module_name):
    """
    A simple wrapper around `__import__` and `reload`, where `reload`
    is called when `module_name` is in `sys.modules`.
    """
    # Raises an exception if the parent module cannot be imported.
    # This hopefully ensures that we only explicitly import modules
    # contained in `pdoc.import_path`.
    if import_path == sys.path:
        # Such a kludge. Allow documentation for __builtin__ if we haven't
        # mangled `sys.path`. But what if other packages do it?
        # Not sure what to do here. Probably the right response is not to
        # care if you can see doco for __builtin__.
        imp.find_module(module_name.split('.')[0])
    else:
        imp.find_module(module_name.split('.')[0], import_path)

    if module_name in sys.modules:
        return sys.modules[module_name]
    else:
        __import__(module_name)
        return sys.modules[module_name]


def _get_tpl(name):
    """
    Returns the Mako template with the given name.
    If the template cannot be found, a nicer error message is
    displayed.
    """
    try:
        t = _tpl_lookup.get_template(name)
    except TopLevelLookupException:
        locs = [path.join(p, name.lstrip('/')) for p in template_path]
        raise IOError(2, 'No template at any of: %s' % ', '.join(locs))
    return t


def _eprint(*args, **kwargs):
    kwargs['file'] = sys.stderr
    print(*args, **kwargs)


def _safe_import(module_name):
    """
    A function for mini-sandboxing a module import. Returns None
    if the import was unsuccessful and the module object otherwise.

    In this instance, "sandboxing" means suppressing errors and
    redirecting stdout/stderr to null.
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


def _fetch_var_docstrings(module, obj, cls=None):
    tree = ast.parse(inspect.getsource(obj))
    return _extract_var_docstrings(module, tree, cls=cls)


def _extract_var_docstrings(module, ast_tree, cls=None):
    vs = {}
    children = list(ast.iter_child_nodes(ast_tree))
    for i, child in enumerate(children):
        if isinstance(child, ast.Assign) and len(child.targets) == 1:
            if isinstance(child.targets[0], ast.Name):
                name = child.targets[0].id
            elif isinstance(child.targets[0], ast.Attribute):
                name = child.targets[0].attr
            else:
                continue
            if not _is_exported(name):
                continue

            docstring = ''
            if (i+1 < len(children)
                    and isinstance(children[i+1], ast.Expr)
                    and isinstance(children[i+1].value, ast.Str)):
                docstring = children[i+1].value.s

            vs[name] = Variable(module, name, docstring, cls=cls)
    return vs


def _is_exported(ident_name):
    """
    Returns true if `ident_name` matches the export criteria for
    an identifier name.

    This should not be used by clients. Instead, use the `Module`
    method `is_exported`.
    """
    return not ident_name.startswith('_')


class Doc (object):
    """
    A base class for all documentation objects.
    """
    def __init__(self, module, name, docstring):
        self.module = module
        """
        The module documentation object that this object was
        defined in.
        """

        self.name = name
        """The identifier name for this object."""

        self.docstring = inspect.cleandoc(docstring or '')
        """The docstring for this object."""

    @property
    def refname(self):
        """
        Returns an appropriate reference name for this documentation
        object. Usually this is its fully qualified path.

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

    def __init__(self, module, docfilter=None, allsubmodules=False):
        """
        Creates a `Module` documentation object given the actual
        module Python object.

        `docfilter` is an optional predicate that controls which
        documentation objects are returned in the following methods:
        `classes`, `functions`, `variables` and `submodules`.
        The filter is propagated to the analogous methods on a
        `Class` object.

        If `allsubmodules` is True, then every submodule of this
        module that can be found will be included in the
        documentation, regardless of whether `__all__` contains it.
        """
        name = getattr(module, '__pdoc_module_name', module.__name__)
        super(Module, self).__init__(module, name, inspect.getdoc(module))

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

        try:
            self.doc = _fetch_var_docstrings(self, self.module)
        except:
            pass

        self.public = self.__fetch_public_objs()
        """
        A mapping from identifier name to Python object for all
        exported identifiers in this module. When `__all__` exists,
        then the keys in this dictionary always correspond to the
        values in `__all__`. When `__all__` does not exist, then the
        public identifiers are inferred heuristically. (Currently,
        all not starting with an underscore are public.)
        """

        for name, obj in self.public.items():
            # Skip any identifiers that already have doco.
            if name in self.doc and not self.doc[name].is_empty():
                continue

            # At the module level, we only document variables, functions and
            # classes. We've already gathered variable doco above.
            if inspect.isfunction(obj) or inspect.isbuiltin(obj):
                self.doc[name] = Function(self, obj)
            elif inspect.isclass(obj):
                self.doc[name] = Class(self, obj)
            elif inspect.ismodule(obj) and self.is_submodule(obj.__name__):
                # Only document modules that are submodules.
                module = self.__new_submodule(obj)
                self.doc[name] = module

        # Now scan the directory if this is a package for all modules.
        pkgdir = getattr(self.module, '__path__',
                         [path.dirname(self.module.__file__)])
        for (_, root, _) in pkgutil.iter_modules(pkgdir):
            if root in self.doc:  # Ignore if this module was already doc'd.
                continue

            # Ignore if it isn't exported, unless we've specifically requested
            # to document all submodules.
            if not self._allsubmodules \
                    and not self.is_exported(root, self.module):
                continue

            fullname = '%s.%s' % (self.name, root)
            m = _safe_import(fullname)
            if m is None:
                continue
            self.doc[root] = self.__new_submodule(m)

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

        # Now see if we can grab inheritance relationships between classes.
        for docobj in self.doc.values():
            if isinstance(docobj, Class):
                docobj._fill_inheritance()

        # Finally look for more docstrings in the __pdoc override.
        for refname, docstring in getattr(self.module, '__pdoc', {}).items():
            dobj = self.find_ident(refname)
            if isinstance(dobj, External):
                continue
            dobj.docstring = inspect.cleandoc(docstring)

    def text(self):
        """
        Returns the documentation for this module as plain text.
        """
        t = _get_tpl('/txt.mako')
        text, _ = re.subn('\n\n\n+', '\n\n', t.render(module=self).strip())
        return text

    def html(self, external_links=False, link_prefix='', **kwargs):
        """
        Returns the documentation for this module as
        self-contained HTML.

        If `external_links` is True, then identifiers to external
        modules are always turned into links.

        If `link_prefix` is set, then all links will be absolute
        with the prefix given. Otherwise, links are always relative.

        `kwargs` is passed to the `mako` render function.
        """
        t = _get_tpl('/html.mako')
        t = t.render(module=self,
                     external_links=external_links,
                     link_prefix=link_prefix,
                     **kwargs)
        return t.strip()

    def is_package(self):
        """
        Returns True if this module is a package.

        Works by checking if `__package__` is not None and whether
        it has the `__path__` attribute.
        """
        return hasattr(self.module, '__path__')

    @property
    def refname(self):
        return self.name

    def mro(self, cls):
        """
        Returns a method resolution list of documentation objects
        for `cls`, which must be a documentation object.

        The list will contain objects belonging to `Class` or
        `External`. Objects belonging to the former are exported
        classes either in this module or in one of its sub-modules.
        """
        def clsname(c):
            return '%s.%s' % (c.__module__, c.__name__)
        return list(map(lambda c: self.find_ident(clsname(c)),
                        inspect.getmro(cls.cls)))

    def descendents(self, cls):
        """
        Returns a descendent list of documentation objects for `cls`,
        which must be a documentation object.

        The list will contain objects belonging to `Class` or
        `External`. Objects belonging to the former are exported
        classes either in this module or in one of its sub-modules.
        """
        if cls.cls == type or not hasattr(cls.cls, '__subclasses__'):
            # Is this right?
            return []

        def clsname(c):
            return '%s.%s' % (c.__module__, c.__name__)
        return list(map(lambda c: self.find_ident(clsname(c)),
                        cls.cls.__subclasses__()))

    def is_public(self, name):
        """
        Returns True if and only if an identifier with name `name`
        is part of the public interface of this module. While the
        names of sub-modules are included, identifiers only exported
        by sub-modules are not checked.

        `name` should be a fully qualified name, e.g.,
        `pdoc.Module.is_public`.
        """
        return name in self.refdoc

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
        sorted alphabetically.
        """
        p = lambda o: isinstance(o, Variable) and self._docfilter(o)
        return sorted(filter(p, self.doc.values()))

    def classes(self):
        """
        Returns all documented module level classes in the module
        sorted alphabetically.
        """
        p = lambda o: isinstance(o, Class) and self._docfilter(o)
        return sorted(filter(p, self.doc.values()))

    def functions(self):
        """
        Returns all documented module level functions in the module
        sorted alphabetically.
        """
        p = lambda o: isinstance(o, Function) and self._docfilter(o)
        return sorted(filter(p, self.doc.values()))

    def submodules(self):
        """
        Returns all documented sub-modules in the module sorted
        alphabetically.
        """
        p = lambda o: isinstance(o, Module) and self._docfilter(o)
        return sorted(filter(p, self.doc.values()))

    def is_exported(self, name, module):
        """
        Returns true if and only if `pdoc` considers `name` to be
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
            return False
        return True

    def is_submodule(self, name):
        return self.name != name and name.startswith(self.name)

    def __fetch_public_objs(self):
        members = dict(inspect.getmembers(self.module))
        return dict([(name, obj)
                     for name, obj in members.items()
                     if self.is_exported(name, inspect.getmodule(obj))])

    def __new_submodule(self, obj):
        """
        Create a new submodule documentation object for this
        submodule and pass along any settings in this module.
        """
        return Module(obj,
                      docfilter=self._docfilter,
                      allsubmodules=self._allsubmodules)


class Class (Doc):
    """
    Representation of a class's documentation.
    """

    def __init__(self, module, class_obj):
        self.cls = class_obj
        """The class object."""

        super(Class, self).__init__(module, self.cls.__name__,
                                    inspect.getdoc(self.cls))

        self.doc = {}
        """A mapping from identifier name to a documentation object."""

        self.doc_init = {}
        """
        A special version of self.doc that contains documentation for
        instance variables found in the __init__ method.
        """

        self.public = self.__fetch_public_objs()
        """
        A mapping from identifier name to Python object for all
        exported identifiers in this class. Exported identifiers
        are any identifier that does not start with underscore.
        """

        try:
            cls_ast = ast.parse(inspect.getsource(self.cls)).body[0]
            self.doc = _extract_var_docstrings(self.module, cls_ast, cls=self)
            if '__init__' in self.public:
                for n in cls_ast.body:
                    if isinstance(n, ast.FunctionDef) and n.name == '__init__':
                        self.doc_init = _extract_var_docstrings(self.module,
                                                                n, cls=self)
                        break
        except:
            pass

        for name, obj in self.public.items():
            # Skip any identifiers that already have doco.
            if name in self.doc and not self.doc[name].is_empty():
                continue

            # At the class level, we only document variables and methods.
            # We've already gathered class and instance variable doco above.
            if inspect.ismethod(obj):
                self.doc[name] = Function(self.module, obj.__func__,
                                          cls=self, method=True)
                self.doc[name].name = name
            elif inspect.isfunction(obj):
                self.doc[name] = Function(self.module, obj,
                                          cls=self, method=False)
                self.doc[name].name = name
            elif isinstance(obj, property):
                docstring = ''
                if hasattr(obj, '__doc__'):
                    docstring = obj.__doc__
                self.doc_init[name] = Variable(self.module, name, docstring,
                                               cls=self)
            elif not inspect.isbuiltin(obj) \
                    and not inspect.isroutine(obj):
                self.doc[name] = Variable(self.module, name, '', cls=self)

    def _fill_inheritance(self):
        mro = filter(lambda c: c != self and isinstance(c, Class),
                     self.module.mro(self))

        def search(d):
            for c in mro:
                if d.name in c.doc_init \
                        and isinstance(d, type(c.doc_init[d.name])):
                    return c.doc_init[d.name]
                if d.name in c.doc \
                        and isinstance(d, type(c.doc[d.name])):
                    return c.doc[d.name]
            return None
        for d in self.doc_init.values():
            dinherit = search(d)
            if dinherit is not None:
                d.inherits = dinherit
        for d in self.doc.values():
            dinherit = search(d)
            if dinherit is not None:
                d.inherits = dinherit

    @property
    def refname(self):
        return '%s.%s' % (self.module.refname, self.cls.__name__)

    def class_variables(self):
        """
        Returns all documented class variables in the class, sorted
        alphabetically.
        """
        p = lambda o: isinstance(o, Variable) and self.module._docfilter(o)
        return sorted(filter(p, self.doc.values()))

    def instance_variables(self):
        """
        Returns all documented instance variables in the class, sorted
        alphabetically.
        """
        p = lambda o: isinstance(o, Variable) and self.module._docfilter(o)
        return sorted(filter(p, self.doc_init.values()))

    def methods(self):
        """
        Returns all documented methods as Function objects in the
        class, sorted alphabetically with __new__ and __init__ always
        coming first.
        """
        p = lambda o: (isinstance(o, Function)
                       and o.method
                       and self.module._docfilter(o))
        return sorted(filter(p, self.doc.values()))

    def functions(self):
        """
        Returns all documented static functions as Function objects in
        the class, sorted alphabetically.
        """
        p = lambda o: (isinstance(o, Function)
                       and not o.method
                       and self.module._docfilter(o))
        return sorted(filter(p, self.doc.values()))

    def __fetch_public_objs(self):
        def exported(name):
            return name in ('__init__', '__new__') or _is_exported(name)

        idents = dict(inspect.getmembers(self.cls))
        return dict([(name, o)
                     for name, o in idents.items()
                     if exported(name)])


class Function (Doc):
    """
    Representation of a function's documentation.
    """

    ClassVariable = 5
    """Doco for class variable."""

    def __init__(self, module, func_obj, cls=None, method=False):
        self.func = func_obj
        """The function object."""

        self.cls = cls
        """
        The Class documentation object if this is a method.
        If not, this is None.
        """

        self.method = method
        """
        Whether this function is a method or not.

        Static class methods have this set to False.
        """

        super(Function, self).__init__(module, self.func.__name__,
                                       inspect.getdoc(self.func))

    @property
    def refname(self):
        if self.cls is None:
            return '%s.%s' % (self.module.refname, self.name)
        else:
            return '%s.%s' % (self.cls.refname, self.name)

    def spec(self):
        """
        Returns a nicely formatted spec of the function's parameter
        list. This includes argument lists, keyword arguments and
        default values.
        """
        return ', '.join(self.params())

    def params(self):
        """
        Returns a nicely formatted list of parameters to this
        function. This includes argument lists, keyword arguments
        and default values.
        """
        def fmt_param(el):
            if isinstance(el, str) or isinstance(el, unicode):
                return el
            else:
                return '(%s)' % (', '.join(map(fmt_param, el)))
        try:
            s = inspect.getargspec(self.func)
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
        if s.keywords is not None:
            params.append('**%s' % s.keywords)
        return params

    def __lt__(self, other):
        # Push __new__ and __init__ to the top.
        if '__new__' in (self.name, other.name):
            if self.name == other.name:
                return False
            return self.name == '__new__'
        elif '__init__' in (self.name, other.name):
            if self.name == other.name:
                return False
            return self.name == '__init__'
        else:
            return self.name < other.name


class Variable (Doc):
    """
    Representation of a variable's documentation. This includes
    module, class and instance variables.
    """
    def __init__(self, module, name, docstring, cls=None):
        super(Variable, self).__init__(module, name, docstring)

        self.cls = cls
        """
        The Class documentation object if this is a method.
        If not, this is None.
        """

    @property
    def refname(self):
        if self.cls is None:
            return '%s.%s' % (self.module.refname, self.name)
        else:
            return '%s.%s' % (self.cls.refname, self.name)


class External (Doc):
    """
    A representation of an external identifier. The textual
    representation is the same as an internal identifier, but the
    HTML version will lack a link while the internal identifier
    will link to its documentation.
    """
    def __init__(self, name):
        super(External, self).__init__(None, name, '')

    @property
    def refname(self):
        return self.name

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
pdoc will heuristically determine the public interface. There are two
simple rules that are applied to each identifier in the module:

    1. If the name starts with an underscore, it is **not** public.

    2. If the name is a module but it is not a sub-module of the
       module being documented, then it is **not** public.

Once documentation for a module is created, it can be outputted
in either HTML or plaintext. Both output formats return a list of
tuples, where the first element is the module name and the second
element is the HTML or plaintext. The first element in the list is
the module being documented while each subsequent element is a
sub-module.
"""
from __future__ import print_function
import ast
import importlib
import inspect
import os
import os.path as path
import re

from mako.lookup import TemplateLookup

__tpl_dir = path.join(path.split(__file__)[0], 'templates')
__tpl_lookup = TemplateLookup(directories=__tpl_dir,
                              cache_args={'cached': True,
                                          'cache_type': 'memory'})


def html(module_name, abc=123, xyz=789, *args, **kws):
    """
    Test.
    """
    pass


def text(module_name):
    """
    Returns the documentation for the module `module_name` in plain
    text format. The module must be importable.
    """
    mod = Module(importlib.import_module(module_name))
    return _tpl_text('module', module=mod)


def _tpl_html(tpl_name, **kwargs):
    """
    Return an HTML template string formatted with the given keyword
    arguments.
    """
    t = __tpl_lookup.get_template('/%s.html.mako' % tpl_name)
    return t.render(**kwargs).strip()


def _tpl_text(tpl_name, **kwargs):
    """
    Return a text template string formatted with the given keyword
    arguments.
    """
    t = __tpl_lookup.get_template('/%s.txt.mako' % tpl_name)
    new, _ = re.subn('\n\n\n+', '\n\n', t.render(**kwargs).strip())
    return new


def _fetch_var_docstrings(module, obj, cls=None):
    tree = ast.parse(inspect.getsource(obj))
    return _extract_var_docstrings(module, tree, cls=cls)


def _extract_var_docstrings(module, ast_tree, cls=None):
    vs = {}
    children = list(ast.iter_child_nodes(ast_tree))
    for i, child in enumerate(children):
        if (isinstance(child, ast.Assign)
                and len(child.targets) == 1
                and i+1 < len(children)
                and isinstance(children[i+1], ast.Expr)
                and isinstance(children[i+1].value, ast.Str)):
            if isinstance(child.targets[0], ast.Name):
                name = child.targets[0].id
            elif isinstance(child.targets[0], ast.Attribute):
                name = child.targets[0].attr
            else:
                continue
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

    def refname(self):
        """
        Returns an appropriate reference name for this documentation
        object. Usually this is its fully qualified path.

        e.g., The refname for this method is `pdoc.Doc.refname`.
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

    def __init__(self, module, parent=None):
        super(Module, self).__init__(module, module.__name__,
                                     inspect.getdoc(module))

        self.doc = {}
        """A mapping from identifier name to a documentation object."""

        self.refdoc = {}
        """
        The same as `pdoc.Module.doc`, but maps fully qualified
        identifier names to documentation objects.
        """

        try:
            self.doc = _fetch_var_docstrings(self.module, self.module)
        except TypeError:
            pass

        self.public = self.__fetch_public_objs()
        """
        A mapping from identifier name to Python object for all
        exported identifiers in this module. When __all__ exists,
        then the keys in this dictionary always correspond to the
        values in __all__. When __all__ does not exist, then the
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
            elif inspect.ismodule(obj) and self.is_submodule(obj):
                # Only document modules that are submodules.
                self.doc[name] = Module(obj)

        # Now try documenting sub-modules recursively if this is a package.
        if not hasattr(self.module, '__all__') \
                and hasattr(self.module, '__file__'):
            pkgdir = os.path.dirname(self.module.__file__)
            if self.module.__package__ is not None \
                    and hasattr(self.module, '__path__') \
                    and path.isdir(pkgdir):
                for f in os.listdir(pkgdir):
                    if not f.endswith('.py') or f.startswith('.'):
                        continue
                    root, _ = path.splitext(f)
                    if root == '__init__' or root in self.doc:
                        continue
                    fullname = '%s.%s' % (self.name, root)
                    try:
                        m = Module(importlib.import_module(fullname))
                    except IOError:
                        continue
                    self.doc[m.name] = m

        # Build the reference name dictionary.
        for basename, docobj in self.doc.items():
            self.refdoc[docobj.refname()] = docobj

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
        if cls.cls == type or not hasattr(cls, '__subclasses__'):
            # Is this right?
            return []

        def clsname(c):
            return '%s.%s' % (c.__module__, c.__name__)
        return list(map(lambda c: self.find_ident(clsname(c)),
                        cls.cls.__subclasses__()))

    def find_ident(self, name):
        """
        Searches this module for an identifier with name `name`.
        If the identifier contains import path separators, then the
        exported identifiers of the matching sub-module are checked.

        A bare identifier will only be checked for in this module.

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
        vs = filter(lambda o: isinstance(o, Variable), self.doc.values())
        return sorted(vs)

    def classes(self):
        """
        Returns all documented module level classes in the module
        sorted alphabetically.
        """
        vs = filter(lambda o: isinstance(o, Class), self.doc.values())
        return sorted(vs)

    def functions(self):
        """
        Returns all documented module level functions in the module
        sorted alphabetically.
        """
        vs = filter(lambda o: isinstance(o, Function), self.doc.values())
        return sorted(vs)

    def submodules(self):
        """
        Returns all documented sub-modules in the module sorted
        alphabetically.
        """
        vs = filter(lambda o: isinstance(o, Module), self.doc.values())
        return sorted(vs)

    def is_exported(self, name, module=None):
        """
        Returns true if and only if `pdoc` considers `name` to be
        a public identifier.

        A `name` is public if any only if it does not start with an
        underscore. If `module` is the module that name is defined in,
        then `name` is considered public only if it is defined in the
        same module as `self.module` or in one of its sub-modules.
        """
        if not _is_exported(name):
            return False
        if module is not None \
                and self.name != module.__name__ \
                and not self.is_submodule(module):
            return False
        return True

    def is_submodule(self, module_obj):
        parent, sub = self.name.lower(), module_obj.__name__.lower()
        return sub.startswith('%s.' % parent)

    def __fetch_public_objs(self):
        members = dict(inspect.getmembers(self.module))
        if '__all__' in members:
            return {name: members[name]
                    for name in members['__all__']}
        else:
            return {name: obj
                    for name, obj in members.items()
                    if self.is_exported(name, inspect.getmodule(obj))}


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
        except IOError:
            pass
        except TypeError:
            pass

        for name, obj in self.public.items():
            # Skip any identifiers that already have doco.
            if name in self.doc and not self.doc[name].is_empty():
                continue

            # At the class level, we only document variables and methods.
            # We've already gathered class and instance variable doco above.
            if inspect.ismethod(obj):
                self.doc[name] = Function(self.module, obj.__func__, cls=self)
            elif not inspect.isbuiltin(obj) \
                    and not inspect.isroutine(obj):
                self.doc[name] = Variable(self.module, name, '', cls=self)

    def refname(self):
        return '%s.%s' % (self.cls.__module__, self.cls.__name__)

    def class_variables(self):
        """
        Returns all documented class variables in the class, sorted
        alphabetically.
        """
        vs = filter(lambda o: isinstance(o, Variable), self.doc.values())
        return sorted(vs)

    def instance_variables(self):
        """
        Returns all documented instance variables in the class, sorted
        alphabetically.
        """
        vs = filter(lambda o: isinstance(o, Variable), self.doc_init.values())
        return sorted(vs)

    def methods(self):
        """
        Returns all documented methods as Function objects in the
        class, sorted alphabetically with __new__ and __init__ always
        coming first.
        """
        vs = filter(lambda o: isinstance(o, Function), self.doc.values())
        return sorted(vs)

    def __fetch_public_objs(self):
        def exported(name):
            return name in ('__init__', '__new__') or _is_exported(name)

        idents = dict(inspect.getmembers(self.cls))
        return {name: o for name, o in idents.items() if exported(name)}


class Function (Doc):
    """
    Representation of a function's documentation.
    """

    ClassVariable = 5
    """Doco for class variable."""

    def __init__(self, module, func_obj, cls=None):
        self.func = func_obj
        """The function object."""

        self.cls = cls
        """
        The Class documentation object if this is a method.
        If not, this is None.
        """

        super(Function, self).__init__(module, self.func.__name__,
                                       inspect.getdoc(self.func))

    def refname(self):
        if self.cls is None:
            return '%s.%s' % (self.module.name, self.name)
        else:
            return '%s.%s' % (self.cls.refname(), self.name)

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
                params.append('%s=%s' % (param, s.defaults[defind]))
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
            return (0 if self.name == '__new__' else 1 <
                    0 if other.name == '__new__' else 1)
        elif '__init__' in (self.name, other.name):
            return (1 if self.name == '__init__' else 0 <
                    1 if other.name == '__init__' else 0)
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

    def refname(self):
        if self.cls is None:
            return '%s.%s' % (self.module.name, self.name)
        else:
            return '%s.%s' % (self.cls.refname(), self.name)


class External (Doc):
    """
    A representation of an external identifier. The textual
    representation is the same as an internal identifier, but the
    HTML version will lack a link while the internal identifier
    will link to its documentation.
    """
    def __init__(self, name):
        super(External, self).__init__(None, name, '')

    def refname(self):
        return '%s (ext)' % self.name

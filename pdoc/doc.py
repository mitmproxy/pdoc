import ast
import inspect

try:
    unicode        # Python 2
except NameError:
    unicode = str  # Python 3

__pdoc__ = {}


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
            elif (
                isinstance(child.targets[0], ast.Attribute)
                and isinstance(child.targets[0].value, ast.Name)
                and child.targets[0].value.id == "self"
            ):
                name = child.targets[0].attr
            else:
                continue
            if not _is_exported(name) and name not in getattr(module, "__all__", []):
                continue

            docstring = ""
            if (
                i + 1 < len(children)
                and isinstance(children[i + 1], ast.Expr)
                and isinstance(children[i + 1].value, ast.Str)
            ):
                docstring = children[i + 1].value.s

            vs[name] = Variable(name, module, docstring, cls=cls)
    return vs


def _is_exported(ident_name):
    """
    Returns `True` if `ident_name` matches the export criteria for an
    identifier name.

    This should not be used by clients. Instead, use
    `pdoc.Module.is_public`.
    """
    return not ident_name.startswith("_")


class Doc(object):
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

        self.docstring = inspect.cleandoc(docstring or "")
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
        assert False, "subclass responsibility"

    @property
    def refname(self):
        """
        Returns an appropriate reference name for this documentation
        object. Usually this is its fully qualified path. Every
        documentation object must provide this property.

        e.g., The refname for this property is
        <code>pdoc.Doc.refname</code>.
        """
        assert False, "subclass responsibility"

    def __lt__(self, other):
        return self.name < other.name

    def is_empty(self):
        """
        Returns true if the docstring for this object is empty.
        """
        return len(self.docstring.strip()) == 0


class Module(Doc):
    """
    Representation of a module's documentation.
    """

    __pdoc__["Module.module"] = "The Python module object."
    __pdoc__[
        "Module.name"
    ] = """
        The name of this module with respect to the context in which
        it was imported. It is always an absolute import path.
        """

    def __init__(self, module, supermodule=None):
        """
        Creates a `Module` documentation object given the actual
        module Python object.
        """
        name = getattr(module, "__pdoc_module_name", module.__name__)
        super(Module, self).__init__(name, module, inspect.getdoc(module))
        self.supermodule = supermodule

        self.doc = {}
        """A mapping from identifier name to a documentation object."""

        self.refdoc = {}
        """
        The same as `pdoc.Module.doc`, but maps fully qualified
        identifier names to documentation objects.
        """

        self.submodules = []

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
            elif name in vardocs:
                self.doc[name] = vardocs[name]
            else:
                # Catch all for variables.
                self.doc[name] = Variable(name, self, "", cls=None)

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
        for name, docstring in getattr(self.module, "__pdoc__", {}).items():
            refname = "%s.%s" % (self.refname, name)
            if docstring is None:
                self.doc.pop(name, None)
                self.refdoc.pop(refname, None)
                continue

            dobj = self.find_ident(refname)
            if isinstance(dobj, External):
                continue
            dobj.docstring = inspect.cleandoc(docstring)

    @property
    def source(self):
        return _source(self.module)

    @property
    def refname(self):
        return self.name

    def mro(self, cls):
        """
        Returns a method resolution list of ancestor documentation objects
        for `cls`, which must be a documentation object.

        The list will contain objects belonging to `pdoc.Class` or
        `pdoc.External`. Objects belonging to the former are exported
        classes either in this module or in one of its sub-modules.
        """
        return [
            self.find_class(c)
            for c in inspect.getmro(cls.cls)
            if c not in (cls.cls, object)
        ]

    def descendents(self, cls):
        """
        Returns a descendent list of documentation objects for `cls`,
        which must be a documentation object.

        The list will contain objects belonging to `pdoc.Class` or
        `pdoc.External`. Objects belonging to the former are exported
        classes either in this module or in one of its sub-modules.
        """
        if cls.cls == type or not hasattr(cls.cls, "__subclasses__"):
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
        for module in self.submodules:
            doc_cls = module.find_class(cls)
            if not isinstance(doc_cls, External):
                return doc_cls
        return External("%s.%s" % (cls.__module__, cls.__name__))

    def find_ident(self, name, _seen=None):
        """
        Searches this module and **all** of its sub/super-modules for an
        identifier with name `name` in its list of exported
        identifiers according to `pdoc`. Note that unexported
        sub-modules are searched.

        A bare identifier (without `.` separators) will only be checked
        for in this module.

        The documentation object corresponding to the identifier is
        returned. If one cannot be found, then an instance of
        `External` is returned populated with the given identifier.
        """
        _seen = _seen or set()
        if self in _seen:
            return None
        _seen.add(self)

        if name == self.refname:
            return self
        if name in self.refdoc:
            return self.refdoc[name]
        for module in self.submodules:
            o = module.find_ident(name, _seen=_seen)
            if not isinstance(o, (External, type(None))):
                return o
        # Traverse also up-level super-modules
        module = self.supermodule
        while module is not None:
            o = module.find_ident(name, _seen=_seen)
            if not isinstance(o, (External, type(None))):
                return o
            module = module.supermodule
        return External(name)

    def variables(self):
        """
        Returns all documented module level variables in the module
        sorted alphabetically as a list of `pdoc.Variable`.
        """
        p = lambda o: isinstance(o, Variable)
        return sorted(filter(p, self.doc.values()))

    def classes(self):
        """
        Returns all documented module level classes in the module
        sorted alphabetically as a list of `pdoc.Class`.
        """
        p = lambda o: isinstance(o, Class)
        return sorted(filter(p, self.doc.values()))

    def functions(self):
        """
        Returns all documented module level functions in the module
        sorted alphabetically as a list of `pdoc.Function`.
        """
        p = lambda o: isinstance(o, Function)
        return sorted(filter(p, self.doc.values()))

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
        if hasattr(self.module, "__all__"):
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
        return dict(
            [
                (name, obj)
                for name, obj in members.items()
                if self.__is_exported(name, inspect.getmodule(obj))
            ]
        )

    def allmodules(self):
        yield self
        for i in self.submodules():
            yield from i.allmodules()


class Class(Doc):
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

            for n in cls_ast.body if "__init__" in public else []:
                if isinstance(n, ast.FunctionDef) and n.name == "__init__":
                    self.doc_init = _var_docstrings(n, self.module, cls=self, init=True)
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
                self.doc[name] = Function(
                    name, self.module, obj.__func__, cls=self, method=True
                )
            elif inspect.isfunction(obj):
                self.doc[name] = Function(
                    name, self.module, obj, cls=self, method=False
                )
            elif isinstance(obj, property):
                docstring = getattr(obj, "__doc__", "")
                self.doc_init[name] = Variable(name, self.module, docstring, cls=self)
            elif not inspect.isbuiltin(obj) and not inspect.isroutine(obj):
                if name in getattr(self.cls, "__slots__", []):
                    self.doc_init[name] = Variable(name, self.module, "", cls=self)
                else:
                    self.doc[name] = Variable(name, self.module, "", cls=self)

    @property
    def source(self):
        return _source(self.cls)

    @property
    def refname(self):
        return "%s.%s" % (self.module.refname, self.cls.__name__)

    def class_variables(self):
        """
        Returns all documented class variables in the class, sorted
        alphabetically as a list of `pdoc.Variable`.
        """
        p = lambda o: isinstance(o, Variable)
        return sorted(filter(p, self.doc.values()))

    def instance_variables(self):
        """
        Returns all instance variables in the class, sorted
        alphabetically as a list of `pdoc.Variable`. Instance variables
        are attributes of `self` defined in a class's `__init__`
        method.
        """
        p = lambda o: isinstance(o, Variable)
        return sorted(filter(p, self.doc_init.values()))

    def methods(self):
        """
        Returns all documented methods as `pdoc.Function` objects in
        the class, sorted alphabetically with `__init__` always coming
        first.

        Unfortunately, this also includes class methods.
        """
        p = lambda o: (
            isinstance(o, Function) and o.method
        )
        return sorted(filter(p, self.doc.values()))

    def functions(self):
        """
        Returns all documented static functions as `pdoc.Function`
        objects in the class, sorted alphabetically.
        """
        p = lambda o: (
            isinstance(o, Function) and not o.method
        )
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
        mro = [c for c in self.module.mro(self) if c != self and isinstance(c, Class)]

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
                self.doc_init[name] = Variable(d.name, d.module, "", cls=self)
                self.doc_init[name].inherits = d

    def __public_objs(self):
        """
        Returns a dictionary mapping a public identifier name to a
        Python object. This counts the `__init__` method as being
        public.
        """
        _pdoc = getattr(self.module.module, "__pdoc__", {})

        def forced_out(name):
            return _pdoc.get("%s.%s" % (self.name, name), False) is None

        def exported(name):
            exported = name == "__init__" or _is_exported(name)
            return not forced_out(name) and exported

        idents = dict(inspect.getmembers(self.cls))
        return dict([(n, o) for n, o in idents.items() if exported(n)])


class Function(Doc):
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
            return "%s.%s" % (self.module.refname, self.name)
        else:
            return "%s.%s" % (self.cls.refname, self.name)

    def funcdef(self):
        """
        Generates the string of keywords used to define the function, for
        example `def` or `async def`.
        """
        keywords = []

        if self._is_async():
            keywords.append("async")

        keywords.append("def")

        return " ".join(keywords)

    def _is_async(self):
        """
        Returns whether is function is asynchronous, either as a coroutine or an
        async generator.
        """
        try:
            # Both of these are required because coroutines aren't classified as
            # async generators and vice versa.
            return inspect.iscoroutinefunction(self.func) or inspect.isasyncgenfunction(
                self.func
            )
        except AttributeError:
            return False

    def spec(self):
        """
        Returns a nicely formatted spec of the function's parameter
        list as a string. This includes argument lists, keyword
        arguments and default values.
        """
        return ", ".join(self.params())

    def params(self):
        """
        Returns a list where each element is a nicely formatted
        parameter of this function. This includes argument lists,
        keyword arguments and default values.
        """

        def fmt_param(el):
            if isinstance(el, (str, unicode)):
                return el
            else:
                return "(%s)" % (", ".join(map(fmt_param, el)))

        try:
            getspec = getattr(inspect, "getfullargspec", inspect.getargspec)
            s = getspec(self.func)
        except TypeError:
            # I guess this is for C builtin functions?
            return ["..."]

        params = []
        for i, param in enumerate(s.args):
            if s.defaults is not None and len(s.args) - i <= len(s.defaults):
                defind = len(s.defaults) - (len(s.args) - i)
                params.append("%s=%s" % (param, repr(s.defaults[defind])))
            else:
                params.append(fmt_param(param))
        if s.varargs is not None:
            params.append("*%s" % s.varargs)

        kwonlyargs = getattr(s, "kwonlyargs", None)
        if kwonlyargs:
            if s.varargs is None:
                params.append("*")
            for param in kwonlyargs:
                try:
                    params.append("%s=%s" % (param, repr(s.kwonlydefaults[param])))
                except KeyError:
                    params.append(param)

        keywords = getattr(s, "varkw", getattr(s, "keywords", None))
        if keywords is not None:
            params.append("**%s" % keywords)
        # TODO: The only thing now missing for Python 3 are type annotations
        return params

    def __lt__(self, other):
        # Push __init__ to the top.
        if "__init__" in (self.name, other.name):
            return self.name != other.name and self.name == "__init__"
        else:
            return self.name < other.name


class Variable(Doc):
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
            return "%s.%s" % (self.module.refname, self.name)
        else:
            return "%s.%s" % (self.cls.refname, self.name)


class External(Doc):
    """
    A representation of an external identifier. The textual
    representation is the same as an internal identifier, but without
    any context. (Usually this makes linking more difficult.)

    External identifiers are also used to represent something that is
    not exported but appears somewhere in the public interface (like
    the ancestor list of a class).
    """

    __pdoc__[
        "External.docstring"
    ] = """
        An empty string. External identifiers do not have
        docstrings.
        """
    __pdoc__[
        "External.module"
    ] = """
        Always `None`. External identifiers have no associated
        `pdoc.Module`.
        """
    __pdoc__[
        "External.name"
    ] = """
        Always equivalent to `pdoc.External.refname` since external
        identifiers are always expressed in their fully qualified
        form.
        """

    def __init__(self, name):
        """
        Initializes an external identifier with `name`, where `name`
        should be a fully qualified name.
        """
        super(External, self).__init__(name, None, "")

    @property
    def source(self):
        return []

    @property
    def refname(self):
        return self.name

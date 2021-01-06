import ast
import importlib
import inspect

__pdoc__ = {}

import pkgutil

import textwrap

import types
import warnings

from abc import ABC, abstractmethod
from collections import Iterable, Iterator
from dataclasses import field
from functools import cached_property, cache
from itertools import tee, zip_longest

from typing import Any, Optional, Union, TypeVar, get_type_hints, get_origin, ClassVar, ForwardRef

empty = inspect.Signature.empty


# https://github.com/python/cpython/blob/faf49573963921033c608b4d2f398309d9f0d2b5/Lib/typing.py#L161-L179
def _type_repr(obj):
    """Return the repr() of an object, special-casing types (internal helper).
    If obj is a type, we return a shorter version than the default
    type.__repr__, based on the module and qualified name, which is
    typically enough to uniquely identify a type.  For everything
    else, we fall back on repr(obj).
    """
    if isinstance(obj, types.GenericAlias):
        return repr(obj)
    if isinstance(obj, type):
        if obj.__module__ == 'builtins':
            return obj.__qualname__
        return f'{obj.__module__}.{obj.__qualname__}'
    if obj is ...:
        return ('...')
    if isinstance(obj, types.FunctionType):
        return obj.__name__
    return repr(obj)


@cache
def _source(obj: Any) -> str:
    """
    Returns the source code of the Python object `obj` as a str.
    This tries to extract the source from the special
    `__wrapped__` attribute if it exists. Otherwise, it falls back
    to `inspect.getsource`.

    If neither works, an empty string is returned.
    """
    while hasattr(obj, "__wrapped__"):
        obj = obj.__wrapped__
    try:
        return inspect.getsource(obj)
    except Exception:
        return ""


@cache
def _parse_module(source: str) -> ast.Module:
    return ast.parse(source)


@cache
def _parse_class(source: str) -> Union[ast.Module, ast.ClassDef]:
    """Returns an empty ast.Module if source is not available."""
    tree = ast.parse(textwrap.dedent(source))
    assert len(tree.body) <= 1
    if tree.body:
        return tree.body[0]
    return tree


T = TypeVar("T")


def _pairwise_longest(iterable: Iterable[T]) -> Iterable[tuple[T, T]]:
    """s -> (s0,s1), (s1,s2), (s2, s3),  ..., (sN, None)"""
    a, b = tee(iterable)
    next(b, None)
    return zip_longest(a, b)


def _init_nodes(tree: ast.FunctionDef) -> Iterator[ast.AST]:
    """
    Transform attribute assignments like "self.foo = 42" to name assignments like "foo = 42",
    keep all constant expressions, and no-op everything else.
    This essentially allows us to inline __init__ when parsing a class definition.
    """
    for a in tree.body:
        if isinstance(a, ast.AnnAssign) and isinstance(a.target, ast.Attribute) and a.target.value.id == "self":
            yield ast.AnnAssign(
                ast.Name(a.target.attr),
                a.annotation,
                a.value,
                simple=1
            )
        elif isinstance(a, ast.Assign) and len(a.targets) == 1 and isinstance(a.targets[0], ast.Attribute) and \
                isinstance(a.targets[0].value, ast.Name) and a.targets[0].value.id == "self":
            yield ast.Assign(
                [ast.Name(a.targets[0].attr)],
                value=a.value,
                type_comment=a.type_comment,
            )
        elif isinstance(a, ast.Expr) and isinstance(a.value, ast.Constant) and isinstance(a.value.value, str):
            yield a
        else:
            yield ast.Pass()


def __nodes(tree: ast.Module) -> Iterator[ast.AST]:
    for a in tree.body:
        yield a
        if isinstance(a, ast.FunctionDef) and a.name == "__init__":
            yield from _init_nodes(a)


@cache
def _nodes(tree: Union[ast.Module, ast.ClassDef]) -> list[ast.AST]:
    return list(__nodes(tree))


def _namespace_var_docstrings(
        tree: Union[ast.Module, ast.ClassDef]
) -> tuple[dict[str, str], dict[str, str]]:
    docstrings = {}
    annotations = {}
    for a, b in _pairwise_longest(_nodes(tree)):
        if isinstance(a, ast.AnnAssign) and a.simple:
            name = a.target.id
            annotations[name] = ast.unparse(a.annotation)
        elif isinstance(a, ast.Assign) and len(a.targets) == 1 and isinstance(a.targets[0], ast.Name):
            name = a.targets[0].id
        else:
            continue
        if isinstance(b, ast.Expr) and isinstance(b.value, ast.Constant) and isinstance(b.value.value, str):
            docstrings[name] = b.value.value
    return docstrings, annotations


def _sort(
        tree: Union[ast.Module, ast.ClassDef],
        sorted: dict[str, T],
        unsorted: dict[str, T]
) -> tuple[dict[str, T], dict[str, T]]:
    """Returns (sorted, not found)"""
    for a in _nodes(tree):
        if isinstance(a, ast.Assign) and len(a.targets) == 1 and isinstance(a.targets[0], ast.Name):
            name = a.targets[0].id
        elif isinstance(a, ast.AnnAssign) and a.simple:
            name = a.target.id
        elif isinstance(a, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            name = a.name
        else:
            continue

        if name in unsorted:
            sorted[name] = unsorted.pop(name)
    return sorted, unsorted


def _is_exported(ident_name):
    """
    Returns `True` if `ident_name` matches the export criteria for an
    identifier name.

    This should not be used by clients. Instead, use
    `pdoc.Module.is_public`.
    """
    return ident_name == "__init__" or not ident_name.startswith("_")


class Doc(ABC):
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

    module_name: str
    """
    The module that this object was defined in.
    """

    qualname: str
    """
    The qualified identifier name for this object, see https://www.python.org/dev/peps/pep-3155/.
    """

    docstring: str = field(repr=None)
    """
    The docstring for this object. It has already been cleaned by `inspect.cleandoc`.
    """

    def __init__(self, module_name: str, qualname: str, docstring: str):
        """
        Initializes a documentation object, where `name` is the public
        identifier name, `module` is a `pdoc.Module` object, and
        `docstring` is a string containing the docstring for `name`.
        """
        self.module_name = module_name
        self.qualname = qualname
        self.docstring = inspect.cleandoc(docstring or "").strip()

    @cached_property
    @abstractmethod
    def source(self) -> str:
        """
        Returns the source code of the Python object as a str.
        If unsucessful, an empty string is returned.
        """

    @property
    def refname(self) -> str:
        return f"{self.module_name}.{self.qualname}"

    @property
    def name(self) -> str:
        return self.qualname.rsplit(".")[-1]

    def __lt__(self, other):
        return (self.module_name, self.qualname) < (self.module_name, self.qualname)


class Module(Doc):
    """
    Representation of a module's documentation.
    """

    module: types.ModuleType
    """The Python module object."""

    doc: dict[str, Doc]
    """A mapping from all members to their documentation objects."""

    submodules: list["Module"]
    parent: Optional["Module"]

    def __init__(self, module_name: str, module: types.ModuleType, parent: Optional["Module"]):
        """
        Creates a `Module` documentation object given the actual
        module Python object.
        """
        super().__init__(module_name, "", inspect.getdoc(module))
        self.parent = parent
        self.module = module

        if not hasattr(self.module, "__annotations__"):
            self.module.__annotations__ = {}

        self._var_docstrings, types = _namespace_var_docstrings(_parse_module(self.source))
        for name, typestr in types.items():
            self.module.__annotations__.setdefault(name, typestr)


        self.submodules = []
        if self.is_package:
            for mod in pkgutil.iter_modules(self.module.__path__, f"{self.module.__name__}."):
                try:
                    module = importlib.import_module(mod.name)
                except Exception as e:
                    warnings.warn(f"Couldn't import {mod.name}: {e!r}", stacklevel=2)
                    continue
                #spec = mod.module_finder.find_spec(mod.name)
                #module = importlib.util.module_from_spec(spec)
                #print(mod)
                self.submodules.append(Module(mod.name, module, self))

        self.doc = {}

        for name, obj in self._public_members.items():
            if inspect.isroutine(obj):
                self.doc[name] = Function(module_name, self.module, name, obj)
            elif inspect.isclass(obj) and not obj is empty:
                self.doc[name] = Class(module_name, self.module, name, obj)
            else:
                self.doc[name] = Variable(
                    module_name,
                    name,
                    docstring=self._var_docstrings.get(name, ""),
                    annotation=self._var_annotations.get(name, empty),
                )

    def __repr__(self):
        children = "\n".join(repr(x) for x in self.doc.values())
        return f"<module {self.module_name}\n{textwrap.indent(children, '    ')}>"

    @property
    def is_package(self) -> bool:
        return hasattr(self.module, "__path__")

    @cached_property
    def source(self):
        return _source(self.module)

    @cached_property
    def _var_annotations(self) -> dict[str, type]:
        return safe_get_type_hints(self.module)

    @cached_property
    def _documented_variables(self) -> set[str]:
        return self._var_docstrings.keys() | self._var_annotations.keys()

    @cached_property
    def _public_members(self) -> dict[str, Any]:
        """
        Returns a dictionary mapping a public identifier name to a
        Python object.

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
            return {
                name: self.module.__dict__.get(name, empty)
                for name in self.module.__all__
            }

        members = {}
        for name, obj in self.module.__dict__.items():
            if not _is_exported(name):
                continue
            module = inspect.getmodule(obj)
            declared_in_this_module = (
                    self.module.__name__ == getattr(module, "__name__", None)
            )
            if declared_in_this_module or name in self._documented_variables:
                members[name] = obj
        for name in self._var_annotations:
            if _is_exported(name):
                members.setdefault(name, empty)

        members, notfound = _sort(_parse_module(self.source), {}, members)
        members.update(notfound)
        return members

    @cached_property
    def variables(self) -> list["Variable"]:
        """
        Returns all documented module level variables.
        """
        return [
            x for x in self.doc.values()
            if isinstance(x, Variable)
        ]

    @cached_property
    def classes(self) -> list["Class"]:
        """
        Returns all documented module level classes.
        """
        return [
            x for x in self.doc.values()
            if isinstance(x, Class)
        ]

    @cached_property
    def functions(self) -> list["Function"]:
        """
        Returns all documented module level functions.
        """
        return [
            x for x in self.doc.values()
            if isinstance(x, Function)
        ]

    """
    def allmodules(self):
        yield self
        for i in self.submodules:
            yield from i.allmodules()

    def toroot(self):
        n = self
        while n:
            yield n
            n = n.parent
    """


def safe_get_type_hints(obj, ns=None, last_err: str=None) -> dict[str, type]:
    try:
        return get_type_hints(obj, ns)
    except AttributeError as e:
        err = str(e)
        x = err.split("'")
        if len(x) != 5:
            raise RuntimeError(x) from e
        mod = f"{x[1]}.{x[3]}"
    except NameError as e:
        err = str(e)
        x = err.split("'")
        if len(x) != 3:
            raise RuntimeError(x) from e
        mod = x[1]
    if err == last_err:
        raise
    try:
        val = importlib.import_module(mod)
    except Exception:
        val = mod
    return safe_get_type_hints(obj, {
        mod: val,
        **(ns or {})
    }, err)

class Class(Doc):
    """
    Representation of a class's documentation.
    """

    cls: type
    """The class Python object."""

    module: types.ModuleType

    doc: dict[str, Doc]
    """A mapping from identifier name to a documentation object."""

    def __init__(self, module_name: str, module: types.ModuleType, qualname: str, cls: type):
        """
        Same as `pdoc.Doc.__init__`, except `cls` must be a
        Python class object. The docstring is gathered automatically.
        """
        super().__init__(module_name, qualname, inspect.getdoc(cls))

        self.module = module
        self.cls = cls
        self.doc = {}

        if not hasattr(self.cls, "__annotations__"):
            try:
                self.cls.__annotations__ = {}
            except TypeError:
                pass

        self._var_docstrings = {}
        for cls in self.cls.mro():
            docstrings, types = _namespace_var_docstrings(_parse_class(_source(cls)))
            for name, docstr in docstrings.items():
                self._var_docstrings.setdefault(name, docstr)
            for name, typestr in types.items():
                if name not in self.cls.__annotations__:
                    try:
                        typ = ForwardRef(typestr, is_argument=False)._evaluate(
                            inspect.getmodule(cls).__dict__,
                            None,
                            frozenset()
                        )
                    except Exception:
                        pass
                    else:
                        self.cls.__annotations__.setdefault(name, typ)

        # Convert the public Python objects to documentation objects.
        for name, obj in self._public_members.items():
            qualname =  f"{self.qualname}.{name}"
            if isinstance(obj, (staticmethod, classmethod)):
                self.doc[name] = Function(module_name, self.module, qualname, obj)
            elif inspect.isroutine(obj):
                self.doc[name] = Function(module_name, self.module, qualname, obj)
            elif inspect.isclass(obj) and not obj is empty:
                self.doc[name] = Class(module_name, self.module,  qualname, obj)
            elif isinstance(obj, property):
                self.doc[name] = Variable(
                    self.module_name,
                    qualname,
                    docstring=obj.__doc__,
                    annotation=safe_get_type_hints(obj.fget).get("return", empty)
                )
            else:
                self.doc[name] = Variable(
                    module_name,
                    qualname,
                    docstring=self._var_docstrings.get(name, ""),
                    annotation=self._var_annotations.get(name, empty),
                )

    def __repr__(self):
        children = "\n".join(repr(x) for x in self.doc.values())
        return (f"<class {self.module_name}.{self.qualname}{_docstr_repr(self.docstring)}\n"
                f"{textwrap.indent(children, '    ')}>")

    @cached_property
    def _var_annotations(self) -> dict[str, type]:
        return safe_get_type_hints(self.cls, inspect.getmodule(self.cls).__dict__)

    @cached_property
    def _public_members(self) -> dict[str, Any]:
        """
        Returns a dictionary mapping a public identifier name to a
        Python object. This counts the `__init__` method as being
        public.
        """
        unsorted = {}
        for cls in self.cls.mro():
            for name, obj in cls.__dict__.items():
                if _is_exported(name):
                    unsorted.setdefault(name, obj)
        for name in self._var_annotations:
            if _is_exported(name):
                unsorted.setdefault(name, empty)
        for name in self._var_docstrings:
            if _is_exported(name):
                unsorted.setdefault(name, empty)

        sorted = {}
        for cls in self.cls.mro():
            tree = _parse_class(_source(cls))
            sorted, unsorted = _sort(tree, sorted, unsorted)
        if "__init__" in unsorted:
            # move to front
            sorted = {
                "__init__": unsorted.pop("__init__"),
                **sorted
            }
        sorted.update(unsorted)
        return sorted

    @cached_property
    def source(self):
        return _source(self.cls)

    @cached_property
    def members(self) -> list[Doc]:
        return list(self.doc.values())

    @cached_property
    def class_variables(self) -> list["Variable"]:
        """
        Returns all documented class variables in the class.
        """
        return [
            x for x in self.doc.values()
            if isinstance(x, Variable) and get_origin(x) is ClassVar
        ]

    @cached_property
    def instance_variables(self) -> list["Variable"]:
        """
        Returns all instance variables in the class, sorted
        alphabetically as a list of `pdoc.Variable`. Instance variables
        are attributes of `self` defined in a class's `__init__`
        method.
        """
        return [
            x for x in self.doc.values()
            if isinstance(x, Variable) and get_origin(x) is not ClassVar
        ]

    @cached_property
    def classmethods(self) -> list["Function"]:
        """
        Returns all documented class methods.
        """
        return [
            x for x in self.doc.values()
            if isinstance(x, Function) and x.is_classmethod
        ]

    @cached_property
    def staticmethods(self) -> list["Function"]:
        """
        Returns all documented static methods.
        """
        return [
            x for x in self.doc.values()
            if isinstance(x, Function) and x.is_staticmethod
        ]

    @cached_property
    def functions(self) -> list["Function"]:
        """
        Returns all documented functions in the class.
        """
        return [
            x for x in self.doc.values()
            if isinstance(x, Function) and not x.is_staticmethod and not x.is_classmethod
        ]


def _cut(x: str) -> str:
    if len(x) < 20:
        return x
    else:
        return x[:20] + "…"


def _docstr_repr(docstring: str) -> str:
    if docstring:
        return f'  # {_cut(docstring)}'
    else:
        return ""


class Function(Doc):
    """
    Representation of documentation for a Python function or method.
    """

    func: Union[types.FunctionType, staticmethod, classmethod]
    """The Python function object."""

    module: types.ModuleType

    def __init__(
            self,
            module_name: str,
            module: types.ModuleType,
            qualname: str,
            func: Union[types.FunctionType, staticmethod, classmethod],
    ):
        """
        Same as `pdoc.Doc.__init__`, except `func_obj` must be a
        Python function object. The docstring is gathered automatically.

        `cls` should be set when this is a method or a static function
        belonging to a class. `cls` should be a `pdoc.Class` object.

        `method` should be `True` when the function is a method. In
        all other cases, it should be `False`.
        """
        if isinstance(func, (classmethod, staticmethod)):
            doc = inspect.getdoc(func.__func__)
        else:
            doc = inspect.getdoc(func)
        super().__init__(module_name, qualname, doc)
        self.func = func
        self.module = module

    def __repr__(self):
        if self.is_classmethod:
            t = "classmethod"
        elif self.is_staticmethod:
            t = "staticmethod"
        elif self.qualname != self.func.__name__:
            t = "method"
        else:
            t = "function"
        return f"<{t} {self.funcdef} {self.qualname.rsplit('.')[-1]}{self.signature}: ...{_docstr_repr(self.docstring)}>"

    @property
    def is_classmethod(self) -> bool:
        """
        Whether this function is a class method.
        """
        return isinstance(self.func, classmethod)

    @property
    def is_staticmethod(self) -> bool:
        """
        Whether this function is a static method.
        """
        # noinspection PyTypeChecker
        return isinstance(self.func, staticmethod)

    @cached_property
    def source(self):
        return _source(self.func)

    @cached_property
    def funcdef(self) -> str:
        """
        Generates the string of keywords used to define the function, for
        example `def` or `async def`.
        """
        if (
                inspect.iscoroutinefunction(self.func)
                or
                inspect.isasyncgenfunction(self.func)
        ):
            return "async def"
        else:
            return "def"

    @cached_property
    def signature(self) -> inspect.Signature:
        if self.is_classmethod or self.is_staticmethod:
            return inspect.signature(self.func.__func__)
        else:
            return inspect.signature(self.func)

    def __lt__(self, other):
        # Push __init__ to the top.
        assert isinstance(other, Doc)
        if "__init__" in (self.qualname, other.qualname):
            return self.qualname != other.qualname and self.qualname == "__init__"
        else:
            return self.qualname < other.qualname


class Variable(Doc):
    """
    Representation of a variable's documentation. This includes
    module, class and instance variables.
    """

    module: Module = field(repr=False)

    annotation: type
    """
    The variable's type annotation.
    """

    default_value: Any

    def __init__(
            self,
            module_name: str,
            qualname: str,
            docstring: str,
            annotation: Union[type, empty] = empty,
            default_value: Any = empty,
    ):
        """
        Same as `pdoc.Doc.__init__`, except `cls` should be provided
        as a `pdoc.Class` object when this is a class or instance
        variable.
        """
        super().__init__(module_name, qualname, docstring)
        self.annotation = annotation
        self.default_value = default_value

    def __repr__(self):
        if self.annotation is not empty:
            annotation = f": {_type_repr(self.annotation)}"
        else:
            annotation = ""
        return f'<var {self.qualname.rsplit(".")[-1]}{annotation}{_docstr_repr(self.docstring)}>'

    @property
    def source(self):
        return ""

    @property
    def is_classvar(self):
        if get_origin(self.annotation) is ClassVar:
            return True
        else:
            return False


class External(Doc):
    """
    A representation of an external identifier. The textual
    representation is the same as an internal identifier, but without
    any context. (Usually this makes linking more difficult.)

    External identifiers are also used to represent something that is
    not exported but appears somewhere in the public interface (like
    the ancestor list of a class).
    """

    docstring: str = field(repr=False)
    """
    An empty string. External identifiers do not have
    docstrings.
    """

    module: None = field(repr=False)
    """
    Always `None`. External identifiers have no associated
    `pdoc.Module`.
    """

    name: str
    """
    Always equivalent to `pdoc.External.refname` since external
    identifiers are always expressed in their fully qualified
    form.
    """

    def __init__(self, module_name: str, qualname: str):
        """
        Initializes an external identifier with `name`, where `name`
        should be a fully qualified name.
        """
        super().__init__(module_name, qualname, "")

    @property
    def source(self):
        return ""

    @property
    def refname(self):
        return self.name

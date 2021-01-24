"""
This module defines pdoc's documentation objects. A documentation object corresponds to *something*
in your Python code that has a docstring or type annotation. Typically, this only includes
modules, classes, functions and methods. However, `pdoc` adds support for extracting documentation
from the abstract syntax tree, which means that variables (module, class or instance) are supported too.

There are four main types of documentation objects:

- `Module`
- `Class`
- `Function`
- `Variable`

All documentation types types make heavy use of `@functools.cached_property` decorators.
This means they have a large set of attributes that are lazily computed on first access.
By convention, all attributes are read-only, although this this not enforced at runtime.
"""
from __future__ import annotations

import inspect
import pkgutil
import re
import sys
import textwrap
import types
import warnings
from abc import abstractmethod, ABCMeta
from functools import cached_property, wraps
from typing import (  # type: ignore
    Any,
    Union,
    TypeVar,
    get_origin,
    ClassVar,
    Generic,
)

from pdoc import doc_ast, extract
from pdoc.doc_types import empty, resolve_annotations, formatannotation, safe_eval_type
from ._compat import cache


def _include_fullname_in_traceback(f):
    """
    Doc.__repr__ should not raise, but it may raise if we screwed up.
    Debugging this is a bit tricky, because, well, we can't repr() in the traceback either then.
    This decorator adds location information to the traceback, which helps tracking down bugs.
    """

    @wraps(f)
    def wrapper(self):
        try:
            return f(self)
        except Exception as e:
            raise RuntimeError(f"Error in {self.fullname}'s repr!") from e

    return wrapper


T = TypeVar("T")


class Doc(Generic[T]):
    """
    A base class for all documentation objects.
    """

    modulename: str
    """
    The module that this object was defined in, for example `pdoc.doc`.
    """

    qualname: str
    """
    The qualified identifier name for this object. For example, if we have the following code:
    
    ```python
    class Foo:
        def bar(self):
            pass
    ```
    
    The qualname of `Foo`'s `bar` method is `Foo.bar`. The qualname of the `Foo` class is just `Foo`.
    
    See <https://www.python.org/dev/peps/pep-3155/> for details.
    """

    obj: T
    """
    The underlying Python object.
    """

    def __init__(self, modulename: str, qualname: str, obj: T):
        """
        Initializes a documentation object, where
        `modulename` is the name this module is defined in,
        `qualname` contains a dotted path leading to the object from the module top-level, and
        `obj` is the object to document.
        """
        self.modulename = modulename
        self.qualname = qualname
        self.obj = obj

    @cached_property
    def fullname(self) -> str:
        """The full qualified name of this doc object, for example `pdoc.doc.Doc`."""
        # qualname is empty for modules
        return f"{self.modulename}.{self.qualname}".rstrip(".")

    @cached_property
    def name(self) -> str:
        """The name of this object. For top-level functions and classes, this is equal to the qualname attribute."""
        return self.fullname.split(".")[-1]

    @cached_property
    def docstring(self) -> str:
        """
        The docstring for this object. It has already been cleaned by `inspect.cleandoc`.

        If no docstring can be found, an empty string is returned.
        """
        doc = inspect.getdoc(self.obj)
        if doc is None or doc == object.__init__.__doc__:
            # inspect.getdoc(Foo.__init__) returns the docstring, for object.__init__ if left undefined...
            doc = ""
        return doc.strip()

    @cached_property
    def source(self) -> str:
        """
        The source code of the Python object as a `str`.

        If the source cannot be obtained (for example, because we are dealing with a native C object),
        an empty string is returned.
        """
        return doc_ast.get_source(self.obj)

    @cached_property
    def declared_at(self) -> tuple[str, str]:
        """Returns `(modulename, qualname)` of where this doc object was declared."""
        mod = _safe_getattr(self.obj, "__module__", None)
        qual = _safe_getattr(self.obj, "__qualname__", None)
        if mod is None or qual is None or "<locals>" in qual:
            return self.modulename, self.qualname
        else:
            return mod, qual

    @cached_property
    def is_inherited(self) -> bool:
        """
        If True, the doc object is inherited from another location.
        This most commonly refers to methods inherited by a subclass,
        but can also apply to variables that are assigned a class defined
        in a different module.
        """
        return (self.modulename, self.qualname) != self.declared_at

    @classmethod
    @property
    def type(cls) -> str:
        """
        The type of the doc object, either `"module"`, `"class"`, or `"function"`.
        """
        return cls.__name__.lower()

    if sys.version_info < (3, 9):  # pragma: no cover
        # no @classmethod @property in 3.8
        @property
        def type(self) -> str:  # noqa
            return self.__class__.__name__.lower()

    def __lt__(self, other):
        assert isinstance(other, Doc)
        return self.fullname.replace("__init__", "").__lt__(
            other.fullname.replace("__init__", "")
        )


class Namespace(Doc[T], metaclass=ABCMeta):
    """
    A documentation object that can have children. In other words, either a module or a class.
    """

    @cached_property
    @abstractmethod
    def _member_objects(self) -> dict[str, Any]:
        """
        A mapping from *all* public and private member names to their Python objects.
        """

    @cached_property
    @abstractmethod
    def _var_docstrings(self) -> dict[str, str]:
        """A mapping from some member variable names to their docstrings."""

    @cached_property
    @abstractmethod
    def _declared_at(self) -> dict[str, tuple[str, str]]:
        """A mapping from some members to their (modulename, qualname) declaration location."""

    @cached_property
    @abstractmethod
    def _var_annotations(self) -> dict[str, Any]:
        """A mapping from some member variable names to their type annotations."""

    @cached_property
    @abstractmethod
    def own_members(self) -> list[Doc]:
        """A list of all own (i.e. non-inherited) members"""

    @cached_property
    def members(self) -> dict[str, Doc]:
        """A mapping from all members to their documentation objects."""
        members: dict[str, Doc] = {}
        for name, obj in self._member_objects.items():
            qualname = f"{self.qualname}.{name}".lstrip(".")
            doc: Doc[Any]

            is_property = (
                isinstance(obj, (property, cached_property))
                or
                # Python 3.9: @classmethod @property is allowed.
                isinstance(
                    _safe_getattr(obj, "__func__", None), (property, cached_property)
                )
            )
            if is_property:
                func = obj
                if _safe_getattr(obj, "__func__", None):
                    func = obj.__func__
                if isinstance(func, property):
                    func = func.fget
                else:
                    func = func.func
                annotation = resolve_annotations(
                    _safe_getattr(func, "__annotations__", {}),
                    inspect.getmodule(func),
                    f"{self.fullname}.{name}",
                ).get("return", empty)
                doc = Variable(
                    self.modulename,
                    qualname,
                    docstring=func.__doc__ or "",
                    annotation=annotation,
                    default_value=empty,
                    declared_at=self._declared_at.get(
                        name, (self.modulename, qualname)
                    ),
                )
            elif inspect.isroutine(obj):
                doc = Function(self.modulename, qualname, obj)
            elif inspect.isclass(obj) and obj is not empty:
                doc = Class(self.modulename, qualname, obj)
            elif inspect.ismodule(obj):
                doc = Module(obj)
            else:
                docstring = self._var_docstrings.get(name, "")
                doc = Variable(
                    self.modulename,
                    qualname,
                    docstring=docstring,
                    annotation=self._var_annotations.get(name, empty),
                    default_value=obj,
                    declared_at=self._declared_at.get(
                        name, (self.modulename, qualname)
                    ),
                )
            members[doc.name] = doc
        return members

    @cached_property
    def _members_by_declared_location(self) -> dict[tuple[str, str], list[Doc]]:
        """A mapping from (modulename, qualname) locations to the attributes declared in that path"""
        locations: dict[tuple[str, str], list[Doc]] = {}
        for member in self.members.values():
            mod, qualname = member.declared_at
            qualname = ".".join(qualname.split(".")[:-1])
            locations.setdefault((mod, qualname), [])
            locations[(mod, qualname)].append(member)
        return locations

    @cached_property
    def inherited_members(self) -> dict[tuple[str, str], list[Doc]]:
        """A mapping from (modulename, qualname) locations to the attributes inherited from that path"""
        return {
            k: v
            for k, v in self._members_by_declared_location.items()
            if k not in (self.declared_at, (self.modulename, self.qualname))
        }

    @cached_property
    def flattened_own_members(self) -> list[Doc]:
        """
        A list of all documented members and their child classes, recursively.
        """
        flattened = []
        for x in self.own_members:
            flattened.append(x)
            if isinstance(x, Class):
                flattened.extend(
                    [cls for cls in x.flattened_own_members if isinstance(cls, Class)]
                )
        return flattened

    @cache
    def contains(self, identifier: str) -> bool:
        """Returns `True` if the current namespace contains a particular identifier, `False` otherwise."""
        head, _, tail = identifier.partition(".")
        if tail:
            h = self.members.get(head, None)
            if isinstance(h, Namespace):
                return h.contains(tail)
            return False
        else:
            return identifier in self.members


class Module(Namespace[types.ModuleType]):
    """
    Representation of a module's documentation.
    """

    def __init__(self, module: types.ModuleType):
        """
        Creates a documentation object given the actual
        Python module object.
        """
        super().__init__(module.__name__, "", module)

    @cache
    @_include_fullname_in_traceback
    def __repr__(self):
        return f"<module {self.modulename}{_docstr(self)}{_children(self)}>"

    @cached_property
    def is_package(self) -> bool:
        """
        `True` if the module is a package, `False` otherwise.

        Packages are special kind of module that may have submodules.
        Typically, this means that this file is in a directory named like the
        module with the name `__init__.py`.
        """
        return _safe_getattr(self.obj, "__path__", None) is not None

    @cached_property
    def _var_docstrings(self) -> dict[str, str]:
        return doc_ast.walk_tree(self.obj).docstrings

    @cached_property
    def _declared_at(self) -> dict[str, tuple[str, str]]:
        return {}

    @cached_property
    def _var_annotations(self) -> dict[str, Any]:
        annotations = doc_ast.walk_tree(self.obj).annotations.copy()
        for k, v in _safe_getattr(self.obj, "__annotations__", {}).items():
            annotations[k] = v

        return resolve_annotations(annotations, self.obj, self.fullname)

    @cached_property
    def own_members(self) -> list[Doc]:
        return list(self.members.values())

    @cached_property
    def submodules(self) -> list["Module"]:
        """A list of all (direct) submodules."""
        if not self.is_package:
            return []

        if _safe_getattr(self.obj, "__all__", False):
            # If __all__ is set, only show submodules specified there.
            return [
                mod
                for mod in self.members.values()
                if isinstance(mod, Module)
                and mod.modulename.startswith(self.modulename)
            ]

        else:
            submodules = []
            for mod in pkgutil.iter_modules(self.obj.__path__, f"{self.fullname}."):  # type: ignore
                if mod.name.split(".")[-1].startswith("_"):
                    continue
                try:
                    module = extract.load_module(mod.name)
                except RuntimeError as e:
                    warnings.warn(f"Couldn't import {mod.name}: {e!r}", RuntimeWarning)
                    continue
                submodules.append(Module(module))
            return submodules

    @cached_property
    def _documented_members(self) -> set[str]:
        return self._var_docstrings.keys() | self._var_annotations.keys()

    @cached_property
    def _member_objects(self) -> dict[str, Any]:
        members = {}

        if all := _safe_getattr(self.obj, "__all__", False):
            for name in all:
                if name in self.obj.__dict__:
                    val = self.obj.__dict__[name]
                elif name in self._var_annotations:
                    val = empty
                else:
                    # this may be an unimported submodule, try importing.
                    # (https://docs.python.org/3/tutorial/modules.html#importing-from-a-package)
                    try:
                        val = extract.load_module(f"{self.modulename}.{name}")
                    except RuntimeError as e:
                        warnings.warn(
                            f"Found {name!r} in {self.modulename}.__all__, but it does not resolve: {e}",
                            RuntimeWarning,
                        )
                        val = empty
                members[name] = val

        else:
            for name, obj in self.obj.__dict__.items():
                if isinstance(obj, TypeVar):
                    continue
                obj_module = inspect.getmodule(obj)
                declared_in_this_module = self.obj.__name__ == _safe_getattr(
                    obj_module, "__name__", None
                )
                if declared_in_this_module or name in self._documented_members:
                    members[name] = obj
            for name in self._var_annotations:
                members.setdefault(name, empty)

            members, notfound = doc_ast.sort_by_source(self.obj, {}, members)
            members.update(notfound)

        return members

    @cached_property
    def variables(self) -> list["Variable"]:
        """
        A list of all documented module level variables.
        """
        return [x for x in self.members.values() if isinstance(x, Variable)]

    @cached_property
    def classes(self) -> list["Class"]:
        """
        A list of all documented module level classes.
        """
        return [x for x in self.members.values() if isinstance(x, Class)]

    @cached_property
    def functions(self) -> list["Function"]:
        """
        A list of all documented module level functions.
        """
        return [x for x in self.members.values() if isinstance(x, Function)]


class Class(Namespace[type]):
    """
    Representation of a class's documentation.
    """

    @cache
    @_include_fullname_in_traceback
    def __repr__(self):
        return f"<{_decorators(self)}class {self.modulename}.{self.qualname}{_docstr(self)}{_children(self)}>"

    @cached_property
    def _var_docstrings(self) -> dict[str, str]:
        docstrings: dict[str, str] = {}
        for cls in self.obj.__mro__:
            for name, docstr in doc_ast.walk_tree(cls).docstrings.items():
                docstrings.setdefault(name, docstr)
        return docstrings

    @cached_property
    def _declared_at(self) -> dict[str, tuple[str, str]]:
        declared_at: dict[str, tuple[str, str]] = {}
        for cls in self.obj.__mro__:
            treeinfo = doc_ast.walk_tree(cls)
            for name in treeinfo.docstrings.keys() | treeinfo.annotations.keys():
                declared_at.setdefault(
                    name, (cls.__module__, f"{cls.__qualname__}.{name}")
                )
            for name in cls.__dict__:
                declared_at.setdefault(
                    name, (cls.__module__, f"{cls.__qualname__}.{name}")
                )
        return declared_at

    @cached_property
    def _var_annotations(self) -> dict[str, type]:
        annotations: dict[str, type] = {}
        for cls in self.obj.__mro__:
            cls_annotations = doc_ast.walk_tree(cls).annotations.copy()
            dynamic_annotations = _safe_getattr(cls, "__annotations__", None)
            if isinstance(dynamic_annotations, dict):
                for k, v in dynamic_annotations.items():
                    cls_annotations[k] = v
            cls_fullname = (
                _safe_getattr(cls, "__module__", "") + "." + cls.__qualname__
            ).lstrip(".")
            cls_annotations = resolve_annotations(
                cls_annotations, inspect.getmodule(cls), cls_fullname
            )

            for k, v in cls_annotations.items():
                annotations.setdefault(k, v)
        return annotations

    @cached_property
    def own_members(self) -> list[Doc]:
        members = self._members_by_declared_location.get(
            (self.modulename, self.qualname), []
        )
        if self.declared_at != (self.modulename, self.qualname):
            # .declared_at may be != (self.modulename, self.qualname), for example when
            # a module re-exports a class from a private submodule.
            members += self._members_by_declared_location.get(self.declared_at, [])
        return members

    @cached_property
    def _member_objects(self) -> dict[str, Any]:
        unsorted: dict[str, Any] = {}
        for cls in self.obj.__mro__:
            for name, obj in cls.__dict__.items():
                unsorted.setdefault(name, obj)
        for name in self._var_annotations:
            unsorted.setdefault(name, empty)
        for name in self._var_docstrings:
            unsorted.setdefault(name, empty)

        sorted: dict[str, Any] = {}
        for cls in self.obj.__mro__:
            sorted, unsorted = doc_ast.sort_by_source(cls, sorted, unsorted)
        sorted.update(unsorted)
        return sorted

    @cached_property
    def bases(self) -> list[tuple[str, str]]:
        """
        A list of all base classes, i.e. all immediate parent classes.

        Each parent class is represented as a `(modulename, qualname)` tuple.
        """
        return [
            (x.__module__, x.__qualname__)
            for x in self.obj.__bases__
            if x is not object
        ]

    @cached_property
    def decorators(self) -> list[str]:
        """A list of all decorators the class is decorated with."""
        decorators = []
        for t in doc_ast.parse(self.obj).decorator_list:
            decorators.append(f"@{doc_ast.unparse(t)}")
        return decorators

    @cached_property
    def class_variables(self) -> list["Variable"]:
        """
        A list of all documented class variables in the class.

        Class variables are variables that are explicitly annotated with `typing.ClassVar`.
        All other variables are treated as instance variables.
        """
        return [
            x
            for x in self.members.values()
            if isinstance(x, Variable) and x.is_classvar
        ]

    @cached_property
    def instance_variables(self) -> list["Variable"]:
        """
        A list of all instance variables in the class.
        """
        return [
            x
            for x in self.members.values()
            if isinstance(x, Variable) and not x.is_classvar
        ]

    @cached_property
    def classmethods(self) -> list["Function"]:
        """
        A list of all documented `@classmethod`s.
        """
        return [
            x
            for x in self.members.values()
            if isinstance(x, Function) and x.is_classmethod
        ]

    @cached_property
    def staticmethods(self) -> list["Function"]:
        """
        A list of all documented `@staticmethod`s.
        """
        return [
            x
            for x in self.members.values()
            if isinstance(x, Function) and x.is_staticmethod
        ]

    @cached_property
    def methods(self) -> list["Function"]:
        """
        A list of all documented methods in the class that are neither static- nor classmethods.
        """
        return [
            x
            for x in self.members.values()
            if isinstance(x, Function)
            and not x.is_staticmethod
            and not x.is_classmethod
        ]


WrappedFunction = Union[types.FunctionType, staticmethod, classmethod]


class Function(Doc[types.FunctionType]):
    """
    Representation of a function's documentation.

    This class covers all "flavors" of functions, for example it also
    supports `@classmethod`s or `@staticmethod`s.
    """

    wrapped: Union[types.FunctionType, staticmethod, classmethod]
    """The original wrapped function (e.g., `staticmethod(func)`)"""

    obj: types.FunctionType
    """The unwrapped "real" function."""

    def __init__(
        self,
        modulename: str,
        qualname: str,
        func: WrappedFunction,
    ):
        """Initialize a function's documentation object."""
        unwrapped: types.FunctionType
        if isinstance(func, (classmethod, staticmethod)):
            unwrapped = func.__func__  # type: ignore
        else:
            unwrapped = func
        super(Function, self).__init__(modulename, qualname, unwrapped)
        self.wrapped = func

    @cache
    @_include_fullname_in_traceback
    def __repr__(self):
        if self.is_classmethod:
            t = "class"
        elif self.is_staticmethod:
            t = "static"
        elif self.qualname != _safe_getattr(self.obj, "__name__", None):
            t = "method"
        else:
            t = "function"
        return f"<{_decorators(self)}{t} {self.funcdef} {self.name}{self.signature}: ...{_docstr(self)}>"

    @cached_property
    def is_classmethod(self) -> bool:
        """
        `True` if this function is a `@classmethod`, `False` otherwise.
        """
        return isinstance(self.wrapped, classmethod)

    @cached_property
    def is_staticmethod(self) -> bool:
        """
        `True` if this function is a `@staticmethod`, `False` otherwise.
        """
        return isinstance(self.wrapped, staticmethod)

    @cached_property
    def decorators(self) -> list[str]:
        """A list of all decorators the function is decorated with."""
        decorators = []
        # noinspection PyTypeChecker
        obj: types.FunctionType = self.obj  # type: ignore
        for t in doc_ast.parse(obj).decorator_list:
            decorators.append(f"@{doc_ast.unparse(t)}")
        return decorators

    @cached_property
    def funcdef(self) -> str:
        """
        The string of keywords used to define the function, i.e. `"def"` or `"async def"`.
        """
        if inspect.iscoroutinefunction(self.obj) or inspect.isasyncgenfunction(
            self.obj
        ):
            return "async def"
        else:
            return "def"

    @cached_property
    def signature(self) -> inspect.Signature:
        """
        The function's signature.

        This usually returns an instance of `_PrettySignature`, a subclass of `inspect.Signature`
        that contains pdoc-specific optimizations. For example, long argument lists are split over multiple lines
        in repr(). Additionally, all types are already resolved.

        If the signature cannot be determined, a placeholder Signature object is returned.
        """
        if self.obj is object.__init__:
            # there is a weird edge case were inspect.signature returns a confusing (self, /, *args, **kwargs)
            # signature for the default __init__ method.
            return inspect.Signature()
        try:
            sig = _PrettySignature.from_callable(self.obj)
        except Exception:
            return inspect.Signature(
                [inspect.Parameter("unknown", inspect.Parameter.POSITIONAL_OR_KEYWORD)]
            )
        mod = inspect.getmodule(self.obj)
        globalns = _safe_getattr(mod, "__dict__", {})
        if self.name == "__init__":
            sig._return_annotation = empty  # type: ignore
        else:
            sig._return_annotation = safe_eval_type(sig.return_annotation, globalns, self.fullname)  # type: ignore
        for p in sig.parameters.values():
            p._annotation = safe_eval_type(p.annotation, globalns, self.fullname)  # type: ignore
        return sig


class Variable(Doc[None]):
    """
    Representation of a variable's documentation. This includes module, class and instance variables.
    """

    default_value: Union[
        Any, empty
    ]  # technically Any includes empty, but this conveys intent.
    """
    The variable's default value.
    
    In some cases, no default value is known. This may either be because a variable is only defined in the constructor,
    or it is only declared with a type annotation without assignment (`foo: int`).
    To distinguish this case from a default value of `None`, `pdoc.doc_types.empty` is used as a placeholder.
    """

    annotation: Union[type, empty]
    """
    The variable's type annotation.
    
    If there is no type annotation, `pdoc.doc_types.empty` is used as a placeholder.
    """

    # noinspection PyPropertyAccess
    def __init__(
        self,
        modulename: str,
        qualname: str,
        docstring: str,
        declared_at: tuple[str, str],
        annotation: Union[type, empty] = empty,
        default_value: Union[Any, empty] = empty,
    ):
        """
        Construct a variable doc object.

        While classes and functions can introspect themselves to see their docstring,
        variables can't do that as we don't have a "variable object" we could query.
        As such, docstring, declaration location, type annotation, and the default value
        must be passed manually in the constructor.
        """
        super().__init__(modulename, qualname, None)
        self.docstring = inspect.cleandoc(docstring)
        self.declared_at = declared_at
        self.annotation = annotation
        self.default_value = default_value

    @cache
    @_include_fullname_in_traceback
    def __repr__(self):
        return f'<var {self.qualname.rsplit(".")[-1]}{self.annotation_str}{self.default_value_str}{_docstr(self)}>'

    @cached_property
    def is_classvar(self) -> bool:
        """`True` if the variable is a class variable, `False` otherwise."""
        if get_origin(self.annotation) is ClassVar:
            return True
        else:
            return False

    @cached_property
    def default_value_str(self) -> str:
        """The variable's default value as a pretty-printed str."""
        if self.default_value is empty:
            return ""
        else:
            try:
                return re.sub(
                    r"(?<=object) at 0x[0-9a-fA-F]+(?=>$)",
                    "",
                    f" = {repr(self.default_value)}",
                )
            except Exception:
                return " = <unable to get value representation>"

    @cached_property
    def annotation_str(self) -> str:
        """The variable's type annotation as a pretty-printed str."""
        if self.annotation is not empty:
            return f": {formatannotation(self.annotation)}"
        else:
            return ""


class _PrettySignature(inspect.Signature):
    """
    A subclass of `inspect.Signature` that pads __str__ over several lines
    for complex signatures.
    """

    def __str__(self):
        # redeclared here to keep code snipped below as-is.
        _POSITIONAL_ONLY = inspect.Parameter.POSITIONAL_ONLY
        _VAR_POSITIONAL = inspect.Parameter.VAR_POSITIONAL
        _KEYWORD_ONLY = inspect.Parameter.KEYWORD_ONLY
        _empty = empty

        # https://github.com/python/cpython/blob/799f8489d418b7f9207d333eac38214931bd7dcc/Lib/inspect.py#L3083-L3123
        # ✂ start ✂
        result = []
        render_pos_only_separator = False
        render_kw_only_separator = True
        for param in self.parameters.values():
            formatted = str(param)

            kind = param.kind

            if kind == _POSITIONAL_ONLY:
                render_pos_only_separator = True
            elif render_pos_only_separator:
                # It's not a positional-only parameter, and the flag
                # is set to 'True' (there were pos-only params before.)
                result.append("/")
                render_pos_only_separator = False

            if kind == _VAR_POSITIONAL:
                # OK, we have an '*args'-like parameter, so we won't need
                # a '*' to separate keyword-only arguments
                render_kw_only_separator = False
            elif kind == _KEYWORD_ONLY and render_kw_only_separator:
                # We have a keyword-only parameter to render and we haven't
                # rendered an '*args'-like parameter before, so add a '*'
                # separator to the parameters list ("foo(arg1, *, arg2)" case)
                result.append("*")
                # This condition should be only triggered once, so
                # reset the flag
                render_kw_only_separator = False

            result.append(formatted)

        if render_pos_only_separator:
            # There were only positional-only parameters, hence the
            # flag was not reset to 'False'
            result.append("/")

        rendered = "({})".format(", ".join(result))

        if self.return_annotation is not _empty:
            anno = formatannotation(self.return_annotation)
            rendered += " -> {}".format(anno)
        # ✂ end ✂

        if len(rendered) > 70:
            rendered = "(\n\t" + ",\n\t".join(result) + "\n)"
            if self.return_annotation is not _empty:
                rendered += f" -> {formatannotation(self.return_annotation)}"

        return rendered


def _cut(x: str) -> str:
    """helper function for Doc.__repr__()"""
    if len(x) < 20:
        return x
    else:
        return x[:20] + "…"


def _docstr(doc: "Doc") -> str:
    """helper function for Doc.__repr__()"""
    docstr = []
    if doc.is_inherited:
        docstr.append(f"inherited from {'.'.join(doc.declared_at)}")
    if doc.docstring:
        docstr.append(_cut(doc.docstring))
    if docstr:
        return f"  # {', '.join(docstr)}"
    else:
        return ""


def _decorators(doc: Union["Class", "Function"]) -> str:
    """helper function for Doc.__repr__()"""
    if doc.decorators:
        return " ".join(doc.decorators) + " "
    else:
        return ""


def _children(doc: Namespace) -> str:
    children = "\n".join(
        repr(x)
        for x in doc.members.values()
        if not x.name.startswith("_") or x.name == "__init__"
    )
    if children:
        children = f"\n{textwrap.indent(children, '    ')}"
    return children


def _safe_getattr(obj, attr, default):
    """Like `getattr()`, but never raises."""
    try:
        return getattr(obj, attr, default)
    except Exception as e:
        warnings.warn(
            f"getattr({obj!r}, {attr!r}, {default!r}) raised an exception: {e}",
            RuntimeWarning,
        )
        return default

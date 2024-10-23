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

All documentation types make heavy use of `@functools.cached_property` decorators.
This means they have a large set of attributes that are lazily computed on first access.
By convention, all attributes are read-only, although this is not enforced at runtime.
"""

from __future__ import annotations

from abc import ABCMeta
from abc import abstractmethod
from collections.abc import Callable
import dataclasses
import enum
from functools import cache
from functools import cached_property
from functools import singledispatchmethod
from functools import wraps
import inspect
import os
from pathlib import Path
import re
import sys
import textwrap
import traceback
import types
from typing import Any
from typing import ClassVar
from typing import Generic
from typing import TypedDict
from typing import TypeVar
from typing import Union
from typing import get_origin
import warnings

from pdoc import doc_ast
from pdoc import doc_pyi
from pdoc import extract
from pdoc._compat import TypeAlias
from pdoc._compat import TypeAliasType
from pdoc._compat import formatannotation
from pdoc._compat import is_typeddict
from pdoc.doc_types import GenericAlias
from pdoc.doc_types import NonUserDefinedCallables
from pdoc.doc_types import empty
from pdoc.doc_types import resolve_annotations
from pdoc.doc_types import safe_eval_type


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
    The module that this object is in, for example `pdoc.doc`.
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

    taken_from: tuple[str, str]
    """
    `(modulename, qualname)` of this doc object's original location.
    In the context of a module, this points to the location it was imported from,
    in the context of classes, this points to the class an attribute is inherited from.
    """

    kind: ClassVar[str]
    """
    The type of the doc object, either `"module"`, `"class"`, `"function"`, or `"variable"`.
    """

    @property
    def type(self) -> str:  # pragma: no cover
        warnings.warn(
            "pdoc.doc.Doc.type is deprecated. Use pdoc.doc.Doc.kind instead.",
            DeprecationWarning,
        )
        return self.kind

    def __init__(
        self, modulename: str, qualname: str, obj: T, taken_from: tuple[str, str]
    ):
        """
        Initializes a documentation object, where
        `modulename` is the name this module is defined in,
        `qualname` contains a dotted path leading to the object from the module top-level, and
        `obj` is the object to document.
        """
        self.modulename = modulename
        self.qualname = qualname
        self.obj = obj
        self.taken_from = taken_from

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
        return _safe_getdoc(self.obj)

    @cached_property
    def source(self) -> str:
        """
        The source code of the Python object as a `str`.

        If the source cannot be obtained (for example, because we are dealing with a native C object),
        an empty string is returned.
        """
        return doc_ast.get_source(self.obj)

    @cached_property
    def source_file(self) -> Path | None:
        """The name of the Python source file in which this object was defined. `None` for built-in objects."""
        try:
            return Path(inspect.getsourcefile(self.obj) or inspect.getfile(self.obj))  # type: ignore
        except TypeError:
            return None

    @cached_property
    def source_lines(self) -> tuple[int, int] | None:
        """
        Return a `(start, end)` line number tuple for this object.

        If no source file can be found, `None` is returned.
        """
        try:
            lines, start = inspect.getsourcelines(self.obj)  # type: ignore
            return start, start + len(lines) - 1
        except Exception:
            return None

    @cached_property
    def is_inherited(self) -> bool:
        """
        If True, the doc object is inherited from another location.
        This most commonly refers to methods inherited by a subclass,
        but can also apply to variables that are assigned a class defined
        in a different module.
        """
        return (self.modulename, self.qualname) != self.taken_from

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
    def _func_docstrings(self) -> dict[str, str]:
        """A mapping from some member function names to their raw (not processed by any @decorators) docstrings."""

    @cached_property
    @abstractmethod
    def _var_annotations(self) -> dict[str, Any]:
        """A mapping from some member variable names to their type annotations."""

    @abstractmethod
    def _taken_from(self, member_name: str, obj: Any) -> tuple[str, str]:
        """The location this member was taken from. If unknown, (modulename, qualname) is returned."""

    @cached_property
    @abstractmethod
    def own_members(self) -> list[Doc]:
        """A list of all own (i.e. non-inherited) `members`."""

    @cached_property
    def members(self) -> dict[str, Doc]:
        """A mapping from all members to their documentation objects.

        This mapping includes private members; they are only filtered out as part of the template logic.
        Constructors for enums, dicts, and abstract base classes are not picked up unless they have a custom docstring.
        """
        members: dict[str, Doc] = {}
        for name, obj in self._member_objects.items():
            qualname = f"{self.qualname}.{name}".lstrip(".")
            taken_from = self._taken_from(name, obj)
            doc: Doc[Any]

            is_classmethod = isinstance(obj, classmethod)
            is_property = (
                isinstance(obj, (property, cached_property))
                or
                # Python 3.9 - 3.10: @classmethod @property is allowed.
                is_classmethod
                and isinstance(obj.__func__, (property, cached_property))
            )
            if is_property:
                func = obj
                if is_classmethod:
                    func = obj.__func__
                if isinstance(func, property):
                    func = func.fget
                else:
                    assert isinstance(func, cached_property)
                    func = func.func

                doc_f = Function(self.modulename, qualname, func, taken_from)
                doc = Variable(
                    self.modulename,
                    qualname,
                    docstring=doc_f.docstring,
                    annotation=doc_f.signature.return_annotation,
                    default_value=empty,
                    taken_from=taken_from,
                )
                doc.source = doc_f.source
                doc.source_file = doc_f.source_file
                doc.source_lines = doc_f.source_lines
            elif inspect.isroutine(obj):
                doc = Function(self.modulename, qualname, obj, taken_from)  # type: ignore
            elif (
                inspect.isclass(obj)
                and obj is not empty
                and not isinstance(obj, GenericAlias)
                and obj.__qualname__.rpartition(".")[2] == qualname.rpartition(".")[2]
            ):
                # `dict[str,str]` is a GenericAlias instance. We want to render type aliases as variables though.
                doc = Class(self.modulename, qualname, obj, taken_from)
            elif inspect.ismodule(obj):
                if os.environ.get("PDOC_SUBMODULES"):  # pragma: no cover
                    doc = Module.from_name(obj.__name__)
                else:
                    continue
            elif inspect.isdatadescriptor(obj):
                doc = Variable(
                    self.modulename,
                    qualname,
                    docstring=getattr(obj, "__doc__", None) or "",
                    annotation=self._var_annotations.get(name, empty),
                    default_value=empty,
                    taken_from=taken_from,
                )
            else:
                doc = Variable(
                    self.modulename,
                    qualname,
                    docstring="",
                    annotation=self._var_annotations.get(name, empty),
                    default_value=obj,
                    taken_from=taken_from,
                )
            if self._var_docstrings.get(name):
                doc.docstring = self._var_docstrings[name]
            if self._func_docstrings.get(name) and not doc.docstring:
                doc.docstring = self._func_docstrings[name]
            members[doc.name] = doc

        if isinstance(self, Module):
            # quirk: doc_pyi expects .members to be set already
            self.members = members  # type: ignore
            doc_pyi.include_typeinfo_from_stub_files(self)

        return members

    @cached_property
    def _members_by_origin(self) -> dict[tuple[str, str], list[Doc]]:
        """A mapping from (modulename, qualname) locations to the attributes taken from that path"""
        locations: dict[tuple[str, str], list[Doc]] = {}
        for member in self.members.values():
            mod, qualname = member.taken_from
            parent_qualname = ".".join(qualname.rsplit(".", maxsplit=1)[:-1])
            locations.setdefault((mod, parent_qualname), [])
            locations[(mod, parent_qualname)].append(member)
        return locations

    @cached_property
    def inherited_members(self) -> dict[tuple[str, str], list[Doc]]:
        """A mapping from (modulename, qualname) locations to the attributes inherited from that path"""
        return {
            k: v
            for k, v in self._members_by_origin.items()
            if k not in (self.taken_from, (self.modulename, self.qualname))
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
    def get(self, identifier: str) -> Doc | None:
        """Returns the documentation object for a particular identifier, or `None` if the identifier cannot be found."""
        head, _, tail = identifier.partition(".")
        if tail:
            h = self.members.get(head, None)
            if isinstance(h, Class):
                return h.get(tail)
            return None
        else:
            return self.members.get(identifier, None)


class Module(Namespace[types.ModuleType]):
    """
    Representation of a module's documentation.
    """

    def __init__(
        self,
        module: types.ModuleType,
    ):
        """
        Creates a documentation object given the actual
        Python module object.
        """
        super().__init__(module.__name__, "", module, (module.__name__, ""))

    kind = "module"

    @classmethod
    @cache
    def from_name(cls, name: str) -> Module:
        """Create a `Module` object by supplying the module's (full) name."""
        return cls(extract.load_module(name))

    @cache
    @_include_fullname_in_traceback
    def __repr__(self):
        return f"<module {self.fullname}{_docstr(self)}{_children(self)}>"

    @cached_property
    def is_package(self) -> bool:
        """
        `True` if the module is a package, `False` otherwise.

        Packages are a special kind of module that may have submodules.
        Typically, this means that this file is in a directory named like the
        module with the name `__init__.py`.
        """
        return _safe_getattr(self.obj, "__path__", None) is not None

    @cached_property
    def _var_docstrings(self) -> dict[str, str]:
        return doc_ast.walk_tree(self.obj).var_docstrings

    @cached_property
    def _func_docstrings(self) -> dict[str, str]:
        return doc_ast.walk_tree(self.obj).func_docstrings

    @cached_property
    def _var_annotations(self) -> dict[str, Any]:
        annotations = doc_ast.walk_tree(self.obj).annotations.copy()
        for k, v in _safe_getattr(self.obj, "__annotations__", {}).items():
            annotations[k] = v

        return resolve_annotations(annotations, self.obj, None, self.fullname)

    def _taken_from(self, member_name: str, obj: Any) -> tuple[str, str]:
        if obj is empty:
            return self.modulename, f"{self.qualname}.{member_name}".lstrip(".")
        if isinstance(obj, types.ModuleType):
            return obj.__name__, ""

        mod = _safe_getattr(obj, "__module__", None)
        qual = _safe_getattr(obj, "__qualname__", None)
        if mod and isinstance(qual, str) and "<locals>" not in qual:
            return mod, qual
        else:
            # This might be wrong, but it's the best guess we have.
            return (mod or self.modulename), f"{self.qualname}.{member_name}".lstrip(
                "."
            )

    @cached_property
    def own_members(self) -> list[Doc]:
        return list(self.members.values())

    @cached_property
    def submodules(self) -> list[Module]:
        """A list of all (direct) submodules."""
        include: Callable[[str], bool]
        mod_all = _safe_getattr(self.obj, "__all__", False)
        if mod_all is not False:
            mod_all_pos = {name: i for i, name in enumerate(mod_all)}
            include = mod_all_pos.__contains__
        else:

            def include(name: str) -> bool:
                # optimization: we don't even try to load modules starting with an underscore as they would not be
                # visible by default. The downside of this is that someone who overrides `is_public` will miss those
                # entries, the upsides are 1) better performance and 2) less warnings because of import failures
                # (think of OS-specific modules, e.g. _linux.py failing to import on Windows).
                return not name.startswith("_")

        submodules: list[Module] = []
        for mod_name, mod in extract.iter_modules2(self.obj).items():
            if not include(mod_name):
                continue
            try:
                module = Module.from_name(mod.name)
            except RuntimeError:
                warnings.warn(f"Couldn't import {mod.name}:\n{traceback.format_exc()}")
                continue
            submodules.append(module)

        if mod_all:
            submodules = sorted(submodules, key=lambda m: mod_all_pos[m.name])

        return submodules

    @cached_property
    def _ast_keys(self) -> set[str]:
        return (
            self._var_docstrings.keys()
            | self._func_docstrings.keys()
            | self._var_annotations.keys()
        )

    @cached_property
    def _member_objects(self) -> dict[str, Any]:
        members = {}

        all_: list[str] | None = _safe_getattr(self.obj, "__all__", None)
        if all_ is not None:
            for name in all_:
                if not isinstance(name, str):
                    # Gracefully handle the case where objects are directly specified in __all__.
                    name = _safe_getattr(name, "__name__", str(name))
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
                            f"Found {name!r} in {self.modulename}.__all__, but it does not resolve: {e}"
                        )
                        val = empty
                members[name] = val

        else:
            # Starting with Python 3.10, __annotations__ is created on demand,
            # so we make a copy here as obj.__dict__ is changed while we iterate over it.
            # Additionally, accessing self._ast_keys may lead to the execution of TYPE_CHECKING blocks,
            # which may also modify obj.__dict__. (https://github.com/mitmproxy/pdoc/issues/351)
            for name, obj in list(self.obj.__dict__.items()):
                # We already exclude everything here that is imported.
                obj_module = inspect.getmodule(obj)
                declared_in_this_module = self.obj.__name__ == _safe_getattr(
                    obj_module, "__name__", None
                )
                include_in_docs = declared_in_this_module or name in self._ast_keys
                if include_in_docs:
                    members[name] = obj

            for name in self._var_docstrings:
                members.setdefault(name, empty)
            for name in self._var_annotations:
                members.setdefault(name, empty)

            members, notfound = doc_ast.sort_by_source(self.obj, {}, members)
            members.update(notfound)

        return members

    @cached_property
    def variables(self) -> list[Variable]:
        """
        A list of all documented module level variables.
        """
        return [x for x in self.members.values() if isinstance(x, Variable)]

    @cached_property
    def classes(self) -> list[Class]:
        """
        A list of all documented module level classes.
        """
        return [x for x in self.members.values() if isinstance(x, Class)]

    @cached_property
    def functions(self) -> list[Function]:
        """
        A list of all documented module level functions.
        """
        return [x for x in self.members.values() if isinstance(x, Function)]


class Class(Namespace[type]):
    """
    Representation of a class's documentation.
    """

    kind = "class"

    @cache
    @_include_fullname_in_traceback
    def __repr__(self):
        return f"<{_decorators(self)}class {self.modulename}.{self.qualname}{_docstr(self)}{_children(self)}>"

    @cached_property
    def docstring(self) -> str:
        doc = Doc.docstring.__get__(self)  # type: ignore
        if doc == dict.__doc__:
            # Don't display default docstring for dict subclasses (primarily TypedDict).
            return ""
        if doc in _Enum_default_docstrings:
            # Don't display default docstring for enum subclasses.
            return ""
        if dataclasses.is_dataclass(self.obj) and doc.startswith(self.obj.__name__):
            try:
                sig = inspect.signature(self.obj)
            except Exception:
                pass
            else:
                # from https://github.com/python/cpython/blob/3.10/Lib/dataclasses.py
                is_dataclass_with_default_docstring = doc == self.obj.__name__ + str(
                    sig
                ).replace(" -> None", "")
                if is_dataclass_with_default_docstring:
                    return ""
        return doc

    @cached_property
    def _var_docstrings(self) -> dict[str, str]:
        docstrings: dict[str, str] = {}
        for cls in self._bases:
            for name, docstr in doc_ast.walk_tree(cls).var_docstrings.items():
                docstrings.setdefault(name, docstr)
        return docstrings

    @cached_property
    def _func_docstrings(self) -> dict[str, str]:
        docstrings: dict[str, str] = {}
        for cls in self._bases:
            for name, docstr in doc_ast.walk_tree(cls).func_docstrings.items():
                docstrings.setdefault(name, docstr)
        return docstrings

    @cached_property
    def _var_annotations(self) -> dict[str, type]:
        # this is a bit tricky: __annotations__ also includes annotations from parent classes,
        # but we need to execute them in the namespace of the parent class.
        # Our workaround for this is to walk the MRO backwards, and only update/evaluate only if the annotation changes.
        annotations: dict[
            str, tuple[Any, type]
        ] = {}  # attribute -> (annotation_unresolved, annotation_resolved)
        for cls in reversed(self._bases):
            cls_annotations = doc_ast.walk_tree(cls).annotations.copy()
            dynamic_annotations = _safe_getattr(cls, "__annotations__", None)
            if isinstance(dynamic_annotations, dict):
                for attr, unresolved_annotation in dynamic_annotations.items():
                    cls_annotations[attr] = unresolved_annotation
            cls_fullname = (
                _safe_getattr(cls, "__module__", "") + "." + cls.__qualname__
            ).lstrip(".")

            new_annotations = {
                attr: unresolved_annotation
                for attr, unresolved_annotation in cls_annotations.items()
                if attr not in annotations
                or annotations[attr][0] is not unresolved_annotation
            }
            localns = _safe_getattr(cls, "__dict__", None)
            for attr, t in resolve_annotations(
                new_annotations, inspect.getmodule(cls), localns, cls_fullname
            ).items():
                annotations[attr] = (new_annotations[attr], t)

        return {k: v[1] for k, v in annotations.items()}

    @cached_property
    def _bases(self) -> tuple[type, ...]:
        orig_bases = _safe_getattr(self.obj, "__orig_bases__", ())

        if is_typeddict(self.obj):
            if sys.version_info < (3, 12):  # pragma: no cover
                # TypedDicts on Python <3.12 have a botched __mro__. We need to fix it.
                return (self.obj, *orig_bases[:-1])
            else:
                # TypedDict on Python >=3.12 removes intermediate classes from __mro__,
                # so we use orig_bases to recover the full mro.
                while orig_bases and orig_bases[-1] is not TypedDict:
                    parent_bases = _safe_getattr(orig_bases[-1], "__orig_bases__", ())
                    if (
                        len(parent_bases) != 1 or parent_bases in orig_bases
                    ):  # sanity check that things look right
                        break  # pragma: no cover
                    orig_bases = (*orig_bases, parent_bases[0])

        # __mro__ and __orig_bases__ differ between Python versions and special cases like TypedDict/NamedTuple.
        # This here is a pragmatic approximation of what we want.
        return (
            *(base for base in orig_bases if isinstance(base, type)),
            *self.obj.__mro__,
        )

    @cached_property
    def _declarations(self) -> dict[str, tuple[str, str]]:
        decls: dict[str, tuple[str, str]] = {}
        for cls in self._bases:
            treeinfo = doc_ast.walk_tree(cls)
            for name in (
                treeinfo.var_docstrings.keys()
                | treeinfo.func_docstrings.keys()
                | treeinfo.annotations.keys()
            ):
                decls.setdefault(name, (cls.__module__, f"{cls.__qualname__}.{name}"))
            for name in cls.__dict__:
                decls.setdefault(name, (cls.__module__, f"{cls.__qualname__}.{name}"))
        if decls.get("__init__", None) == ("builtins", "object.__init__"):
            decls["__init__"] = (
                self.obj.__module__,
                f"{self.obj.__qualname__}.__init__",
            )
        return decls

    def _taken_from(self, member_name: str, obj: Any) -> tuple[str, str]:
        try:
            return self._declarations[member_name]
        except KeyError:  # pragma: no cover
            # TypedDict botches __mro__ on Python <3.12 and may need special casing here.
            # One workaround is to also specify TypedDict as a base class, see pdoc.doc.Class._bases.
            warnings.warn(
                f"Cannot determine where {self.fullname}.{member_name} is taken from, assuming current file."
            )
            return self.modulename, f"{self.qualname}.{member_name}"

    @cached_property
    def own_members(self) -> list[Doc]:
        members = self._members_by_origin.get((self.modulename, self.qualname), [])
        if self.taken_from != (self.modulename, self.qualname):
            # .taken_from may be != (self.modulename, self.qualname), for example when
            # a module re-exports a class from a private submodule.
            members += self._members_by_origin.get(self.taken_from, [])
        return members

    @cached_property
    def _member_objects(self) -> dict[str, Any]:
        unsorted: dict[str, Any] = {}
        for cls in self._bases:
            for name, obj in cls.__dict__.items():
                unsorted.setdefault(name, obj)
        for name in self._var_docstrings:
            unsorted.setdefault(name, empty)
        for name in self._var_annotations:
            unsorted.setdefault(name, empty)

        init_has_no_doc = unsorted.get("__init__", object.__init__).__doc__ in (
            None,
            object.__init__.__doc__,
        )
        if init_has_no_doc:
            if inspect.isabstract(self.obj):
                # Special case: We don't want to show constructors for abstract base classes unless
                # they have a custom docstring.
                del unsorted["__init__"]
            elif issubclass(self.obj, enum.Enum):
                # Special case: Do not show a constructor for enums. They are typically not constructed by users.
                # The alternative would be showing __new__, as __call__ is too verbose.
                del unsorted["__init__"]
            elif issubclass(self.obj, dict):
                # Special case: Do not show a constructor for dict subclasses.
                unsorted.pop(
                    "__init__", None
                )  # TypedDict subclasses may not have __init__.
            else:
                # Check if there's a helpful Metaclass.__call__ or Class.__new__. This dance is very similar to
                # https://github.com/python/cpython/blob/9feae41c4f04ca27fd2c865807a5caeb50bf4fc4/Lib/inspect.py#L2359-L2376
                call = _safe_getattr(type(self.obj), "__call__", None)
                custom_call_with_custom_docstring = (
                    call is not None
                    and not isinstance(call, NonUserDefinedCallables)
                    and call.__doc__ not in (None, object.__call__.__doc__)
                )
                if custom_call_with_custom_docstring:
                    unsorted["__init__"] = call
                else:
                    # Does our class define a custom __new__ method?
                    new = _safe_getattr(self.obj, "__new__", None)
                    custom_new_with_custom_docstring = (
                        new is not None
                        and not isinstance(new, NonUserDefinedCallables)
                        and new.__doc__ not in (None, object.__new__.__doc__)
                    )
                    if custom_new_with_custom_docstring:
                        unsorted["__init__"] = new

        sorted: dict[str, Any] = {}
        for cls in self._bases:
            sorted, unsorted = doc_ast.sort_by_source(cls, sorted, unsorted)
        sorted.update(unsorted)
        return sorted

    @cached_property
    def bases(self) -> list[tuple[str, str, str]]:
        """
        A list of all base classes, i.e. all immediate parent classes.

        Each parent class is represented as a `(modulename, qualname, display_text)` tuple.
        """
        bases = []
        for x in _safe_getattr(self.obj, "__orig_bases__", self.obj.__bases__):
            if x is object:
                continue
            o = get_origin(x)
            if o:
                bases.append((o.__module__, o.__qualname__, str(x)))
            elif x.__module__ == self.modulename:
                bases.append((x.__module__, x.__qualname__, x.__qualname__))
            else:
                bases.append(
                    (x.__module__, x.__qualname__, f"{x.__module__}.{x.__qualname__}")
                )
        return bases

    @cached_property
    def decorators(self) -> list[str]:
        """A list of all decorators the class is decorated with."""
        decorators = []
        for t in doc_ast.parse(self.obj).decorator_list:
            decorators.append(f"@{doc_ast.unparse(t)}")
        return decorators

    @cached_property
    def class_variables(self) -> list[Variable]:
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
    def instance_variables(self) -> list[Variable]:
        """
        A list of all instance variables in the class.
        """
        return [
            x
            for x in self.members.values()
            if isinstance(x, Variable) and not x.is_classvar
        ]

    @cached_property
    def classmethods(self) -> list[Function]:
        """
        A list of all documented `@classmethod`s.
        """
        return [
            x
            for x in self.members.values()
            if isinstance(x, Function) and x.is_classmethod
        ]

    @cached_property
    def staticmethods(self) -> list[Function]:
        """
        A list of all documented `@staticmethod`s.
        """
        return [
            x
            for x in self.members.values()
            if isinstance(x, Function) and x.is_staticmethod
        ]

    @cached_property
    def methods(self) -> list[Function]:
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


if sys.version_info >= (3, 10):
    WrappedFunction = types.FunctionType | staticmethod | classmethod
else:  # pragma: no cover
    WrappedFunction = Union[types.FunctionType, staticmethod, classmethod]


class Function(Doc[types.FunctionType]):
    """
    Representation of a function's documentation.

    This class covers all "flavors" of functions, for example it also
    supports `@classmethod`s or `@staticmethod`s.
    """

    kind = "function"

    wrapped: WrappedFunction
    """The original wrapped function (e.g., `staticmethod(func)`)"""

    obj: types.FunctionType
    """The unwrapped "real" function."""

    def __init__(
        self,
        modulename: str,
        qualname: str,
        func: WrappedFunction,
        taken_from: tuple[str, str],
    ):
        """Initialize a function's documentation object."""
        unwrapped: types.FunctionType
        if isinstance(func, (classmethod, staticmethod)):
            unwrapped = func.__func__  # type: ignore
        elif isinstance(func, singledispatchmethod):
            unwrapped = func.func  # type: ignore
        elif hasattr(func, "__wrapped__"):
            unwrapped = func.__wrapped__
        else:
            unwrapped = func
        super().__init__(modulename, qualname, unwrapped, taken_from)
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
    def docstring(self) -> str:
        doc = Doc.docstring.__get__(self)  # type: ignore
        if not doc:
            # inspect.getdoc fails for inherited @classmethods and unbound @property descriptors.
            # We now do an ugly dance to obtain the bound object instead,
            # that somewhat resembles what inspect._findclass is doing.
            cls = sys.modules.get(_safe_getattr(self.obj, "__module__", None), None)
            for name in _safe_getattr(self.obj, "__qualname__", "").split(".")[:-1]:
                cls = _safe_getattr(cls, name, None)

            unbound = _safe_getattr(cls, "__dict__", {}).get(self.name)
            is_classmethod_property = isinstance(unbound, classmethod) and isinstance(
                unbound.__func__, (property, cached_property)
            )
            if not is_classmethod_property:
                # We choke on @classmethod @property, but that's okay because it's been deprecated with Python 3.11.
                # Directly accessing them would give us the return value, which has the wrong docstring.
                doc = _safe_getdoc(_safe_getattr(cls, self.name, None))

        if doc == object.__init__.__doc__:
            # inspect.getdoc(Foo.__init__) returns the docstring, for object.__init__ if left undefined...
            return ""
        else:
            return doc

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
        localns = globalns
        for parent_cls_name in self.qualname.split(".")[:-1]:
            parent_cls = localns.get(parent_cls_name, object)
            localns = _safe_getattr(parent_cls, "__dict__", None)
            if localns is None:
                break  # pragma: no cover

        if self.name == "__init__":
            sig = sig.replace(return_annotation=empty)
        else:
            sig = sig.replace(
                return_annotation=safe_eval_type(
                    sig.return_annotation, globalns, localns, mod, self.fullname
                )
            )
        for p in sig.parameters.values():
            p._annotation = safe_eval_type(  # type: ignore
                p.annotation, globalns, localns, mod, self.fullname
            )
        return sig

    @cached_property
    def signature_without_self(self) -> inspect.Signature:
        """Like `signature`, but without the first argument.

        This is useful to display constructors.
        """
        return self.signature.replace(
            parameters=list(self.signature.parameters.values())[1:]
        )


class Variable(Doc[None]):
    """
    Representation of a variable's documentation. This includes module, class and instance variables.
    """

    kind = "variable"

    default_value: (
        Any | empty
    )  # technically Any includes empty, but this conveys intent.
    """
    The variable's default value.
    
    In some cases, no default value is known. This may either be because a variable is only defined in the constructor,
    or it is only declared with a type annotation without assignment (`foo: int`).
    To distinguish this case from a default value of `None`, `pdoc.doc_types.empty` is used as a placeholder.
    """

    annotation: type | empty
    """
    The variable's type annotation.
    
    If there is no type annotation, `pdoc.doc_types.empty` is used as a placeholder.
    """

    def __init__(
        self,
        modulename: str,
        qualname: str,
        *,
        taken_from: tuple[str, str],
        docstring: str,
        annotation: type | empty = empty,
        default_value: Any | empty = empty,
    ):
        """
        Construct a variable doc object.

        While classes and functions can introspect themselves to see their docstring,
        variables can't do that as we don't have a "variable object" we could query.
        As such, docstring, declaration location, type annotation, and the default value
        must be passed manually in the constructor.
        """
        super().__init__(modulename, qualname, None, taken_from)
        # noinspection PyPropertyAccess
        self.docstring = inspect.cleandoc(docstring)
        self.annotation = annotation
        self.default_value = default_value

    @cache
    @_include_fullname_in_traceback
    def __repr__(self):
        if self.default_value_str:
            default = f" = {self.default_value_str}"
        else:
            default = ""
        return f'<var {self.qualname.rsplit(".")[-1]}{self.annotation_str}{default}{_docstr(self)}>'

    @cached_property
    def is_classvar(self) -> bool:
        """`True` if the variable is a class variable, `False` otherwise."""
        if get_origin(self.annotation) is ClassVar:
            return True
        else:
            return False

    @cached_property
    def is_typevar(self) -> bool:
        """`True` if the variable is a `typing.TypeVar`, `False` otherwise."""
        if isinstance(self.default_value, TypeVar):
            return True
        else:
            return False

    @cached_property
    def is_type_alias_type(self) -> bool:
        """`True` if the variable is a `typing.TypeAliasType`, `False` otherwise."""
        return isinstance(self.default_value, TypeAliasType)

    @cached_property
    def is_enum_member(self) -> bool:
        """`True` if the variable is an enum member, `False` otherwise."""
        if isinstance(self.default_value, enum.Enum):
            return True
        else:
            return False

    @cached_property
    def default_value_str(self) -> str:
        """The variable's default value as a pretty-printed str."""
        if self.default_value is empty:
            return ""
        if isinstance(self.default_value, TypeAliasType):
            formatted = formatannotation(self.default_value.__value__)
            return _remove_collections_abc(formatted)
        elif self.annotation == TypeAlias:
            formatted = formatannotation(self.default_value)
            return _remove_collections_abc(formatted)

        # This is not perfect, but a solid attempt at preventing accidental leakage of secrets.
        # If you have input on how to improve the heuristic, please send a pull request!
        value_taken_from_env_var = (
            isinstance(self.default_value, str)
            and len(self.default_value) >= 8
            and self.default_value in _environ_lookup()
        )
        if value_taken_from_env_var and not os.environ.get("PDOC_DISPLAY_ENV_VARS", ""):
            env_var = "$" + _environ_lookup()[self.default_value]
            warnings.warn(
                f"The default value of {self.fullname} matches the {env_var} environment variable. "
                f"To prevent accidental leakage of secrets, the default value is not displayed. "
                f"Disable this behavior by setting PDOC_DISPLAY_ENV_VARS=1 as an environment variable.",
                RuntimeWarning,
            )
            return env_var

        try:
            pretty = repr(self.default_value)
        except Exception as e:
            warnings.warn(f"repr({self.fullname}) raised an exception ({e!r})")
            return ""

        pretty = _remove_memory_addresses(pretty)
        return pretty

    @cached_property
    def annotation_str(self) -> str:
        """The variable's type annotation as a pretty-printed str."""
        if self.annotation is not empty:
            formatted = formatannotation(self.annotation)
            return f": {_remove_collections_abc(formatted)}"
        else:
            return ""


@cache
def _environ_lookup():
    """
    A reverse lookup of os.environ. This is a cached function so that it is evaluated lazily.
    """
    return {value: key for key, value in os.environ.items()}


class _PrettySignature(inspect.Signature):
    """
    A subclass of `inspect.Signature` that pads __str__ over several lines
    for complex signatures.
    """

    MULTILINE_CUTOFF = 70

    def _params(self) -> list[str]:
        # redeclared here to keep code snipped below as-is.
        _POSITIONAL_ONLY = inspect.Parameter.POSITIONAL_ONLY
        _VAR_POSITIONAL = inspect.Parameter.VAR_POSITIONAL
        _KEYWORD_ONLY = inspect.Parameter.KEYWORD_ONLY

        # https://github.com/python/cpython/blob/799f8489d418b7f9207d333eac38214931bd7dcc/Lib/inspect.py#L3083-L3117
        # Change: added re.sub() to formatted = ....
        # ✂ start ✂
        result = []
        render_pos_only_separator = False
        render_kw_only_separator = True
        for param in self.parameters.values():
            formatted = str(param)
            formatted = _remove_memory_addresses(formatted)
            formatted = _remove_collections_abc(formatted)

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
        # ✂ end ✂

        return result

    def _return_annotation_str(self) -> str:
        if self.return_annotation is not empty:
            formatted = formatannotation(self.return_annotation)
            return _remove_collections_abc(formatted)
        else:
            return ""

    def __str__(self):
        result = self._params()
        return_annot = self._return_annotation_str()

        total_len = sum(len(x) + 2 for x in result) + len(return_annot)

        if total_len > self.MULTILINE_CUTOFF:
            rendered = "(\n    " + ",\n    ".join(result) + "\n)"
        else:
            rendered = "({})".format(", ".join(result))
        if return_annot:
            rendered += f" -> {return_annot}"

        return rendered


def _cut(x: str) -> str:
    """helper function for Doc.__repr__()"""
    if len(x) < 20:
        return x
    else:
        return x[:20] + "…"


def _docstr(doc: Doc) -> str:
    """helper function for Doc.__repr__()"""
    docstr = []
    if doc.is_inherited:
        docstr.append(f"inherited from {'.'.join(doc.taken_from).rstrip('.')}")
    if doc.docstring:
        docstr.append(_cut(doc.docstring))
    if docstr:
        return f"  # {', '.join(docstr)}"
    else:
        return ""


def _decorators(doc: Class | Function) -> str:
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
        children += "\n"
        children = f"\n{textwrap.indent(children, '    ')}"
    return children


def _safe_getattr(obj, attr, default):
    """Like `getattr()`, but never raises."""
    try:
        return getattr(obj, attr, default)
    except Exception as e:
        warnings.warn(
            f"getattr({obj!r}, {attr!r}, {default!r}) raised an exception: {e!r}"
        )
        return default


def _safe_getdoc(obj: Any) -> str:
    """Like `inspect.getdoc()`, but never raises. Always returns a stripped string."""
    try:
        doc = inspect.getdoc(obj) or ""
    except Exception as e:
        warnings.warn(f"inspect.getdoc({obj!r}) raised an exception: {e!r}")
        return ""
    else:
        return doc.strip()


_Enum_default_docstrings = tuple(
    {
        _safe_getdoc(enum.Enum),
        _safe_getdoc(enum.IntEnum),
        _safe_getdoc(_safe_getattr(enum, "StrEnum", enum.Enum)),
    }
)


def _remove_memory_addresses(x: str) -> str:
    """Remove memory addresses from repr() output"""
    return re.sub(r" at 0x[0-9a-fA-F]+(?=>)", "", x)


def _remove_collections_abc(x: str) -> str:
    """Remove 'collections.abc' from type signatures."""
    return re.sub(r"(?!\.)\bcollections\.abc\.", "", x)

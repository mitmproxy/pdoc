import ast
import importlib
import inspect
import pkgutil
import textwrap
import types
import warnings
from abc import abstractmethod, ABCMeta
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from functools import cached_property, cache, wraps
from itertools import tee, zip_longest

from typing import (  # type: ignore
    Any,
    Union,
    TypeVar,
    get_origin,
    ClassVar,
    ForwardRef,
    _eval_type,
    Optional,
    Generic,
    TYPE_CHECKING,
)

if TYPE_CHECKING:

    class empty:
        pass


else:
    empty = inspect.Signature.empty


# taken from
# https://github.com/python/cpython/blob/faf49573963921033c608b4d2f398309d9f0d2b5/Lib/typing.py#L161-L179
# extended to support empty
def type_repr(obj):
    """Return the repr() of an object, special-casing types (internal helper).
    If obj is a type, we return a shorter version than the default
    type.__repr__, based on the module and qualified name, which is
    typically enough to uniquely identify a type.  For everything
    else, we fall back on repr(obj).
    """
    if obj is empty:
        return ""
    if isinstance(obj, types.GenericAlias):
        return repr(obj)
    if isinstance(obj, type):
        if obj.__module__ == "builtins":
            return obj.__qualname__
        return f"{obj.__module__}.{obj.__qualname__}"
    if obj is ...:
        return "..."
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
        t = tree.body[0]
        assert isinstance(t, (ast.Module, ast.ClassDef))
        return t
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
        if (
            isinstance(a, ast.AnnAssign)
            and isinstance(a.target, ast.Attribute)
            and isinstance(a.target.value, ast.Name)
            and a.target.value.id == "self"
        ):
            yield ast.AnnAssign(
                ast.Name(a.target.attr), a.annotation, a.value, simple=1
            )
        elif (
            isinstance(a, ast.Assign)
            and len(a.targets) == 1
            and isinstance(a.targets[0], ast.Attribute)
            and isinstance(a.targets[0].value, ast.Name)
            and a.targets[0].value.id == "self"
        ):
            yield ast.Assign(
                [ast.Name(a.targets[0].attr)],
                value=a.value,
                type_comment=a.type_comment,
            )
        elif (
            isinstance(a, ast.Expr)
            and isinstance(a.value, ast.Constant)
            and isinstance(a.value.value, str)
        ):
            yield a
        else:
            yield ast.Pass()


def __nodes(tree: Union[ast.Module, ast.ClassDef]) -> Iterator[ast.AST]:
    for a in tree.body:
        yield a
        if isinstance(a, ast.FunctionDef) and a.name == "__init__":
            yield from _init_nodes(a)


@cache
def _nodes(tree: Union[ast.Module, ast.ClassDef]) -> list[ast.AST]:
    return list(__nodes(tree))


@dataclass
class AstInfo:
    docstrings: dict[str, str]
    annotations: dict[str, str]


@cache
def _walk_tree(tree: Union[ast.Module, ast.ClassDef]) -> AstInfo:
    """Returns (docstrings, annotations) extracted from AST"""
    docstrings = {}
    annotations = {}
    for a, b in _pairwise_longest(_nodes(tree)):
        if isinstance(a, ast.AnnAssign) and isinstance(a.target, ast.Name) and a.simple:
            name = a.target.id
            annotations[name] = ast.unparse(a.annotation)
        elif (
            isinstance(a, ast.Assign)
            and len(a.targets) == 1
            and isinstance(a.targets[0], ast.Name)
        ):
            name = a.targets[0].id
        else:
            continue
        if (
            isinstance(b, ast.Expr)
            and isinstance(b.value, ast.Constant)
            and isinstance(b.value.value, str)
        ):
            docstrings[name] = inspect.cleandoc(b.value.value).strip()
    return AstInfo(docstrings, annotations)


def _cut(x: str) -> str:
    if len(x) < 20:
        return x
    else:
        return x[:20] + "…"


def _docstr(doc: "Doc") -> str:
    docstr = []
    if doc.is_inherited:
        docstr.append(f"inherited from {'.'.join(doc.declared_at)}")
    if doc.docstring:
        docstr.append(_cut(doc.docstring))
    if docstr:
        return f"  # {', '.join(docstr)}"
    else:
        return ""


def _sort(
    tree: Union[ast.Module, ast.ClassDef], sorted: dict[str, T], unsorted: dict[str, T]
) -> tuple[dict[str, T], dict[str, T]]:
    """Returns (sorted, not found)"""

    if "__init__" in unsorted:
        sorted["__init__"] = unsorted.pop("__init__")

    for a in _nodes(tree):
        if (
            isinstance(a, ast.Assign)
            and len(a.targets) == 1
            and isinstance(a.targets[0], ast.Name)
        ):
            name = a.targets[0].id
        elif (
            isinstance(a, ast.AnnAssign) and isinstance(a.target, ast.Name) and a.simple
        ):
            name = a.target.id
        elif isinstance(a, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            name = a.name
        else:
            continue

        if name in unsorted:
            sorted[name] = unsorted.pop(name)
    return sorted, unsorted


def _is_exported(ident_name: str, default_value: Any = None):
    """
    Returns `True` if `ident_name` matches the export criteria for an
    identifier name.

    This should not be used by clients. Instead, use
    `pdoc.Module.is_public`.
    """
    if ident_name == "__init__":
        return True
    if isinstance(default_value, TypeVar):
        return False
    if ident_name.startswith("_"):
        return False
    return True


def _safe_eval_type(
    t: Any,
    globalns,
    refname: str,
    last_err: Optional[str] = None,
) -> Any:
    try:
        return _eval_type(t, globalns, None)
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
    except Exception as e:
        err = last_err = str(e)
    if err == last_err:
        warnings.warn(f"Error parsing type annotation for {refname}: {err}")
        return t
    try:
        val = importlib.import_module(mod)
    except Exception:
        warnings.warn(
            f"Error parsing type annotation for {refname}. Import of {mod} failed: {err}"
        )
        return t
    return _safe_eval_type(t, {mod: val, **globalns}, refname, err)


def resolve_type_annotations(
    annotations: dict[str, Any],
    module: Optional[types.ModuleType],
    refname: str,
) -> dict[str, Any]:
    ns = getattr(module, "__dict__", {})

    resolved = {}
    for name, value in annotations.items():
        if value is None:
            value = type(None)
        if isinstance(value, str):
            value = ForwardRef(value, is_argument=False)

        resolved[name] = _safe_eval_type(value, ns, refname)
    return resolved


class Doc(Generic[T]):
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

    obj: T
    """
    The object
    """

    def __init__(self, module_name: str, qualname: str, obj: T):
        """
        Initializes a documentation object, where `name` is the public
        identifier name, `module` is a `pdoc.Module` object, and
        `docstring` is a string containing the docstring for `name`.
        """
        self.module_name = module_name
        self.qualname = qualname
        self.obj = obj

    @cached_property
    def docstring(self) -> str:
        """
        The docstring for this object. It has already been cleaned by `inspect.cleandoc`.
        If unsuccessful, an empty string is returned.
        """
        doc = inspect.getdoc(self.obj)
        if doc is None or doc == object.__init__.__doc__:
            # inspect.getdoc(Foo.__init__) returns the docstring, for object.__init__ if left undefined...
            doc = ""
        return doc.strip()

    @cached_property
    def source(self) -> str:
        """
        Returns the source code of the Python object as a str.
        If unsuccessful, an empty string is returned.
        """
        return _source(self.obj)

    @cached_property
    def declared_at(self) -> tuple[str, str]:
        mod = getattr(self.obj, "__module__", None)
        qual = getattr(self.obj, "__qualname__", None)
        if mod is None or qual is None or "<locals>" in qual:
            return self.module_name, self.qualname
        else:
            return mod, qual

    @cached_property
    def is_inherited(self) -> bool:
        return (self.module_name, self.qualname) != self.declared_at

    @classmethod
    @property
    def type(cls) -> str:
        return cls.__name__.lower()

    @cached_property
    def refname(self) -> str:
        return f"{self.module_name}.{self.qualname}".removesuffix(".")

    @cached_property
    def name(self) -> str:
        return self.refname.split(".")[-1]

    @cached_property
    def doc(self):
        warnings.warn("deprecated", DeprecationWarning)
        return self.members

    def __lt__(self, other):
        assert isinstance(other, Doc)
        return self.refname.replace("__init__", "") < other.refname.replace(
            "__init__", ""
        )


class Namespace(Doc[T], metaclass=ABCMeta):
    """Can have children. Either a module or a class."""

    @cached_property
    @abstractmethod
    def _member_objects(self) -> dict[str, Any]:
        ...

    @cached_property
    @abstractmethod
    def _var_docstrings(self) -> dict[str, str]:
        ...

    @cached_property
    @abstractmethod
    def _declared_at(self) -> dict[str, tuple[str, str]]:
        ...

    @cached_property
    @abstractmethod
    def _var_annotations(self) -> dict[str, Any]:
        ...

    @cached_property
    def members(self) -> list[Doc]:
        """A mapping from all members to their documentation objects."""
        members: list[Doc] = []
        for name, obj in self._member_objects.items():
            qualname = f"{self.qualname}.{name}".removeprefix(".")
            doc: Doc[Any]

            if isinstance(obj, (property, cached_property)):
                if isinstance(obj, property):
                    func = obj.fget
                else:
                    func = obj.func
                annotation = resolve_type_annotations(
                    getattr(func, "__annotations__", {}),
                    inspect.getmodule(func),
                    f"{self.refname}.{name}",
                ).get("return", empty)
                doc = Variable(
                    self.module_name,
                    qualname,
                    docstring=obj.__doc__,
                    annotation=annotation,
                    default_value=empty,
                    declared_at=self._declared_at.get(
                        name, (self.module_name, qualname)
                    ),
                )
            elif inspect.isroutine(obj):
                doc = Function(self.module_name, qualname, obj)
            elif inspect.isclass(obj) and not obj is empty:
                doc = Class(self.module_name, qualname, obj)
            else:
                doc = Variable(
                    self.module_name,
                    qualname,
                    docstring=self._var_docstrings.get(name, ""),
                    annotation=self._var_annotations.get(name, empty),
                    default_value=obj,
                    declared_at=self._declared_at.get(
                        name, (self.module_name, qualname)
                    ),
                )
            members.append(doc)
        return members

    @cached_property
    def _members_by_declared_location(self) -> dict[tuple[str, str], list[Doc]]:
        locations = {}
        for member in self.members:
            mod, qualname = member.declared_at
            qualname = ".".join(qualname.split(".")[:-1])
            locations.setdefault((mod, qualname), [])
            locations[(mod, qualname)].append(member)
        return locations

    @cached_property
    def own_members(self) -> list[Doc]:
        return self._members_by_declared_location.get(
            (self.module_name, self.qualname), []
        )

    @cached_property
    def inherited_members(self) -> dict[tuple[str, str], list[Doc]]:
        return {
            k: v
            for k, v in self._members_by_declared_location.items()
            if k != (self.module_name, self.qualname)
        }

    @cached_property
    def flattened_members(self) -> list[Doc]:
        """
        Returns all documented members and their child classes, recursively.
        """
        flattened = []
        for x in self.members:
            flattened.append(x)
            if isinstance(x, Class):
                flattened.extend(
                    [cls for cls in x.flattened_members if isinstance(cls, Class)]
                )
        return flattened


def include_refname_in_traceback(f):
    @wraps(f)
    def wrapper(self):
        try:
            return f(self)
        except Exception as e:
            raise RuntimeError(f"Error in {self.refname}'s repr!") from e

    return wrapper


class Module(Namespace[types.ModuleType]):
    """
    Representation of a module's documentation.
    """

    def __init__(self, module: types.ModuleType):
        """
        Creates a `Module` documentation object given the actual
        module Python object.
        """
        super().__init__(module.__name__, "", module)

    @cache
    @include_refname_in_traceback
    def __repr__(self):
        children = "\n".join(repr(x) for x in self.members)
        if children:
            children = f"\n{textwrap.indent(children, '    ')}"
        return f"<module {self.module_name}{_docstr(self)}{children}>"

    @cached_property
    def is_package(self) -> bool:
        return hasattr(self.obj, "__path__")  # type: ignore

    @cached_property
    def _var_docstrings(self) -> dict[str, str]:
        return _walk_tree(_parse_module(self.source)).docstrings

    @cached_property
    def _declared_at(self) -> dict[str, tuple[str, str]]:
        return {}

    @cached_property
    def _var_annotations(self) -> dict[str, Any]:
        annotations = _walk_tree(_parse_module(self.source)).annotations
        for k, v in getattr(self.obj, "__annotations__", {}).items():
            annotations[k] = v

        return resolve_type_annotations(annotations, self.obj, self.refname)

    @cached_property
    def submodules(self) -> list["Module"]:
        if not self.is_package:
            return []
        submodules = []
        for mod in pkgutil.iter_modules(self.obj.__path__, f"{self.refname}."):  # type: ignore
            try:
                module = importlib.import_module(mod.name)
            except BaseException as e:
                warnings.warn(f"Couldn't import {mod.name}: {e!r}", stacklevel=2)
                continue
            submodules.append(Module(module))
        return submodules

    @cached_property
    def _documented_members(self) -> set[str]:
        return self._var_docstrings.keys() | self._var_annotations.keys()

    @cached_property
    def _member_objects(self) -> dict[str, Any]:
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
        if all := getattr(self.obj, "__all__", False):
            return {name: self.obj.__dict__.get(name, empty) for name in all}

        members = {}
        for name, obj in self.obj.__dict__.items():
            if not _is_exported(name, obj):
                continue
            obj_module = inspect.getmodule(obj)
            declared_in_this_module = self.obj.__name__ == getattr(
                obj_module, "__name__", None
            )
            if declared_in_this_module or name in self._documented_members:
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
        return [x for x in self.members if isinstance(x, Variable)]

    @cached_property
    def classes(self) -> list["Class"]:
        """
        Returns all documented module level classes.
        """
        return [x for x in self.members if isinstance(x, Class)]

    @cached_property
    def functions(self) -> list["Function"]:
        """
        Returns all documented module level functions.
        """
        return [x for x in self.members if isinstance(x, Function)]


class Class(Namespace[type]):
    """
    Representation of a class's documentation.
    """

    @cache
    @include_refname_in_traceback
    def __repr__(self):
        children = "\n".join(repr(x) for x in self.members)
        return (
            f"<class {self.module_name}.{self.qualname}{_docstr(self)}\n"
            f"{textwrap.indent(children, '    ')}>"
        )

    @cached_property
    def _var_docstrings(self) -> dict[str, str]:
        docstrings: dict[str, str] = {}
        for cls in self.obj.__mro__:
            for name, docstr in _walk_tree(
                _parse_class(_source(cls))
            ).docstrings.items():
                docstrings.setdefault(name, docstr)
        return docstrings

    @cached_property
    def _declared_at(self) -> dict[str, tuple[str, str]]:
        declared_at = {}
        for cls in self.obj.__mro__:
            treeinfo = _walk_tree(_parse_class(_source(cls)))
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
            cls_annotations = _walk_tree(_parse_class(_source(cls))).annotations
            dynamic_annotations = getattr(cls, "__annotations__", None)
            if isinstance(dynamic_annotations, dict):
                for k, v in dynamic_annotations.items():
                    cls_annotations[k] = v
            cls_refname = (
                getattr(cls, "__module__", "") + "." + cls.__qualname__
            ).removeprefix(".")
            cls_annotations = resolve_type_annotations(
                cls_annotations, inspect.getmodule(cls), cls_refname
            )

            for k, v in cls_annotations.items():
                annotations.setdefault(k, v)
        return annotations

    @cached_property
    def _member_objects(self) -> dict[str, Any]:
        """
        Returns a dictionary mapping a public identifier name to a
        Python object. This counts the `__init__` method as being
        public.
        """
        unsorted: dict[str, Any] = {}
        for cls in self.obj.__mro__:
            for name, obj in cls.__dict__.items():
                if _is_exported(name, obj):
                    unsorted.setdefault(name, obj)
        for name in self._var_annotations:
            if _is_exported(name):
                unsorted.setdefault(name, empty)
        for name in self._var_docstrings:
            if _is_exported(name):
                unsorted.setdefault(name, empty)

        sorted: dict[str, Any] = {}
        for cls in self.obj.__mro__:
            tree = _parse_class(_source(cls))
            sorted, unsorted = _sort(tree, sorted, unsorted)
        if "__init__" in unsorted:
            # move to front
            sorted = {"__init__": unsorted.pop("__init__"), **sorted}
        sorted.update(unsorted)
        return sorted

    @cached_property
    def class_variables(self) -> list["Variable"]:
        """
        Returns all documented class variables in the class.
        """
        return [
            x
            for x in self.members
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
            x
            for x in self.members
            if isinstance(x, Variable) and get_origin(x) is not ClassVar
        ]

    @cached_property
    def classmethods(self) -> list["Function"]:
        """
        Returns all documented class methods.
        """
        return [x for x in self.members if isinstance(x, Function) and x.is_classmethod]

    @cached_property
    def staticmethods(self) -> list["Function"]:
        """
        Returns all documented static methods.
        """
        return [
            x for x in self.members if isinstance(x, Function) and x.is_staticmethod
        ]

    @cached_property
    def methods(self) -> list["Function"]:
        """
        Returns all documented functions in the class.
        """
        return [
            x
            for x in self.members
            if isinstance(x, Function)
            and not x.is_staticmethod
            and not x.is_classmethod
        ]

    @cached_property
    def bases(self) -> list[tuple[str, str]]:
        return [
            (x.__module__, x.__qualname__)
            for x in self.obj.__bases__
            if x is not object
        ]


WrappedFunction = Union[types.FunctionType, staticmethod, classmethod]


class Function(Doc[types.FunctionType]):
    """
    Representation of documentation for a Python function or method.
    """

    wrapped: Union[types.FunctionType, staticmethod, classmethod]

    def __init__(
        self,
        module_name: str,
        qualname: str,
        wrapped: WrappedFunction,
    ):
        func: types.FunctionType
        if isinstance(wrapped, (classmethod, staticmethod)):
            func = wrapped.__func__  # type: ignore
            # TODO: In Python 3.9 this could also be a property.
        else:
            func = wrapped
        super(Function, self).__init__(module_name, qualname, func)
        self.wrapped = wrapped

    @cache
    @include_refname_in_traceback
    def __repr__(self):
        if self.is_classmethod:
            t = "classmethod"
        elif self.is_staticmethod:
            t = "staticmethod"
        elif self.qualname != getattr(self.obj, "__name__", None):
            t = "method"
        else:
            t = "function"
        return f"<{t} {self.funcdef} {self.name}{self.signature}: ...{_docstr(self)}>"

    @cached_property
    def is_classmethod(self) -> bool:
        """
        Whether this function is a class method.
        """
        return isinstance(self.wrapped, classmethod)

    @cached_property
    def is_staticmethod(self) -> bool:
        """
        Whether this function is a static method.
        """
        return isinstance(self.wrapped, staticmethod)

    @cached_property
    def funcdef(self) -> str:
        """
        Generates the string of keywords used to define the function, for
        example `def` or `async def`.
        """
        if inspect.iscoroutinefunction(self.obj) or inspect.isasyncgenfunction(
            self.obj
        ):
            return "async def"
        else:
            return "def"

    @cached_property
    def signature(self) -> inspect.Signature:
        if self.obj is object.__init__:
            # there is a weird edge case were inspect.signature returns a confusing (self, /, *args, **kwargs)
            # signature for the default __init__ method.
            return inspect.Signature()
        try:
            sig = inspect.signature(self.obj)
        except Exception:
            return inspect.Signature(
                [inspect.Parameter("unknown", inspect.Parameter.POSITIONAL_OR_KEYWORD)]
            )
        mod = inspect.getmodule(self.obj)
        sig._return_annotation = resolve_type_annotations(
            {"t": sig.return_annotation}, mod, self.refname
        )["t"]
        for p in sig.parameters.values():
            p._annotation = resolve_type_annotations(
                {"t": p.annotation}, mod, self.refname
            )["t"]
        return sig


class Variable(Doc[None]):
    """
    Representation of a variable's documentation. This includes
    module, class and instance variables.
    """

    _docstring: str

    default_value: Union[
        Any, empty
    ]  # technically Any includes empty, but this conveys intent.
    """
    The variable's default value.
    """

    annotation: Union[type, empty]
    """
    The variable's type annotation.
    """

    _declared_at: tuple[str, str]
    """(module, qualname) the variable was declared at"""

    def __init__(
        self,
        module_name: str,
        qualname: str,
        docstring: str,
        declared_at: tuple[str, str],
        annotation: Union[type, empty] = empty,
        default_value: Union[Any, empty] = empty,
    ):
        super().__init__(module_name, qualname, None)
        self._docstring = docstring
        self._declared_at = declared_at
        self.annotation = annotation
        self.default_value = default_value

    @cache
    @include_refname_in_traceback
    def __repr__(self):
        if self.annotation is not empty:
            annotation = f": {type_repr(self.annotation)}"
        else:
            annotation = ""
        if self.default_value is not empty:
            val = f" = {self.default_value}"
        else:
            val = ""
        return f'<var {self.qualname.rsplit(".")[-1]}{annotation}{val}{_docstr(self)}>'

    @cached_property
    def docstring(self) -> str:
        return self._docstring

    @cached_property
    def declared_at(self) -> tuple[str, str]:
        return self._declared_at

    @cached_property
    def is_classvar(self):
        if get_origin(self.annotation) is ClassVar:
            return True
        else:
            return False

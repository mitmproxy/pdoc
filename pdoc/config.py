"""This module implements configuration files for pdoc.

Every field is optional with a default of None,
so that the actual defaults can be defined in `__main__.py`.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import fields
import logging
from pathlib import Path
import sys
from typing import Any
from typing import BinaryIO
from typing import Literal
from typing import TypeVar

if sys.version_info < (3, 15):  # pragma: no cover
    import tomli as tomllib
else:  # pragma: no cover
    import tomllib

logger = logging.getLogger(__name__)


class ConfigError(Exception):
    pass


T = TypeVar("T")


def or_else(*args: T | None) -> T | None:
    """Take the first non-None argument going left-to-right."""
    for a in args:
        if a is not None:
            return a
    return None


@dataclass
class Config:
    """Configuration for pdoc, representing most command-line arguments."""

    # Main Arguments
    modules: list[str] | None = None
    """Python module names. These may be importable Python module names ("pdoc.doc")
    or file paths ("./pdoc/doc.py"). Exclude submodules by specifying a negative
    !regex pattern, e.g. "foo !foo.bar"."""

    output_directory: Path | None = None
    """Write rendered documentation to the specified directory, don't start a webserver."""

    # Customize Rendering
    docformat: Literal["markdown", "google", "numpy", "restructuredtext"] | None = None
    """The default docstring format. For non-Markdown formats, pdoc will first convert
    matching syntax elements to Markdown and then process everything as Markdown."""

    include_undocumented: bool | None = None
    """Show classes/functions/variables that do not have a docstring."""

    edit_url: list[str] | None = None
    """A mapping between module names and URL prefixes, used to display an 'Edit' button.
    Example: pdoc=https://github.com/mitmproxy/pdoc/blob/main/pdoc/"""

    favicon: str | None = None
    """Specify a custom favicon URL."""

    footer_text: str | None = None
    """Custom text for the page footer, for example the project name and current version number."""

    logo: str | None = None
    """Add a project logo image."""

    logo_link: str | None = None
    """Optional URL the logo should point to."""

    math: bool | None = None
    """Include MathJax from a CDN to enable math formula rendering."""

    mermaid: bool | None = None
    """Include Mermaid.js from a CDN to enable Mermaid diagram rendering."""

    search: bool | None = None
    """Enable search functionality if multiple modules are documented."""

    show_source: bool | None = None
    """Display "View Source" buttons."""

    template_directory: Path | None = None
    """A directory containing Jinja2 templates to customize output.
    Alternatively, put your templates in $XDG_CONFIG_HOME/pdoc and pdoc will automatically find them."""

    # Miscellaneous Options
    host: str | None = None
    """The host on which to run the HTTP server."""

    port: int | None = None
    """The port on which to run the HTTP server."""

    no_browser: bool | None = None
    """Don't open a browser after the web server has started."""

    @classmethod
    def from_config_arg(cls, path: Path | None) -> Config:
        if path is None:
            return cls.from_toml_discover()
        elif path.is_dir():
            return cls.from_toml_dir(path)
        else:
            return cls.from_toml_path(path)

    @classmethod
    def _from_toml_dir(cls, path: Path) -> Config | None:
        """Load from a configuration file in the given path.

        Return None if none are found.
        """
        for fname in ("pdoc.toml", "pyproject.toml"):
            p = path / fname
            logger.debug("Looking for config file at %s", p)
            if p.is_file():
                return cls.from_toml_path(p)
        return None

    @classmethod
    def from_toml_dir(cls, path: Path) -> Config:
        """Load from a configuration file in the given path."""
        maybe = cls._from_toml_dir(path)
        if maybe is None:
            return cls()
        return maybe

    @classmethod
    def from_toml_discover(cls, path: Path | None = None) -> Config:
        """Load from a configuration file in the given directory and its ancestors."""
        if path is None:
            path = Path.cwd()
        if not path.is_dir():
            raise NotADirectoryError("Not a directory: %s")
        if maybe := cls._from_toml_dir(path):
            return maybe
        for p in path.resolve().parents:
            try:
                if maybe := cls._from_toml_dir(p):
                    return maybe
            except PermissionError:
                break
        return cls()

    @classmethod
    def from_toml_path(cls, path: Path) -> Config:
        """Load configuration from the given file path."""
        pyproject = path.name == "pyproject.toml"
        logger.debug("Reading config from %s", path)
        with path.open("rb") as f:
            return cls.from_toml_file(f, pyproject)

    @classmethod
    def from_toml_file(cls, f: BinaryIO, pyproject: bool = False) -> Config:
        """Load a configuration from the given binary IO (e.g. a file object in `"rb"` mode)."""
        table = tomllib.load(f)
        return cls.from_toml_table(table, pyproject)

    @classmethod
    def from_toml_str(cls, toml: str, pyproject: bool = False) -> Config:
        """Load a configuration from a given string."""
        table = tomllib.loads(toml)
        return cls.from_toml_table(table, pyproject)

    @classmethod
    def from_toml_table(cls, table: dict[str, Any], pyproject: bool = False) -> Config:
        """Load a configuration from the given dict."""
        if pyproject:
            table = table.get("tool", dict())
            if not isinstance(table, dict):
                raise ConfigError("pyproject.toml `tool` field is not a table")
            table = table.get("pdoc", dict())
            if not isinstance(table, dict):
                raise ConfigError("pyproject.toml `tool.pdoc` field is not a table")

        f = {
            field.name: table.pop(field.name.replace("_", "-"), None)
            for field in fields(cls)
        }
        if table:
            logger.warning("Config has unsupported keys %s", ", ".join(table))

        for name, fn in [
            ("output_directory", Path),
            ("template_directory", Path),
            ("edit_url", dict_to_list),
        ]:
            val = f.get(name)
            if val is not None:
                f[name] = fn(val)  # type:ignore

        return cls(**f)


def dict_to_list(d: dict[str, str]) -> list[str]:
    return [f"{k}={v}" for k, v in d.items()]

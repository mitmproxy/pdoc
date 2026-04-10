from contextlib import contextmanager
import os
from pathlib import Path
import sys

import pytest

from pdoc.config import Config
from pdoc.config import ConfigError

if sys.version_info < (3, 15):
    import tomli as tomllib
else:
    import tomllib

config_dir = Path(__file__).resolve().parent / "config"


expected_str = """
modules = ["a.b", "a/b/c.py", "!hidden.py"]
output-directory = "path/to/output/"
docformat = "markdown"
include-undocumented = false
edit-url = { key = "https://value.com", key2 = "https://value.com/somethingelse" }
favicon = "https://pictures.com/sheep"
footer-text = "And that's the way the cookie crumbles."
logo = "./logo.png"
logo-link = "https://pictures.com/logo.png"
math = true
mermaid = true
search = false
show-source = false
template-directory = "path/to/templates"
host = "remotehost"
port = 1234
no-browser = true
"""


@pytest.fixture(scope="session")
def expected_config() -> Config:
    return Config.from_toml_str(expected_str)


def test_read_pyproject(expected_config: Config):
    path = config_dir / "pyproject/pyproject.toml"
    c = Config.from_toml_path(path)
    assert c == expected_config


def test_read_pdoc(expected_config: Config):
    path = config_dir / "pdoc/pdoc.toml"
    c = Config.from_toml_path(path)
    assert c == expected_config


def test_prefers_pdoc(expected_config: Config):
    path = config_dir / "both"
    c = Config.from_toml_dir(path)
    assert c == expected_config


def test_finds_parent(expected_config: Config):
    path = config_dir / "parent/child"
    c = Config.from_toml_discover(path)
    assert c == expected_config


def test_empty():
    path = config_dir / "parent/child"
    c = Config.from_toml_dir(path)
    assert c == Config()


def test_discover_not_dir():
    with pytest.raises(NotADirectoryError):
        Config.from_toml_discover(config_dir / "pdoc/pdoc.toml")


def test_parses_str():
    Config.from_toml_str(expected_str)


def test_parses_table():
    Config.from_toml_table(tomllib.loads(expected_str))


def test_not_table():
    with pytest.raises(ConfigError):
        Config.from_toml_str('tool = "spade"', True)
    with pytest.raises(ConfigError):
        Config.from_toml_str('tool.pdoc = "spade"', True)


def test_extra_keys():
    Config.from_toml_str('potato = "spade"')


@contextmanager
def chdir_tmp(path: Path):
    old = Path.cwd()
    os.chdir(path)
    yield
    os.chdir(old)


def test_with_cwd(expected_config: Config):
    with chdir_tmp(config_dir / "parent/child"):
        c = Config.from_toml_discover()
    assert c == expected_config


def test_from_arg(expected_config):
    c = Config.from_config_arg(config_dir / "pdoc")
    assert c == expected_config


def test_permissions(tmpdir, expected_config):
    root = Path(tmpdir)
    p = root / "pdoc.toml"
    p.write_text(expected_str)
    sub = root / "sub"
    sub.mkdir()
    # check that the file was read correctly
    assert Config.from_toml_discover(sub) == expected_config

    # nobody can read, everyone can write and execute
    p.chmod(mode=222)
    # check that the file was not read
    assert Config.from_toml_discover(sub) == Config()

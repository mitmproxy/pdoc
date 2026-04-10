from contextlib import contextmanager
import os
from pathlib import Path

import pytest
import tomllib

from pdoc.config import Config

config_dir = Path(__file__).resolve().parent / "config"


expected_dict = tomllib.loads(
    """
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
)


@pytest.fixture(scope="session")
def expected_config() -> Config:
    return Config.from_toml_table(expected_dict)


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

import re
from pathlib import Path

from setuptools import setup, find_packages

here = Path(__file__).parent

long_description = (here / "README.md").read_text("utf8")

VERSION = re.search(
    r'__version__ = "(.+?)"', (here / "pdoc" / "__init__.py").read_text("utf8")
).group(1)


setup(
    name="pdoc",
    author="Maximilian Hils",
    author_email="pdoc@maximilianhils.com",
    version=VERSION,
    license="UNLICENSE",
    description="A simple program and library to auto generate API documentation for Python modules.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://pdoc.dev/",
    project_urls={
        "Source": "https://github.com/mitmproxy/pdoc/",
        "Documentation": "https://pdoc.dev/docs/pdoc.html",
        "Issues": "https://github.com/mitmproxy/pdoc/issues",
    },
    classifiers=[
        "Topic :: Documentation",
        "Topic :: Software Development :: Documentation",
        "Topic :: Utilities",
        "License :: Public Domain",
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    packages=find_packages(
        include=[
            "pdoc",
            "pdoc.*",
        ]
    ),
    include_package_data=True,
    entry_points={"console_scripts": ["pdoc = pdoc.__main__:cli"]},
    python_requires=">=3.8",
    install_requires=[
        "Jinja2",
        "markdown2",
        "pygments",
        "astunparse; python_version<'3.9'",
    ],
    extras_require={
        "dev": [
            "flake8",
            "mypy",
            "pytest",
            "pytest-cov",
            "pytest-timeout",
            "tox",
            "twine",
            "wheel",
        ]
    },
)

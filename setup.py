import re
from pathlib import Path

from setuptools import find_packages, setup

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
    description="API Documentation for Python Projects",
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
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Typing :: Typed",
    ],
    packages=find_packages(
        include=[
            "pdoc",
            "pdoc.*",
        ]
    ),
    include_package_data=True,
    entry_points={"console_scripts": ["pdoc = pdoc.__main__:cli"]},
    python_requires=">=3.7",
    install_requires=[
        "Jinja2 >= 2.11.0",
        "pygments >= 2.12.0",
        "MarkupSafe",
        "astunparse; python_version<'3.9'",
    ],
    extras_require={
        "dev": [
            "flake8",
            "hypothesis",
            "mypy",
            "pytest",
            "pytest-cov",
            "pytest-timeout",
            "tox",
        ]
    },
)

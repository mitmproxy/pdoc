import os
import re
from distutils.core import setup

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

with open(os.path.join(here, "pdoc", "__init__.py")) as f:
    VERSION = re.search(r'__version__ = "(.+?)"', f.read()).group(1)

setup(
    name="pdoc",
    author="Andrew Gallant",
    author_email="pdoc@burntsushi.net",
    version=VERSION,
    license="UNLICENSE",
    description="A simple program and library to auto generate API "
    "documentation for Python modules.",
    long_description=long_description,
    url="https://github.com/BurntSushi/pdoc",
    classifiers=[
        "Topic :: Documentation",
        "Topic :: Software Development :: Documentation",
        "Topic :: Utilities",
        "License :: Public Domain",
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    platforms="ANY",
    packages=["pdoc"],
    package_data={"pdoc": ["templates/*"]},
    entry_points={"console_scripts": ["pdoc = pdoc.cli:main"]},
    provides=["pdoc"],
    extras_require={
        "dev": [
            "flake8>=3.5, <3.6",
            "mypy>=0.620, <0.621",
            "pytest>=3.3,<4",
            "pytest-cov>=2.5.1,<3",
            "pytest-faulthandler>=1.3.1,<2",
            "pytest-timeout>=1.2.1,<2",
            "pytest-xdist>=1.22,<2",
        ]
    },
    install_requires=[
        "mako>=1.0.7,<1.1",
        "markdown",
        "pygments>=2.2.0,<2.3",
    ],
)

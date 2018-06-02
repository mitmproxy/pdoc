import codecs
from distutils.core import setup
import os.path as path

cwd = path.dirname(__file__)
longdesc = codecs.open(path.join(cwd, "longdesc.rst"), "r", "utf-8").read()
version = "0.0.0"
with codecs.open(path.join(cwd, "pdoc", "__init__.py"), "r", "utf-8") as f:
    for line in f:
        if line.startswith("__version__"):
            exec(line.strip())
            version = __version__
            break

setup(
    name="pdoc",
    author="Andrew Gallant",
    author_email="pdoc@burntsushi.net",
    version=version,
    license="UNLICENSE",
    description="A simple program and library to auto generate API "
    "documentation for Python modules.",
    long_description=longdesc,
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
        "Programming Language :: Python :: 3",
    ],
    platforms="ANY",
    packages=["pdoc"],
    package_data={"pdoc": ["templates/*"]},
    data_files=[
        (
            "share/pdoc",
            ["README.md", "longdesc.rst", "UNLICENSE", "INSTALL", "CHANGELOG"],
        ),
        ("share/doc/pdoc", ["doc/pdoc/index.html"]),
    ],
    entry_points={"console_scripts": ["pdoc = pdoc.cli:cli"]},
    provides=["pdoc"],
    extras_require={
        "dev": {
            "flake8>=3.5, <3.6",
            "pytest-cov>=2.5.1,<3",
            "pytest>=3.3,<4",
        }
    },
    install_requires=["mako", "markdown", "pygments"],
)

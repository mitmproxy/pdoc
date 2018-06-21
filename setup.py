from distutils.core import setup
import os.path
import re


here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()
with open(os.path.join(here, "pdoc", "version.py")) as f:
    VERSION = re.search(r'VERSION = "(.+?)"', f.read()).group(1)

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
        "Programming Language :: Python :: 3",
    ],
    platforms="ANY",
    packages=["pdoc"],
    package_data={"pdoc": ["templates/*"]},
    entry_points={"console_scripts": ["pdoc = pdoc.cli:main"]},
    provides=["pdoc"],
    extras_require={
        "dev": {
            "black",
            "flake8>=3.5, <3.6",
            "mypy",
            "pytest>=3.3,<4",
            "pytest-cov>=2.5.1,<3",
            "pytest-faulthandler>=1.3.1,<2",
            "pytest-timeout>=1.2.1,<2",
            "pytest-xdist>=1.22,<2",
        }
    },
    install_requires=["mako", "markdown", "pygments"],
)

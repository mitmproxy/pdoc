import re
from pathlib import Path

from setuptools import setup, find_packages

here = Path(__file__).parent

long_description = (here / "README.md").read_text()

VERSION = re.search(
    r'__version__ = "(.+?)"', (here / "pdoc" / "__init__.py").read_text()
).group(1)

setup(
    name="pdoc",
    author="Andrew Gallant",
    author_email="pdoc@burntsushi.net",
    version=VERSION,
    license="UNLICENSE",
    description="A simple program and library to auto generate API documentation for Python modules.",
    long_description=long_description,
    url="https://github.com/mitmproxy/pdoc",
    classifiers=[
        "Topic :: Documentation",
        "Topic :: Software Development :: Documentation",
        "Topic :: Utilities",
        "License :: Public Domain",
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
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
    python_requires=">=3.9",
    install_requires=[
        "mako>=1.1.3,<1.2",
        "markdown2>=2.3.10,<2.4",
        "pygments>=2.7.3,<2.8",
    ],
    extras_require={
        "dev": [
            "flake8>=3.84, <3.9",
            "mypy>=0.790, <0.791",
            "pytest>=6.2.1,<6.3",
        ]
    },
)

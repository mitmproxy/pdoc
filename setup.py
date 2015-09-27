from sys import version_info as v
if any([v < (2, 7), (3,) < v < (3, 3)]):
    raise Exception("Unsupported Python version %d.%d. Requires Python >= 2.7 "
                    "or >= 3.3." % v[:2])
from setuptools import setup, find_packages
import codecs
from os import path

cwd = path.dirname(__file__)
with codecs.open(path.join(cwd, 'longdesc.rst'), 'r', 'utf-8') as f:
    longdesc = f.read()

setup(
    name='pdoc',
    author='Andrew Gallant',
    author_email='pdoc@burntsushi.net',
    use_scm_version={
        'version_scheme': 'guess-next-dev',
        'local_scheme': 'dirty-tag',
        'write_to': 'pdoc/_version.py'
    },

    setup_requires=[
        'setuptools>=18.0',
        'setuptools-scm>1.5.4'
    ],
    license='UNLICENSE',
    description='A simple program and library to auto generate API '
                'documentation for Python modules.',
    long_description=longdesc,
    url='https://github.com/BurntSushi/pdoc',
    classifiers=[
        'Topic :: Documentation',
        'Topic :: Software Development :: Documentation',
        'Topic :: Utilities',
        'License :: Public Domain',
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
    ],
    platforms='ANY',
    packages=find_packages(),
    package_data={'pdoc': ['templates/*']},
    data_files=[('share/pdoc', ['README.md', 'longdesc.rst',
                                'UNLICENSE', 'INSTALL', 'CHANGELOG']),
                ('share/doc/pdoc', ['doc/pdoc/index.html']),
               ],
    provides=['pdoc'],
    install_requires=[
        'mako', 'markdown'
    ],    
    extras_require={
        'syntax_highlighting': ['pygments']
    },
    entry_points={
        'console_scripts': [
            'pdoc = pdoc.__main__:main',
        ],
    },    
)

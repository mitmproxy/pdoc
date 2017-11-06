import codecs
from distutils.core import setup
import os.path as path

install_requires = ['mako', 'markdown < 2.5']
try:  # Is this really the right way? Couldn't find anything better...
    import argparse
except ImportError:
    install_requires.append('argparse')

cwd = path.dirname(__file__)
longdesc = codecs.open(path.join(cwd, 'longdesc.rst'), 'r', 'utf-8').read()
version = '0.0.0'
with codecs.open(path.join(cwd, 'pdoc', '__init__.py'), 'r', 'utf-8') as f:
    for line in f:
        if line.startswith('__version__'):
            exec(line.strip())
            version = __version__
            break

setup(
    name='pdoc',
    author='Andrew Gallant',
    author_email='pdoc@burntsushi.net',
    version=version,
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
    packages=['pdoc'],
    package_data={'pdoc': ['templates/*']},
    data_files=[('share/pdoc', ['README.md', 'longdesc.rst',
                                'UNLICENSE', 'INSTALL', 'CHANGELOG']),
                ('share/doc/pdoc', ['doc/pdoc/index.html']),
               ],
    entry_points={'console_scripts':['pdoc = pdoc.cli:cli'] },
    provides=['pdoc'],
    requires=['argparse', 'mako', 'markdown'],
    install_requires=install_requires,
    extras_require={'syntax_highlighting': ['pygments']},
)

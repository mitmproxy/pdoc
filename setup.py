import codecs
from distutils.core import setup
from glob import glob

longdesc = []
with codecs.open('pdoc.py', 'r', 'utf-8') as f:
    for i, line in enumerate(f):
        if i == 0:
            continue
        if line.startswith('"""'):
            break
        longdesc.append(line)
longdesc = ''.join(longdesc)

install_requires = ['mako', 'markdown']
try:  # Is this really the right way? Couldn't find anything better...
    import argparse
except ImportError:
    install_requires.append('argparse')

version = '0.0.0'
with open('pdoc.py') as f:
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
    description='A simple program to auto generate API documentation for '
                'Python libraries.',
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
    py_modules = ['pdoc'],
    data_files=[('share/pdoc', ['README.md', 'UNLICENSE', 'INSTALL']),
                ('share/pdoc/doc', ['doc/pdoc.m.html']),
                ('share/pdoc/templates', glob('templates/*')),
               ],
    scripts=['pdoc'],
    provides=['pdoc'],
    requires=['argparse', 'mako', 'markdown'],
    install_requires=install_requires,
    extras_require={'syntax_highlighting': ['pygments']},
)

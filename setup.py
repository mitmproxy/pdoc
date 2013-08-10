from distutils.core import setup
from glob import glob

longdesc = \
'''A simple program (and library) to auto generate API documentation for Python 
libraries. All documentation text is parsed as Markdown and can be outputted as 
HTML or as plain text for console use. There are no special syntax rules, just 
pure Markdown.

While pdoc tries to stay consistent with documentation practices recommend by 
PEP 8 and PEP 257, pdoc also looks for documentation of representation in some 
places just as epydoc does. Namely, docstrings proceeding module level 
variables, class variables and instance variables in __init__ methods. This is 
done by traversing the ast of the source text.'''

install_requires = ['mako', 'markdown']
try:  # Is this really the right way? Couldn't find anything better...
    import argparse
except ImportError:
    install_requires.append('argparse')

setup(
    name='pdoc',
    author='Andrew Gallant',
    author_email='pdoc@burntsushi.net',
    version='0.0.9',
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
    data_files=[('share/doc/pdoc', ['README.md', 'UNLICENSE', 'INSTALL',
                                    'doc/pdoc.m.html']),
                ('share/pdoc/', glob('templates/*')),
               ],
    scripts=['pdoc'],
    provides=['pdoc'],
    requires=['argparse', 'mako', 'markdown'],
    install_requires=install_requires,
    extras_require={'syntax_highlighting': ['pygments']},
)

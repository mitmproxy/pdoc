from distutils.core import setup
from glob import glob
# import os 

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

# try: 
    # docfiles = map(lambda s: 'doc/%s' % s, list(os.walk('doc'))[0][2]) 
# except IndexError: 
    # docfiles = [] 

setup(
    name='pdoc',
    author='Andrew Gallant',
    author_email='pdoc@burntsushi.net',
    version='0.0.1',
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
    requires=['mako', 'markdown'],
    provides=['pdoc'],
    platforms='ANY',
    py_modules = ['pdoc'],
    data_files=[('share/doc/pdoc', ['README.md', 'COPYING', 'INSTALL']),
                ('share/pdoc/', glob('templates/*')),
               ],
    scripts=['pdoc']
)

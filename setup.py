from distutils.core import setup
import os

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

try:
    docfiles = map(lambda s: 'doc/%s' % s, list(os.walk('doc'))[0][2])
except IndexError:
    docfiles = []

setup(
    name='pdoc',
    author='Andrew Gallant',
    author_email='pdoc@burntsushi.net',
    version='0.0.1',
    license='WTFPL',
    description='A simple program to auto generate API documentation for '
                'Python libraries.',
    long_description=longdesc,
    url='https://github.com/BurntSushi/pdoc',
    classifiers=[
        'License :: Public Domain',
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Other Audience',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    ],
    platforms='ANY',
    packages=['pdoc'],
    package_dir={'pdoc': 'pdoc'},
    package_data={'pdoc': ['templates/*.html', 'templates/*.css']},
    data_files=[('share/doc/pdoc', ['README.md', 'COPYING', 'INSTALL']),
                ('share/doc/pdoc/doc', docfiles)],
    scripts=['scripts/pdoc']
)

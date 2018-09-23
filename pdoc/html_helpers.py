import os
import re
from functools import partial

import markdown

import pdoc.doc
import pdoc.render

# From language reference, but adds '.' to allow fully qualified names.
pyident = re.compile("^[a-zA-Z_][a-zA-Z0-9_.]+$")

_md = markdown.Markdown(
    output_format='html5',
    extensions=[
        "markdown.extensions.abbr",
        "markdown.extensions.fenced_code",
        "markdown.extensions.footnotes",
        "markdown.extensions.tables",
        "markdown.extensions.admonition",
        "markdown.extensions.headerid",
        "markdown.extensions.smarty",
        "markdown.extensions.toc",
    ]
)


def ident(s):
    return '<span class="ident">%s</span>' % s


def sourceid(dobj):
    return "source-%s" % dobj.refname


def clean_source_lines(lines, *, _indent=re.compile(r'^\s*').match):
    """
        Cleans the source code so that the first non-empty line's
        indentation is lstripped from it and subsequent lines.

        Returns one string with all of the raw source code.
    """
    base_indent = next((len(_indent(line).group(0))
                        for line in lines if line.rstrip()), 0)
    lines = [line[base_indent:] for line in lines]
    return ''.join(lines)


def linkify(match, parent, link_prefix):
    matched = match.group(0)
    ident = matched[1:-1]
    name, url = lookup(parent, ident, link_prefix)
    if name is None:
        return matched
    return "[`%s`](%s)" % (name, url)


def mark(s, parent, link_prefix, module_list=None, linky=True):
    if linky:
        s, _ = re.subn("\b\n\b", " ", s)
    if not module_list:
        _linkify = partial(linkify, parent=parent, link_prefix=link_prefix)
        s, _ = re.subn("`[^`]+`", _linkify, s)
    s = _md.reset().convert(s.strip())
    return s


def extract_toc(s):
    s = '[TOC]\n\n@CUT@' + s
    s = _md.reset().convert(s.strip())
    toc, _ = s.split('@CUT@', 1)
    return toc


def glimpse(s, length=100):
    if len(s) < length:
        return s
    return s[0:length] + " …"


def module_url(parent, m, link_prefix):
    """
        Returns a URL for `m`, which must be an instance of `Module`.
        `parent` is the Module being documented.

        Namely, '.' import separators are replaced with '/' URL
        separators. Also, packages are translated as directories
        containing `index.html` corresponding to the `__init__` module,
        while modules are translated as regular HTML files with an
        `.m.html` suffix. (Given default values of
        `pdoc.html_module_suffix` and `pdoc.html_package_name`.)
    """
    if parent.name == m.name:
        return ""

    # We use absolute paths, full name is ok
    if len(link_prefix) > 0:
        return link_prefix + pdoc.static.module_to_path(m).as_posix()

    # Otherwise, compute relative path from current module to link target
    url = os.path.relpath(str(pdoc.static.module_to_path(m)),
                          str(pdoc.static.module_to_path(parent)))
    # If documented module (parent) is not a package (directory),
    # we have one set of '..' too many
    if url.startswith('..'):# and not parent.submodules:
        url = url[3:]
    return url


def external_url(refname):
    """
        Attempts to guess an absolute URL for the external identifier
        given.

        Note that this just returns the refname with an ".ext" suffix.
        It will be up to whatever is interpreting the URLs to map it
        to an appropriate documentation page.
    """
    return "/%s.ext" % refname


def is_external_linkable(name):
    return pyident.match(name) and "." in name


def lookup(module, refname, link_prefix, get_qualname=True):
    """
        Given a fully qualified identifier name, return its refname
        with respect to the current module and a value for a `href`
        attribute. If `refname` is not in the public interface of
        this module or its submodules, then `None` is returned for
        both return values. (Unless this module has enabled external
        linking.)

        In particular, this takes into account sub-modules and external
        identifiers. If `refname` is in the public API of the current
        module, then a local anchor link is given. If `refname` is in the
        public API of a sub-module, then a link to a different page with
        the appropriate anchor is given. Otherwise, `refname` is
        considered external and no link is used.
    """
    d = module.find_ident(refname)
    if isinstance(d, pdoc.doc.External):
        if is_external_linkable(refname):
            return d.refname, external_url(d.refname)
        else:
            return None, None
    if isinstance(d, pdoc.doc.Module):
        return d.refname, module_url(module, d, link_prefix)
    suffix = '()' if isinstance(d, pdoc.doc.Function) else ''
    name = d.qualname if get_qualname else d.name
    if module.is_public(d.refname):
        return name + suffix, "#%s" % d.refname
    return name + suffix, "%s#%s" % (module_url(module, d.module, link_prefix), d.refname)


def link(parent, refname, link_prefix, qualname=True):
    """
        A convenience wrapper around `href` to produce the full
        `a` tag if `refname` is found. Otherwise, plain text of
        `refname` is returned.
    """
    name, url = lookup(parent, refname, link_prefix, qualname)
    if name is None:
        return refname
    return '<a href="%s">%s</a>' % (url, name)

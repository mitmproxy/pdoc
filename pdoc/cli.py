import argparse
import pathlib

import sys

import pdoc.doc
import pdoc.extract
import pdoc.render
import pdoc.static
import pdoc.version
import pdoc.web
import pdoc.markup

parser = argparse.ArgumentParser(
    description="Automatically generate API docs for Python modules.",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
aa = parser.add_argument
aa("--version", action="version", version="%(prog)s " + pdoc.__version__)
aa(
    "modules",
    type=str,
    metavar="module",
    nargs="+",
    help="Python module names. These may be import paths resolvable in "
    "the current environment, or file paths to a Python module or "
    "package.",
)
aa(
    "--filter",
    type=str,
    default=None,
    help="When specified, only identifiers containing the name given "
    "will be shown in the output. Search is case sensitive. "
    "Has no effect when --http is set.",
)
aa("--html", action="store_true", help="When set, the output will be HTML formatted.")
aa(
    "--html-dir",
    type=str,
    default=".",
    help="The directory to output HTML files to. This option is ignored when "
    "outputting documentation as plain text.",
)
aa(
    "--html-no-source",
    action="store_true",
    help="When set, source code will not be viewable in the generated HTML. "
    "This can speed up the time required to document large modules.",
)
aa(
    "--overwrite",
    action="store_true",
    help="Overwrites any existing HTML files instead of producing an error.",
)
aa(
    "--all-submodules",
    action="store_true",
    help="When set, every submodule will be included, regardless of whether "
    "__all__ is set and contains the submodule.",
)
aa(
    "--external-links",
    action="store_true",
    help="When set, identifiers to external modules are turned into links. "
    "This is automatically set when using --http.",
)
aa(
    "--template-dir",
    type=str,
    default=None,
    help="Specify a directory containing Mako templates. "
    "Alternatively, put your templates in $XDG_CONFIG_HOME/pdoc and "
    "pdoc will automatically find them.",
)
aa(
    "--link-prefix",
    type=str,
    default="",
    help="A prefix to use for every link in the generated documentation. "
    "No link prefix results in all links being relative. "
    "Has no effect when combined with --http.",
)
aa(
    "--http",
    action="store_true",
    help="When set, pdoc will run as an HTTP server providing documentation "
    "of all installed modules. Only modules found in PYTHONPATH will be "
    "listed.",
)
aa(
    "--http-host",
    type=str,
    default="localhost",
    help="The host on which to run the HTTP server.",
)
aa(
    "--http-port",
    type=int,
    default=8080,
    help="The port on which to run the HTTP server.",
)
aa(
    "--style",
    type=str,
    choices=['pre', 'markdown'],
    default='markdown',
    help='''
        The style of docstrings. Docstrings are converted to HTML as this option.
        "markdown" is Markdown (Default).
        "pre" does not convert docstrings and just wrappd <pre>...</pre>.
    ''',
)

Markups = {
    'markdown': pdoc.markup.Markdown(),
    'pre': pdoc.markup.Pre(),
}

def _eprint(*args, **kwargs):
    kwargs["file"] = sys.stderr
    print(*args, **kwargs)


def run():
    """ Command-line entry point """
    args = parser.parse_args()

    docfilter = None
    if args.filter and len(args.filter.strip()) > 0:
        search = args.filter.strip()

        def docfilter(o):
            rname = o.refname
            if rname.find(search) > -1 or search.find(o.name) > -1:
                return True
            if isinstance(o, pdoc.doc.Class):
                return search in o.doc or search in o.doc_init
            return False

    roots = []
    for mod in args.modules:
        try:
            m = pdoc.extract.extract_module(mod)
        except pdoc.extract.ExtractError as e:
            _eprint(str(e))
            sys.exit(1)
        roots.append(m)

    if args.template_dir is not None:
        pdoc.doc.tpl_lookup.directories.insert(0, args.template_dir)
    if args.http:
        args.html = True
        args.external_links = True
        args.overwrite = True
        args.link_prefix = "/"

    args.markup = Markups[args.markup]

    if args.http:
        # Run the HTTP server.
        httpd = pdoc.web.DocServer((args.http_host, args.http_port), args, roots)
        print(
            "pdoc server ready at http://%s:%d" % (args.http_host, args.http_port),
            file=sys.stderr,
        )
        httpd.serve_forever()
        httpd.server_close()
    elif args.html:
        dst = pathlib.Path(args.html_dir)
        if not args.overwrite and pdoc.static.would_overwrite(dst, roots):
            _eprint("Rendering would overwrite files, but --overwite is not set")
            sys.exit(1)
        pdoc.static.html_out(dst, roots, args.markup)
    else:
        # Plain text
        for m in roots:
            output = pdoc.render.text(m)
            print(output)


def main():
    try:
        run()
    except KeyboardInterrupt:
        pass

import argparse
import sys
from pathlib import Path

import pdoc
import pdoc.doc
import pdoc.extract
import pdoc.render_old
import pdoc.static
import pdoc.web

parser = argparse.ArgumentParser(
    description="Automatically generate API docs for Python modules.",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
parser.add_argument(
    "--version", action="version", version="%(prog)s " + pdoc.__version__
)
parser.add_argument(
    "modules",
    type=str,
    metavar="module",
    nargs="+",
    help="Python module names. These may be import paths resolvable in "
    "the current environment, or file paths to a Python module or "
    "package.",
)
formats = parser.add_mutually_exclusive_group()
formats.add_argument("--html", dest="format", action="store_const", const="html")
formats.add_argument(
    "--markdown", dest="format", action="store_const", const="markdown"
)
parser.add_argument(
    "-o",
    "--output-directory",
    type=Path,
    default="html",
    help="Output directory.",
)

"""
parser.add_argument(
    "--filter",
    type=str,
    default=None,
    help="When specified, only identifiers containing the name given "
         "will be shown in the output. Search is case sensitive. "
         "Has no effect when --http is set.",
)
parser.add_argument("--html", action="store_true", help="When set, the output will be HTML formatted.")

parser.add_argument(
    "--html-no-source",
    action="store_true",
    help="When set, source code will not be viewable in the generated HTML. "
         "This can speed up the time required to document large modules.",
)
parser.add_argument(
    "--overwrite",
    action="store_true",
    help="Overwrites any existing HTML files instead of producing an error.",
)
parser.add_argument(
    "--all-submodules",
    action="store_true",
    help="When set, every submodule will be included, regardless of whether "
         "__all__ is set and contains the submodule.",
)
parser.add_argument(
    "--external-links",
    action="store_true",
    help="When set, identifiers to external modules are turned into links. "
         "This is automatically set when using --http.",
)
parser.add_argument(
    "--template-dir",
    type=str,
    default=None,
    help="Specify a directory containing Mako templates. "
         "Alternatively, put your templates in $XDG_CONFIG_HOME/pdoc and "
         "pdoc will automatically find them.",
)
parser.add_argument(
    "--link-prefix",
    type=str,
    default="",
    help="A prefix to use for every link in the generated documentation. "
         "No link prefix results in all links being relative. "
         "Has no effect when combined with --http.",
)
parser.add_argument(
    "--http",
    action="store_true",
    help="When set, pdoc will run as an HTTP server providing documentation "
         "of all installed modules. Only modules found in PYTHONPATH will be "
         "listed.",
)
parser.add_argument(
    "--http-host",
    type=str,
    default="localhost",
    help="The host on which to run the HTTP server.",
)
parser.add_argument(
    "--http-port",
    type=int,
    default=8080,
    help="The port on which to run the HTTP server.",
)
"""


def cli(args=None):
    """ Command-line entry point """
    args = parser.parse_args(args)

    pdoc.pdoc(
        *args.modules,
        output_directory=args.output_directory,
        format=args.format or "html",
    )
    return

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
            print(str(e), file=sys.stderr)
            sys.exit(1)
        roots.append(m)

    if args.template_dir is not None:
        pdoc.doc.tpl_lookup.directories.insert(0, args.template_dir)
    if args.http:
        args.html = True
        args.external_links = True
        args.overwrite = True
        args.link_prefix = "/"

    if args.http:
        # Run the HTTP server.
        httpd = pdoc.web.DocServer((args.http_host, args.http_port), args, roots)
        print(
            f"pdoc server ready at http://{args.http_host}:{args.http_port}",
            file=sys.stderr,
        )
        httpd.serve_forever()
        httpd.server_close()
    elif args.html:
        dst = pathlib.Path(args.html_dir)
        if not args.overwrite and pdoc.static.would_overwrite(dst, roots):
            print(
                "Rendering would overwrite files, but --overwite is not set",
                file=sys.stderr,
            )
            sys.exit(1)
        pdoc.static.html_out(dst, roots)
    else:
        # Plain text
        for m in roots:
            output = pdoc.render_old.text(m)
            print(output)


if __name__ == "__main__":
    cli()

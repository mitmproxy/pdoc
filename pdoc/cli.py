import argparse

import codecs
import imp
import os
import os.path
import sys
import tempfile

import pdoc.web
import pdoc.doc

version_suffix = "%d.%d" % (sys.version_info[0], sys.version_info[1])
default_http_dir = os.path.join(tempfile.gettempdir(), "pdoc-%s" % version_suffix)

parser = argparse.ArgumentParser(
    description="Automatically generate API docs for Python modules.",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
aa = parser.add_argument
aa(
    "module_name",
    type=str,
    nargs="?",
    help="The Python module name. This may be an import path resolvable in "
    "the current environment, or a file path to a Python module or "
    "package.",
)
aa(
    "ident_name",
    type=str,
    nargs="?",
    help="When specified, only identifiers containing the name given "
    "will be shown in the output. Search is case sensitive. "
    "Has no effect when --http is set.",
)
aa("--version", action="store_true", help="Print the version of pdoc and exit.")
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
    "--only-pypath",
    action="store_true",
    help="When set, only modules in your PYTHONPATH will be documented.",
)
aa(
    "--http",
    action="store_true",
    help="When set, pdoc will run as an HTTP server providing documentation "
    "of all installed modules. Only modules found in PYTHONPATH will be "
    "listed.",
)
aa(
    "--http-dir",
    type=str,
    default=default_http_dir,
    help="The directory to cache HTML documentation when running as an HTTP " "server.",
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
aa("--http-html", action="store_true", help="Internal use only. Do not set.")


def _eprint(*args, **kwargs):
    kwargs["file"] = sys.stderr
    print(*args, **kwargs)


def module_file(args, m):
    mbase = os.path.join(args.html_dir, *m.name.split("."))
    if m.is_package():
        return os.path.join(mbase, pdoc.doc.html_package_name)
    else:
        return "%s%s" % (mbase, pdoc.doc.html_module_suffix)


def quit_if_exists(args, m):
    def check_file(f):
        if os.access(f, os.R_OK):
            _eprint("%s already exists. Delete it or run with --overwrite" % f)
            sys.exit(1)

    if args.overwrite:
        return
    f = module_file(args, m)
    check_file(f)

    # If this is a package, make sure the package directory doesn't exist
    # either.
    if m.is_package():
        check_file(os.path.dirname(f))


def html_out(args, m, html=True):
    f = module_file(args, m)
    if not html:
        f = module_file(args, m).replace(".html", ".md")
    dirpath = os.path.dirname(f)
    if not os.access(dirpath, os.R_OK):
        os.makedirs(dirpath)
    try:
        with codecs.open(f, "w+", "utf-8") as w:
            if not html:
                out = m.text()
            else:
                out = m.html(
                    external_links=args.external_links,
                    link_prefix=args.link_prefix,
                    http_server=args.http_html,
                    source=not args.html_no_source,
                )
            print(out, file=w)
    except Exception:
        try:
            os.unlink(f)
        except:
            pass
        raise
    for submodule in m.submodules():
        html_out(args, submodule, html)


def main():
    """ Command-line entry point """
    args = parser.parse_args()

    if args.version:
        print(pdoc.doc.__version__)
        sys.exit(0)

    # We close stdin because some modules, upon import, are not very polite
    # and block on stdin.
    try:
        sys.stdin.close()
    except:
        pass

    if not args.http and args.module_name is None:
        _eprint("No module name specified.")
        sys.exit(1)
    if args.template_dir is not None:
        pdoc.doc.tpl_lookup.directories.insert(0, args.template_dir)
    if args.http:
        args.html = True
        args.external_links = True
        args.html_dir = args.http_dir
        args.overwrite = True
        args.link_prefix = "/"

    # If PYTHONPATH is set, let it override everything if we want it to.
    pypath = os.getenv("PYTHONPATH")
    if args.only_pypath and pypath is not None and len(pypath) > 0:
        pdoc.doc.import_path = pypath.split(os.path.pathsep)

    if args.http:
        if args.module_name is not None:
            _eprint("Module names cannot be given with --http set.")
            sys.exit(1)

        # Run the HTTP server.
        httpd = pdoc.web.DocServer((args.http_host, args.http_port), args)
        print(
            "pdoc server ready at http://%s:%d" % (args.http_host, args.http_port),
            file=sys.stderr,
        )

        httpd.serve_forever()
        httpd.server_close()
        sys.exit(0)

    docfilter = None
    if args.ident_name and len(args.ident_name.strip()) > 0:
        search = args.ident_name.strip()

        def docfilter(o):
            rname = o.refname
            if rname.find(search) > -1 or search.find(o.name) > -1:
                return True
            if isinstance(o, pdoc.doc.Class):
                return search in o.doc or search in o.doc_init
            return False

    # Try to do a real import first. I think it's better to prefer
    # import paths over files. If a file is really necessary, then
    # specify the absolute path, which is guaranteed not to be a
    # Python import path.
    try:
        module = pdoc.doc.import_module(args.module_name)
    except Exception as e:
        module = None

    # Get the module that we're documenting. Accommodate for import paths,
    # files and directories.
    if module is None:
        isdir = os.path.isdir(args.module_name)
        isfile = os.path.isfile(args.module_name)
        if isdir or isfile:
            fp = os.path.realpath(args.module_name)
            module_name = os.path.basename(fp)
            if isdir:
                fp = os.path.join(fp, "__init__.py")
            else:
                module_name, _ = os.path.splitext(module_name)

            # Use a special module name to avoid import conflicts.
            # It is hidden from view via the `Module` class.
            with open(fp) as f:
                module = imp.load_source("__pdoc_file_module__", fp, f)
                if isdir:
                    module.__path__ = [os.path.realpath(args.module_name)]
                module.__pdoc_module_name = module_name
        else:
            module = pdoc.doc.import_module(args.module_name)
    module = pdoc.doc.Module(module, docfilter=docfilter, allsubmodules=args.all_submodules)

    # Plain text?
    if not args.html and not args.all_submodules:
        output = module.text()
        try:
            print(output)
        except IOError as e:
            # This seems to happen for long documentation.
            # This is obviously a hack. What's the real cause? Dunno.
            if e.errno == 32:
                pass
            else:
                raise e
        sys.exit(0)

    # HTML output depends on whether the module being documented is a package
    # or not. If not, then output is written to {MODULE_NAME}.html in
    # `html-dir`. If it is a package, then a directory called {MODULE_NAME}
    # is created, and output is written to {MODULE_NAME}/index.html.
    # Submodules are written to {MODULE_NAME}/{MODULE_NAME}.m.html and
    # subpackages are written to {MODULE_NAME}/{MODULE_NAME}/index.html. And
    # so on... The same rules apply for `http_dir` when `pdoc` is run as an
    # HTTP server.
    if not args.http:
        quit_if_exists(args, module)
        html_out(args, module, args.html)
        sys.exit(0)


if __name__ == "__main__":
    main()

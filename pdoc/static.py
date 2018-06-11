import codecs
import os.path

import pdoc.render


class StaticError(Exception):
    pass


def module_file(args, m):
    mbase = os.path.join(args.html_dir, *m.name.split("."))
    if m.is_package():
        return os.path.join(mbase, pdoc.render.html_package_name)
    else:
        return "%s%s" % (mbase, pdoc.render.html_module_suffix)


def quit_if_exists(args, m):
    def check_file(f):
        if os.access(f, os.R_OK):
            raise StaticError("%s already exists. Delete it or run with --overwrite" % f)
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
                out = pdoc.render.text(m)
            else:
                out = pdoc.render.html_module(
                    m,
                    external_links=args.external_links,
                    link_prefix=args.link_prefix,
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

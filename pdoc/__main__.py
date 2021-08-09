from __future__ import annotations

import argparse
import platform
import subprocess
from pathlib import Path

import pdoc
import pdoc.doc
import pdoc.extract
import pdoc.web
from pdoc import extract, render
from pdoc._compat import BooleanOptionalAction

parser = argparse.ArgumentParser(
    description="Automatically generate API docs for Python modules.",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    add_help=False,
)
mainargs = parser.add_argument_group("\x1b[1mMain Arguments\x1b[0m")
mainargs.add_argument(
    "modules",
    type=str,
    default=[],
    metavar="module",
    nargs="*",
    help='Python module names. These may be importable Python module names ("pdoc.doc") or file paths ("./pdoc/doc.py").',
)
mainargs.add_argument(
    "-o",
    "--output-directory",
    metavar="DIR",
    type=Path,
    help="Write rendered documentation to the specified directory, don't start a webserver.",
)
# may be added again in the future:
# formats = parser.add_mutually_exclusive_group()
# formats.add_argument("--html", dest="format", action="store_const", const="html")
# formats.add_argument(
#     "--markdown", dest="format", action="store_const", const="markdown"
# )

renderopts = parser.add_argument_group("\x1b[1mCustomize Rendering\x1b[0m")
renderopts.add_argument(
    "-d",
    "--docformat",
    type=str,
    default=None,
    choices=("google", "numpy", "restructuredtext"),
    help="The default docstring format.",
)
renderopts.add_argument(
    "-e",
    "--edit-url",
    action="append",
    type=str,
    default=[],
    metavar="module=url",
    help="A mapping between module names and URL prefixes, used to display an 'Edit' button. "
    "May be passed multiple times. "
    "Example: pdoc=https://github.com/mitmproxy/pdoc/blob/main/pdoc/",
)
renderopts.add_argument(
    "--math",
    action=BooleanOptionalAction,
    default=False,
    help="Include MathJax to enable math formula rendering.",
)
renderopts.add_argument(
    "--show-source",
    action=BooleanOptionalAction,
    default=True,
    help='Display "View Source" buttons.',
)
renderopts.add_argument(
    "--logo",
    type=str,
    metavar="URL",
    help='Add a project logo image.',
)
renderopts.add_argument(
    "--logo-link",
    type=str,
    metavar="URL",
    help='Optional URL the logo should point to.',
)
renderopts.add_argument(
    "--footer-text",
    type=str,
    metavar="TEXT",
    help="Custom text for the page footer, for example the project name and current version number.",
)
renderopts.add_argument(
    "-t",
    "--template-directory",
    metavar="DIR",
    type=Path,
    default=None,
    help="A directory containing Jinja2 templates to customize output. "
    "Alternatively, put your templates in $XDG_CONFIG_HOME/pdoc and pdoc will automatically find them.",
)

miscargs = parser.add_argument_group("\x1b[1mMiscellaneous Options\x1b[0m")
miscargs.add_argument(
    "-h",
    "--host",
    type=str,
    default="localhost",
    help="The host on which to run the HTTP server.",
)
miscargs.add_argument(
    "-p",
    "--port",
    type=int,
    default=8080,
    help="The port on which to run the HTTP server.",
)
miscargs.add_argument(
    "-n",
    "--no-browser",
    action="store_true",
    help="Don't open a browser after the web server has started.",
)
miscargs.add_argument("--help", action="help", help="Show this help message and exit.")
miscargs.add_argument(
    "--version",
    action="store_true",
    default=argparse.SUPPRESS,
    help="Show version information and exit.",
)


def get_dev_version() -> str:
    """
    Return a detailed version string, sourced either from VERSION or obtained dynamically using git.
    """

    pdoc_version = pdoc.__version__

    here = Path(__file__).parent

    try:
        # Check that we're in the pdoc repository:
        # 60665024af9af2cda4229e91b4d15f2359a4a3dd is the first pdoc commit.
        subprocess.run(
            ["git", "cat-file", "-e", "60665024af9af2cda4229e91b4d15f2359a4a3dd"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd=here,
            check=True,
        )
        git_describe = subprocess.check_output(
            ["git", "describe", "--tags", "--long"],
            stderr=subprocess.STDOUT,
            cwd=here,
        )
        last_tag, tag_dist_str, commit = git_describe.decode().strip().rsplit("-", 2)
        commit = commit.lstrip("g")[:7]
        tag_dist = int(tag_dist_str)
    except Exception:  # pragma: no cover
        pass
    else:
        # Add commit info for non-tagged releases
        if tag_dist > 0:  # pragma: no cover
            pdoc_version += f" (+{tag_dist}, commit {commit})"

    return pdoc_version


def cli(args: list[str] = None) -> None:
    """Command-line entry point"""
    opts = parser.parse_args(args)
    if getattr(opts, "version", False):
        print(
            f"pdoc: {get_dev_version()}\n"
            f"Python: {platform.python_version()}\n"
            f"Platform: {platform.platform()}"
        )
        return

    if not opts.modules:
        parser.print_help()
        print(
            "\n\x1b[31mError: Please specify which files or modules you want to document.\x1b[0m"
        )
        return

    render.configure(
        edit_url_map=dict(x.split("=", 1) for x in opts.edit_url),
        template_directory=opts.template_directory,
        docformat=opts.docformat,
        math=opts.math,
        show_source=opts.show_source,
        logo=opts.logo,
        logo_link=opts.logo_link,
        footer_text=opts.footer_text,
    )

    if opts.output_directory:
        pdoc.pdoc(
            *opts.modules,
            output_directory=opts.output_directory,
            format="html",  # opts.format or
        )
        return
    else:
        all_modules = extract.walk_specs(opts.modules)
        with pdoc.web.DocServer(
            (opts.host, opts.port),
            all_modules,
        ) as httpd:
            url = f"http://{opts.host}:{opts.port}"
            print(f"pdoc server ready at {url}")
            if not opts.no_browser:
                if len(opts.modules) == 1:
                    mod = next(iter(all_modules))
                    url += f"/{mod.replace('.', '/')}.html"
                pdoc.web.open_browser(url)
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                httpd.server_close()
                return


if __name__ == "__main__":  # pragma: no cover
    cli()

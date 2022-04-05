from __future__ import annotations

import argparse
import platform
import subprocess
import sys
import warnings
from pathlib import Path

import pdoc
import pdoc.doc
import pdoc.extract
import pdoc.render
import pdoc.web
from pdoc._compat import BooleanOptionalAction

if sys.stdout.isatty():  # pragma: no cover
    red = "\x1b[31m"
    yellow = "\x1b[33m"
    gray = "\x1b[2m"
    white = "\x1b[1m"
    default = "\x1b[0m"
else:
    red = yellow = gray = white = default = ""

parser = argparse.ArgumentParser(
    description="Automatically generate API docs for Python modules.",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    add_help=False,
)
mainargs = parser.add_argument_group(f"{white}Main Arguments{default}")
mainargs.add_argument(
    "modules",
    type=str,
    default=[],
    metavar="module",
    nargs="*",
    help='Python module names. These may be importable Python module names ("pdoc.doc") or file paths ("./pdoc/doc.py")'
    '. Exclude submodules by specifying a negative !regex pattern, e.g. "foo !foo.bar".',
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

renderopts = parser.add_argument_group(f"{white}Customize Rendering{default}")
renderopts.add_argument(
    "-d",
    "--docformat",
    type=str,
    default="restructuredtext",
    choices=("markdown", "google", "numpy", "restructuredtext"),
    help="The default docstring format. For non-Markdown formats, pdoc will first convert matching syntax elements to "
         "Markdown and then process everything as Markdown.",
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
    "--favicon",
    type=str,
    metavar="URL",
    help="Specify a custom favicon URL.",
)
renderopts.add_argument(
    "--footer-text",
    type=str,
    metavar="TEXT",
    help="Custom text for the page footer, for example the project name and current version number.",
)
renderopts.add_argument(
    "--logo",
    type=str,
    metavar="URL",
    help="Add a project logo image.",
)
renderopts.add_argument(
    "--logo-link",
    type=str,
    metavar="URL",
    help="Optional URL the logo should point to.",
)
renderopts.add_argument(
    "--math",
    action=BooleanOptionalAction,
    default=False,
    help="Include MathJax from a CDN to enable math formula rendering.",
)
renderopts.add_argument(
    "--search",
    action=BooleanOptionalAction,
    default=True,
    help="Enable search functionality.",
)
renderopts.add_argument(
    "--show-source",
    action=BooleanOptionalAction,
    default=True,
    help='Display "View Source" buttons.',
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

miscargs = parser.add_argument_group(f"{white}Miscellaneous Options{default}")
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
    default=None,
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
            f"\n{red}Error: Please specify which files or modules you want to document.{default}"
        )
        sys.exit(1)

    warnings.showwarning = _nicer_showwarning

    pdoc.render.configure(
        docformat=opts.docformat,
        edit_url_map=dict(x.split("=", 1) for x in opts.edit_url),
        favicon=opts.favicon,
        footer_text=opts.footer_text,
        logo=opts.logo,
        logo_link=opts.logo_link,
        math=opts.math,
        search=opts.search,
        show_source=opts.show_source,
        template_directory=opts.template_directory,
    )

    if opts.output_directory:
        pdoc.pdoc(
            *opts.modules,
            output_directory=opts.output_directory,
            format="html",  # opts.format or
        )
        return
    else:
        try:
            try:
                httpd = pdoc.web.DocServer((opts.host, opts.port or 8080), opts.modules)
            except OSError:
                # Couldn't bind, let's try again with a random port.
                httpd = pdoc.web.DocServer((opts.host, opts.port or 0), opts.modules)
        except OSError as e:
            print(
                f"{red}Cannot start web server on {opts.host}:{opts.port}: {e}{default}"
            )
            sys.exit(1)

        with httpd:
            url = f"http://{opts.host}:{httpd.server_port}"
            print(f"pdoc server ready at {url}")
            if not opts.no_browser:
                pdoc.web.open_browser(url)
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                httpd.server_close()
                return


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


def _nicer_showwarning(message, category, filename, lineno, file=None, line=None):
    """A replacement for `warnings.showwarning` that renders warnings in a more visually pleasing way."""
    if category == UserWarning:
        print(
            f"{yellow}Warn:{default} {message} {gray}({filename}:{lineno}){default}",
            file=sys.stderr,
        )
    elif category == RuntimeWarning:
        print(
            f"{yellow}Warn:{default} {message}",
            file=sys.stderr,
        )
    else:
        print(
            f"{yellow}{category.__name__}:{default} {message} {gray}({filename}:{lineno}){default}",
            file=sys.stderr,
        )


if __name__ == "__main__":  # pragma: no cover
    cli()

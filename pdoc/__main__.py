import argparse
import importlib.util
import pkgutil
import sys
import sysconfig
import webbrowser
from pathlib import Path

import pdoc
import pdoc.doc
import pdoc.extract
import pdoc.web
from pdoc import extract, render

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
    nargs="*",
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
    # default="html",
    help="Output directory.",
)
parser.add_argument(
    "--edit-on-github", "--edit-url",
    action="extend",
    nargs="+",
    type=str,
    default=[],
    help="module=url-prefix",
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
parser.add_argument(
    "--no-browser", "-n",
    action="store_true",
    help="Don't start a browser",
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

parser.add_argument(
    "--template-dir",
    type=str,
    default=None,
    help="Specify a directory containing Mako templates. "
         "Alternatively, put your templates in $XDG_CONFIG_HOME/pdoc and "
         "pdoc will automatically find them.",
)
"""


# https://github.com/mitmproxy/mitmproxy/blob/af3dfac85541ce06c0e3302a4ba495fe3c77b18a/mitmproxy/tools/web/webaddons.py#L35-L61
def open_browser(url: str) -> bool:
    """
    Open a URL in a browser window.
    In contrast to webbrowser.open, we limit the list of suitable browsers.
    This gracefully degrades to a no-op on headless servers, where webbrowser.open
    would otherwise open lynx.
    Returns:
        True, if a browser has been opened
        False, if no suitable browser has been found.
    """
    browsers = (
        "windows-default", "macosx",
        "wslview %s",
        "x-www-browser %s", "gnome-open %s",
        "google-chrome", "chrome", "chromium", "chromium-browser",
        "firefox", "opera", "safari",
    )
    for browser in browsers:
        try:
            b = webbrowser.get(browser)
        except webbrowser.Error:
            pass
        else:
            if b.open(url):
                return True
    return False


def cli(args=None):
    """ Command-line entry point """
    sys.stdin.close()
    args = parser.parse_args(args)

    github_sources = dict(x.split("=", 1) for x in args.edit_on_github)
    if args.output_directory:
        pdoc.pdoc(
            *args.modules,
            output_directory=args.output_directory,
            format=args.format or "html",
            github_sources=github_sources,
        )
        return
    else:
        if args.modules:
            render.roots = [
                extract.parse_spec(mod) for mod in args.modules
            ]
        else:
            stdlib = sysconfig.get_path("stdlib")
            platstdlib = sysconfig.get_path("platstdlib")
            for m in pkgutil.iter_modules():
                if m.name.startswith("_"):
                    continue
                if m.module_finder.path.startswith(stdlib) or m.module_finder.path.startswith(platstdlib):
                    if "site-packages" not in m.module_finder.path:
                        continue
                render.roots.append(m.name)

        with pdoc.web.DocServer((args.http_host, args.http_port)) as httpd:
            url = f"http://{args.http_host}:{args.http_port}"
            if len(render.roots) == 1:
                url += f"/{render.roots[0]}"
            print(f"pdoc server ready at {url}")
            if not args.no_browser:
                open_browser(url)
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                httpd.server_close()
                raise


if __name__ == "__main__":
    cli()

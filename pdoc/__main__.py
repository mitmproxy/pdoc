from __future__ import annotations

import argparse
from pathlib import Path
import platform
import subprocess
import sys
import warnings

from pdoc.config import Config
from pdoc.config import or_else
import pdoc.render
import pdoc.web

if sys.stdout.isatty():  # pragma: no cover
    red = "\x1b[31m"
    yellow = "\x1b[33m"
    gray = "\x1b[2m"
    white = "\x1b[1m"
    default = "\x1b[0m"
else:
    red = yellow = gray = white = default = ""


def build_parser(config: Config) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Automatically generate API docs for Python modules.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        add_help=False,
    )
    mainargs = parser.add_argument_group(f"{white}Main Arguments{default}")
    mainargs.add_argument(
        "modules",
        type=str,
        default=or_else(config.modules, []),
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
        default=config.output_directory,
        help="Write rendered documentation to the specified directory, don't start a webserver.",
    )

    # this is only here for documentation purposes;
    # the value is parsed earlier
    mainargs.add_argument(
        "-c",
        "--config",
        type=Path,
        help="Path to TOML configuration file. "
        "If the file name is `pyproject.toml`, config is under the `tool.pdoc` key; "
        "otherwise, look in the root of the TOML file.",
    )

    renderopts = parser.add_argument_group(f"{white}Customize Rendering{default}")
    renderopts.add_argument(
        "-d",
        "--docformat",
        type=str,
        default=or_else(config.docformat, "restructuredtext"),
        choices=("markdown", "google", "numpy", "restructuredtext"),
        help="The default docstring format. For non-Markdown formats, pdoc will first convert matching syntax elements to "
        "Markdown and then process everything as Markdown.",
    )
    renderopts.add_argument(
        "--include-undocumented",
        action=argparse.BooleanOptionalAction,
        default=or_else(config.include_undocumented, True),
        help="Show classes/functions/variables that do not have a docstring.",
    )
    renderopts.add_argument(
        "-e",
        "--edit-url",
        action="append",
        type=str,
        default=or_else(config.edit_url, []),
        metavar="module=url",
        help="A mapping between module names and URL prefixes, used to display an 'Edit' button. "
        "May be passed multiple times. "
        "Example: pdoc=https://github.com/mitmproxy/pdoc/blob/main/pdoc/",
    )
    renderopts.add_argument(
        "--favicon",
        type=str,
        default=config.favicon,
        metavar="URL",
        help="Specify a custom favicon URL.",
    )
    renderopts.add_argument(
        "--footer-text",
        type=str,
        default=config.footer_text,
        metavar="TEXT",
        help="Custom text for the page footer, for example the project name and current version number.",
    )
    renderopts.add_argument(
        "--logo",
        type=str,
        default=config.logo,
        metavar="URL",
        help="Add a project logo image.",
    )
    renderopts.add_argument(
        "--logo-link",
        type=str,
        default=config.logo_link,
        metavar="URL",
        help="Optional URL the logo should point to.",
    )
    renderopts.add_argument(
        "--math",
        action=argparse.BooleanOptionalAction,
        default=or_else(config.math, False),
        help="Include MathJax from a CDN to enable math formula rendering.",
    )
    renderopts.add_argument(
        "--mermaid",
        action=argparse.BooleanOptionalAction,
        default=or_else(config.mermaid, False),
        help="Include Mermaid.js from a CDN to enable Mermaid diagram rendering.",
    )
    renderopts.add_argument(
        "--search",
        action=argparse.BooleanOptionalAction,
        default=or_else(config.search, True),
        help="Enable search functionality if multiple modules are documented.",
    )
    renderopts.add_argument(
        "--show-source",
        action=argparse.BooleanOptionalAction,
        default=or_else(config.show_source, True),
        help='Display "View Source" buttons.',
    )
    renderopts.add_argument(
        "-t",
        "--template-directory",
        metavar="DIR",
        type=Path,
        default=config.template_directory,
        help="A directory containing Jinja2 templates to customize output. "
        "Alternatively, put your templates in $XDG_CONFIG_HOME/pdoc and pdoc will automatically find them.",
    )

    miscargs = parser.add_argument_group(f"{white}Miscellaneous Options{default}")
    miscargs.add_argument(
        "-h",
        "--host",
        type=str,
        default=or_else(config.host, "localhost"),
        help="The host on which to run the HTTP server.",
    )
    miscargs.add_argument(
        "-p",
        "--port",
        type=int,
        default=or_else(config.port, None),
        help="The port on which to run the HTTP server.",
    )
    miscargs.add_argument(
        "-n",
        "--no-browser",
        action="store_true",
        default=config.no_browser,
        help="Don't open a browser after the web server has started.",
    )
    miscargs.add_argument(
        "--help", action="help", help="Show this help message and exit."
    )
    miscargs.add_argument(
        "--version",
        action="store_true",
        default=argparse.SUPPRESS,
        help="Show version information and exit.",
    )
    return parser


def get_config(args: list[str] | None = None) -> Config:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-c", "--config", type=Path)
    known, _ = parser.parse_known_args(args)
    return Config.from_config_arg(known.config)


def cli(args: list[str] | None = None) -> None:
    """Command-line entry point"""
    config = get_config(args)

    parser = build_parser(config)
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
        include_undocumented=opts.include_undocumented,
        edit_url_map=dict(x.split("=", 1) for x in opts.edit_url),
        favicon=opts.favicon,
        footer_text=opts.footer_text,
        logo=opts.logo,
        logo_link=opts.logo_link,
        math=opts.math,
        mermaid=opts.mermaid,
        search=opts.search,
        show_source=opts.show_source,
        template_directory=opts.template_directory,
    )

    if opts.output_directory:
        pdoc.pdoc(
            *opts.modules,
            output_directory=opts.output_directory,
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

    try:  # pragma: no cover
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
    if category is UserWarning:
        print(
            f"{yellow}Warn:{default} {message} {gray}({filename}:{lineno}){default}",
            file=sys.stderr,
        )
    elif category is RuntimeWarning:
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

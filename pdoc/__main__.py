import argparse
import platform
import subprocess
from pathlib import Path

import pdoc
import pdoc.doc
import pdoc.extract
import pdoc.web
from pdoc import extract

parser = argparse.ArgumentParser(
    description="Automatically generate API docs for Python modules.",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
parser.add_argument(
    "--version",
    action="store_true",
    help="Show program's version number and exit.",
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
    help="Output directory.",
)
parser.add_argument(
    "--edit-on-github",
    "--edit-url",
    action="extend",
    nargs="+",
    type=str,
    default=[],
    help="module=url-prefix FIXME document",
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
    "--no-browser",
    "-n",
    action="store_true",
    help="Don't start a browser",
)
parser.add_argument(
    "-t", "--template-directory",
    type=Path,
    default=None,
    help="Specify a directory containing Jinja2 templates. "
         "Alternatively, put your templates in $XDG_CONFIG_HOME/pdoc and pdoc will automatically find them.",
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
            ['git', 'cat-file', '-e', '60665024af9af2cda4229e91b4d15f2359a4a3dd'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd=here,
            check=True)
        git_describe = subprocess.check_output(
            ['git', 'describe', '--tags', '--long'],
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


def cli(args=None):
    """ Command-line entry point """
    args = parser.parse_args(args)

    if args.version:
        print(
            f"pdoc: {get_dev_version()}\n"
            f"Python: {platform.python_version()}\n"
            f"Platform: {platform.platform()}"
        )
        return

    render.configure(
        edit_url_map=dict(x.split("=", 1) for x in args.edit_on_github),
        template_directory=args.template_directory,
    )

    if args.output_directory:
        pdoc.pdoc(
            *args.modules,
            output_directory=args.output_directory,
            format=args.format or "html",
            edit_url=edit_url,
        )
        return
    else:
        all_modules = extract.parse_specs(args.modules)

        with pdoc.web.DocServer(
            (args.http_host, args.http_port), all_modules, edit_url
        ) as httpd:
            url = f"http://{args.http_host}:{args.http_port}"
            print(f"pdoc server ready at {url}")
            if not args.no_browser:
                if len(args.modules) == 1:
                    mod = next(iter(all_modules))
                    url += f"/{mod.replace('.','/')}.html"
                pdoc.web.open_browser(url)
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                httpd.server_close()
                raise


if __name__ == "__main__":  # pragma: no cover
    cli()

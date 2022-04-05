"""
This module implements pdoc's live-reloading webserver.

We want to keep the number of dependencies as small as possible,
so we are content with the builtin `http.server` module.
It is a bit unergonomic compared to let's say flask, but good enough for our purposes.
"""

from __future__ import annotations

import http.server
import traceback
import warnings
import webbrowser
from collections.abc import Iterable, Iterator
from typing import Mapping

from pdoc import doc, extract, render
from pdoc._compat import cache, removesuffix


class DocHandler(http.server.BaseHTTPRequestHandler):
    """A handler for individual requests."""

    server: DocServer
    """A reference to the main web server."""

    def do_HEAD(self):
        try:
            return self.handle_request()
        except ConnectionError:  # pragma: no cover
            pass

    def do_GET(self):
        try:
            self.wfile.write(self.handle_request().encode())
        except ConnectionError:  # pragma: no cover
            pass

    def handle_request(self) -> str | None:
        """Actually handle a request. Called by `do_HEAD` and `do_GET`."""
        path = self.path.split("?", 1)[0]

        if path == "/" or path == "/index.html":
            out = render.html_index(self.server.all_modules)
        elif path == "/search.js":
            self.send_response(200)
            self.send_header("content-type", "application/javascript")
            self.end_headers()
            return self.server.render_search_index()
        else:
            module_name = removesuffix(path.lstrip("/"), ".html").replace("/", ".")
            if module_name not in self.server.all_modules:
                self.send_response(404)
                self.send_header("content-type", "text/html")
                self.end_headers()
                return render.html_error(error=f"Module {module_name!r} not found")

            mtime = ""
            t = extract.module_mtime(module_name)
            if t:
                mtime = f"{t:.1f}"
            if "mtime=1" in self.path:
                self.send_response(200)
                self.send_header("content-type", "text/plain")
                self.end_headers()
                return mtime

            try:
                extract.invalidate_caches(module_name)
                mod = self.server.all_modules[module_name]
                out = render.html_module(
                    module=mod,
                    all_modules=self.server.all_modules,
                    mtime=mtime,
                )
            except Exception:
                self.send_response(500)
                self.send_header("content-type", "text/html")
                self.end_headers()
                return render.html_error(
                    error=f"Error importing {module_name!r}",
                    details=traceback.format_exc(),
                )

        self.send_response(200)
        self.send_header("content-type", "text/html")
        self.end_headers()
        return out

    def log_request(self, code: int | str = ..., size: int | str = ...) -> None:
        """Override logging to disable it."""
        pass


class DocServer(http.server.HTTPServer):
    """pdoc's live-reloading web server"""

    all_modules: AllModules

    def __init__(self, addr: tuple[str, int], specs: list[str], **kwargs):
        super().__init__(addr, DocHandler, **kwargs)  # type: ignore
        module_names = extract.walk_specs(specs)
        self.all_modules = AllModules(module_names)

    @cache
    def render_search_index(self) -> str:
        """Render the search index. For performance reasons this is always cached."""
        # Some modules may not be importable, which means that they would raise an RuntimeError
        # when accessed. We "fix" this by pre-loading all modules here and only passing the ones that work.
        all_modules_safe = {}
        for mod in self.all_modules:
            try:
                all_modules_safe[mod] = doc.Module.from_name(mod)
            except RuntimeError:
                warnings.warn(f"Error importing {mod!r}:\n{traceback.format_exc()}")
        return render.search_index(all_modules_safe)


class AllModules(Mapping[str, doc.Module]):
    """A lazy-loading implementation of all_modules.

    This behaves like a regular dict, but modules are only imported on demand for performance reasons.
    This has the somewhat annoying side effect that __getitem__ may raise a RuntimeError.
    We can ignore that when rendering HTML as the default templates do not access all_modules values,
    but we need to perform additional steps for the search index.
    """

    def __init__(self, allowed_modules: Iterable[str]):
        # use a dict to preserve order
        self.allowed_modules: dict[str, None] = dict.fromkeys(allowed_modules)

    def __len__(self) -> int:
        return self.allowed_modules.__len__()

    def __iter__(self) -> Iterator[str]:
        return self.allowed_modules.__iter__()

    def __contains__(self, item):
        return self.allowed_modules.__contains__(item)

    def __getitem__(self, item: str):
        if item in self.allowed_modules:
            return doc.Module.from_name(item)
        else:  # pragma: no cover
            raise KeyError(item)


# https://github.com/mitmproxy/mitmproxy/blob/af3dfac85541ce06c0e3302a4ba495fe3c77b18a/mitmproxy/tools/web/webaddons.py#L35-L61
def open_browser(url: str) -> bool:  # pragma: no cover
    """
    Open a URL in a browser window.
    In contrast to `webbrowser.open`, we limit the list of suitable browsers.
    This gracefully degrades to a no-op on headless servers, where `webbrowser.open`
    would otherwise open lynx.

    Returns:

    - `True`, if a browser has been opened
    - `False`, if no suitable browser has been found.
    """
    browsers = (
        "windows-default",
        "macosx",
        "wslview %s",
        "x-www-browser %s",
        "gnome-open %s",
        "google-chrome",
        "chrome",
        "chromium",
        "chromium-browser",
        "firefox",
        "opera",
        "safari",
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

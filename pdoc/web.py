"""
This module implements pdoc's live-reloading webserver.

We want to keep the number of dependencies as small as possible,
so we are content with the builtin `http.server` module.
It is a bit unergonomic compared to let's say flask, but good enough for our purposes.
"""

from __future__ import annotations

import http.server
import importlib.util
import pkgutil
import sysconfig
import traceback
import webbrowser
from typing import Optional, Union, Collection

from pdoc import render, extract, doc
from pdoc._compat import removesuffix, cache


class DocHandler(http.server.BaseHTTPRequestHandler):
    """A handler for individual requests."""

    server: "DocServer"
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

    def handle_request(self) -> Optional[str]:
        """Actually handle a request. Called by `do_HEAD` and `do_GET`."""
        path = self.path.split("?", 1)[0]

        if path == "/":
            out = render.html_index(self.server.all_modules)
        else:
            module = removesuffix(path.lstrip("/"), ".html").replace("/", ".")
            if module not in self.server.all_modules:
                self.send_response(404)
                self.send_header("content-type", "text/html")
                self.end_headers()
                return render.html_error(error=f"Module {module!r} not found")

            mtime = ""
            if t := extract.module_mtime(module):
                mtime = f"{t:.1f}"
            if "mtime=1" in self.path:
                self.send_response(200)
                self.send_header("content-type", "text/plain")
                self.end_headers()
                return mtime

            extract.invalidate_caches(module)

            try:
                mod = doc.Module(extract.load_module(module))
            except Exception:
                self.send_response(500)
                self.send_header("content-type", "text/html")
                self.end_headers()
                return render.html_error(
                    error=f"Error importing {module!r}",
                    details=traceback.format_exc(),
                )
            out = render.html_module(
                module=mod,
                all_modules=self.server.all_modules,
                mtime=mtime,
            )

        self.send_response(200)
        self.send_header("content-type", "text/html")
        self.end_headers()
        return out

    def log_request(
        self, code: Union[int, str] = ..., size: Union[int, str] = ...
    ) -> None:
        """Override logging to disable it."""
        pass


class DocServer(http.server.HTTPServer):
    """pdoc's live-reloading web server"""

    all_modules: Collection[str]

    def __init__(
        self,
        addr: tuple[str, int],
        all_modules: Collection[str],
    ):
        super().__init__(addr, DocHandler)
        self.all_modules = all_modules


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


class AllModules(Collection[str]):
    """
    A fake collection that contains all modules installed by the user.
    This is used when `pdoc` is invoked without any arguments,
    using `pkgutil.walk_packages` would take multiple seconds.

    When being __iter__ated, it returns the list of all top-level modules,
    but it __contains__ all submodules as well.
    """

    def __init__(self):
        root_modules = []
        stdlib = sysconfig.get_path("stdlib").lower()
        platstdlib = sysconfig.get_path("platstdlib").lower()
        for m in pkgutil.iter_modules():
            if m.name.startswith("_") or m.name[0].isdigit():
                continue
            if getattr(m.module_finder, "path", "").lower() in (stdlib, platstdlib):
                continue
            root_modules.append(m.name)
        self._root_mods: dict[str, None] = dict.fromkeys(sorted(root_modules))

    def __iter__(self):
        return self._root_mods.__iter__()

    def __len__(self):
        return self._root_mods.__len__()

    @cache
    def __contains__(self, modname):
        if modname.split(".", maxsplit=1)[0] not in self._root_mods:
            return False
        try:
            with extract.mock_some_common_side_effects():
                modspec = importlib.util.find_spec(modname)
            if modspec is None:
                raise ModuleNotFoundError(modname)
        except BaseException:
            return False
        else:
            return True

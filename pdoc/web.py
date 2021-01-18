from __future__ import annotations

import http.server
import traceback
import webbrowser
from typing import Optional, Union, Collection

from pdoc import render, extract, doc
# the builtin http.server module is a bit unergonomic,
# but we can deal with that to avoid additional dependencies.
from pdoc._compat import removesuffix


class DocHandler(http.server.BaseHTTPRequestHandler):
    server: "DocServer"

    def do_HEAD(self):
        return self.handle_request()

    def do_GET(self):
        self.wfile.write(self.handle_request().encode())

    def log_request(
        self, code: Union[int, str] = ..., size: Union[int, str] = ...
    ) -> None:
        pass

    def handle_request(self) -> Optional[str]:
        extract.invalidate_caches(self.server.all_modules)
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


class DocServer(http.server.HTTPServer):
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
    In contrast to webbrowser.open, we limit the list of suitable browsers.
    This gracefully degrades to a no-op on headless servers, where webbrowser.open
    would otherwise open lynx.
    Returns:
        True, if a browser has been opened
        False, if no suitable browser has been found.
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

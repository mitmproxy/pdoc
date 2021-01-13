import http.server
import traceback
from typing import Optional, Union, Collection

import pdoc.doc
import pdoc.extract
import pdoc.render
from pdoc import render, extract


# the builtin http.server module is a bit unergonomic,
# but we can deal with that to avoid additional dependencies.


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
            module = path.removeprefix("/").removesuffix(".html").replace("/", ".")
            if module not in self.server.all_modules:
                self.send_response(404)
                self.send_header("content-type", "text/html")
                self.end_headers()
                return pdoc.render.html_error(error=f"Module {module!r} not found")

            mtime = f"{extract.module_mtime(module):.1f}"
            if "mtime=1" in self.path:
                self.send_response(200)
                self.send_header("content-type", "text/plain")
                self.end_headers()
                return mtime
            try:
                mod = pdoc.doc.Module(extract.load_module(module))
            except Exception:
                self.send_response(500)
                self.send_header("content-type", "text/html")
                self.end_headers()
                return pdoc.render.html_error(
                    error=f"Error importing {module!r}",
                    details=traceback.format_exc(),
                )
            out = pdoc.render.html_module(mod, mtime=mtime)

        self.send_response(200)
        self.send_header("content-type", "text/html")
        self.end_headers()
        return out


class DocServer(http.server.HTTPServer):
    all_modules: Collection[str]

    def __init__(self, addr: tuple[str, int], all_modules: Collection[str]):
        super().__init__(addr, DocHandler)
        self.all_modules = all_modules

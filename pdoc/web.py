import http.server
import traceback
from typing import Optional, Union

import pdoc.doc
import pdoc.extract
import pdoc.render
from pdoc import render, extract


# the builtin http.server module is a bit unergonomic,
# but we can deal with that to avoid additional dependencies.

class DocHandler(http.server.BaseHTTPRequestHandler):
    def do_HEAD(self):
        return self.handle_request()

    def do_GET(self):
        self.wfile.write(self.handle_request().encode())

    def log_request(self, code: Union[int, str] = ..., size: Union[int, str] = ...) -> None:
        pass

    def handle_request(self) -> Optional[str]:
        extract.invalidate_caches(render.roots)
        path = self.path.split("?", 1)[0]

        if path == "/":
            out = render.html_index()
        else:
            module = path.removeprefix("/").removesuffix(".html").replace("/", ".")
            if not any(module.startswith(r) for r in render.roots) or not extract.module_exists(module):
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
    def __init__(self, addr: tuple[str, int]):
        super().__init__(addr, DocHandler)

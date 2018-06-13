import http.server
import re
import os.path
import logging

import pdoc.doc
import pdoc.render
import pdoc.extract


class DocHandler(http.server.BaseHTTPRequestHandler):
    def do_HEAD(self):
        if self.path != "/":
            out = self.html()
            if out is None:
                self.send_response(404)
                self.end_headers()
                return

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

    def do_GET(self):
        if self.path == "/":
            midx = []
            for m in self.server.modules:
                midx.append((m.name, m.docstring))
            midx = sorted(midx, key=lambda x: x[0].lower())
            out = pdoc.render.html_index(midx, self.server.args.link_prefix)
        elif self.path.endswith(".ext"):
            # External links are a bit weird. You should view them as a giant
            # hack. Basically, the idea is to "guess" where something lives
            # when documenting another module and hope that guess can actually
            # track something down in a more global context.
            #
            # The idea here is to start specific by looking for HTML that
            # exists that matches the full external path given. Then trim off
            # one component at the end and try again.
            #
            # If no HTML is found, then we ask `pdoc` to do its thang on the
            # parent module in the external path. If all goes well, that
            # module will then be able to find the external identifier.

            import_path = self.path[:-4].lstrip("/")
            resolved = self.resolve_ext(import_path)
            if resolved is None:  # Try to generate the HTML...
                logging.info("Generating HTML for %s on the fly..." % import_path)
                self.html(import_path.split(".")[0])

                # Try looking once more.
                resolved = self.resolve_ext(import_path)
            if resolved is None:  # All hope is lost.
                self.send_response(404)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.echo(
                    "External identifier <code>%s</code> not found." % import_path
                )
                return
            self.send_response(302)
            self.send_header("Location", resolved)
            self.end_headers()
            return
        else:
            out = self.html()
            if out is None:
                self.send_response(404)
                self.send_header("Content-type", "text/html")
                self.end_headers()

                err = "Module <code>%s</code> not found." % self.import_path
                self.echo(err)
                return

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.echo(out)

    def echo(self, s):
        self.wfile.write(s.encode("utf-8"))

    def html(self):
        """
        Retrieves and sends the HTML belonging to the path given in
        URL. This method is smart and will look for HTML files already
        generated and account for whether they are stale compared to
        the source code.
        """
        # Deny favico shortcut early.
        if self.path == "/favicon.ico":
            return None
        return pdoc.render.html_module(pdoc.extract.extract_module(self.import_path))

    def resolve_ext(self, import_path):
        def exists(p):
            p = os.path.join(self.server.args.html_dir, p)
            pkg = os.path.join(p, pdoc.render.html_package_name)
            mod = p + pdoc.render.html_module_suffix

            if os.path.isfile(pkg):
                return pkg[len(self.server.args.html_dir) :]
            elif os.path.isfile(mod):
                return mod[len(self.server.args.html_dir) :]
            return None

        parts = import_path.split(".")
        for i in range(len(parts), 0, -1):
            p = os.path.join(*parts[0:i])
            realp = exists(p)
            if realp is not None:
                return "/%s#%s" % (realp.lstrip("/"), import_path)
        return None

    @property
    def file_path(self):
        fp = os.path.join(self.server.args.html_dir, *self.import_path.split("."))
        pkgp = os.path.join(fp, pdoc.render.html_package_name)
        if os.path.isdir(fp) and os.path.isfile(pkgp):
            fp = pkgp
        else:
            fp += pdoc.render.html_module_suffix
        return fp

    @property
    def import_path(self):
        pieces = self.clean_path.split("/")
        if pieces[-1].startswith(pdoc.render.html_package_name):
            pieces = pieces[:-1]
        if pieces[-1].endswith(pdoc.render.html_module_suffix):
            pieces[-1] = pieces[-1][: -len(pdoc.render.html_module_suffix)]
        return ".".join(pieces)

    @property
    def clean_path(self):
        new, _ = re.subn("//+", "/", self.path)
        if "#" in new:
            new = new[0 : new.index("#")]
        return new.strip("/")

    def address_string(self):
        return "%s:%s" % (self.client_address[0], self.client_address[1])


class DocServer(http.server.HTTPServer):
    def __init__(self, addr, args, modules):
        self.args = args
        self.modules = modules
        super().__init__(addr, DocHandler)

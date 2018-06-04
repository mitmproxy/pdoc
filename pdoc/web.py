import http.server
import pkgutil
import re
import os.path
import codecs
import logging

import pdoc.doc
import pdoc.render
import pdoc.extract


def quick_desc(imp, name, ispkg):
    if not hasattr(imp, "path"):
        # See issue #7.
        return ""

    if ispkg:
        fp = os.path.join(imp.path, name, "__init__.py")
    else:
        fp = os.path.join(imp.path, "%s.py" % name)
    if os.path.isfile(fp):
        with codecs.open(fp, "r", "utf-8") as f:
            quotes = None
            doco = []
            for i, line in enumerate(f):
                if i == 0:
                    if len(line) >= 3 and line[0:3] in ("'''", '"""'):
                        quotes = line[0:3]
                        line = line[3:]
                    else:
                        break
                line = line.rstrip()
                if line.endswith(quotes):
                    doco.append(line[0:-3])
                    break
                else:
                    doco.append(line)
            desc = "\n".join(doco)
            if len(desc) > 200:
                desc = desc[0:200] + "..."
            return desc
    return ""


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
            modules = []
            for (imp, name, ispkg) in pkgutil.iter_modules(pdoc.doc.import_path):
                if name == "setup" and not ispkg:
                    continue
                modules.append((name, quick_desc(imp, name, ispkg)))
            modules = sorted(modules, key=lambda x: x[0].lower())

            out = pdoc.doc.tpl_lookup.get_template("/html.mako")
            out = out.render(modules=modules, link_prefix=self.server.args.link_prefix)
            out = out.strip()
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
        return pdoc.render.html(
            pdoc.doc.Module(pdoc.extract.extract_module(self.import_path))
        )

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
    def __init__(self, addr, args):
        self.args = args
        super().__init__(addr, DocHandler)

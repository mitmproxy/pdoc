import io
import socket
import threading
from pathlib import Path

import pytest

from pdoc.web import DocServer, DocHandler


here = Path(__file__).parent


class ReadResponse(threading.Thread):
    def __init__(self, sock):
        super().__init__()
        self.sock = sock
        self.data = io.BytesIO()

    def run(self) -> None:
        while True:
            data = self.sock.recv(65536)
            if data:
                self.data.write(data)
            else:
                return


def handle_request(data: bytes) -> bytes:
    server = DocServer(
        ("", 8080),
        specs=[
            "dataclasses",
            str(here / "testdata" / "import_err_simple.py"),
            "jinja2",
            "!jinja2.",
        ],
        bind_and_activate=False,
    )
    a, b = socket.socketpair()
    b.send(data)
    t = ReadResponse(b)
    t.start()
    # noinspection PyTypeChecker
    DocHandler(a, ("127.0.0.1", 54321), server)  # type: ignore
    a.close()
    t.join()
    return t.data.getvalue()


def test_head_index():
    assert b"200 OK" in handle_request(b"HEAD / HTTP/1.1\r\n\r\n")


def test_get_index():
    assert b'<a href="dataclasses.html">' in handle_request(b"GET / HTTP/1.1\r\n\r\n")


def test_get_search_json():
    with pytest.warns(UserWarning, match="Error importing 'import_err_simple'"):
        assert b'"dataclasses.is_dataclass"' in handle_request(
            b"GET /search.js HTTP/1.1\r\n\r\n"
        )


def test_get_module():
    assert b"make_dataclass" in handle_request(
        b"GET /dataclasses.html HTTP/1.1\r\n\r\n"
    )


def test_get_dependency():
    assert b"a template engine written in pure Python" in handle_request(
        b"GET /jinja2.html HTTP/1.1\r\n\r\n"
    )


def test_get_module_err():
    assert b"I fail on import" in handle_request(
        b"GET /import_err_simple.html HTTP/1.1\r\n\r\n"
    )


def test_get_module_mtime():
    assert float(
        handle_request(b"GET /dataclasses.html?mtime=1 HTTP/1.1\r\n\r\n")
        .splitlines()[-1]
        .decode()
    )


def test_get_unknown():
    assert b"404 Not Found" in handle_request(b"GET /unknown HTTP/1.1\r\n\r\n")

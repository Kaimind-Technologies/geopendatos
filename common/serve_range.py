"""Servidor HTTP local con CORS y lectura por rangos (HTTP 206), para probar capas
GeoParquet en GeoLibre antes de subirlas al repo.

GeoLibre (DuckDB-WASM) lee GeoParquet por rangos de bytes; el http.server estándar
no los soporta y la capa no carga. Chrome además debe lanzarse con
--disable-features=LocalNetworkAccessChecks,BlockInsecurePrivateNetworkRequests
para que web.geolibre.app pueda leer de localhost.

Uso como módulo:
    from serve_range import serve
    server = serve(directorio, puerto)   # corre en un hilo; server.shutdown() al terminar
"""

import os
import re
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

RANGE_RE = re.compile(r"bytes=(\d*)-(\d*)")


class RangeCORSHandler(SimpleHTTPRequestHandler):
    def end_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Private-Network", "true")
        self.send_header("Access-Control-Expose-Headers", "Content-Range, Content-Length, Accept-Ranges")
        self.send_header("Accept-Ranges", "bytes")
        super().end_headers()

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Headers", "Range, *")
        self.send_header("Access-Control-Allow-Methods", "GET, HEAD, OPTIONS")
        self.end_headers()

    def do_GET(self) -> None:
        m = RANGE_RE.fullmatch(self.headers.get("Range", "").strip())
        path = self.translate_path(self.path)
        if not m or not os.path.isfile(path):
            return super().do_GET()
        size = os.path.getsize(path)
        start_s, end_s = m.groups()
        if start_s == "":
            start, end = max(size - int(end_s), 0), size - 1
        else:
            start = int(start_s)
            end = min(int(end_s), size - 1) if end_s else size - 1
        if start >= size or start > end:
            self.send_response(416)
            self.send_header("Content-Range", f"bytes */{size}")
            self.end_headers()
            return
        length = end - start + 1
        self.send_response(206)
        self.send_header("Content-Type", self.guess_type(path))
        self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Content-Length", str(length))
        self.end_headers()
        with open(path, "rb") as f:
            f.seek(start)
            self.wfile.write(f.read(length))

    def log_message(self, *args) -> None:
        pass


def serve(directory: str, port: int) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer(("127.0.0.1", port), partial(RangeCORSHandler, directory=directory))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server

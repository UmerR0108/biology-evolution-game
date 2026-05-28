"""Small static server for Railway's pygbag build.

Python's default http.server is fine for local tests, but Railway/mobile users can
see stale gray loader screens if an old game.tar.gz is cached. This server keeps
serving simple static files while explicitly disabling browser/intermediary cache.
"""

from __future__ import annotations

import os
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer


class NoCacheStaticHandler(SimpleHTTPRequestHandler):
    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()


def main() -> None:
    port = int(os.environ.get("PORT", "8000"))
    directory = os.environ.get("STATIC_DIR", "build/web")
    handler = partial(NoCacheStaticHandler, directory=directory)
    server = ThreadingHTTPServer(("0.0.0.0", port), handler)
    print(f"Serving {directory} on 0.0.0.0:{port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()

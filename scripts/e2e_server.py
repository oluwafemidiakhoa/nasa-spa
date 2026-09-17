#!/usr/bin/env python3
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

CLEAN_URLS = {
    "/": "/trainer.html",
    "/trainer": "/trainer.html",
    "/navigator": "/navigator.html",
}


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urlsplit(self.path)
        mapped = CLEAN_URLS.get(parsed.path)
        if mapped:
            self.path = mapped + (f"?{parsed.query}" if parsed.query else "")
        return super().do_GET()


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 4173), Handler)
    print("E2E server listening on http://127.0.0.1:4173", flush=True)
    server.serve_forever()

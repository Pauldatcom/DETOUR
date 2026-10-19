#!/usr/bin/env python3
"""Serve the slide engine and its local Markdown exercises."""

import argparse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]


class CourseHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):
        parsed = urlsplit(self.path)
        if parsed.path in ("/", "/index.html"):
            destination = "/slides/index.html"
            if parsed.query:
                destination += "?" + parsed.query
            self.send_response(302)
            self.send_header("Location", destination)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        return super().do_GET()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), CourseHandler)
    print(f"Slides : http://{args.host}:{args.port}/", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()

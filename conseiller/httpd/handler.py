"""Generic HTTP handler: plumbing, dispatch to the router, error handling.

The application (app.py) subclasses HttpHandler to set `ctx` and `router`
and to map its business errors via `repondre_erreur`.
"""

import json
import mimetypes
import traceback

from http.server import BaseHTTPRequestHandler
from typing import TYPE_CHECKING
from urllib.parse import parse_qs, urlparse

from utils import SESSION_COOKIE

from .context import WEB_ROOT
from .errors import ApiError, SessionError
from .gardes import verifier_acces
from .request import Request

if TYPE_CHECKING:
    from .context import Context
    from .router import Router


class HttpHandler(BaseHTTPRequestHandler):
    """Generic handler. `ctx` and `router` are set as class attributes."""

    ctx: "Context"
    router: "Router"

    def log_message(self, format, *args):
        print("%s %s" % (self.address_string(), format % args))

    # ---- responses ----

    def send_json(self, status, payload, extra_headers=None):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for name, value in (extra_headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)

    def redirect(self, location):
        self.send_response(302)
        self.send_header("Location", location)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def send_static(self, filename):
        path = self.ctx.root / filename
        if not path.exists():
            raise ApiError(404, "not_found", "Fichier introuvable.")
        mime, _ = mimetypes.guess_type(filename)
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", f"{mime or 'application/octet-stream'}; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, base, filename):
        full = base / filename
        if not full.exists() or not full.is_file():
            raise ApiError(404, "not_found", "Fichier introuvable.")
        mime, _ = mimetypes.guess_type(filename)
        body = full.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", f"{mime or 'application/octet-stream'}; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        if not 0 < length <= 50000:
            raise ApiError(400, "invalid_body", "Corps JSON requis (50 Ko maximum).")
        try:
            data = json.loads(self.rfile.read(length))
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise ApiError(400, "invalid_json", "JSON invalide.")
        if not isinstance(data, dict):
            raise ApiError(400, "invalid_json", "Un objet JSON est attendu.")
        return data

    def _session_cookie(self, token, supprime=False):
        if supprime:
            valeur = f"{SESSION_COOKIE}=; Max-Age=0; Path=/; HttpOnly; SameSite=Strict"
        else:
            valeur = f"{SESSION_COOKIE}={token}; Path=/; HttpOnly; SameSite=Strict"
        return {"Set-Cookie": valeur}

    # ---- dispatch ----

    def do_GET(self):
        self._handle("GET")

    def do_POST(self):
        self._handle("POST")

    def do_PATCH(self):
        self._handle("PATCH")

    def _handle(self, method):
        try:
            parsed = urlparse(self.path)
            path, query = parsed.path, parse_qs(parsed.query)
            session = self.ctx.sessions.depuis_cookie(self.headers)
            func, params = self.router.resoudre(method, path)
            req = Request(self, method, path, query, session, self.ctx)
            if path.startswith("/api/"):
                verifier_acces(req, method, path)
            if func is not None:
                return func(req, **params)
            # No route matched: React SPA (web/dist) as a last resort.
            if method == "GET" and WEB_ROOT.exists() and not path.startswith("/api/"):
                asset = WEB_ROOT / path.lstrip("/")
                if asset.exists() and asset.is_file():
                    return self.send_file(WEB_ROOT, path.lstrip("/"))
                index = WEB_ROOT / "index.html"
                if index.exists():
                    return self.send_file(WEB_ROOT, "index.html")
            raise ApiError(404, "not_found", "Route inconnue.")
        except SessionError as exc:
            self.send_json(exc.status, {"erreur": {"code": exc.code, "message": exc.message}})
        except ApiError as exc:
            self.send_json(exc.status, {"erreur": {"code": exc.code, "message": exc.message}})
        except Exception as exc:
            self.repondre_erreur(exc)

    def repondre_erreur(self, exc):
        """Erreurs hors httpd : l'application surcharge pour mapper ses classes."""
        traceback.print_exc()
        self.send_json(500, {"erreur": {"code": "internal_error", "message": "Erreur interne."}})

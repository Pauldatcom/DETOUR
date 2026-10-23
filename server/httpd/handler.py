"""Generic HTTP handler: plumbing, dispatch to the router, error handling.

The application (app.py) subclasses HttpHandler to set `ctx` and `router`.
"""

import json
import ssl
from http.cookies import CookieError, SimpleCookie
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from .context import DASHBOARD_COOKIE, Context
from .errors import ApiError
from .gardes import verifier_acces
from .request import Request
from .router import Router


class HttpHandler(BaseHTTPRequestHandler):
    """Generic handler. `ctx` and `router` are set as class attributes."""

    ctx: Context
    router: Router

    def log_message(self, fmt, *args):
        print("%s %s" % (self.address_string(), fmt % args))

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

    def send_dashboard_asset(self, filename, content_type):
        body = (self.ctx.static_root / filename).read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; base-uri 'none'; form-action 'self'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(body)

    def send_brand_asset(self, filename):
        """Serve the official brand-2026 logo untouched: no distortion, no recolouring.

        `detour-logo-negatif-transparent.svg` is the official negative without
        the kit's Encre background, for legacy dark surfaces (#07101E, #06101C).
        """
        if filename not in self.ctx.logos:
            raise ApiError(404, "not_found", "Logo introuvable.")
        body = (self.ctx.brand_dir / filename).read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "image/svg+xml")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "public, max-age=3600")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'self'; img-src 'self' data:; base-uri 'none'")
        self.end_headers()
        self.wfile.write(body)

    def send_static_yaml(self, filename):
        body = (self.ctx.docs_root / filename).read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "application/yaml; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    # ---- request helpers ----

    def read_json(self):
        length = self.headers.get("Content-Length", "0")
        try:
            length = int(length)
        except ValueError:
            raise ApiError(400, "invalid_body", "Content-Length invalide.")
        if not 0 < length <= 10000:
            raise ApiError(400, "invalid_body", "Corps JSON requis (10 Ko maximum).")
        try:
            data = json.loads(self.rfile.read(length))
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise ApiError(400, "invalid_json", "JSON invalide.")
        if not isinstance(data, dict):
            raise ApiError(400, "invalid_json", "Un objet JSON est attendu.")
        return data

    def dashboard_cookie(self):
        try:
            cookies = SimpleCookie()
            cookies.load(self.headers.get("Cookie", ""))
            return cookies[DASHBOARD_COOKIE].value if DASHBOARD_COOKIE in cookies else None
        except CookieError:
            return None

    def session_cookie_header(self, token, max_age):
        secure = "; Secure" if isinstance(self.connection, ssl.SSLSocket) else ""
        return f"{DASHBOARD_COOKIE}={token}; Path=/dashboard; Max-Age={max_age}; HttpOnly; SameSite=Strict{secure}"

    def require_same_origin(self):
        if self.headers.get("Sec-Fetch-Site") == "cross-site":
            raise ApiError(403, "origin_invalid", "Origine de la requête refusée.")
        origin = self.headers.get("Origin")
        if origin and urlparse(origin).netloc != self.headers.get("Host"):
            raise ApiError(403, "origin_invalid", "Origine de la requête refusée.")

    # ---- dispatch ----

    def handle_request(self):
        try:
            parsed = urlparse(self.path)
            path, query = parsed.path, parse_qs(parsed.query)
            req = Request(self, self.command, path, query, self.ctx)
            verifier_acces(req, self.command, path)
            func, params = self.router.resoudre(self.command, path)
            if func is None:
                raise ApiError(404, "not_found", "Route inconnue.")
            return func(req, **params)
        except ApiError as exc:
            self.send_json(exc.status, {"erreur": {"code": exc.code, "message": exc.message}})
        except Exception:
            self.send_json(500, {"erreur": {"code": "internal_error", "message": "Erreur interne du serveur."}})

    do_GET = handle_request
    do_POST = handle_request

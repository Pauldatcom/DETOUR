"""View of a request passed to route functions."""

from .errors import SessionError


class Request:
    """Decoded request (handler, method, path, query, session)."""

    def __init__(self, handler, method, path, query, session, ctx):
        self.handler = handler
        self.method = method
        self.path = path
        self.query = query
        self.session = session
        self.ctx = ctx

    # ---- HTTP (delegation to handler) ----

    def send_json(self, status, payload, extra_headers=None):
        self.handler.send_json(status, payload, extra_headers)

    def redirect(self, location):
        self.handler.redirect(location)

    def send_static(self, filename):
        self.handler.send_static(filename)

    def send_file(self, base, filename):
        self.handler.send_file(base, filename)

    def send_brand_asset(self, filename):
        self.handler.send_brand_asset(filename)

    def send_static_yaml(self, filename):
        self.handler.send_static_yaml(filename)

    def read_json(self):
        return self.handler.read_json()

    def session_cookie(self, token, supprime=False):
        return self.handler._session_cookie(token, supprime)

    # ---- session guards ----

    def client_exige(self):
        session = self.session
        if self.ctx.users is None:
            return session or {"role": "client", "user_id": "", "email": "", "nom": ""}
        if session and session["role"] == "client":
            return session
        raise SessionError(401, "auth_requise", "Connectez-vous avec votre compte voyageur.")

    def admin_exige(self):
        session = self.session
        if self.ctx.users is None:
            # Default test-mode name, matching login-conseiller:
            # every decision stays signed "Conseiller DÉTOUR".
            return session or {"role": "conseiller", "user_id": "", "email": "",
                               "nom": "Conseiller DÉTOUR"}
        if session and session["role"] == "conseiller":
            return session
        raise SessionError(401, "auth_requise", "Accès conseiller requis.")

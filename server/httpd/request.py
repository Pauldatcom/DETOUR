"""View of a request passed to route functions."""


class Request:
    """Decoded request (handler, method, path, query, team)."""

    def __init__(self, handler, method, path, query, ctx):
        self.handler = handler
        self.method = method
        self.path = path
        self.query = query
        self.ctx = ctx
        self.team = None

    # ---- HTTP (delegation to handler) ----

    def send_json(self, status, payload, extra_headers=None):
        self.handler.send_json(status, payload, extra_headers)

    def send_dashboard_asset(self, filename, content_type):
        self.handler.send_dashboard_asset(filename, content_type)

    def send_brand_asset(self, filename):
        self.handler.send_brand_asset(filename)

    def read_json(self):
        return self.handler.read_json()

    def dashboard_cookie(self):
        return self.handler.dashboard_cookie()

    def session_cookie_header(self, token, max_age):
        return self.handler.session_cookie_header(token, max_age)

    def require_same_origin(self):
        self.handler.require_same_origin()

    # ---- domain guards ----

    def dashboard_team(self):
        return self.ctx.store.dashboard_team(self.dashboard_cookie())

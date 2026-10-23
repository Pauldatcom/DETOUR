"""HTTP errors shared by the router and the routes."""


class ApiError(Exception):
    """Expected error, converted to a JSON response {status, code, message}."""

    def __init__(self, status, code, message):
        super().__init__(message)
        self.status, self.code, self.message = status, code, message


class SessionError(Exception):
    """Session missing or insufficient for the requested route."""

    def __init__(self, status, code, message):
        super().__init__(message)
        self.status, self.code, self.message = status, code, message

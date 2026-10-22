"""HTTP router: decentralized registry of API routes.

Each business module registers its own routes with a decorator,
mirroring the feature folders of a Next.js app (App Router).
"""

import re


class Route:
    """A registered route: method + regex pattern + handler function."""

    __slots__ = ("method", "pattern", "regex", "func")

    def __init__(self, method, pattern, regex, func):
        self.method = method
        self.pattern = pattern
        self.regex = regex
        self.func = func


class Router:
    """Route registry. Business modules register on it at import time."""

    def __init__(self):
        self._routes = []

    def route(self, method, pattern):
        """Decorator: registers a route function.

        The pattern is a full regex (fullmatch), e.g.:
            @router.route("GET", r"/api/demandes/(?P<id>dem_[a-f0-9]+)")
        Named groups become named arguments of the handler.
        """
        regex = re.compile(pattern)
        if regex.groups > 0 and not regex.groupindex:
            raise ValueError(
                f"Route {method} {pattern}: named groups required (?P<id>...)")

        def decorateur(func):
            self._routes.append(Route(method, pattern, regex, func))
            return func

        return decorateur

    def resoudre(self, method, path):
        """Find the matching route. Returns (func, params) or (None, None)."""
        for route in self._routes:
            if route.method != method:
                continue
            match = route.regex.fullmatch(path)
            if match:
                return route.func, match.groupdict()
        return None, None

    @property
    def routes(self):
        return list(self._routes)

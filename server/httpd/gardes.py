"""Access guard for the supplier API.

The historical router checked credentials before route resolution:
- a POST to the instructor routes requires ``X-Instructor-Key``;
- every other ``/api/v1/`` path requires ``X-Team-Key``;
- dashboard and health routes handle their own authentication.
"""

import re

INSTRUCTOR_ROUTE = re.compile(
    r"/api/v1/instructor/teams/(?P<team>[a-zA-Z0-9_-]+)/(?P<action>incidents|reset)")


def verifier_acces(req, method, path):
    """Raise an ApiError when the request lacks the required credential."""
    if method == "POST" and INSTRUCTOR_ROUTE.fullmatch(path):
        req.ctx.store.require_instructor(req.handler.headers.get("X-Instructor-Key"))
        return
    if path.startswith("/api/v1/"):
        req.team = req.ctx.store.team_for_key(req.handler.headers.get("X-Team-Key"))

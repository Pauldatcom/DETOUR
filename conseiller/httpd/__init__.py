"""Mécanique HTTP partagée : erreurs, sessions, handler et contexte de requête."""

from .context import Context, WEB_ROOT
from .errors import ApiError, SessionError
from .handler import HttpHandler
from .request import Request
from .sessions import SessionManager, nom_conseiller

__all__ = [
    "ApiError",
    "Context",
    "HttpHandler",
    "Request",
    "SessionError",
    "SessionManager",
    "WEB_ROOT",
    "nom_conseiller",
]

"""In-memory sessions (tokens) and advisor naming utilities."""

import secrets
import threading

from http.cookies import SimpleCookie

from utils import SESSION_COOKIE, SESSION_MAX


def nom_conseiller(session):
    """Name of the advisor who decides. Never empty: a decision is signed."""
    if isinstance(session, dict):
        nom = session.get("nom")
        if isinstance(nom, str) and nom.strip():
            return nom.strip()
    return "conseiller"


class SessionManager:
    """Registry of active sessions, protected for server threads."""

    def __init__(self):
        self._sessions = {}
        self._lock = threading.Lock()

    def creer(self, role, user_id="", email="", nom=""):
        token = secrets.token_hex(24)
        with self._lock:
            if len(self._sessions) > SESSION_MAX:
                self._sessions.clear()
            self._sessions[token] = {"role": role, "user_id": user_id, "email": email, "nom": nom}
        return token

    def supprimer(self, token):
        with self._lock:
            self._sessions.pop(token, None)

    def lire(self, token):
        if not token:
            return None
        with self._lock:
            entree = self._sessions.get(token)
            return dict(entree) if entree else None

    def depuis_cookie(self, headers):
        cookies = SimpleCookie()
        cookies.load(headers.get("Cookie", "") or "")
        morsel = cookies.get(SESSION_COOKIE)
        return self.lire(morsel.value) if morsel else None

    def token_depuis_cookie(self, headers):
        cookies = SimpleCookie()
        cookies.load(headers.get("Cookie", "") or "")
        morsel = cookies.get(SESSION_COOKIE)
        return morsel.value if morsel else ""

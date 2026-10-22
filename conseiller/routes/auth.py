"""Authentication routes: session, traveler accounts, advisor key, Google OAuth."""

import base64
import hashlib
import json
import os
import secrets
import threading
import time
import urllib.parse
import urllib.request

from utils import GOOGLE_OAUTH_URL, GOOGLE_TOKEN_URL, GOOGLE_USERINFO_URL

from httpd.errors import ApiError


class EtatsOAuth:
    """PKCE states awaiting the Google callback (protected for threads)."""

    def __init__(self):
        self._states = {}
        self._lock = threading.Lock()

    def creer(self, verifier):
        state = secrets.token_hex(16)
        with self._lock:
            self._states[state] = {"verifier": verifier, "ts": time.time()}
        return state

    def pop(self, state):
        with self._lock:
            return self._states.pop(state, None)


def session(req):
    session = req.session
    if session:
        return req.send_json(200, {"connecte": True, "role": session["role"],
                                   "nom": session.get("nom", "")})
    if req.ctx.users is None:  # test/dev: access without an account
        return req.send_json(200, {"connecte": True, "role": "client", "nom": ""})
    return req.send_json(200, {"connecte": False})


def logout(req):
    if req.session:
        req.ctx.sessions.supprimer(
            req.ctx.sessions.token_depuis_cookie(req.handler.headers))
    req.send_json(200, {"deconnecte": True},
                  extra_headers=req.session_cookie("", supprime=True))


def login(req):
    users = req.ctx.users
    if users is None:
        raise ApiError(503, "auth_desactivee", "Portail non configuré (users).")
    data = req.read_json()
    compte = users.authentifier(data.get("email"), data.get("mot_de_passe"))
    if compte is None:
        raise ApiError(401, "identifiants_invalides", "E-mail ou mot de passe incorrect.")
    token = req.ctx.sessions.creer("client", user_id=compte["id"],
                                   email=compte["email"], nom=compte["nom"])
    req.send_json(200, {"session": {"role": "client", "nom": compte["nom"]}},
                  extra_headers=req.session_cookie(token))


def register(req):
    users = req.ctx.users
    if users is None:
        raise ApiError(503, "auth_desactivee", "Portail non configuré (users).")
    data = req.read_json()
    compte = users.creer(data.get("email"), data.get("nom"), data.get("mot_de_passe"))
    token = req.ctx.sessions.creer("client", user_id=compte["id"],
                                   email=compte["email"], nom=compte["nom"])
    req.send_json(201, {"session": {"role": "client", "nom": compte["nom"]}},
                  extra_headers=req.session_cookie(token))


def login_conseiller(req):
    data = req.read_json()
    cle = data.get("cle")
    if not isinstance(cle, str) or not cle or \
            not secrets.compare_digest(cle, req.ctx.team_key or ""):
        raise ApiError(401, "cle_invalide", "Clé d'accès incorrecte.")
    token = req.ctx.sessions.creer("conseiller", nom="Conseiller DÉTOUR")
    req.send_json(200, {"session": {"role": "conseiller", "nom": "Conseiller DÉTOUR"}},
                  extra_headers=req.session_cookie(token))


def google(req):
    client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
    if not client_id:
        raise ApiError(503, "google_oauth_desactivee",
                       "Google OAuth non configuré (GOOGLE_CLIENT_ID).")
    redirect_uri = os.environ.get(
        "GOOGLE_REDIRECT_URI",
        f"http://127.0.0.1:{req.handler.server.server_port}/api/auth/google/callback")
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("ascii").rstrip("=")
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode("ascii")).digest()
    ).decode("ascii").rstrip("=")
    state = req.ctx.oauth_states.creer(code_verifier)
    params = urllib.parse.urlencode({
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "state": state,
    })
    req.redirect(f"{GOOGLE_OAUTH_URL}?{params}")


def google_callback(req):
    client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        raise ApiError(503, "google_oauth_desactivee", "Google OAuth non configuré.")
    code = req.query.get("code", [None])[0]
    state = req.query.get("state", [None])[0]
    if not code or not state:
        raise ApiError(400, "oauth_invalid", "Code ou state manquant.")
    state_data = req.ctx.oauth_states.pop(state)
    if not state_data:
        raise ApiError(400, "oauth_state_invalide", "State OAuth invalide ou expiré.")
    redirect_uri = os.environ.get(
        "GOOGLE_REDIRECT_URI",
        f"http://127.0.0.1:{req.handler.server.server_port}/api/auth/google/callback")
    token_payload = urllib.parse.urlencode({
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
        "code_verifier": state_data["verifier"],
    }).encode("utf-8")
    token_req = urllib.request.Request(GOOGLE_TOKEN_URL, data=token_payload,
                                       headers={"Content-Type": "application/x-www-form-urlencoded"},
                                       method="POST")
    with urllib.request.urlopen(token_req, timeout=10) as resp:
        tokens = json.loads(resp.read())
    access_token = tokens.get("access_token", "")
    if not access_token:
        raise ApiError(502, "oauth_token_error", "Google n'a pas renvoyé de token.")
    userinfo_req = urllib.request.Request(GOOGLE_USERINFO_URL,
                                          headers={"Authorization": f"Bearer {access_token}"})
    with urllib.request.urlopen(userinfo_req, timeout=10) as resp2:
        userinfo = json.loads(resp2.read())
    google_sub = str(userinfo.get("sub", ""))
    email = userinfo.get("email", "")
    nom = userinfo.get("name", "") or userinfo.get("given_name", "")
    if not google_sub or not email:
        raise ApiError(502, "oauth_userinfo_error", "Google n'a pas renvoyé sub ou email.")
    users = req.ctx.users
    if users is None:
        raise ApiError(503, "auth_desactivee", "Portail non configuré (users).")
    compte = users.creer_ou_lier_google(email, nom, google_sub)
    token = req.ctx.sessions.creer("client", user_id=compte["id"],
                                   email=compte["email"], nom=compte["nom"])
    req.send_json(200, {"session": {"role": "client", "nom": compte["nom"]}},
                  extra_headers=req.session_cookie(token))


def enregistrer(router):
    router.route("GET", r"/api/session")(session)
    router.route("POST", r"/api/logout")(logout)
    router.route("POST", r"/api/login")(login)
    router.route("POST", r"/api/register")(register)
    router.route("POST", r"/api/login-conseiller")(login_conseiller)
    router.route("GET", r"/api/auth/google")(google)
    router.route("GET", r"/api/auth/google/callback")(google_callback)

#!/usr/bin/env python3
"""Parcours de demande client DÉTOUR : serveur HTTP stdlib, sans dépendance."""

import argparse
import base64
import hashlib
import json
import mimetypes
import os
import re
import secrets
import sys
import threading
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from http.cookies import SimpleCookie
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

from agent import Agent, DEFAULT_MODEL, OpenRouterError
from fournisseur import DEFAULT_URL, SupplierClient, SupplierError
from horaires import est_ouvert, fenetre_reponse
from lecture import (
    enrichir_propositions,
    marquer_a_revoir_si_ecart,
    proposition_avec_changements,
)
from propositions import PropositionError, PropositionStore

from store import DemandStore, ValidationError, criteres_depuis_demande
from traces import finaliser_et_persister
from users import UserStore, UserError
from utils import (DECISION_ACCEPTER, DECISION_CORRECTION, DECISION_REFUSER,
                   GOOGLE_OAUTH_URL, GOOGLE_TOKEN_URL, GOOGLE_USERINFO_URL,
                   PROP_STATUTS, SESSION_COOKIE, SESSION_MAX)

ROOT = Path(__file__).resolve().parent
WEB_ROOT = ROOT.parent / "web" / "dist"


def load_env_file(path=None):
    env_path = Path(path) if path else ROOT.parent / ".env"
    try:
        lines = env_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip("'\"")
        if key and key not in os.environ:
            os.environ[key] = value


class ApiError(Exception):
    def __init__(self, status, code, message):
        super().__init__(message)
        self.status, self.code, self.message = status, code, message


class SessionError(Exception):
    """Session absente ou insuffisante pour la route demandée."""

    def __init__(self, status, code, message):
        super().__init__(message)
        self.status, self.code, self.message = status, code, message


def make_handler(store, supplier=None, agent=None, users=None, team_key="",
                 propositions=None, traces_dir=None):
    """Construit le handler HTTP.

    - `users=None` : mode développement/tests, aucune authentification requise
      (comportement historique préservé).
    - `users=UserStore(...)` : portail actif — les pages et les routes
      protégées exigent une session (voyageur ou conseiller).
    - `propositions=None` : store de propositions en mémoire (mode tests).
    - `traces_dir` : dossier pour les traces agent expurgées (#5); None = pas d'écriture.
    """

    if propositions is None:
        propositions = PropositionStore(None)
    sessions = {}
    oauth_states = {}
    sessions_lock = threading.Lock()

    def session_creer(role, user_id="", email="", nom=""):
        token = secrets.token_hex(24)
        with sessions_lock:
            if len(sessions) > SESSION_MAX:
                sessions.clear()
            sessions[token] = {"role": role, "user_id": user_id, "email": email, "nom": nom}
        return token

    def session_supprimer(token):
        with sessions_lock:
            sessions.pop(token, None)

    def session_invalider_utilisateur(user_id, token_conserve=None):
        with sessions_lock:
            for t in [t for t, s in sessions.items()
                      if s.get("user_id") == user_id and t != token_conserve]:
                sessions.pop(t, None)

    def session_lire(token):
        if not token:
            return None
        with sessions_lock:
            entree = sessions.get(token)
            return dict(entree) if entree else None

    def client_depuis_cookie(headers):
        cookies = SimpleCookie()
        cookies.load(headers.get("Cookie", "") or "")
        morsel = cookies.get(SESSION_COOKIE)
        return session_lire(morsel.value) if morsel else None

    def client_exige(handler):
        """Retourne la session voyageur ou lève une erreur 401 selon le mode."""
        session = client_depuis_cookie(handler.headers)
        if users is None:
            return session or {"role": "client", "user_id": "", "email": "", "nom": ""}
        if session and session["role"] == "client":
            return session
        raise SessionError(401, "auth_requise", "Connectez-vous avec votre compte voyageur.")

    def admin_exige(handler):
        session = client_depuis_cookie(handler.headers)
        if users is None:
            # Match login-conseiller default so decisions always have an advisor name.
            return session or {
                "role": "conseiller", "user_id": "", "email": "", "nom": "Conseiller DÉTOUR",
            }
        if session and session["role"] == "conseiller":
            return session
        raise SessionError(401, "auth_requise", "Accès conseiller requis.")

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            print("%s %s" % (self.address_string(), format % args))

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
            path = ROOT / filename
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

        def _metrics(self, demand_store, prop_store):
            demandes = demand_store.lister()
            props = prop_store.lister()
            par_statut = {}
            for d in demandes:
                s = d.get("statut", "inconnu")
                par_statut[s] = par_statut.get(s, 0) + 1
            lignes = [
                "# HELP detour_demandes_total Nombre total de demandes",
                "# TYPE detour_demandes_total gauge",
                f"detour_demandes_total {len(demandes)}",
                "# HELP detour_propositions_total Nombre total de propositions",
                "# TYPE detour_propositions_total gauge",
                f"detour_propositions_total {len(props)}",
            ]
            for s, n in sorted(par_statut.items()):
                lignes.append(f'detour_demandes_par_statut{{statut="{s}"}} {n}')
            body = "\n".join(lignes) + "\n"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
            self.send_header("Content-Length", str(len(body.encode("utf-8"))))
            self.end_headers()
            self.wfile.write(body.encode("utf-8"))

        def do_GET(self):
            self._handle("GET")

        def do_POST(self):
            self._handle("POST")

        def do_PATCH(self):
            self._handle("PATCH")

        def _session_cookie(self, token, supprime=False):
            if supprime:
                valeur = f"{SESSION_COOKIE}=; Max-Age=0; Path=/; HttpOnly; SameSite=Strict"
            else:
                valeur = f"{SESSION_COOKIE}={token}; Path=/; HttpOnly; SameSite=Strict"
            return {"Set-Cookie": valeur}

        def _handle(self, method):
            try:
                parsed = urlparse(self.path)
                path, query = parsed.path, parse_qs(parsed.query)
                session = client_depuis_cookie(self.headers)

                # ---------- Pages ----------
                if method == "GET" and path == "/health":
                    return self.send_json(200, {"status": "ok", "simulation": True})

                if method == "GET" and path in ("/app.css", "/pages.js", "/pages-propositions.js",
                                                "/agent-widget.css", "/agent-widget.js"):
                    return self.send_static(path.lstrip("/"))
                if method == "GET" and path == "/app.js":
                    return self.send_static("app.js")

                if method == "GET" and path == "/login":
                    return self.send_static("login.html")

                if method == "GET" and path in ("/", "/index.html", "/chat"):
                    if users is not None:
                        if session and session["role"] == "conseiller":
                            return self.redirect("/conseiller")
                        if not (session and session["role"] == "client"):
                            return self.redirect("/login")
                    return self.send_static("chat.html")

                if method == "GET" and path == "/conseiller":
                    if users is not None:
                        if session and session["role"] == "client":
                            return self.redirect("/chat")
                        if not (session and session["role"] == "conseiller"):
                            return self.redirect("/login")
                    return self.send_static("conseiller.html")

                # ---------- React SPA (web/dist) ----------
                if method == "GET" and WEB_ROOT.exists() \
                        and not path.startswith("/api/") \
                        and path != "/metrics":
                    if path == "/":
                        index = WEB_ROOT / "index.html"
                        if index.exists():
                            return self.send_file(WEB_ROOT, "index.html")
                    asset = WEB_ROOT / path.lstrip("/")
                    if asset.exists() and asset.is_file():
                        return self.send_file(WEB_ROOT, path.lstrip("/"))
                    index = WEB_ROOT / "index.html"
                    if index.exists():
                        return self.send_file(WEB_ROOT, "index.html")

                if method == "GET" and path == "/metrics":
                    token_attendu = os.environ.get("METRICS_TOKEN", "")
                    if token_attendu:
                        recus = query.get("token", [])
                        auth = self.headers.get("Authorization", "")
                        bearer = auth.replace("Bearer ", "", 1) if auth.startswith("Bearer ") else ""
                        if not (recus and secrets.compare_digest(recus[0], token_attendu)) and \
                           not (bearer and secrets.compare_digest(bearer, token_attendu)):
                            raise ApiError(401, "metrics_forbidden", "Token métriques requis.")
                    return self._metrics(store, propositions)

                if not path.startswith("/api/"):
                    raise ApiError(404, "not_found", "Route inconnue.")

                # ---------- Config (public) ----------
                if method == "GET" and path == "/api/config":
                    return self.send_json(200, {
                        "simulation": True,
                        "agent_actif": bool(os.environ.get("OPENROUTER_API_KEY", "")),
                        "google_oauth": bool(os.environ.get("GOOGLE_CLIENT_ID", "")),
                        "model": os.environ.get("OPENROUTER_MODEL", DEFAULT_MODEL),
                    })

                # ---------- Advisor availability (#48, #53) ----------
                if method == "GET" and path == "/api/disponibilite":
                    maintenant = datetime.now(timezone.utc)
                    return self.send_json(200, {
                        "simulation": True,
                        "ouvert": est_ouvert(maintenant),
                        "fenetre": fenetre_reponse(maintenant),
                    })

                # ---------- Authentification ----------
                if method == "GET" and path == "/api/session":
                    if session:
                        return self.send_json(200, {"connecte": True, "role": session["role"],
                                                    "nom": session.get("nom", ""),
                                                    "email": session.get("email", "")})
                    if users is None:  # tests/dev mode: access without account
                        return self.send_json(200, {"connecte": True, "role": "client", "nom": ""})
                    return self.send_json(200, {"connecte": False})

                if method == "POST" and path == "/api/logout":
                    if session:
                        session_supprimer(_token_depuis_cookie(self.headers))
                    return self.send_json(200, {"deconnecte": True},
                                           extra_headers=self._session_cookie("", supprime=True))

                if users is None:
                    pass  # mode tests : les routes ci-dessous restent ouvertes
                elif path in ("/api/login", "/api/register", "/api/login-conseiller",
                              "/api/auth/google", "/api/auth/google/callback"):
                    pass  # routes publiques d'authentification
                else:
                    admin = session and session["role"] == "conseiller"
                    client = session and session["role"] == "client"

                    if path in ("/api/mes-demandes", "/api/mes-propositions",
                                "/api/account", "/api/account/password"):
                        if not client:
                            raise ApiError(401, "auth_requise", "Connectez-vous avec un compte voyageur.")
                    elif method == "POST" and path == "/api/demandes":
                        if not client:
                            raise ApiError(401, "auth_requise", "Connectez-vous pour envoyer une demande.")
                    elif path in ("/api/stats", "/api/propositions") and method == "GET":
                        if not admin:
                            raise ApiError(401, "auth_requise", "Accès conseiller requis.")
                    elif method == "GET" and (m := re.fullmatch(r"/api/demandes/(dem_[a-f0-9]+)", path)):
                        if not (admin or (client and _proprietaire(store, m.group(1), session))):
                            raise ApiError(404, "demande_not_found", "Demande introuvable.")
                    elif method == "GET" and (m := re.fullmatch(r"/api/propositions/(prop_[a-f0-9]+)", path)):
                        if not (admin or (client and _proprietaire_proposition(propositions, store, m.group(1), session))):
                            raise ApiError(404, "proposition_not_found", "Proposition introuvable.")
                    elif method == "POST" and (m2 := re.fullmatch(r"/api/demandes/(dem_[a-f0-9]+)/recherche", path)):
                        if not (admin or (client and _proprietaire(store, m2.group(1), session))):
                            raise ApiError(401, "auth_requise", "Connectez-vous pour relancer une recherche.")
                    elif method == "POST" and (m2 := re.fullmatch(r"/api/demandes/(dem_[a-f0-9]+)/propositions(?:/generer)?", path)):
                        if not admin:
                            raise ApiError(401, "auth_requise", "Accès conseiller requis.")
                    elif method == "POST" and re.fullmatch(
                            r"/api/propositions/(prop_[a-f0-9]+)/decisions", path):
                        if not admin:
                            raise ApiError(401, "auth_requise", "Accès conseiller requis.")
                    elif method == "POST" and re.fullmatch(
                            r"/api/propositions/(prop_[a-f0-9]+)/(accepter|correction|refuser)", path):
                        if not admin:
                            raise ApiError(401, "auth_requise", "Accès conseiller requis.")
                    elif method == "PATCH":
                        if not admin:
                            raise ApiError(401, "auth_requise", "Accès conseiller requis.")
                    else:
                        if not (admin or client):
                            raise ApiError(401, "auth_requise", "Authentification requise.")

                if method == "POST" and path == "/api/login":
                    if users is None:
                        raise ApiError(503, "auth_desactivee", "Portail non configuré (users).")
                    data = self.read_json()
                    email = data.get("email")
                    mot_de_passe = data.get("mot_de_passe")
                    compte = users.authentifier(email, mot_de_passe)
                    if compte is None:
                        raise ApiError(401, "identifiants_invalides",
                                        "E-mail ou mot de passe incorrect.")
                    token = session_creer("client", user_id=compte["id"],
                                          email=compte["email"], nom=compte["nom"])
                    return self.send_json(200, {"session": {"role": "client", "nom": compte["nom"]}},
                                          extra_headers=self._session_cookie(token))

                if method == "POST" and path == "/api/register":
                    if users is None:
                        raise ApiError(503, "auth_desactivee", "Portail non configuré (users).")
                    data = self.read_json()
                    compte = users.creer(data.get("email"), data.get("nom"), data.get("mot_de_passe"))
                    token = session_creer("client", user_id=compte["id"],
                                          email=compte["email"], nom=compte["nom"])
                    return self.send_json(201, {"session": {"role": "client", "nom": compte["nom"]}},
                                          extra_headers=self._session_cookie(token))

                if method == "POST" and path == "/api/login-conseiller":
                    data = self.read_json()
                    cle = data.get("cle")
                    if not isinstance(cle, str) or not cle or not secrets.compare_digest(cle, team_key or ""):
                        raise ApiError(401, "cle_invalide", "Clé d'accès incorrecte.")
                    token = session_creer("conseiller", nom="Conseiller DÉTOUR")
                    return self.send_json(200, {"session": {"role": "conseiller", "nom": "Conseiller DÉTOUR"}},
                                          extra_headers=self._session_cookie(token))

                # ---------- Google OAuth (PKCE) ----------
                if method == "GET" and path == "/api/auth/google":
                    client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
                    if not client_id:
                        raise ApiError(503, "google_oauth_desactivee",
                                       "Google OAuth non configuré (GOOGLE_CLIENT_ID).")
                    redirect_uri = os.environ.get(
                        "GOOGLE_REDIRECT_URI",
                        f"http://127.0.0.1:{self.server.server_port}/api/auth/google/callback")
                    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("ascii").rstrip("=")
                    code_challenge = base64.urlsafe_b64encode(
                        hashlib.sha256(code_verifier.encode("ascii")).digest()
                    ).decode("ascii").rstrip("=")
                    state = secrets.token_hex(16)
                    with sessions_lock:
                        oauth_states[state] = {"verifier": code_verifier, "ts": time.time()}
                    params = urlencode({
                        "client_id": client_id,
                        "redirect_uri": redirect_uri,
                        "response_type": "code",
                        "scope": "openid email profile",
                        "code_challenge": code_challenge,
                        "code_challenge_method": "S256",
                        "state": state,
                    })
                    return self.redirect(f"{GOOGLE_OAUTH_URL}?{params}")

                if method == "GET" and path == "/api/auth/google/callback":
                    client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
                    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET", "")
                    if not client_id or not client_secret:
                        raise ApiError(503, "google_oauth_desactivee",
                                       "Google OAuth non configuré.")
                    code = query.get("code", [None])[0]
                    state = query.get("state", [None])[0]
                    if not code or not state:
                        raise ApiError(400, "oauth_invalid", "Code ou state manquant.")
                    with sessions_lock:
                        state_data = oauth_states.pop(state, None)
                    if not state_data:
                        raise ApiError(400, "oauth_state_invalide", "State OAuth invalide ou expiré.")
                    redirect_uri = os.environ.get(
                        "GOOGLE_REDIRECT_URI",
                        f"http://127.0.0.1:{self.server.server_port}/api/auth/google/callback")
                    token_payload = urlencode({
                        "code": code,
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "redirect_uri": redirect_uri,
                        "grant_type": "authorization_code",
                        "code_verifier": state_data["verifier"],
                    }).encode("utf-8")
                    req = urllib.request.Request(GOOGLE_TOKEN_URL, data=token_payload,
                                                 headers={"Content-Type": "application/x-www-form-urlencoded"},
                                                 method="POST")
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        tokens = json.loads(resp.read())
                    access_token = tokens.get("access_token", "")
                    if not access_token:
                        raise ApiError(502, "oauth_token_error", "Google n'a pas renvoyé de token.")
                    req2 = urllib.request.Request(GOOGLE_USERINFO_URL,
                                                  headers={"Authorization": f"Bearer {access_token}"})
                    with urllib.request.urlopen(req2, timeout=10) as resp2:
                        userinfo = json.loads(resp2.read())
                    google_sub = str(userinfo.get("sub", ""))
                    email = userinfo.get("email", "")
                    nom = userinfo.get("name", "") or userinfo.get("given_name", "")
                    if not google_sub or not email:
                        raise ApiError(502, "oauth_userinfo_error",
                                       "Google n'a pas renvoyé sub ou email.")
                    if users is None:
                        raise ApiError(503, "auth_desactivee", "Portail non configuré (users).")
                    compte = users.creer_ou_lier_google(email, nom, google_sub)
                    token = session_creer("client", user_id=compte["id"],
                                          email=compte["email"], nom=compte["nom"])
                    return self.send_json(200, {"session": {"role": "client", "nom": compte["nom"]}},
                                          extra_headers=self._session_cookie(token))

                # ---------- API ----------
                if method == "GET" and path == "/api/mes-demandes":
                    session = client_exige(self)
                    demandes = [d for d in store.lister()
                                if d.get("demande", {}).get("user_id") == session.get("user_id")]
                    demandes.sort(key=lambda d: d.get("cree_le", ""), reverse=True)
                    if users is not None:
                        for d in demandes:
                            d["client"] = users.obtenir(d.get("demande", {}).get("user_id", ""))
                    return self.send_json(200, {"demandes": demandes, "simulation": True})

                if method == "GET" and path == "/api/account":
                    session = client_exige(self)
                    if users is None:
                        raise ApiError(503, "auth_desactivee", "Portail non configuré (users).")
                    compte = users.obtenir(session.get("user_id", ""))
                    if compte is None:
                        raise UserError("Compte introuvable.", 404, "compte_introuvable")
                    compte["mot_de_passe_defini"] = users.mot_de_passe_defini(session["user_id"])
                    return self.send_json(200, {"compte": compte})

                if method == "GET" and path == "/api/catalogue":
                    if supplier is None:
                        raise ApiError(503, "supplier_not_configured", "Serveur fictif non configuré.")
                    prestations = supplier.catalogue()
                    return self.send_json(200, {"prestations": prestations, "simulation": True})

                if method == "GET" and path == "/api/demandes":
                    admin_exige(self)
                    demandes = store.lister()
                    demandes.sort(key=lambda d: d.get("cree_le", ""), reverse=True)
                    if users is not None:
                        for d in demandes:
                            d["client"] = users.obtenir(d.get("demande", {}).get("user_id", ""))
                    return self.send_json(200, {"demandes": demandes, "simulation": True})

                if method == "GET":
                    match = re.fullmatch(r"/api/demandes/(dem_[a-f0-9]+)", path)
                    if match:
                        record = store.obtenir(match.group(1))
                        if not record:
                            raise ApiError(404, "demande_not_found", "Demande introuvable.")
                        return self.send_json(200, {"demande": record, "simulation": True})

                if method == "POST":
                    match = re.fullmatch(r"/api/demandes/(dem_[a-f0-9]+)/recherche", path)
                    if match:
                        record = store.obtenir(match.group(1))
                        if not record:
                            raise ApiError(404, "demande_not_found", "Demande introuvable.")
                        if supplier is None:
                            raise ApiError(503, "supplier_not_configured", "Serveur fictif non configuré.")
                        resultat = supplier.rechercher(criteres_depuis_demande(record))
                        recherche = store.ajouter_recherche(match.group(1), resultat)
                        # Re-read may expose a delta vs proposal v1; never rewrite v1.
                        marquer_a_revoir_si_ecart(
                            store, propositions, match.group(1), recherche)
                        dem = store.obtenir(match.group(1))
                        return self.send_json(201, {
                            "recherche": recherche,
                            "demande": dem,
                            "simulation": True,
                        })

                if method == "PATCH":
                    if path == "/api/account":
                        session = client_exige(self)
                        if users is None:
                            raise ApiError(503, "auth_desactivee", "Portail non configuré (users).")
                        data = self.read_json()
                        if users.mot_de_passe_defini(session.get("user_id", "")):
                            if not users.verifier_mot_de_passe(
                                    session.get("user_id", ""),
                                    data.get("mot_de_passe_actuel", "")):
                                raise UserError("Le mot de passe actuel est incorrect.",
                                                401, "mot_de_passe_actuel_invalide")
                        compte = users.mettre_a_jour_profil(
                            session.get("user_id", ""), data.get("email"), data.get("nom"))
                        compte["mot_de_passe_defini"] = users.mot_de_passe_defini(session["user_id"])
                        token = _token_depuis_cookie(self.headers)
                        with sessions_lock:
                            session_stockee = sessions.get(token)
                            if session_stockee is not None:
                                session_stockee.update(email=compte["email"], nom=compte["nom"])
                        return self.send_json(200, {"compte": compte})

                    match = re.fullmatch(r"/api/demandes/(dem_[a-f0-9]+)/qualification", path)
                    if match:
                        session = admin_exige(self)
                        data = self.read_json()
                        record = store.definir_qualification(
                            match.group(1), data.get("qualification"), acteur="conseiller",
                            par=_nom_conseiller(session), motif=data.get("motif"))
                        if record is None:
                            raise ApiError(404, "demande_not_found", "Demande introuvable.")
                        if users is not None:
                            record["client"] = users.obtenir(record.get("demande", {}).get("user_id", ""))
                        return self.send_json(200, {"demande": record, "simulation": True})

                    match = re.fullmatch(r"/api/demandes/(dem_[a-f0-9]+)/correction", path)
                    if match:
                        # Only a logged-in advisor can correct a request; the agent cannot.
                        session = admin_exige(self)
                        data = self.read_json()
                        record = store.corriger(match.group(1), data.get("champs"),
                                                _nom_conseiller(session), data.get("motif"))
                        if record is None:
                            raise ApiError(404, "demande_not_found", "Request not found.")
                        if users is not None:
                            record["client"] = users.obtenir(record.get("demande", {}).get("user_id", ""))
                        return self.send_json(200, {"demande": record, "simulation": True})

                    match = re.fullmatch(r"/api/demandes/(dem_[a-f0-9]+)/statut", path)
                    if match:
                        session = admin_exige(self)
                        data = self.read_json()
                        record = store.changer_statut(match.group(1), data.get("statut"),
                                                     _nom_conseiller(session), data.get("motif"))
                        if record is None:
                            raise ApiError(404, "demande_not_found", "Demande introuvable.")
                        if users is not None:
                            record["client"] = users.obtenir(record.get("demande", {}).get("user_id", ""))
                        return self.send_json(200, {"demande": record, "simulation": True})

                if method == "POST" and path == "/api/chat":
                    if agent is None:
                        raise ApiError(503, "agent_not_configured",
                                       "Agent non configuré : définir OPENROUTER_API_KEY.")
                    session = client_exige(self)
                    data = self.read_json()
                    messages = data.get("messages")
                    if not isinstance(messages, list) or not 1 <= len(messages) <= 60:
                        raise ApiError(400, "invalid_messages",
                                       "messages doit être une liste de 1 à 60 messages.")
                    for message in messages:
                        if (not isinstance(message, dict)
                                or message.get("role") not in ("user", "assistant")
                                or not isinstance(message.get("content"), str)
                                or not message["content"].strip()):
                            raise ApiError(400, "invalid_messages",
                                           "Chaque message doit avoir un role (user ou assistant) et un content texte non vide.")
                    demande_id = data.get("demande_id")
                    if demande_id is not None and not (isinstance(demande_id, str)
                                                      and re.fullmatch(r"dem_[a-f0-9]+", demande_id)):
                        demande_id = None
                    result = agent.chat(
                        messages,
                        user_id=session.get("user_id", "") if isinstance(session, dict) else "",
                        demande_id=demande_id,
                    )
                    # #5: persist a redacted trace (also printed for local debug).
                    thread_id = demande_id or (result.get("demande") or {}).get("id")
                    result["trace"] = finaliser_et_persister(
                        result.get("trace") or {},
                        traces_dir,
                        request_id=thread_id or (result.get("trace") or {}).get("request_id"),
                        reponse_finale=result.get("reply") or "",
                    )
                    print("[agent] " + json.dumps(result["trace"], ensure_ascii=False), flush=True)

                    if thread_id and (result.get("reply") or "").strip():
                        historique = [dict(m) for m in messages]
                        historique.append({"role": "assistant", "content": result["reply"]})
                        try:
                            store.definir_messages(thread_id, historique)
                        except ValidationError:
                            pass
                    return self.send_json(200, {**result, "simulation": True})

                if method == "POST" and path == "/api/account/password":
                    session = client_exige(self)
                    if users is None:
                        raise ApiError(503, "auth_desactivee", "Portail non configuré (users).")
                    data = self.read_json()
                    users.changer_mot_de_passe(
                        session.get("user_id", ""),
                        data.get("mot_de_passe_actuel", ""),
                        data.get("nouveau_mot_de_passe"),
                    )
                    session_invalider_utilisateur(
                        session.get("user_id", ""),
                        _token_depuis_cookie(self.headers),
                    )
                    return self.send_json(200, {"mot_de_passe_modifie": True})

                if method == "POST" and path == "/api/demandes":
                    data = self.read_json()
                    if users is not None:
                        session = client_exige(self)
                        # Never trust a client-supplied owner id.
                        data["user_id"] = session.get("user_id", "")
                    record = store.creer(data)
                    return self.send_json(201, {"demande": record, "simulation": True})

                # ---------- Stats (conseiller) ----------
                if method == "GET" and path == "/api/stats":
                    admin_exige(self)
                    demandes = store.lister()
                    par_statut = {}
                    for d in demandes:
                        s = d.get("statut", "inconnu")
                        par_statut[s] = par_statut.get(s, 0) + 1
                    props = propositions.lister()
                    return self.send_json(200, {
                        "demandes_total": len(demandes),
                        "propositions_total": len(props),
                        "par_statut": par_statut,
                        "simulation": True,
                    })

                # ---------- Mes propositions (voyageur) ----------
                if method == "GET" and path == "/api/mes-propositions":
                    session = client_exige(self)
                    props = propositions.lister_par_user(session.get("user_id", ""), store)
                    props = enrichir_propositions(props, store)
                    props.sort(key=lambda p: p.get("cree_le", ""), reverse=True)
                    return self.send_json(200, {"propositions": props, "simulation": True})

                # ---------- Propositions (conseiller) ----------
                if method == "GET" and path == "/api/propositions":
                    admin_exige(self)
                    props = enrichir_propositions(propositions.lister(), store)
                    props.sort(key=lambda p: p.get("cree_le", ""), reverse=True)
                    return self.send_json(200, {"propositions": props, "simulation": True})

                if method == "GET":
                    match = re.fullmatch(r"/api/propositions/(prop_[a-f0-9]+)", path)
                    if match:
                        record = propositions.obtenir(match.group(1))
                        if not record:
                            raise ApiError(404, "proposition_not_found", "Proposition introuvable.")
                        enrichie = enrichir_propositions([record], store)[0]
                        return self.send_json(200, {"proposition": enrichie, "simulation": True})

                if method == "POST":
                    # Advisor decision on a proposal: accept, ask for a correction
                    # or reject. The reason is required for a correction and a
                    # rejection; accepting may go without one.
                    match_action = re.fullmatch(
                        r"/api/propositions/(prop_[a-f0-9]+)/(accepter|correction|refuser)", path)
                    if match_action:
                        session = admin_exige(self)
                        data = self.read_json()
                        action = {
                            "accepter": DECISION_ACCEPTER,
                            "correction": DECISION_CORRECTION,
                            "refuser": DECISION_REFUSER,
                        }[match_action.group(2)]
                        record = propositions.decider(
                            match_action.group(1), action,
                            _nom_conseiller(session),
                            data.get("motif"), data.get("instructions"))
                        if record is None:
                            raise ApiError(404, "proposition_not_found", "Proposition introuvable.")
                        dem = store.obtenir(record.get("demande_id", ""))
                        recherches = (dem or {}).get("recherches") or []
                        enrichie = proposition_avec_changements(record, recherches)
                        return self.send_json(200, {"proposition": enrichie, "simulation": True})

                    # Advisor keep/replace/drop on a changed line — no send, no option call.
                    match_dec = re.fullmatch(
                        r"/api/propositions/(prop_[a-f0-9]+)/decisions", path)
                    if match_dec:
                        session = admin_exige(self)
                        data = self.read_json()
                        record = propositions.enregistrer_decision(
                            match_dec.group(1),
                            data.get("prestation_id"),
                            data.get("choix"),
                            session.get("nom", ""),
                            data.get("motif"),
                            remplacement_id=data.get("remplacement_id"),
                        )
                        if record is None:
                            raise ApiError(404, "proposition_not_found", "Proposition introuvable.")
                        dem = store.obtenir(record.get("demande_id", ""))
                        recherches = (dem or {}).get("recherches") or []
                        enrichie = proposition_avec_changements(record, recherches)
                        # When every changed line has a decision, create draft v2.
                        recherche = recherches[-1] if recherches else None
                        prop_v2 = propositions.creer_v2_si_complet(
                            record["id"], recherche, conseiller=session.get("nom", ""))
                        payload = {"proposition": enrichie, "simulation": True}
                        if prop_v2 is not None:
                            payload["proposition_v2"] = prop_v2
                            # v1 must still be readable with its original prices.
                            payload["proposition"] = enrichir_propositions(
                                [propositions.obtenir(record["id"])], store)[0]
                        return self.send_json(200, payload)

                    match_gen = re.fullmatch(r"/api/demandes/(dem_[a-f0-9]+)/propositions/generer", path)
                    if match_gen:
                        record = store.obtenir(match_gen.group(1))
                        if not record:
                            raise ApiError(404, "demande_not_found", "Demande introuvable.")
                        if agent is None:
                            raise ApiError(503, "agent_not_configured",
                                           "Agent non configuré : définir OPENROUTER_API_KEY.")
                        recherches = record.get("recherches", [])
                        recherche = recherches[-1] if recherches else None
                        prop_data = agent.generer_proposition(record, recherche)
                        session = admin_exige(self)
                        prop = propositions.creer(match_gen.group(1), prop_data,
                                                  conseiller=session.get("nom", ""))
                        return self.send_json(201, {"proposition": prop, "simulation": True})

                    match = re.fullmatch(r"/api/demandes/(dem_[a-f0-9]+)/propositions", path)
                    if match:
                        record = store.obtenir(match.group(1))
                        if not record:
                            raise ApiError(404, "demande_not_found", "Demande introuvable.")
                        data = self.read_json()
                        session = admin_exige(self)
                        prop = propositions.creer(match.group(1), data,
                                                  conseiller=session.get("nom", ""))
                        return self.send_json(201, {"proposition": prop, "simulation": True})

                if method == "PATCH":
                    match = re.fullmatch(r"/api/propositions/(prop_[a-f0-9]+)/statut", path)
                    if match:
                        session = admin_exige(self)
                        data = self.read_json()
                        record = propositions.changer_statut(
                            match.group(1), data.get("statut"),
                            _nom_conseiller(session), data.get("motif"))
                        if record is None:
                            raise ApiError(404, "proposition_not_found", "Proposition introuvable.")
                        return self.send_json(200, {"proposition": record, "simulation": True})

                    match = re.fullmatch(r"/api/propositions/(prop_[a-f0-9]+)", path)
                    if match:
                        data = self.read_json()
                        record = propositions.mettre_a_jour(match.group(1), data)
                        if record is None:
                            raise ApiError(404, "proposition_not_found", "Proposition introuvable.")
                        return self.send_json(200, {"proposition": record, "simulation": True})

                raise ApiError(404, "not_found", "Route inconnue.")

            except SessionError as exc:
                self.send_json(exc.status, {"erreur": {"code": exc.code, "message": exc.message}})
            except (ValidationError, PropositionError) as exc:
                self.send_json(400, {"erreur": {"code": "validation_error", "message": str(exc)}})
            except UserError as exc:
                self.send_json(exc.status, {"erreur": {"code": exc.code, "message": str(exc)}})
            except ApiError as exc:
                self.send_json(exc.status, {"erreur": {"code": exc.code, "message": exc.message}})
            except SupplierError as exc:
                self.send_json(exc.status, {"erreur": {"code": "supplier_error", "message": str(exc)}})
            except OpenRouterError as exc:
                self.send_json(exc.status, {"erreur": {"code": "openrouter_error", "message": str(exc)}})
            except Exception:
                import traceback
                traceback.print_exc()
                self.send_json(500, {"erreur": {"code": "internal_error", "message": "Erreur interne."}})

    return Handler


def _nom_conseiller(session):
    """Nom du conseiller qui décide. Jamais vide : une décision est signée."""
    if isinstance(session, dict):
        nom = session.get("nom")
        if isinstance(nom, str) and nom.strip():
            return nom.strip()
    return "conseiller"


def _token_depuis_cookie(headers):
    cookies = SimpleCookie()
    cookies.load(headers.get("Cookie", "") or "")
    morsel = cookies.get(SESSION_COOKIE)
    return morsel.value if morsel else ""


def _proprietaire(store, dem_id, session):
    record = store.obtenir(dem_id)
    return bool(record) and record.get("demande", {}).get("user_id") == session.get("user_id")


def _proprietaire_proposition(prop_store, demand_store, prop_id, session):
    prop = prop_store.obtenir(prop_id)
    if not prop:
        return False
    dem = demand_store.obtenir(prop.get("demande_id", ""))
    return bool(dem) and dem.get("demande", {}).get("user_id") == session.get("user_id")


def main():
    parser = argparse.ArgumentParser(description="Parcours de demande client DÉTOUR")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--state-file", default=str(ROOT / ".local" / "demandes.json"))
    parser.add_argument("--users-file", default=str(ROOT / ".local" / "users.json"))
    parser.add_argument("--propositions-file", default=str(ROOT / ".local" / "propositions.json"))
    parser.add_argument("--traces-dir", default=str(ROOT / ".local" / "traces"),
                        help="Directory for redacted agent traces (#5).")
    parser.add_argument("--supplier-url", default=os.environ.get("TRAVEL_API_URL", DEFAULT_URL))
    args = parser.parse_args()

    load_env_file()
    store = DemandStore(args.state_file)
    users = UserStore(args.users_file)
    propositions = PropositionStore(args.propositions_file)
    team_key = os.environ.get("TRAVEL_TEAM_KEY", "demo-key")
    supplier = SupplierClient(args.supplier_url, team_key)
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    model = os.environ.get("OPENROUTER_MODEL", DEFAULT_MODEL)
    agent = Agent(supplier, store, api_key=api_key, model=model)
    server = ThreadingHTTPServer((args.host, args.port),
                                  make_handler(store, supplier, agent, users, team_key,
                                               propositions=propositions,
                                               traces_dir=args.traces_dir))
    print(f"Portail sur http://{args.host}:{server.server_port} "
          "(voyageur : /login · conseiller : clé TRAVEL_TEAM_KEY)", flush=True)
    print(f"Serveur de prestations : {args.supplier_url}", flush=True)
    print("Agent conversationnel : " + (f"actif (modèle {model})" if api_key
                                         else "désactivé — définir OPENROUTER_API_KEY dans .env"), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Parcours de demande client DÉTOUR : serveur HTTP stdlib, sans dépendance."""

import argparse
import json
import mimetypes
import os
import re
import secrets
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from http.cookies import SimpleCookie
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from agent import Agent, DEFAULT_MODEL, OpenRouterError
from fournisseur import DEFAULT_URL, SupplierClient, SupplierError
from store import DemandStore, ValidationError, criteres_depuis_demande
from users import UserStore, UserError
from utils import SESSION_COOKIE, SESSION_MAX

ROOT = Path(__file__).resolve().parent

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


def make_handler(store, supplier=None, agent=None, users=None, team_key=""):
    """Construit le handler HTTP.

    - `users=None` : mode développement/tests, aucune authentification requise
      (comportement historique préservé).
    - `users=UserStore(...)` : portail actif — les pages et les routes
      protégées exigent une session (voyageur ou conseiller).
    """

    sessions = {}
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
            return session or {"role": "conseiller", "user_id": "", "email": "", "nom": ""}
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

                if method == "GET" and path in ("/app.css", "/pages.js"):
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

                if not path.startswith("/api/"):
                    raise ApiError(404, "not_found", "Route inconnue.")

                # ---------- Authentification ----------
                if method == "POST" and path == "/api/logout":
                    if session:
                        session_supprimer(_token_depuis_cookie(self.headers))
                    return self.send_json(200, {"deconnecte": True},
                                           extra_headers=self._session_cookie("", supprime=True))

                if users is None:
                    pass  # mode tests : les routes ci-dessous restent ouvertes
                elif path == "/api/login" or path == "/api/register" or path == "/api/login-conseiller":
                    pass  # routes publiques d'authentification
                else:
                    admin = session and session["role"] == "conseiller"
                    client = session and session["role"] == "client"

                    if path == "/api/mes-demandes":
                        if not client:
                            raise ApiError(401, "auth_requise", "Connectez-vous pour voir vos demandes.")
                    elif path == "/api/demandes" and method == "GET":
                        if not admin:
                            raise ApiError(401, "auth_requise", "Accès conseiller requis.")
                    elif method == "GET" and (m := re.fullmatch(r"/api/demandes/(dem_[a-f0-9]+)", path)):
                        if not (admin or (client and _proprietaire(store, m.group(1), session))):
                            raise ApiError(404, "demande_not_found", "Demande introuvable.")
                    elif method == "POST" and (m2 := re.fullmatch(r"/api/demandes/(dem_[a-f0-9]+)/recherche", path)):
                        if not (admin or (client and _proprietaire(store, m2.group(1), session))):
                            raise ApiError(401, "auth_requise", "Connectez-vous pour relancer une recherche.")
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
                        return self.send_json(201, {"recherche": recherche, "simulation": True})

                if method == "PATCH":
                    match = re.fullmatch(r"/api/demandes/(dem_[a-f0-9]+)/qualification", path)
                    if match:
                        admin_exige(self)
                        data = self.read_json()
                        record = store.definir_qualification(
                            match.group(1), data.get("qualification"), acteur="conseiller")
                        if record is None:
                            raise ApiError(404, "demande_not_found", "Demande introuvable.")
                        if users is not None:
                            record["client"] = users.obtenir(record.get("demande", {}).get("user_id", ""))
                        return self.send_json(200, {"demande": record, "simulation": True})

                    match = re.fullmatch(r"/api/demandes/(dem_[a-f0-9]+)/statut", path)
                    if match:
                        data = self.read_json()
                        record = store.changer_statut(match.group(1), data.get("statut"))
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
                    result = agent.chat(messages, user_id=session.get("user_id", ""))
                    print("[agent] " + json.dumps(result["trace"], ensure_ascii=False), flush=True)

                    thread_id = demande_id or (result.get("demande") or {}).get("id")
                    if thread_id and (result.get("reply") or "").strip():
                        historique = [dict(m) for m in messages]
                        historique.append({"role": "assistant", "content": result["reply"]})
                        try:
                            store.definir_messages(thread_id, historique)
                        except ValidationError:
                            pass
                    return self.send_json(200, {**result, "simulation": True})

                if method == "POST" and path == "/api/demandes":
                    data = self.read_json()
                    record = store.creer(data)
                    return self.send_json(201, {"demande": record, "simulation": True})

                raise ApiError(404, "not_found", "Route inconnue.")

            except SessionError as exc:
                self.send_json(exc.status, {"erreur": {"code": exc.code, "message": exc.message}})
            except ValidationError as exc:
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


def _token_depuis_cookie(headers):
    cookies = SimpleCookie()
    cookies.load(headers.get("Cookie", "") or "")
    morsel = cookies.get(SESSION_COOKIE)
    return morsel.value if morsel else ""


def _proprietaire(store, dem_id, session):
    record = store.obtenir(dem_id)
    return bool(record) and record.get("demande", {}).get("user_id") == session.get("user_id")


def main():
    parser = argparse.ArgumentParser(description="Parcours de demande client DÉTOUR")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--state-file", default=str(ROOT / ".local" / "demandes.json"))
    parser.add_argument("--users-file", default=str(ROOT / ".local" / "users.json"))
    parser.add_argument("--supplier-url", default=os.environ.get("TRAVEL_API_URL", DEFAULT_URL))
    args = parser.parse_args()

    load_env_file()
    store = DemandStore(args.state_file)
    users = UserStore(args.users_file)
    team_key = os.environ.get("TRAVEL_TEAM_KEY", "demo-key")
    supplier = SupplierClient(args.supplier_url, team_key)
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    model = os.environ.get("OPENROUTER_MODEL", DEFAULT_MODEL)
    agent = Agent(supplier, store, api_key=api_key, model=model)
    server = ThreadingHTTPServer((args.host, args.port),
                                  make_handler(store, supplier, agent, users, team_key))
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

#!/usr/bin/env python3
"""API de prestations et réservations simulées, sans dépendances externes."""

import argparse
import copy
import json
import os
import re
import secrets
import ssl
import threading
from datetime import date, datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from http.cookies import CookieError, SimpleCookie
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from catalogue import BY_ID, PRESTATIONS


def utc_now():
    return datetime.now(timezone.utc)


def valid_date(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return False
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False


class ApiError(Exception):
    def __init__(self, status, code, message):
        super().__init__(message)
        self.status, self.code, self.message = status, code, message


class StateStore:
    def __init__(self, teams, instructor_key, path=None):
        self.teams = teams
        self.instructor_key = instructor_key
        self.path = Path(path) if path else None
        self.lock = threading.RLock()
        self.sessions = {}
        self.state = {"teams": {}}
        if self.path and self.path.exists():
            self.state = json.loads(self.path.read_text(encoding="utf-8"))
        for name in teams:
            self.state["teams"].setdefault(name, {"options": {}, "reservations": {}, "incidents": {}})

    def save(self):
        if not self.path:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.path.with_suffix(".tmp")
        temp_path.write_text(json.dumps(self.state, ensure_ascii=False, indent=2), encoding="utf-8")
        temp_path.replace(self.path)

    def team_for_key(self, supplied):
        if not supplied:
            raise ApiError(401, "team_key_missing", "En-tête X-Team-Key requis.")
        for name, credentials in self.teams.items():
            if secrets.compare_digest(supplied, credentials["key"]):
                return name
        raise ApiError(403, "team_key_invalid", "Clé d'équipe invalide.")

    def new_dashboard_session(self, supplied):
        if not isinstance(supplied, str) or not supplied:
            raise ApiError(400, "team_key_missing", "Saisissez une clé d'équipe.")
        team = self.team_for_key(supplied)
        token = secrets.token_urlsafe(32)
        with self.lock:
            self.sessions = {key: value for key, value in self.sessions.items()
                             if value[1] > utc_now()}
            self.sessions[token] = (team, utc_now() + timedelta(minutes=30))
        return token, team

    def dashboard_team(self, supplied):
        if not supplied:
            raise ApiError(401, "dashboard_login_required", "Connectez-vous avec la clé de votre équipe.")
        with self.lock:
            session = self.sessions.get(supplied)
            if not session or session[1] <= utc_now():
                self.sessions.pop(supplied, None)
                raise ApiError(401, "dashboard_session_expired", "Session expirée. Reconnectez-vous.")
            return session[0]

    def close_dashboard_session(self, supplied):
        with self.lock:
            self.sessions.pop(supplied, None)

    def require_approval(self, team, supplied):
        expected = self.teams[team]["approval_key"]
        if not supplied or not secrets.compare_digest(supplied, expected):
            raise ApiError(403, "human_approval_required", "Confirmation humaine requise : en-tête X-Approval-Key invalide ou absent.")

    def require_instructor(self, supplied):
        if not supplied or not secrets.compare_digest(supplied, self.instructor_key):
            raise ApiError(403, "instructor_key_invalid", "Clé formateur invalide ou absente.")

    def remaining(self, team, prestation_id, on_date):
        item = BY_ID[prestation_id]
        tstate = self.state["teams"][team]
        incident = tstate["incidents"].get(f"{prestation_id}|{on_date}", {})
        capacity = incident.get("capacite", item["capacite"])
        now = utc_now()
        held = sum(o["participants"] for o in tstate["options"].values()
                   if o["prestation_id"] == prestation_id and o["date"] == on_date
                   and o["statut"] == "active" and datetime.fromisoformat(o["expire_le"]) > now)
        booked = sum(r["participants"] for r in tstate["reservations"].values()
                     if r["prestation_id"] == prestation_id and r["date"] == on_date and r["statut"] == "confirmee")
        return max(0, capacity - held - booked), incident.get("prix_unitaire_eur", item["prix_unitaire_eur"])

    def availability(self, team, prestation_id, on_date, participants):
        if prestation_id not in BY_ID:
            raise ApiError(404, "prestation_not_found", "Prestation inconnue.")
        if not valid_date(on_date):
            raise ApiError(400, "invalid_date", "La date doit suivre le format AAAA-MM-JJ.")
        if type(participants) is not int or not 1 <= participants <= 20:
            raise ApiError(400, "invalid_participants", "participants doit être un entier de 1 à 20.")
        with self.lock:
            remaining, price = self.remaining(team, prestation_id, on_date)
        return {"prestation_id": prestation_id, "date": on_date, "participants": participants,
                "disponible": remaining >= participants, "places_restantes": remaining,
                "prix_unitaire_eur": price, "prix_total_eur": price * participants,
                "devise": "EUR", "simulation": True}

    def create_option(self, team, data):
        prestation_id, on_date, participants = data.get("prestation_id"), data.get("date"), data.get("participants")
        with self.lock:
            result = self.availability(team, prestation_id, on_date, participants)
            if not result["disponible"]:
                raise ApiError(409, "unavailable", "Places insuffisantes pour cette prestation.")
            option_id = "opt_" + secrets.token_hex(6)
            option = {"id": option_id, "prestation_id": prestation_id, "date": on_date,
                      "participants": participants, "prix_total_eur": result["prix_total_eur"],
                      "statut": "active", "expire_le": (utc_now() + timedelta(minutes=30)).isoformat(),
                      "simulation": True}
            self.state["teams"][team]["options"][option_id] = option
            self.save()
            return copy.deepcopy(option)

    def confirm(self, team, data, approval_key):
        self.require_approval(team, approval_key)
        option_id = data.get("option_id")
        approved_by = data.get("approuve_par")
        if not isinstance(approved_by, str) or not approved_by.strip() or len(approved_by) > 80:
            raise ApiError(400, "approval_identity_required", "approuve_par doit identifier la personne qui valide.")
        with self.lock:
            tstate = self.state["teams"][team]
            option = tstate["options"].get(option_id)
            if option is None:
                raise ApiError(404, "option_not_found", "Option inconnue dans cette équipe.")
            if option["statut"] != "active":
                raise ApiError(409, "option_not_active", "Cette option n'est plus active.")
            if datetime.fromisoformat(option["expire_le"]) <= utc_now():
                option["statut"] = "expiree"
                self.save()
                raise ApiError(409, "option_expired", "Cette option a expiré.")
            reservation_id = "res_" + secrets.token_hex(6)
            reservation = {"id": reservation_id, "option_id": option_id,
                           "prestation_id": option["prestation_id"], "date": option["date"],
                           "participants": option["participants"], "prix_total_eur": option["prix_total_eur"],
                           "statut": "confirmee", "approuve_par": approved_by.strip(),
                           "confirmee_le": utc_now().isoformat(), "simulation": True}
            option["statut"] = "confirmee"
            tstate["reservations"][reservation_id] = reservation
            self.save()
            return copy.deepcopy(reservation)

    def cancel(self, team, reservation_id, approval_key):
        self.require_approval(team, approval_key)
        with self.lock:
            reservation = self.state["teams"][team]["reservations"].get(reservation_id)
            if reservation is None:
                raise ApiError(404, "reservation_not_found", "Réservation inconnue dans cette équipe.")
            if reservation["statut"] != "confirmee":
                raise ApiError(409, "reservation_not_active", "Réservation déjà annulée.")
            reservation["statut"] = "annulee"
            reservation["annulee_le"] = utc_now().isoformat()
            self.save()
            return copy.deepcopy(reservation)

    def incident(self, team, data):
        prestation_id, on_date = data.get("prestation_id"), data.get("date")
        if team not in self.teams:
            raise ApiError(404, "team_not_found", "Équipe inconnue.")
        if prestation_id not in BY_ID:
            raise ApiError(404, "prestation_not_found", "Prestation inconnue.")
        if not valid_date(on_date):
            raise ApiError(400, "invalid_date", "Date invalide.")
        incident_type, value = data.get("type"), data.get("valeur")
        if incident_type not in ("capacite", "prix_unitaire_eur") or type(value) is not int or value < 0 or value > 10000:
            raise ApiError(400, "invalid_incident", "type doit être capacite ou prix_unitaire_eur ; valeur doit être un entier positif.")
        with self.lock:
            incident = self.state["teams"][team]["incidents"].setdefault(f"{prestation_id}|{on_date}", {})
            incident[incident_type] = value
            self.save()
            return {"equipe": team, "prestation_id": prestation_id, "date": on_date, **incident, "simulation": True}

    def reset_team(self, team):
        if team not in self.teams:
            raise ApiError(404, "team_not_found", "Équipe inconnue.")
        with self.lock:
            self.state["teams"][team] = {"options": {}, "reservations": {}, "incidents": {}}
            self.save()


def make_handler(store):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            print("%s %s" % (self.address_string(), fmt % args))

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

        def send_dashboard_asset(self, filename, content_type):
            body = (Path(__file__).parent / filename).read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; base-uri 'none'; form-action 'self'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(body)

        def dashboard_cookie(self):
            try:
                cookies = SimpleCookie()
                cookies.load(self.headers.get("Cookie", ""))
                return cookies["detour_session"].value if "detour_session" in cookies else None
            except CookieError:
                return None

        def session_cookie_header(self, token, max_age):
            secure = "; Secure" if isinstance(self.connection, ssl.SSLSocket) else ""
            return f"detour_session={token}; Path=/dashboard; Max-Age={max_age}; HttpOnly; SameSite=Strict{secure}"

        def require_same_origin(self):
            if self.headers.get("Sec-Fetch-Site") == "cross-site":
                raise ApiError(403, "origin_invalid", "Origine de la requête refusée.")
            origin = self.headers.get("Origin")
            if origin and urlparse(origin).netloc != self.headers.get("Host"):
                raise ApiError(403, "origin_invalid", "Origine de la requête refusée.")

        def handle_dashboard(self, path, query):
            assets = {
                "/dashboard": ("dashboard.html", "text/html; charset=utf-8"),
                "/dashboard/": ("dashboard.html", "text/html; charset=utf-8"),
                "/dashboard/dashboard.css": ("dashboard.css", "text/css; charset=utf-8"),
                "/dashboard/dashboard.js": ("dashboard.js", "text/javascript; charset=utf-8"),
            }
            if self.command == "GET" and path in assets:
                return self.send_dashboard_asset(*assets[path])
            if self.command == "POST" and path == "/dashboard/api/login":
                self.require_same_origin()
                supplied = self.read_json().get("team_key")
                token, team = store.new_dashboard_session(supplied)
                return self.send_json(200, {"equipe": team, "expire_dans_secondes": 1800},
                                      {"Set-Cookie": self.session_cookie_header(token, 1800)})
            if self.command == "POST" and path == "/dashboard/api/logout":
                self.require_same_origin()
                store.close_dashboard_session(self.dashboard_cookie())
                return self.send_json(200, {"deconnecte": True},
                                      {"Set-Cookie": self.session_cookie_header("", 0)})
            if self.command != "GET":
                raise ApiError(405, "method_not_allowed", "Le tableau de bord ne modifie pas les réservations.")
            team = store.dashboard_team(self.dashboard_cookie())
            if path == "/dashboard/api/me":
                return self.send_json(200, {"equipe": team, "simulation": True})
            if path == "/dashboard/api/catalogue":
                type_filter = query.get("type", [None])[0]
                destination_filter = query.get("destination", [None])[0]
                items = [copy.deepcopy(item) for item in PRESTATIONS
                         if (not type_filter or item["type"] == type_filter)
                         and (not destination_filter or item["destination"].casefold() == destination_filter.casefold())]
                return self.send_json(200, {"prestations": items, "simulation": True})
            item_match = re.fullmatch(r"/dashboard/api/prestations/([a-z0-9-]+)", path)
            if item_match:
                item = BY_ID.get(item_match.group(1))
                if not item:
                    raise ApiError(404, "prestation_not_found", "Prestation inconnue.")
                return self.send_json(200, {"prestation": item, "simulation": True})
            if path == "/dashboard/api/disponibilites":
                try:
                    participants = int(query.get("participants", [""])[0])
                except ValueError:
                    participants = None
                result = store.availability(team, query.get("prestation_id", [None])[0],
                                            query.get("date", [None])[0], participants)
                return self.send_json(200, result)
            if path == "/dashboard/api/options":
                with store.lock:
                    options = copy.deepcopy(list(store.state["teams"][team]["options"].values()))
                return self.send_json(200, {"options": options, "simulation": True})
            if path == "/dashboard/api/reservations":
                with store.lock:
                    reservations = copy.deepcopy(list(store.state["teams"][team]["reservations"].values()))
                return self.send_json(200, {"reservations": reservations, "simulation": True})
            raise ApiError(404, "not_found", "Route inconnue.")

        def read_json(self):
            length = self.headers.get("Content-Length", "0")
            try:
                length = int(length)
            except ValueError:
                raise ApiError(400, "invalid_body", "Content-Length invalide.")
            if not 0 < length <= 10000:
                raise ApiError(400, "invalid_body", "Corps JSON requis (10 Ko maximum).")
            try:
                data = json.loads(self.rfile.read(length))
            except (json.JSONDecodeError, UnicodeDecodeError):
                raise ApiError(400, "invalid_json", "JSON invalide.")
            if not isinstance(data, dict):
                raise ApiError(400, "invalid_json", "Un objet JSON est attendu.")
            return data

        def handle_request(self):
            try:
                parsed = urlparse(self.path)
                path, query = parsed.path, parse_qs(parsed.query)
                if self.command == "GET" and path == "/health":
                    return self.send_json(200, {"status": "ok", "simulation": True})
                if path == "/dashboard" or path.startswith("/dashboard/"):
                    return self.handle_dashboard(path, query)
                instructor_match = re.fullmatch(r"/api/v1/instructor/teams/([a-zA-Z0-9_-]+)/(incidents|reset)", path)
                if instructor_match and self.command == "POST":
                    store.require_instructor(self.headers.get("X-Instructor-Key"))
                    team, action = instructor_match.groups()
                    if action == "reset":
                        store.reset_team(team)
                        return self.send_json(200, {"equipe": team, "reinitialisee": True, "simulation": True})
                    return self.send_json(201, store.incident(team, self.read_json()))
                if not path.startswith("/api/v1/"):
                    raise ApiError(404, "not_found", "Route inconnue.")
                team = store.team_for_key(self.headers.get("X-Team-Key"))
                if self.command == "GET" and path == "/api/v1/catalogue":
                    type_filter = query.get("type", [None])[0]
                    destination_filter = query.get("destination", [None])[0]
                    items = [copy.deepcopy(item) for item in PRESTATIONS
                             if (not type_filter or item["type"] == type_filter)
                             and (not destination_filter or item["destination"].casefold() == destination_filter.casefold())]
                    return self.send_json(200, {"prestations": items, "simulation": True})
                item_match = re.fullmatch(r"/api/v1/prestations/([a-z0-9-]+)", path)
                if self.command == "GET" and item_match:
                    item = BY_ID.get(item_match.group(1))
                    if not item:
                        raise ApiError(404, "prestation_not_found", "Prestation inconnue.")
                    return self.send_json(200, {"prestation": item, "simulation": True})
                if self.command == "GET" and path == "/api/v1/disponibilites":
                    try:
                        participants = int(query.get("participants", [""])[0])
                    except ValueError:
                        participants = None
                    result = store.availability(team, query.get("prestation_id", [None])[0],
                                                query.get("date", [None])[0], participants)
                    return self.send_json(200, result)
                if self.command == "POST" and path == "/api/v1/options":
                    return self.send_json(201, {"option": store.create_option(team, self.read_json())})
                if self.command == "GET" and path == "/api/v1/options":
                    with store.lock:
                        options = copy.deepcopy(list(store.state["teams"][team]["options"].values()))
                    return self.send_json(200, {"options": options, "simulation": True})
                if self.command == "POST" and path == "/api/v1/reservations":
                    return self.send_json(201, {"reservation": store.confirm(team, self.read_json(), self.headers.get("X-Approval-Key"))})
                if self.command == "GET" and path == "/api/v1/reservations":
                    with store.lock:
                        reservations = copy.deepcopy(list(store.state["teams"][team]["reservations"].values()))
                    return self.send_json(200, {"reservations": reservations, "simulation": True})
                cancel_match = re.fullmatch(r"/api/v1/reservations/(res_[a-f0-9]+)/annuler", path)
                if self.command == "POST" and cancel_match:
                    return self.send_json(200, {"reservation": store.cancel(team, cancel_match.group(1), self.headers.get("X-Approval-Key"))})
                raise ApiError(404, "not_found", "Route inconnue.")
            except ApiError as exc:
                self.send_json(exc.status, {"erreur": {"code": exc.code, "message": exc.message}})
            except Exception:
                self.send_json(500, {"erreur": {"code": "internal_error", "message": "Erreur interne du serveur."}})

        do_GET = handle_request
        do_POST = handle_request

    return Handler


def load_teams(path, demo):
    if demo:
        return {"demo": {"key": "demo-key", "approval_key": "demo-approval"},
                "equipe-b": {"key": "equipe-b-key", "approval_key": "equipe-b-approval"}}
    if not path:
        raise SystemExit("Fournir --teams-file ou --demo.")
    teams = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(teams, dict) or not teams or any(not isinstance(v, dict) or not v.get("key") or not v.get("approval_key") for v in teams.values()):
        raise SystemExit("Fichier équipes invalide.")
    all_keys = [v[k] for v in teams.values() for k in ("key", "approval_key")]
    if len(all_keys) != len(set(all_keys)):
        raise SystemExit("Chaque clé doit être unique.")
    return teams


def main():
    parser = argparse.ArgumentParser(description="Serveur de réservations fictives WEB3")
    parser.add_argument("--demo", action="store_true", help="Deux équipes de démonstration avec clés connues")
    parser.add_argument("--teams-file", help="JSON des clés d'équipes (voir README)")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--state-file", default=str(Path(__file__).parent / ".local" / "state.json"))
    args = parser.parse_args()
    teams = load_teams(args.teams_file, args.demo)
    instructor_key = "demo-instructor" if args.demo else os.environ.get("INSTRUCTOR_KEY")
    if not instructor_key:
        raise SystemExit("Définir INSTRUCTOR_KEY pour les routes formateur.")
    store = StateStore(teams, instructor_key, args.state_file)
    server = ThreadingHTTPServer((args.host, args.port), make_handler(store))
    print(f"API fictive sur http://{args.host}:{server.server_port} : {len(teams)} équipe(s)", flush=True)
    print(f"Tableau de bord sur http://{args.host}:{server.server_port}/dashboard", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

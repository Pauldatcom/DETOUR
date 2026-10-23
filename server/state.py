"""Simulated supplier state: teams, options, reservations and incidents."""

import copy
import json
import re
import secrets
import threading
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from catalogue import BY_ID, MIS_A_JOUR_LE_BASE, PRESTATIONS

from httpd.errors import ApiError


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


class StateStore:
    def __init__(self, teams, instructor_key, path=None):
        self.teams = teams
        self.instructor_key = instructor_key
        self.path = Path(path) if path else None
        self.lock = threading.RLock()
        self.state = {"teams": {}}
        if self.path and self.path.exists():
            self.state = json.loads(self.path.read_text(encoding="utf-8"))
        self.state.setdefault("sessions", {})
        for name in teams:
            self.state["teams"].setdefault(name, {"options": {}, "reservations": {}, "incidents": {}})
        self._prune_sessions()

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

    def _prune_sessions(self):
        """Drop expired sessions. Call while holding the lock."""
        now = utc_now()
        self.state["sessions"] = {
            token: entree for token, entree in self.state["sessions"].items()
            if datetime.fromisoformat(entree["expire_le"]) > now
        }

    def new_dashboard_session(self, supplied):
        if not isinstance(supplied, str) or not supplied:
            raise ApiError(400, "team_key_missing", "Saisissez une clé d'équipe.")
        team = self.team_for_key(supplied)
        token = secrets.token_urlsafe(32)
        with self.lock:
            self._prune_sessions()
            self.state["sessions"][token] = {"equipe": team,
                                            "expire_le": (utc_now() + timedelta(minutes=30)).isoformat()}
            self.save()
        return token, team

    def dashboard_team(self, supplied):
        if not supplied:
            raise ApiError(401, "dashboard_login_required", "Connectez-vous avec la clé de votre équipe.")
        with self.lock:
            entree = self.state["sessions"].get(supplied)
            if not entree or datetime.fromisoformat(entree["expire_le"]) <= utc_now():
                if entree is not None:
                    self.state["sessions"].pop(supplied, None)
                    self.save()
                raise ApiError(401, "dashboard_session_expired", "Session expirée. Reconnectez-vous.")
            return entree["equipe"]

    def close_dashboard_session(self, supplied):
        with self.lock:
            if supplied and self.state["sessions"].pop(supplied, None) is not None:
                self.save()

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

    def updated_at(self, team, prestation_id, on_date):
        incident = self.state["teams"][team]["incidents"].get(f"{prestation_id}|{on_date}", {})
        return incident.get("mis_a_jour_le", MIS_A_JOUR_LE_BASE)

    def search(self, team, params):
        """Search prestations. Destination is a hard filter; other criteria are reported, not hidden."""
        destination = params.get("destination")
        if not isinstance(destination, str) or not destination.strip():
            raise ApiError(400, "invalid_destination", "destination est obligatoire.")
        date_depart, date_retour = params.get("date_depart"), params.get("date_retour")
        if not valid_date(date_depart):
            raise ApiError(400, "invalid_date", "date_depart doit suivre le format AAAA-MM-JJ.")
        if date_retour is not None and (not valid_date(date_retour) or date_retour < date_depart):
            raise ApiError(400, "invalid_date", "date_retour doit être une date AAAA-MM-JJ postérieure ou égale à date_depart.")
        participants = params.get("participants")
        if type(participants) is not int or not 1 <= participants <= 20:
            raise ApiError(400, "invalid_participants", "participants doit être un entier de 1 à 20.")
        budget = params.get("budget_max")
        if budget is not None and (type(budget) is not int or budget <= 0):
            raise ApiError(400, "invalid_budget", "budget_max doit être un entier positif (euros par personne).")
        type_voyage = params.get("type_voyage")
        activites = params.get("activites") or []
        results = []
        with self.lock:
            for item in PRESTATIONS:
                if item["destination"].casefold() != destination.strip().casefold():
                    continue
                remaining, price = self.remaining(team, item["id"], date_depart)
                results.append({
                    "id": item["id"], "nom": item["nom"], "type": item["type"],
                    "destination": item["destination"], "description": item["description"],
                    "tags": list(item["tags"]),
                    "prix_unitaire_eur": price, "prix_total_eur": price * participants,
                    "disponible": remaining >= participants, "places_restantes": remaining,
                    "mis_a_jour_le": self.updated_at(team, item["id"], date_depart),
                    "dans_budget": None if budget is None else price <= budget,
                    "correspond_type_voyage": None if not type_voyage else type_voyage in item["voyages"],
                    "activites_correspondantes": [a for a in activites if a in item["tags"]],
                })
        return {"source": "serveur-fictif-detour", "route": "/api/v1/recherche",
                "consulte_le": utc_now().isoformat(),
                "criteres": {"destination": destination.strip(), "date_depart": date_depart,
                             "date_retour": date_retour, "participants": participants,
                             "budget_max": budget, "type_voyage": type_voyage or None,
                             "activites": activites,
                             "date_verifiee": date_depart},
                "resultats": results, "simulation": True}

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
            incident["mis_a_jour_le"] = utc_now().isoformat()
            self.save()
            return {"equipe": team, "prestation_id": prestation_id, "date": on_date, **incident, "simulation": True}

    def reset_team(self, team):
        if team not in self.teams:
            raise ApiError(404, "team_not_found", "Équipe inconnue.")
        with self.lock:
            self.state["teams"][team] = {"options": {}, "reservations": {}, "incidents": {}}
            self.save()

    def list_options(self, team):
        with self.lock:
            return copy.deepcopy(list(self.state["teams"][team]["options"].values()))

    def list_reservations(self, team):
        with self.lock:
            return copy.deepcopy(list(self.state["teams"][team]["reservations"].values()))

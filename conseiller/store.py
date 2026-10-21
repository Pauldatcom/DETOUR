"""Persistance JSON des demandes client de DÉTOUR."""

import json
import re
import secrets
import threading
from datetime import datetime, timezone
from pathlib import Path

from utils import (ACTIVITES_POSSIBLES, NIVEAUX_AVENTURE, STATUTS,
                   STATUT_A_ANALYSER, TYPES_VOYAGE)

_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


def utc_now_iso():
    return datetime.now(timezone.utc).isoformat()


def _valid_date(value):
    if not isinstance(value, str) or not _DATE_RE.fullmatch(value):
        return False
    try:
        datetime.fromisoformat(value)
        return True
    except ValueError:
        return False


class ValidationError(ValueError):
    pass


def valider_demande(data):
    """Valide et normalise les champs d'une demande. Lève ValidationError si invalide."""
    if not isinstance(data, dict):
        raise ValidationError("Corps JSON attendu.")

    type_voyage = data.get("type_voyage")
    if type_voyage not in TYPES_VOYAGE:
        raise ValidationError(f"type_voyage doit être l'un de {', '.join(TYPES_VOYAGE)}.")

    destination = data.get("destination")
    if not isinstance(destination, str) or not destination.strip():
        raise ValidationError("destination est obligatoire.")
    destination = destination.strip()

    date_depart = data.get("date_depart")
    if not _valid_date(date_depart):
        raise ValidationError("date_depart au format AAAA-MM-JJ est obligatoire.")
    date_depart = str(date_depart)

    date_retour = data.get("date_retour")
    if not _valid_date(date_retour):
        raise ValidationError("date_retour au format AAAA-MM-JJ est obligatoire.")
    date_retour = str(date_retour)
    if date_retour < date_depart:
        raise ValidationError("date_retour doit être postérieure ou égale à date_depart.")

    nombre_voyageurs = data.get("nombre_voyageurs")
    if type(nombre_voyageurs) is not int or not 1 <= nombre_voyageurs <= 20:
        raise ValidationError("nombre_voyageurs doit être un entier de 1 à 20.")

    has_enfants = bool(data.get("has_enfants", False))
    nombre_enfants = data.get("nombre_enfants", 0)
    if type(nombre_enfants) is not int or not 0 <= nombre_enfants <= nombre_voyageurs:
        raise ValidationError("nombre_enfants doit être un entier de 0 au nombre de voyageurs.")

    budget = data.get("budget_max_par_personne")
    if type(budget) is not int or budget <= 0 or budget > 100000:
        raise ValidationError("budget_max_par_personne doit être un entier positif.")

    niveau = data.get("niveau_aventure")
    if niveau not in NIVEAUX_AVENTURE:
        raise ValidationError(f"niveau_aventure doit être l'un de {', '.join(NIVEAUX_AVENTURE)}.")

    besoin_guide = bool(data.get("besoin_guide", False))

    activites = data.get("activites", [])
    if not isinstance(activites, list):
        raise ValidationError("activites doit être une liste.")
    activites = [a for a in activites if isinstance(a, str) and a.strip()]
    activites = list(dict.fromkeys(activites))

    contraintes = data.get("contraintes", "")
    if not isinstance(contraintes, str):
        raise ValidationError("contraintes doit être une chaîne.")
    contraintes = contraintes.strip()

    conseiller = data.get("conseiller", "Non attribué")
    if not isinstance(conseiller, str):
        raise ValidationError("conseiller doit être une chaîne.")
    conseiller = conseiller.strip() or "Non attribué"

    souhaits = data.get("souhaits", "")
    if not isinstance(souhaits, str):
        raise ValidationError("souhaits doit être une chaîne.")
    souhaits = souhaits.strip()

    user_id = data.get("user_id", "")
    if not isinstance(user_id, str):
        raise ValidationError("user_id doit être une chaîne.")
    user_id = user_id.strip()

    return {
        "type_voyage": type_voyage,
        "destination": destination,
        "date_depart": date_depart,
        "date_retour": date_retour,
        "nombre_voyageurs": nombre_voyageurs,
        "has_enfants": has_enfants,
        "nombre_enfants": nombre_enfants,
        "budget_max_par_personne": budget,
        "niveau_aventure": niveau,
        "besoin_guide": besoin_guide,
        "activites": activites,
        "contraintes": contraintes,
        "conseiller": conseiller,
        "souhaits": souhaits,
        "user_id": user_id,
    }


class DemandStore:
    def __init__(self, path=None):
        self.path = Path(path) if path else None
        self.lock = threading.RLock()
        self.demandes = {}
        if self.path and self.path.exists():
            self.demandes = json.loads(self.path.read_text(encoding="utf-8"))

    def save(self):
        if not self.path:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.demandes, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.path)

    def creer(self, data):

        valide = valider_demande(data)
        with self.lock:
            dem_id = "dem_" + secrets.token_hex(6)
            record = {
                "id": dem_id,
                "statut": STATUT_A_ANALYSER,
                "cree_le": utc_now_iso(),
                "demande": valide,
            }
            self.demandes[dem_id] = record
            self.save()
            return json.loads(json.dumps(record))
    
    
    def create_draft(self, user_id, request_id=None):
        """Create or retrieve a client's travel request draft."""
        if not isinstance(user_id, str) or not user_id.strip():
            raise ValidationError("user_id is required.")

        user_id = user_id.strip()

        with self.lock:
            if request_id:
                record = self.demandes.get(request_id)

                if not record:
                    raise ValidationError("Draft not found.")

                existing_user_id = record.get("demande", {}).get("user_id")

                if existing_user_id != user_id:
                    raise ValidationError(
                        "This draft belongs to another client."
                    )

                return json.loads(json.dumps(record))

            request_id = "dem_" + secrets.token_hex(6)

            record = {
                "id": request_id,
                "statut": "brouillon",
                "cree_le": utc_now_iso(),
                "demande": {
                    "user_id": user_id
                },
                "messages": [],
            }

            self.demandes[request_id] = record
            self.save()

            return json.loads(json.dumps(record))


    def lister(self):
        with self.lock:
            return json.loads(json.dumps(list(self.demandes.values())))

    def obtenir(self, dem_id):
        with self.lock:
            record = self.demandes.get(dem_id)
            return json.loads(json.dumps(record)) if record else None

    def get_draft(self, request_id, user_id):
        """Retrieve a draft only if it belongs to the requesting client."""
        if not isinstance(user_id, str) or not user_id.strip():
            raise ValidationError("user_id is required.")

        with self.lock:
            record = self.demandes.get(request_id)

            if not record:
                raise ValidationError("Draft not found.")

            request_data = record.get("demande", {})

            if request_data.get("user_id") != user_id.strip():
                raise ValidationError("This draft belongs to another client.")

            if record.get("statut") != "brouillon":
                raise ValidationError("This request is not a draft.")

            return json.loads(json.dumps(record))     

    def mettre_a_jour(self, dem_id, **champs):
        with self.lock:
            record = self.demandes.get(dem_id)
            if not record:
                return None
            record.update(champs)
            self.save()
            return json.loads(json.dumps(record))

    
    def update_draft_answers(self, request_id, user_id, answers):
        """Save validated answers without overwriting unrelated fields."""
        if not isinstance(answers, dict):
            raise ValidationError("Answers must be a dictionary.")

        if not isinstance(user_id, str) or not user_id.strip():
            raise ValidationError("user_id is required.")

        allowed_fields = {
            "type_voyage",
            "destination",
            "date_depart",
            "date_retour",
            "nombre_voyageurs",
            "has_enfants",
            "nombre_enfants",
            "budget_max_par_personne",
            "niveau_aventure",
            "besoin_guide",
            "activites",
            "contraintes",
            "souhaits",
        }

        if not answers or not set(answers).issubset(allowed_fields):
            raise ValidationError("Answers contain missing or unsupported fields.")

        with self.lock:
            record = self.demandes.get(request_id)

            if not record:
                raise ValidationError("Draft not found.")

            request_data = record.get("demande", {})

            if request_data.get("user_id") != user_id.strip():
                raise ValidationError("This draft belongs to another client.")

            request_data.update(answers)
            record["demande"] = request_data

            self.save()

            return json.loads(json.dumps(record))



    def ajouter_recherche(self, dem_id, recherche):
        """Ajoute une recherche à la demande, sans écraser les précédentes."""
        with self.lock:
            record = self.demandes.get(dem_id)
            if not record:
                return None
            entree = dict(recherche)
            entree["id"] = "rech_" + secrets.token_hex(4)
            record.setdefault("recherches", []).append(entree)
            self.save()
            return json.loads(json.dumps(entree))

    def changer_statut(self, dem_id, statut):
        """Change le statut d'une demande. Retourne None si inconnue ou refusée."""
        if statut not in STATUTS:
            raise ValidationError(f"statut doit être l'un de {', '.join(STATUTS)}.")
        with self.lock:
            record = self.demandes.get(dem_id)
            if not record:
                return None
            record["statut"] = statut
            self.save()
            return json.loads(json.dumps(record))

    def definir_messages(self, dem_id, messages):
        """Remplace l'historique de conversation d'une demande (liste de messages)."""
        if not isinstance(messages, list):
            raise ValidationError("messages doit être une liste.")
        for message in messages:
            if (not isinstance(message, dict)
                    or message.get("role") not in ("user", "assistant")
                    or not isinstance(message.get("content"), str)
                    or not message["content"].strip()):
                raise ValidationError(
                    "Chaque message doit avoir un role (user ou assistant) et un content texte non vide.")
        with self.lock:
            record = self.demandes.get(dem_id)
            if not record:
                return None
            record["messages"] = json.loads(json.dumps(messages[-60:]))
            self.save()
            return json.loads(json.dumps(record))


def criteres_depuis_demande(demande):
    """Critères de recherche structurés dérivés des réponses du formulaire."""
    d = demande["demande"]
    return {
        "destination": d["destination"],
        "date_depart": d["date_depart"],
        "date_retour": d["date_retour"],
        "participants": d["nombre_voyageurs"],
        "budget_max": d["budget_max_par_personne"],
        "type_voyage": d["type_voyage"],
        "activites": list(d["activites"]),
    }

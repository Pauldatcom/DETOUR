"""Persistance JSON des propositions de voyage DÉTOUR."""

import json
import re
import secrets
import threading
from datetime import datetime, timezone
from pathlib import Path

from utils import PROP_STATUTS, STATUT_BROUILLON


def utc_now_iso():
    return datetime.now(timezone.utc).isoformat()


class PropositionError(ValueError):
    pass


def valider_prestation(data):
    if not isinstance(data, dict):
        raise PropositionError("Prestation invalide (objet attendu).")
    nom = data.get("nom")
    if not isinstance(nom, str) or not nom.strip():
        raise PropositionError("nom est obligatoire.")
    type_ = data.get("type", "")
    if not isinstance(type_, str):
        raise PropositionError("type doit être une chaîne.")
    prix_unitaire = data.get("prix_unitaire_eur")
    if type(prix_unitaire) is not int or prix_unitaire < 0:
        raise PropositionError("prix_unitaire_eur doit être un entier positif.")
    quantite = data.get("quantite", 1)
    if type(quantite) is not int or quantite < 1:
        raise PropositionError("quantite doit être un entier >= 1.")
    return {
        "id": str(data.get("id") or f"prest_{secrets.token_hex(4)}"),
        "nom": nom.strip(),
        "type": type_.strip(),
        "prix_unitaire_eur": prix_unitaire,
        "quantite": quantite,
        "prix_total_eur": prix_unitaire * quantite,
    }


def valider_proposition(data):
    if not isinstance(data, dict):
        raise PropositionError("Corps JSON attendu.")
    titre = data.get("titre", "")
    if not isinstance(titre, str) or not titre.strip():
        raise PropositionError("titre est obligatoire.")
    description = data.get("description", "")
    if not isinstance(description, str):
        raise PropositionError("description doit être une chaîne.")
    prestations = data.get("prestations", [])
    if not isinstance(prestations, list):
        raise PropositionError("prestations doit être une liste.")
    prestations_validees = [valider_prestation(p) for p in prestations]
    prix_total = sum(p["prix_total_eur"] for p in prestations_validees)
    return {
        "titre": titre.strip(),
        "description": description.strip(),
        "prestations": prestations_validees,
        "prix_total_eur": prix_total,
    }


class PropositionStore:
    def __init__(self, path=None):
        self.path = Path(path) if path else None
        self.lock = threading.RLock()
        self.propositions = {}
        if self.path and self.path.exists():
            try:
                self.propositions = json.loads(self.path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                self.propositions = {}

    def save(self):
        if not self.path:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.propositions, ensure_ascii=False, indent=2),
                       encoding="utf-8")
        tmp.replace(self.path)

    def creer(self, demande_id, data, conseiller=""):
        valide = valider_proposition(data)
        with self.lock:
            prop_id = "prop_" + secrets.token_hex(6)
            record = {
                "id": prop_id,
                "demande_id": demande_id,
                "statut": STATUT_BROUILLON,
                "cree_le": utc_now_iso(),
                "modifiee_le": utc_now_iso(),
                "conseiller": conseiller,
                **valide,
            }
            self.propositions[prop_id] = record
            self.save()
            return json.loads(json.dumps(record))

    def lister(self):
        with self.lock:
            return json.loads(json.dumps(list(self.propositions.values())))

    def lister_par_demande(self, dem_id):
        with self.lock:
            return json.loads(json.dumps([
                p for p in self.propositions.values()
                if p.get("demande_id") == dem_id
            ]))

    def lister_par_user(self, user_id, demand_store):
        with self.lock:
            result = []
            for p in self.propositions.values():
                dem = demand_store.obtenir(p.get("demande_id", ""))
                if dem and dem.get("demande", {}).get("user_id") == user_id:
                    result.append(json.loads(json.dumps(p)))
            return result

    def obtenir(self, prop_id):
        with self.lock:
            record = self.propositions.get(prop_id)
            return json.loads(json.dumps(record)) if record else None

    def mettre_a_jour(self, prop_id, data):
        if not isinstance(data, dict):
            raise PropositionError("Corps JSON attendu.")
        with self.lock:
            record = self.propositions.get(prop_id)
            if not record:
                return None
            champs = valider_proposition(data)
            record["titre"] = champs["titre"]
            record["description"] = champs["description"]
            record["prestations"] = champs["prestations"]
            record["prix_total_eur"] = champs["prix_total_eur"]
            record["modifiee_le"] = utc_now_iso()
            self.save()
            return json.loads(json.dumps(record))

    def changer_statut(self, prop_id, statut):
        if statut not in PROP_STATUTS:
            raise PropositionError(f"statut doit être l'un de {', '.join(PROP_STATUTS)}.")
        with self.lock:
            record = self.propositions.get(prop_id)
            if not record:
                return None
            record["statut"] = statut
            record["modifiee_le"] = utc_now_iso()
            self.save()
            return json.loads(json.dumps(record))

    def supprimer(self, prop_id):
        with self.lock:
            if prop_id not in self.propositions:
                return False
            del self.propositions[prop_id]
            self.save()
            return True
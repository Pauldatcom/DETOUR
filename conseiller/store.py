"""Persistance JSON des demandes client de DÉTOUR."""

import json
import re
import secrets
import threading
from datetime import datetime, timezone
from pathlib import Path

from utils import (ACTIVITES_POSSIBLES, ACTEUR_AGENT, NIVEAUX_AVENTURE,
                   QUALIF_EN_COURS,
                   QUALIF_INCOMPLET, QUALIF_PRET_PROPOSITION, QUALIF_PRET_RELECTURE,
                   STATUTS, STATUT_A_ANALYSER, STATUT_PROPOSE, STATUT_VALIDE,
                   TYPES_ACTIVITE_PHYSIQUE, TYPES_AVEC_GUIDE, TYPES_VOYAGE,
                   TRANSITIONS_DEMANDE)


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


def _valider_auteur(par):
    """Every advisor decision needs an author. The reason is optional."""
    if not isinstance(par, str) or not par.strip():
        raise ValidationError("Le nom du conseiller est obligatoire.")


def _refuser_agent(identite):
    """The agent never takes a human decision."""
    if isinstance(identite, str) and identite.strip().lower() == ACTEUR_AGENT:
        raise ValidationError(
            "L'agent ne peut pas prendre une décision. Seul le conseiller tranche.")


def _journaliser(record, action, par, motif, avant=None, apres=None, champs=None):
    """Append an advisor decision to the request journal.

    The journal is append-only: author, date and reason are kept for every
    decision so the history stays auditable. The reason is optional but is
    recorded whenever the advisor gives one.
    """
    entry = {
        "action": action,
        "par": par.strip(),
        "le": utc_now_iso(),
        "motif": (motif or "").strip(),
        "avant": avant,
        "apres": apres,
        "champs": list(champs) if champs else None,
    }
    journal = list(record.get("decisions") or [])
    journal.append(entry)
    record["decisions"] = journal
    return entry


# Required fields for a travel request (agent must not re-ask when already provided).
CHAMPS_REQUIS = (
    "type_voyage",
    "destination",
    "date_depart",
    "date_retour",
    "nombre_voyageurs",
    "budget_max_par_personne",
    "niveau_aventure",
)

CHAMPS_REQUIS_LABELS = {
    "type_voyage": "type de voyage",
    "destination": "destination",
    "date_depart": "date de départ",
    "date_retour": "date de retour",
    "nombre_voyageurs": "nombre de voyageurs",
    "budget_max_par_personne": "budget maximum par personne",
    "niveau_aventure": "niveau d'aventure",
}


def champs_manquants(demande):
    """Champs obligatoires absents ou invalides. Une liste vide signifie que la demande est complète."""
    if not isinstance(demande, dict):
        return list(CHAMPS_REQUIS)
    manquants = []
    if demande.get("type_voyage") not in TYPES_VOYAGE:
        manquants.append("type_voyage")
    destination = demande.get("destination")
    if not isinstance(destination, str) or not destination.strip():
        manquants.append("destination")
    date_depart = demande.get("date_depart")
    date_retour = demande.get("date_retour")
    if not _valid_date(date_depart):
        manquants.append("date_depart")
    if not _valid_date(date_retour):
        manquants.append("date_retour")
    elif _valid_date(date_depart) and str(date_retour) < str(date_depart):
        manquants.append("date_retour")
    nombre = demande.get("nombre_voyageurs")
    if type(nombre) is not int or not 1 <= nombre <= 20:
        manquants.append("nombre_voyageurs")
    budget = demande.get("budget_max_par_personne")
    if type(budget) is not int or budget <= 0 or budget > 100000:
        manquants.append("budget_max_par_personne")
    if demande.get("niveau_aventure") not in NIVEAUX_AVENTURE:
        manquants.append("niveau_aventure")
    return manquants


def questions_conditionnelles(demande):
    """Return the extra questions that apply to this request (#22).

    Only relevant questions are returned: the agent must not ask the others.
    """
    if not isinstance(demande, dict):
        return []
    questions = []
    type_voyage = demande.get("type_voyage")
    if type_voyage in TYPES_ACTIVITE_PHYSIQUE:
        questions.append("niveau_aventure")
    if type_voyage in TYPES_AVEC_GUIDE:
        questions.append("besoin_guide")
    if demande.get("avec_voiture") is True:
        questions.append("permis_conduire")
    return questions


def analyser_informations(demande):
    """Split required fields into provided vs missing for the agent.

    Already valid fields are listed in fournis so the agent must not ask again.
    """
    manquants = champs_manquants(demande if isinstance(demande, dict) else {})
    manquants_set = set(manquants)
    fournis = [c for c in CHAMPS_REQUIS if c not in manquants_set]
    return {
        "champs_requis": list(CHAMPS_REQUIS),
        "fournis": fournis,
        "manquants": manquants,
        "complet": len(manquants) == 0,
        "labels": {c: CHAMPS_REQUIS_LABELS[c] for c in CHAMPS_REQUIS},
        "questions_conditionnelles": questions_conditionnelles(demande),
    }


# Fields the traveler (via the agent) may set on a request.
CHAMPS_REPONSE = (
    "type_voyage", "destination", "date_depart", "date_retour",
    "nombre_voyageurs", "has_enfants", "nombre_enfants",
    "budget_max_par_personne", "niveau_aventure", "besoin_guide",
    "avec_voiture", "permis_conduire",
    "activites", "contraintes", "souhaits", "conseiller",
)


def _normaliser_champ(key, value, contexte):
    """Validate one answer field. Raises ValidationError if the value is unusable."""
    if key == "type_voyage":
        if value not in TYPES_VOYAGE:
            raise ValidationError(f"type_voyage must be one of {', '.join(TYPES_VOYAGE)}.")
        return value
    if key == "destination":
        if not isinstance(value, str) or not value.strip():
            raise ValidationError("destination is required.")
        return value.strip()
    if key in ("date_depart", "date_retour"):
        if not _valid_date(value):
            raise ValidationError(f"{key} must be YYYY-MM-DD.")
        return str(value)
    if key == "nombre_voyageurs":
        if type(value) is not int or not 1 <= value <= 20:
            raise ValidationError("nombre_voyageurs must be an integer from 1 to 20.")
        return value
    if key == "has_enfants":
        return bool(value)
    if key == "nombre_enfants":
        if type(value) is not int or value < 0:
            raise ValidationError("nombre_enfants must be an integer >= 0.")
        return value
    if key == "budget_max_par_personne":
        if type(value) is not int or value <= 0 or value > 100000:
            raise ValidationError("budget_max_par_personne must be a positive integer.")
        return value
    if key == "niveau_aventure":
        if value not in NIVEAUX_AVENTURE:
            raise ValidationError(
                f"niveau_aventure must be one of {', '.join(NIVEAUX_AVENTURE)}.")
        return value
    if key == "besoin_guide":
        return bool(value)
    if key in ("avec_voiture", "permis_conduire"):
        if not isinstance(value, bool):
            raise ValidationError(f"{key} must be true or false.")
        return value
    if key == "activites":
        if not isinstance(value, list):
            raise ValidationError("activites must be a list.")
        return list(dict.fromkeys(
            a.strip() for a in value if isinstance(a, str) and a.strip()))
    if key in ("contraintes", "souhaits", "conseiller"):
        if not isinstance(value, str):
            raise ValidationError(f"{key} must be a string.")
        return value.strip()
    return value


def fusionner_reponses(existant, champs):
    """Merge traveler answers into an existing demande dict.

    Returns (merged, champs_mis_a_jour). Unknown keys are ignored. Invalid
    values raise ValidationError — nothing is applied in that case by the caller.
    """
    if not isinstance(champs, dict):
        raise ValidationError("Invalid answers (object expected).")
    merged = dict(existant) if isinstance(existant, dict) else {}
    mis_a_jour = []
    for key in CHAMPS_REPONSE:
        if key not in champs or champs[key] is None:
            continue
        nouveau = _normaliser_champ(key, champs[key], merged)
        if merged.get(key) != nouveau:
            mis_a_jour.append(key)
        merged[key] = nouveau
    return merged, mis_a_jour


def recalculer_qualification(record):
    """Pose la qualification à partir des champs et de la décision du conseiller.

    L'agent ne peut pas atteindre « prête pour proposition » : seul
    qualification_validee_par, posé par le conseiller, y mène.
    Un renvoi manuel en incomplet est conservé tant que le conseiller ne le lève pas.
    """
    demande = record.get("demande") if isinstance(record.get("demande"), dict) else {}
    manquants = champs_manquants(demande)
    record["champs_manquants"] = manquants
    if record.get("qualification_retenue") == QUALIF_INCOMPLET:
        record["qualification"] = QUALIF_INCOMPLET
        record["qualification_validee_par"] = None
        return record
    if manquants:
        record["qualification"] = QUALIF_EN_COURS if record.get("messages") else QUALIF_INCOMPLET
        record["qualification_validee_par"] = None
        return record
    if record.get("qualification_validee_par"):
        record["qualification"] = QUALIF_PRET_PROPOSITION
        return record
    record["qualification"] = QUALIF_PRET_RELECTURE
    return record


def _publier(record):
    copie = json.loads(json.dumps(record))
    return recalculer_qualification(copie)


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

    avec_voiture = data.get("avec_voiture", False)
    if not isinstance(avec_voiture, bool):
        raise ValidationError("avec_voiture must be true or false.")
    permis_conduire = data.get("permis_conduire")
    if permis_conduire is not None and not isinstance(permis_conduire, bool):
        raise ValidationError("permis_conduire must be true, false or null.")
    if not avec_voiture:
        permis_conduire = None  # the driving license only matters for a self-drive trip

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
        "avec_voiture": avec_voiture,
        "permis_conduire": permis_conduire,
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
                "qualification_retenue": None,
                "qualification_validee_par": None,
            }
            recalculer_qualification(record)
            self.demandes[dem_id] = record
            self.save()
            return _publier(record)

    def lister(self):
        with self.lock:
            return [_publier(record) for record in self.demandes.values()]

    def obtenir(self, dem_id):
        with self.lock:
            record = self.demandes.get(dem_id)
            return _publier(record) if record else None

    def mettre_a_jour(self, dem_id, **champs):
        with self.lock:
            record = self.demandes.get(dem_id)
            if not record:
                return None
            record.update(champs)
            if "demande" in champs or "messages" in champs:
                recalculer_qualification(record)
            self.save()
            return _publier(record)

    def enregistrer_reponses(self, dem_id, champs, user_id=""):
        """Save traveler answers on an existing request, or create one.

        Merges only the provided fields; other values are preserved. Ownership
        is enforced when the request already has a user_id. Real field changes
        clear advisor validation and are appended to `modifications`. Returns
        (record, champs_mis_a_jour). record is None if dem_id was set but unknown.
        """
        if not isinstance(user_id, str):
            user_id = ""
        user_id = user_id.strip()
        with self.lock:
            if dem_id:
                record = self.demandes.get(dem_id)
                if not record:
                    return None, []
                existant_uid = (record.get("demande") or {}).get("user_id", "")
                if not isinstance(existant_uid, str):
                    existant_uid = ""
                existant_uid = existant_uid.strip()
                if existant_uid and existant_uid != user_id:
                    raise ValidationError(
                        "This request belongs to another traveler.")
                avant = dict(record.get("demande") or {})
                merged, mis_a_jour = fusionner_reponses(avant, champs)
                if user_id:
                    merged["user_id"] = user_id
                elif "user_id" not in merged:
                    merged["user_id"] = existant_uid or ""
                if not champs_manquants(merged):
                    merged = valider_demande(merged)
                if mis_a_jour:
                    now = utc_now_iso()
                    history = record.setdefault("modifications", [])
                    auteur = user_id or "traveler"
                    for key in mis_a_jour:
                        history.append({
                            "champ": key,
                            "avant": avant.get(key),
                            "apres": merged.get(key),
                            "par": auteur,
                            "le": now,
                        })
                    record["qualification_validee_par"] = None
                    record["qualification_validee_le"] = None
                record["demande"] = merged
                recalculer_qualification(record)
                self.save()
                return _publier(record), mis_a_jour

            merged, mis_a_jour = fusionner_reponses({}, champs)
            merged["user_id"] = user_id
            if not mis_a_jour:
                raise ValidationError("No usable answer to save.")
            dem_id = "dem_" + secrets.token_hex(6)
            if not champs_manquants(merged):
                merged = valider_demande(merged)
            record = {
                "id": dem_id,
                "statut": STATUT_A_ANALYSER,
                "cree_le": utc_now_iso(),
                "demande": merged,
                "qualification_retenue": None,
                "qualification_validee_par": None,
            }
            recalculer_qualification(record)
            self.demandes[dem_id] = record
            self.save()
            return _publier(record), mis_a_jour

    def corriger(self, dem_id, champs, auteur, motif=""):
        """Let the advisor correct fields of a request. Every change is recorded.

        A correction invalidates a previous validation: the advisor must review
        the corrected request again before it goes to proposal. The decision
        needs an author and a reason, and is kept in the request journal.
        """
        if not isinstance(champs, dict) or not champs:
            raise ValidationError("fields must be a non-empty object.")
        if "user_id" in champs:
            raise ValidationError("user_id cannot be changed.")
        if not isinstance(auteur, str) or not auteur.strip():
            raise ValidationError("author is required.")
        _refuser_agent(auteur)
        _valider_auteur(auteur)
        with self.lock:
            record = self.demandes.get(dem_id)
            if not record:
                return None
            before = record["demande"]
            updated = valider_demande({**before, **champs})
            now = utc_now_iso()
            history = record.setdefault("modifications", [])
            changed = False
            champs_modifies = []
            for field, value in updated.items():
                if before.get(field) != value:
                    changed = True
                    champs_modifies.append(field)
                    history.append({
                        "champ": field,
                        "avant": before.get(field),
                        "apres": value,
                        "par": auteur.strip(),
                        "le": now,
                    })
            record["demande"] = updated
            if changed:
                record["qualification_validee_par"] = None
                record["qualification_validee_le"] = None
            recalculer_qualification(record)
            if changed:
                _journaliser(record, "correction", auteur, motif,
                             champs=champs_modifies)
            self.save()
            return _publier(record)

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

    def recalculer(self, dem_id):
        """Recalcule la qualification après un changement de champs ou de messages."""
        with self.lock:
            record = self.demandes.get(dem_id)
            if not record:
                return None
            recalculer_qualification(record)
            self.save()
            return _publier(record)

    def definir_qualification(self, dem_id, qualification, acteur="conseiller",
                              par="", motif=""):
        """Décision du conseiller : renvoyer en incomplet, ou valider pour proposition.

        L'agent n'est pas un acteur autorisé. Une validation exige les champs
        obligatoires, un nom de conseiller et un motif.
        """
        if acteur != "conseiller":
            raise ValidationError(
                "Seul le conseiller peut changer la qualification. "
                "L'agent ne peut pas marquer une demande prête pour proposition.")
        if qualification not in (QUALIF_INCOMPLET, QUALIF_PRET_PROPOSITION):
            raise ValidationError(
                "Le conseiller peut renvoyer la demande en incomplet ou la valider pour proposition.")
        _refuser_agent(par)
        _valider_auteur(par)
        with self.lock:
            record = self.demandes.get(dem_id)
            if not record:
                return None
            avant = record.get("qualification")
            if qualification == QUALIF_PRET_PROPOSITION:
                manquants = champs_manquants(record.get("demande"))
                if manquants:
                    raise ValidationError(
                        "Informations obligatoires incomplètes : " + ", ".join(manquants) + ".")
                record["qualification_retenue"] = None
                record["qualification_validee_par"] = "conseiller"
                record["qualification_validee_le"] = utc_now_iso()
            else:
                record["qualification_retenue"] = QUALIF_INCOMPLET
                record["qualification_validee_par"] = None
                record["qualification_validee_le"] = None
            recalculer_qualification(record)
            _journaliser(record, "qualification", par, motif,
                         avant=avant, apres=record.get("qualification"))
            self.save()
            return _publier(record)

    def changer_statut(self, dem_id, statut, par, motif):
        """Décision du conseiller sur le statut de la demande.

        Le changement est journalisé (auteur, date, motif) et la transition
        doit être autorisée. Retourne None si la demande est inconnue.
        """
        if statut not in STATUTS:
            raise ValidationError(f"statut doit être l'un de {', '.join(STATUTS)}.")
        _refuser_agent(par)
        _valider_auteur(par)
        with self.lock:
            record = self.demandes.get(dem_id)
            if not record:
                return None
            avant = self._appliquer_statut(record, statut)
            _journaliser(record, "statut", par, motif,
                         avant=avant, apres=statut)
            self.save()
            return _publier(record)

    def changer_statut_automatique(self, dem_id, statut):
        """Transition système : lecture serveur plus récente, pas de décision humaine.

        Aucun journal n'est écrit : personne n'a décidé, le programme a constaté.
        """
        if statut not in STATUTS:
            raise ValidationError(f"statut doit être l'un de {', '.join(STATUTS)}.")
        with self.lock:
            record = self.demandes.get(dem_id)
            if not record:
                return None
            self._appliquer_statut(record, statut)
            self.save()
            return _publier(record)

    def _appliquer_statut(self, record, statut):
        """Applique un statut en vérifiant la transition et la qualification.

        Retourne le statut précédent.
        """
        actuel = record.get("statut")
        if statut not in TRANSITIONS_DEMANDE.get(actuel, frozenset()):
            raise ValidationError(
                f"Transition de statut interdite : {actuel} → {statut}.")
        recalculer_qualification(record)
        if statut in (STATUT_PROPOSE, STATUT_VALIDE) and record.get("qualification") != QUALIF_PRET_PROPOSITION:
            raise ValidationError(
                "La demande ne peut partir en proposition que si le conseiller l'a validée.")
        record["statut"] = statut
        return actuel

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
            recalculer_qualification(record)
            self.save()
            return _publier(record)


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
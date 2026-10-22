"""JSON persistence for DÉTOUR travel propositions."""

import json
import secrets
import threading
from datetime import date, datetime, timezone
from pathlib import Path

from utils import (
    ACTEUR_AGENT,
    DECISION_ACCEPTER,
    DECISION_ACTIONS,
    DECISION_CORRECTION,
    DECISION_REFUSER,
    DECISION_REPLACE,
    DECISIONS_AVEC_MOTIF,
    DECISIONS_PRESTATION,
    PROP_STATUTS,
    SOURCE_LABEL,
    STATUT_BROUILLON,
    STATUT_PAR_DECISION,
    TRANSITIONS_PROPOSITION,
)

# Provenance of a line in a proposition. Only "verifie" may show a price.
VERIFICATION_VERIFIE = "verifie"
VERIFICATION_MANQUANT = "manquant"


def utc_now_iso():
    return datetime.now(timezone.utc).isoformat()


def parse_iso8601(value):
    """Parse an ISO-8601 timestamp, or return None if unusable."""
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None


class PropositionError(ValueError):
    pass


def _provenance_complete(data):
    """True when price, availability, source and ISO read time are all present."""
    prix = data.get("prix_unitaire_eur")
    disponible = data.get("disponible")
    source = data.get("source")
    consulte_le = data.get("consulte_le")
    return (
        type(prix) is int and prix >= 0
        and type(disponible) is bool
        and isinstance(source, str) and bool(source.strip())
        and parse_iso8601(consulte_le) is not None
    )


def _ligne_manquante(prest_id, nom, type_, quantite):
    """Store a line without inventing price, availability, source or time."""
    return {
        "id": prest_id,
        "nom": nom,
        "type": type_,
        "quantite": quantite,
        "verification": VERIFICATION_MANQUANT,
        "prix_unitaire_eur": None,
        "prix_total_eur": None,
        "disponible": None,
        "source": None,
        "consulte_le": None,
    }


def valider_prestation(data):
    """Validate one prestation line and keep its provenance.

    A verified line keeps id, price, availability, source and read time.
    Any incomplete line is stored as missing — never filled with invented values.
    """
    if not isinstance(data, dict):
        raise PropositionError("Prestation invalide (objet attendu).")
    prest_id = str(data.get("id") or "").strip()
    if not prest_id:
        raise PropositionError("id de prestation est obligatoire.")
    nom = data.get("nom", "")
    if not isinstance(nom, str) or not nom.strip():
        raise PropositionError("nom est obligatoire.")
    type_ = data.get("type", "")
    if not isinstance(type_, str):
        raise PropositionError("type doit être une chaîne.")
    quantite = data.get("quantite", 1)
    if type(quantite) is not int or quantite < 1:
        raise PropositionError("quantite doit être un entier >= 1.")

    if data.get("verification") == VERIFICATION_MANQUANT or not _provenance_complete(data):
        return _ligne_manquante(prest_id, nom.strip(), type_.strip(), quantite)

    prix = data["prix_unitaire_eur"]
    return {
        "id": prest_id,
        "nom": nom.strip(),
        "type": type_.strip(),
        "quantite": quantite,
        "verification": VERIFICATION_VERIFIE,
        "prix_unitaire_eur": prix,
        "prix_total_eur": prix * quantite,
        "disponible": data["disponible"],
        "source": data["source"].strip(),
        "consulte_le": data["consulte_le"].strip(),
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
    # Only verified lines contribute to the total; missing ones stay out of the sum.
    prix_total = sum(
        p["prix_total_eur"] for p in prestations_validees
        if p.get("verification") == VERIFICATION_VERIFIE
    )
    return {
        "titre": titre.strip(),
        "description": description.strip(),
        "prestations": prestations_validees,
        "prix_total_eur": prix_total,
    }


def aligner_sur_serveur(data, resultats, source_label=None, consulte_le=None):
    """Stamp each line from the fictional server, or mark it missing.

    The model may invent names or prices. Only a real search result plus a
    consultation time may produce a verified line. Unknown ids become missing.
    """
    if not isinstance(data, dict):
        raise PropositionError("Proposition invalide (objet attendu).")
    par_id = {r["id"]: r for r in resultats or []
              if isinstance(r, dict) and r.get("id")}
    label = (source_label or "").strip() or SOURCE_LABEL
    lu_le = (consulte_le or "").strip()
    if lu_le and parse_iso8601(lu_le) is None:
        lu_le = ""
    prestations = []
    for p in data.get("prestations", []):
        if not isinstance(p, dict):
            raise PropositionError("Prestation invalide (objet attendu).")
        prest_id = str(p.get("id") or "").strip()
        quantite = p.get("quantite", 1)
        if type(quantite) is not int or quantite < 1:
            quantite = 1
        serveur = par_id.get(prest_id)
        if serveur is None or not lu_le:
            prestations.append(_ligne_manquante(
                prest_id or f"prest_{secrets.token_hex(4)}",
                str(p.get("nom") or "").strip() or "Prestation",
                str(p.get("type") or "").strip(),
                quantite,
            ))
            continue
        prix = serveur.get("prix_unitaire_eur")
        if type(prix) is not int or prix < 0:
            prestations.append(_ligne_manquante(
                serveur["id"],
                str(serveur.get("nom") or "").strip() or "Prestation",
                str(serveur.get("type") or "").strip(),
                quantite,
            ))
            continue
        prestations.append({
            "id": serveur["id"],
            "nom": str(serveur.get("nom") or "").strip() or "Prestation",
            "type": str(serveur.get("type") or "").strip(),
            "prix_unitaire_eur": prix,
            "quantite": quantite,
            "disponible": bool(serveur.get("disponible")),
            "source": label,
            "consulte_le": lu_le,
            "verification": VERIFICATION_VERIFIE,
        })
    return {**data, "prestations": prestations}

# Quantities are computed by the program from the request, never by the model (#34).
ACCOMMODATION_TYPES = ("hebergement", "hébergement")


def count_nights(demande):
    """Return the number of nights between departure and return dates.

    Missing, invalid or reversed dates count as one night.
    """
    try:
        departure = date.fromisoformat(str(demande.get("date_depart") or ""))
        return_date = date.fromisoformat(str(demande.get("date_retour") or ""))
    except ValueError:
        return 1
    return max((return_date - departure).days, 1)


def apply_quantities(data, demande):
    """Set each line quantity from the request.

    Transport and activities: one per traveler.
    Accommodation: one per traveler and per night (server price is per person per night).
    """
    travelers = demande.get("nombre_voyageurs", 1)
    if type(travelers) is not int or travelers < 1:
        travelers = 1
    nights = count_nights(demande)
    lines = []
    for line in data.get("prestations", []):
        quantity = travelers
        if str(line.get("type") or "").strip().lower() in ACCOMMODATION_TYPES:
            quantity = travelers * nights
        lines.append({**line, "quantite": quantity})
    return {**data, "prestations": lines}


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

    def creer(self, demande_id, data, conseiller="", version=1, parente_id=None):
        valide = valider_proposition(data)
        if type(version) is not int or version < 1:
            raise PropositionError("version doit être un entier >= 1.")
        if parente_id is not None:
            parente_id = str(parente_id).strip()
            if not parente_id:
                parente_id = None
        with self.lock:
            prop_id = "prop_" + secrets.token_hex(6)
            record = {
                "id": prop_id,
                "demande_id": demande_id,
                "statut": STATUT_BROUILLON,
                "cree_le": utc_now_iso(),
                "modifiee_le": utc_now_iso(),
                "conseiller": conseiller,
                "version": version,
                "parente_id": parente_id,
                "decisions": [],
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

    def decider(self, prop_id, action, par, motif="", instructions=""):
        """Décision du conseiller sur une proposition : accepter, corriger ou refuser.

        La décision suit la représentation partagée : action, auteur, date,
        motif, instructions, proposition visée et version visée. Elle est
        journalisée dans `decisions_statut` et le statut de la proposition
        suit l'action. Une correction et un refus exigent un motif.

        L'agent ne peut jamais porter la décision : seul le conseiller
        tranche, donc seul son clic peut déclencher la confirmation (#113).
        """
        if action not in DECISION_ACTIONS:
            raise PropositionError(
                f"action doit être l'une de {', '.join(DECISION_ACTIONS)}.")
        if not isinstance(par, str) or not par.strip():
            raise PropositionError("Le nom du conseiller est obligatoire.")
        if par.strip().lower() == ACTEUR_AGENT:
            raise PropositionError(
                "L'agent ne peut pas confirmer une proposition. Seul le conseiller tranche.")
        motif = (motif or "").strip()
        instructions = (instructions or "").strip()
        if action in DECISIONS_AVEC_MOTIF and not motif:
            raise PropositionError(
                "Le motif de la décision est obligatoire pour cette action.")
        if action == DECISION_CORRECTION and not instructions:
            raise PropositionError(
                "Les instructions de correction sont obligatoires.")
        with self.lock:
            record = self.propositions.get(prop_id)
            if not record:
                return None
            actuel = record.get("statut")
            cible = STATUT_PAR_DECISION[action]
            if cible not in TRANSITIONS_PROPOSITION.get(actuel, frozenset()):
                raise PropositionError(
                    f"Transition de statut interdite : {actuel} → {cible}.")
            record["statut"] = cible
            record["modifiee_le"] = utc_now_iso()
            journal = list(record.get("decisions_statut") or [])
            journal.append({
                "action": action,
                "par": par.strip(),
                "le": utc_now_iso(),
                "motif": motif,
                "avant": actuel,
                "apres": cible,
                "proposition_id": record.get("id"),
                "version": record.get("version", 1),
                "instructions": instructions or None,
            })
            record["decisions_statut"] = journal
            self.save()
            return json.loads(json.dumps(record))

    def changer_statut(self, prop_id, statut, par, motif=""):
        """Décision du conseiller sur le statut d'une proposition.

        La transition doit être autorisée et la décision est journalisée
        (auteur, date, motif) dans l'historique de la proposition. Le motif
        est facultatif : il est enregistré quand le conseiller le fournit.
        """
        if statut not in PROP_STATUTS:
            raise PropositionError(f"statut doit être l'un de {', '.join(PROP_STATUTS)}.")
        if not isinstance(par, str) or not par.strip():
            raise PropositionError("Le nom du conseiller est obligatoire.")
        with self.lock:
            record = self.propositions.get(prop_id)
            if not record:
                return None
            actuel = record.get("statut")
            if statut not in TRANSITIONS_PROPOSITION.get(actuel, frozenset()):
                raise PropositionError(
                    f"Transition de statut interdite : {actuel} → {statut}.")
            record["statut"] = statut
            record["modifiee_le"] = utc_now_iso()
            journal = list(record.get("decisions_statut") or [])
            journal.append({
                "action": "statut",
                "par": par.strip(),
                "le": utc_now_iso(),
                "motif": (motif or "").strip(),
                "avant": actuel,
                "apres": statut,
                "version": record.get("version", 1),
                "instructions": None,
            })
            record["decisions_statut"] = journal
            self.save()
            return json.loads(json.dumps(record))

    def enregistrer_decision(self, prop_id, prestation_id, choix, par, motif,
                             remplacement_id=None):
        """Store keep/replace/drop for a changed line. Does not send or book.

        Requires a non-empty advisor name. Decisions are append-only so the
        advisor history stays auditable; builders use the latest choice per
        service id. replace requires remplacement_id from a server reading.
        """
        prest_id = str(prestation_id or "").strip()
        if not prest_id:
            raise PropositionError("prestation_id est obligatoire.")
        if choix not in DECISIONS_PRESTATION:
            raise PropositionError(
                f"choix doit être l'un de {', '.join(DECISIONS_PRESTATION)}.")
        if not isinstance(par, str) or not par.strip():
            raise PropositionError("Le nom du conseiller est obligatoire.")
        if not isinstance(motif, str) or not motif.strip():
            raise PropositionError("motif est obligatoire.")
        remp = str(remplacement_id or "").strip()
        if choix == DECISION_REPLACE and not remp:
            raise PropositionError(
                "remplacement_id est obligatoire pour un remplacement.")
        if choix != DECISION_REPLACE:
            remp = None
        with self.lock:
            record = self.propositions.get(prop_id)
            if not record:
                return None
            ids = {p.get("id") for p in record.get("prestations") or []}
            if prest_id not in ids:
                raise PropositionError(f"Prestation inconnue dans la proposition : {prest_id}.")
            statut_avant = record.get("statut")
            entree = {
                "prestation_id": prest_id,
                "choix": choix,
                "par": par.strip(),
                "le": utc_now_iso(),
                "motif": motif.strip(),
                "remplacement_id": remp,
            }
            decisions = list(record.get("decisions") or [])
            decisions.append(entree)
            record["decisions"] = decisions
            # Never send to the customer and never change send/book status here.
            record["statut"] = statut_avant
            record["modifiee_le"] = utc_now_iso()
            self.save()
            return json.loads(json.dumps(record))

    def _v2_pour_parente(self, parente_id):
        for record in self.propositions.values():
            if record.get("parente_id") == parente_id:
                return record
        return None

    def creer_v2_si_complet(self, prop_v1_id, recherche, conseiller=""):
        """Create or refresh draft v2 when every changed line has a decision.

        Returns the v2 record, or None if decisions are still incomplete.
        Does not alter v1. v2 stays brouillon (not sent, not booked).
        """
        from versions import construire_donnees_v2, decisions_completes

        with self.lock:
            v1 = self.propositions.get(prop_v1_id)
            if not v1:
                return None
            if v1.get("parente_id"):
                raise PropositionError("Seule une proposition v1 peut engendrer une v2.")
            if not decisions_completes(v1, recherche, v1.get("decisions")):
                return None
            data = construire_donnees_v2(v1, recherche, v1.get("decisions"))
            existante = self._v2_pour_parente(prop_v1_id)
            if existante is not None:
                if existante.get("statut") != STATUT_BROUILLON:
                    raise PropositionError(
                        "La proposition v2 n'est plus un brouillon ; elle ne peut pas être régénérée.")
                champs = valider_proposition(data)
                existante["titre"] = champs["titre"]
                existante["description"] = champs["description"]
                existante["prestations"] = champs["prestations"]
                existante["prix_total_eur"] = champs["prix_total_eur"]
                existante["conseiller"] = conseiller or existante.get("conseiller", "")
                existante["version"] = 2
                existante["parente_id"] = prop_v1_id
                existante["statut"] = STATUT_BROUILLON
                existante["modifiee_le"] = utc_now_iso()
                self.save()
                return json.loads(json.dumps(existante))
            # RLock allows re-entering creer while still holding this lock.
            return self.creer(
                v1["demande_id"], data, conseiller=conseiller,
                version=2, parente_id=prop_v1_id)

    def supprimer(self, prop_id):
        with self.lock:
            if prop_id not in self.propositions:
                return False
            del self.propositions[prop_id]
            self.save()
            return True

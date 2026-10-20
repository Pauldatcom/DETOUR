"""Build proposal v2 from advisor decisions and a new server reading.

v1 is never mutated. Replaced services must come from the search payload,
never from a typed-in price. v2 stays a draft (not sent, not booked).
"""

from lecture import (
    comparer_proposition,
    lecture_plus_recente_que_proposition,
)
from propositions import VERIFICATION_VERIFIE, PropositionError
from utils import (
    DECISION_DROP,
    DECISION_KEEP,
    DECISION_REPLACE,
    DECISIONS_PRESTATION,
    SOURCE_LABEL,
)


def _ligne_depuis_serveur(serveur, quantite, source_label, consulte_le):
    """Stamp a verified line from a search result — no invented price."""
    prix = serveur.get("prix_unitaire_eur")
    if type(prix) is not int or prix < 0:
        raise PropositionError(
            f"Lecture serveur incomplète pour {serveur.get('id')} (prix manquant).")
    if not isinstance(serveur.get("disponible"), bool):
        raise PropositionError(
            f"Lecture serveur incomplète pour {serveur.get('id')} (disponibilité manquante).")
    if type(quantite) is not int or quantite < 1:
        quantite = 1
    return {
        "id": serveur["id"],
        "nom": str(serveur.get("nom") or "").strip() or "Prestation",
        "type": str(serveur.get("type") or "").strip(),
        "quantite": quantite,
        "prix_unitaire_eur": prix,
        "disponible": bool(serveur["disponible"]),
        "source": source_label,
        "consulte_le": consulte_le,
        "verification": VERIFICATION_VERIFIE,
    }


def ids_a_decider(proposition_v1, recherche):
    """Service ids that show a real change and still need keep/replace/drop."""
    if not lecture_plus_recente_que_proposition(proposition_v1, recherche):
        return []
    return [
        c["id"] for c in comparer_proposition(
            proposition_v1, (recherche or {}).get("resultats"))
        if not c.get("inchange")
    ]


def decisions_completes(proposition_v1, recherche, decisions):
    """True when every changed line has a keep/replace/drop choice."""
    needed = set(ids_a_decider(proposition_v1, recherche))
    if not needed:
        return False
    presents = {
        d.get("prestation_id") for d in decisions or []
        if isinstance(d, dict) and d.get("choix") in DECISIONS_PRESTATION
    }
    return needed <= presents


def construire_donnees_v2(proposition_v1, recherche, decisions):
    """Assemble v2 payload from decisions + latest server reading.

    keep → same id from the new reading; replace → remplacement_id from that
    reading; drop → omitted. Unchanged lines are refreshed from the reading
    when present.
    """
    if not isinstance(proposition_v1, dict):
        raise PropositionError("Proposition v1 invalide.")
    if not isinstance(recherche, dict):
        raise PropositionError("Une nouvelle lecture serveur est obligatoire pour la v2.")
    label = (recherche.get("source_label") or "").strip() or SOURCE_LABEL
    consulte_le = (recherche.get("consulte_le") or "").strip()
    if not consulte_le:
        raise PropositionError("consulte_le manquant sur la nouvelle lecture.")
    par_id = {
        r["id"]: r for r in recherche.get("resultats") or []
        if isinstance(r, dict) and r.get("id")
    }
    par_decision = {
        d["prestation_id"]: d for d in decisions or []
        if isinstance(d, dict) and d.get("prestation_id")
    }
    needed = set(ids_a_decider(proposition_v1, recherche))
    prestations = []
    for ligne in proposition_v1.get("prestations") or []:
        if not isinstance(ligne, dict):
            continue
        prest_id = ligne.get("id")
        quantite = ligne.get("quantite", 1)
        dec = par_decision.get(prest_id)
        if prest_id in needed:
            if not dec:
                raise PropositionError(
                    f"Décision manquante pour la prestation modifiée : {prest_id}.")
            choix = dec.get("choix")
            if choix == DECISION_DROP:
                continue
            if choix == DECISION_REPLACE:
                remp_id = (dec.get("remplacement_id") or "").strip()
                if not remp_id:
                    raise PropositionError(
                        f"remplacement_id obligatoire pour remplacer {prest_id}.")
                serveur = par_id.get(remp_id)
                if serveur is None:
                    raise PropositionError(
                        f"Remplacement {remp_id} absent de la nouvelle lecture serveur.")
                prestations.append(
                    _ligne_depuis_serveur(serveur, quantite, label, consulte_le))
                continue
            if choix == DECISION_KEEP:
                serveur = par_id.get(prest_id)
                if serveur is None:
                    raise PropositionError(
                        f"Prestation {prest_id} absente de la nouvelle lecture serveur.")
                prestations.append(
                    _ligne_depuis_serveur(serveur, quantite, label, consulte_le))
                continue
            raise PropositionError(f"Choix inconnu : {choix}.")
        # Unchanged line: refresh from the new reading when available.
        serveur = par_id.get(prest_id)
        if serveur is not None:
            prestations.append(
                _ligne_depuis_serveur(serveur, quantite, label, consulte_le))
        elif ligne.get("verification") == VERIFICATION_VERIFIE:
            prestations.append(dict(ligne))
    return {
        "titre": proposition_v1.get("titre") or "Proposition",
        "description": proposition_v1.get("description") or "",
        "prestations": prestations,
    }

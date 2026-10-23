"""Six verification states for prices and availability (#116).

One place decides the state of a search result or a proposal line, so the
advisor screens, the chat and the proposals all say the same thing. The
historical ``verification`` field (``verifie`` / ``manquant``) is kept.
"""

import json
from datetime import datetime

ETAT_VERIFIED = "verified"          # server price + availability + read time
ETAT_CHECKING = "checking"          # in progress, or a v1 price copied into v2, not re-read
ETAT_MODIFIED = "modified"          # price changed since the previous reading
ETAT_UNAVAILABLE = "unavailable"    # disponible is false
ETAT_NOT_VERIFIED = "not_verified"  # missing or incomplete data
ETAT_ERROR = "error"                # the supplier call failed

ETATS_VERIFICATION = (ETAT_VERIFIED, ETAT_CHECKING, ETAT_MODIFIED,
                      ETAT_UNAVAILABLE, ETAT_NOT_VERIFIED, ETAT_ERROR)


def _read_time_ok(value):
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def etat_resultat(resultat, consulte_le):
    """State of one search result; an unavailable option is never "verified"."""
    if not isinstance(resultat, dict):
        return ETAT_NOT_VERIFIED
    prix = resultat.get("prix_unitaire_eur")
    disponible = resultat.get("disponible")
    if (type(prix) is not int or prix < 0 or type(disponible) is not bool
            or not _read_time_ok(consulte_le)):
        return ETAT_NOT_VERIFIED
    if disponible is False:
        return ETAT_UNAVAILABLE
    return ETAT_VERIFIED


def marquer_etats(recherche):
    """Return a copy of a search with ``etat_verification`` on each result."""
    if not isinstance(recherche, dict):
        return recherche
    copie = json.loads(json.dumps(recherche))
    for resultat in copie.get("resultats") or []:
        if isinstance(resultat, dict):
            resultat["etat_verification"] = etat_resultat(resultat, copie.get("consulte_le"))
    return copie


def etat_ligne(ligne, changement=None):
    """State of a proposal line, given its delta with a newer reading (if any).

    Unavailable wins over modified: an option that is no longer available must
    never look available, even if its price also changed.
    """
    if not isinstance(ligne, dict) or ligne.get("verification") != "verifie":
        return ETAT_NOT_VERIFIED
    # Same rule as the traveler view (#127): a copied v1 price is never current.
    if ligne.get("copie_depuis_v1"):
        return ETAT_CHECKING
    if isinstance(changement, dict):
        if changement.get("disponible_apres") is False:
            return ETAT_UNAVAILABLE
        if changement.get("prix_change"):
            return ETAT_MODIFIED
    if ligne.get("disponible") is False:
        return ETAT_UNAVAILABLE
    return ETAT_VERIFIED
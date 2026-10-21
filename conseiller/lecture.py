"""Compare proposal v1 lines with a newer fictional-server reading.

Does not mutate stored proposals. A missing second reading is not a change.
"""

import json

from propositions import VERIFICATION_VERIFIE, parse_iso8601
from utils import STATUT_A_REVOIR


def _resultat_lecture_complet(resultat):
    """True when a new server reading has both a price and an availability."""
    if not isinstance(resultat, dict):
        return False
    prix = resultat.get("prix_unitaire_eur")
    return type(prix) is int and prix >= 0 and isinstance(resultat.get("disponible"), bool)


def comparer_ligne(ancienne, nouvelle):
    """Compare a verified v1 line with a new server reading.

    Returns None when the second reading is missing or incomplete — that must
    not be shown as a change. Never mutates the proposal line.
    """
    if not isinstance(ancienne, dict):
        return None
    if ancienne.get("verification") != VERIFICATION_VERIFIE:
        return None
    if not _resultat_lecture_complet(nouvelle):
        return None
    prix_avant = ancienne["prix_unitaire_eur"]
    dispo_avant = bool(ancienne["disponible"])
    prix_apres = nouvelle["prix_unitaire_eur"]
    dispo_apres = bool(nouvelle["disponible"])
    prix_change = prix_avant != prix_apres
    dispo_change = dispo_avant != dispo_apres
    return {
        "id": ancienne["id"],
        "nom": ancienne.get("nom") or "",
        "prix_avant": prix_avant,
        "prix_apres": prix_apres,
        "disponible_avant": dispo_avant,
        "disponible_apres": dispo_apres,
        "prix_change": prix_change,
        "disponibilite_change": dispo_change,
        "inchange": not prix_change and not dispo_change,
    }


def comparer_proposition(proposition, resultats):
    """Build per-line deltas for a proposal against a new search result list."""
    par_id = {
        r["id"]: r for r in resultats or []
        if isinstance(r, dict) and r.get("id")
    }
    changements = []
    for ligne in proposition.get("prestations") or []:
        if not isinstance(ligne, dict):
            continue
        delta = comparer_ligne(ligne, par_id.get(ligne.get("id")))
        if delta is not None:
            changements.append(delta)
    return changements


def lecture_plus_recente_que_proposition(proposition, recherche):
    """True when the search was read after at least one verified proposal line.

    Timestamps must be ISO-8601; raw string inequality is not enough.
    """
    if not isinstance(recherche, dict):
        return False
    lu_dt = parse_iso8601(recherche.get("consulte_le"))
    if lu_dt is None:
        return False
    for ligne in proposition.get("prestations") or []:
        if not isinstance(ligne, dict):
            continue
        if ligne.get("verification") != VERIFICATION_VERIFIE:
            continue
        ligne_dt = parse_iso8601(ligne.get("consulte_le"))
        if ligne_dt is not None and lu_dt > ligne_dt:
            return True
    return False


def proposition_avec_changements(proposition, recherches):
    """Attach comparison data without altering stored v1 prices."""
    if not isinstance(proposition, dict):
        return proposition
    copie = json.loads(json.dumps(proposition))
    if not recherches:
        return copie
    derniere = recherches[-1]
    if not lecture_plus_recente_que_proposition(copie, derniere):
        return copie
    copie["changements"] = comparer_proposition(copie, derniere.get("resultats"))
    return copie


def a_des_ecarts(changements):
    """True when at least one line has a real price or availability change."""
    return any(isinstance(c, dict) and not c.get("inchange") for c in changements or [])


def enrichir_propositions(props, demand_store):
    """Attach price/availability deltas from the latest search; v1 lines stay intact."""
    enrichies = []
    for prop in props or []:
        dem = demand_store.obtenir(prop.get("demande_id", ""))
        recherches = (dem or {}).get("recherches") or []
        enrichies.append(proposition_avec_changements(prop, recherches))
    return enrichies


def marquer_a_revoir_si_ecart(store, propositions, dem_id, recherche):
    """Set request status to review when a newer reading changes a proposal line."""
    props = propositions.lister_par_demande(dem_id)
    for prop in props:
        if not lecture_plus_recente_que_proposition(prop, recherche):
            continue
        changements = comparer_proposition(prop, recherche.get("resultats"))
        if a_des_ecarts(changements):
            store.changer_statut(dem_id, STATUT_A_REVOIR, auteur="System", motif="Automatic review triggered by a newer server reading.")
            return True
    return False

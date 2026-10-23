"""DÉTOUR advisor working hours: single source of truth for availability.

Centralises the opening-hours configuration (issue #48) and the response
deadline calculations (issues #51 and #53):
- advisors respond Monday to Friday, 09:00 to 18:00, business timezone;
- Saturday and Sunday do not count;
- requests may arrive at any time: outside opening hours the count starts
  at the next opening period;
- target response time is 24 working hours, maximum 48.

Other modules read this configuration here: no chatbot message may
hard-code the hours.
"""

from datetime import datetime, time, timedelta, timezone

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover - Python < 3.9, CI runs 3.11+
    ZoneInfo = None

# Opening-hours configuration (issue #48). Edit here only.
FUSEAU_METIER = "Europe/Paris"
JOURS_OUVRES = frozenset({0, 1, 2, 3, 4})  # weekday(): Monday=0 … Friday=4
HEURE_OUVERTURE = time(9, 0)
HEURE_FERMETURE = time(18, 0)

# Response delays (issues #51 and #53), in working hours.
DELAI_CIBLE_HEURES_OUVREES = 24
DELAI_MAX_HEURES_OUVREES = 48

# Display thresholds for the advisor queue (issue #51).
ECHEANCE_DANS_DELAI = "dans_delai"
ECHEANCE_APPROCHE = "approche"
ECHEANCE_DEPASSEE = "depassee"


def fuseau_metier():
    """Return the business timezone (Europe/Paris), or UTC as fallback."""
    if ZoneInfo is None:
        return timezone.utc
    return ZoneInfo(FUSEAU_METIER)


def vers_metier(moment):
    """Convert an instant (aware or naive, assumed UTC) to the business timezone."""
    if not isinstance(moment, datetime):
        raise ValueError("moment must be a datetime.")
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(fuseau_metier())


def _ouvert_a(copie):
    """True if this business-timezone moment falls within opening hours (Mon-Fri, 9-18h)."""
    return copie.weekday() in JOURS_OUVRES and HEURE_OUVERTURE <= copie.time() < HEURE_FERMETURE


def est_ouvert(moment=None):
    """True if the service is open at this moment (default: now)."""
    return _ouvert_a(vers_metier(moment or datetime.now(timezone.utc)))


def prochaine_ouverture(moment=None):
    """Next opening instant, after the given moment (default: now)."""
    courant = vers_metier(moment or datetime.now(timezone.utc))
    jour = courant.date()
    debut = datetime.combine(jour, HEURE_OUVERTURE, tzinfo=courant.tzinfo)
    if _ouvert_a(courant):
        return courant
    if debut > courant and jour.weekday() in JOURS_OUVRES:
        return debut
    # Advance day by day until the next working day.
    un_jour = timedelta(days=1)
    suivant = courant + un_jour
    while suivant.weekday() not in JOURS_OUVRES:
        suivant += un_jour
    return datetime.combine(suivant.date(), HEURE_OUVERTURE, tzinfo=courant.tzinfo)


def _debut_jour_ouvrable_apres(copie):
    """Return 09:00 of the next working day strictly after the day of `copie`."""
    un_jour = timedelta(days=1)
    suivant = copie + un_jour
    while suivant.weekday() not in JOURS_OUVRES:
        suivant += un_jour
    return datetime.combine(suivant.date(), HEURE_OUVERTURE, tzinfo=copie.tzinfo)


def avancer_heures_ouvrees(depart, heures):
    """Advance `heures` counted only during opening hours.

    The departure may fall outside opening hours: the count starts at the
    next opening period. Nights and weekends do not count.
    """
    heures = int(heures)
    if heures <= 0:
        raise ValueError("heures must be a strictly positive integer.")
    courant = vers_metier(depart)
    if not _ouvert_a(courant):
        courant = prochaine_ouverture(courant)
    reste = heures
    while True:
        fin_jour = datetime.combine(courant.date(), HEURE_FERMETURE, tzinfo=courant.tzinfo)
        duree_jour = fin_jour - courant
        if reste * 3600 <= duree_jour.total_seconds():
            break
        reste -= int(duree_jour.total_seconds() // 3600)
        courant = _debut_jour_ouvrable_apres(courant)
    return courant + timedelta(hours=reste)


def echeance_reponse(soumis_le, heures=DELAI_CIBLE_HEURES_OUVREES):
    """Response deadline after `heures` working hours (default: 24h target)."""
    return avancer_heures_ouvrees(soumis_le, heures)


def heures_ouvrees_entre(debut, fin):
    """Working hours elapsed between two instants (issue #52).

    Counts only Monday-Friday opening hours, so it is the exact inverse of
    `avancer_heures_ouvrees`: nights and weekends do not count, and a start
    outside opening hours only counts from the next opening. Returns a float
    number of hours, 0.0 if `fin` is not after `debut`.
    """
    debut = vers_metier(debut)
    fin = vers_metier(fin)
    if fin <= debut:
        return 0.0

    total = 0.0
    jour = debut.date()
    un_jour = timedelta(days=1)

    while jour <= fin.date():
        if jour.weekday() in JOURS_OUVRES:
            ouverture = datetime.combine(
                jour, HEURE_OUVERTURE, tzinfo=debut.tzinfo
            )
            fermeture = datetime.combine(
                jour, HEURE_FERMETURE, tzinfo=debut.tzinfo
            )
            commence = max(ouverture, debut)
            termine = min(fermeture, fin)

            if termine > commence:
                total += (termine - commence).total_seconds() / 3600

        jour += un_jour

    return total


def _statut_echeance(instant, cible, maximum):
    """Position of `instant` against the 24h target and the 48h maximum."""
    if instant >= maximum:
        return ECHEANCE_DEPASSEE
    if instant >= cible:
        return ECHEANCE_APPROCHE
    return ECHEANCE_DANS_DELAI


def evaluer_delai_reponse(soumis_le, repondu_le):
    """Actual response time of a request, compared with the deadlines (issue #52).

    Returns `heures_ouvrees` (actual response time, in working hours, rounded
    to 2 decimals) and `statut`, using the same thresholds as the advisor
    queue (#51): dans_delai (within the 24h target), approche (target exceeded,
    still within the 48h maximum) or depassee (after the 48h maximum).
    """
    soumis = vers_metier(soumis_le)
    repondu = vers_metier(repondu_le)

    cible = echeance_reponse(soumis, DELAI_CIBLE_HEURES_OUVREES)
    maximum = echeance_reponse(soumis, DELAI_MAX_HEURES_OUVREES)

    return {
        "heures_ouvrees": round(
            heures_ouvrees_entre(soumis, repondu), 2
        ),
        "statut": _statut_echeance(repondu, cible, maximum),
    }


def fenetre_reponse(soumis_le=None):
    """Expected response window, to be communicated to the traveller (issue #53).

    `soumis_le` is optional: defaults to the current moment.
    Returns a neutral dict: `ouvert`, `prochaine_ouverture`, `echeance_cible`,
    `echeance_max`, and ready-to-display labels. The chatbot relies on these
    labels — never on hours hard-coded elsewhere.
    """
    soumis = vers_metier(soumis_le or datetime.now(timezone.utc))
    ouvert = _ouvert_a(soumis)
    prochaine = prochaine_ouverture(soumis)
    if ouvert:
        retour = (
            "Le service est ouvert : votre demande peut être traitée par un conseiller."
        )
    else:
        retour = (
            "Le service est actuellement fermé : votre demande sera traitée "
            "à partir de la prochaine période d'ouverture."
        )
    return {
        "ouvert": ouvert,
        "prochaine_ouverture": prochaine.isoformat(),
        "echeance_cible": echeance_reponse(soumis, DELAI_CIBLE_HEURES_OUVREES).isoformat(),
        "echeance_max": echeance_reponse(soumis, DELAI_MAX_HEURES_OUVREES).isoformat(),
        "message": retour,
        "promesse_delai": (
            f"Les conseillers répondent du lundi au vendredi, de {HEURE_OUVERTURE.strftime('%H:%M')} "
            f"à {HEURE_FERMETURE.strftime('%H:%M')} ; réponse attendue sous "
            f"{DELAI_CIBLE_HEURES_OUVREES} h ouvrées (48 h maximum)."
        ),
    }


def marquer_echeances(record, maintenant=None):
    """Add computed deadlines to a request record (issue #51).

    Adds `echeance_cible` (24h working hours), `echeance_max` (48h) and
    `echeance_statut`: dans_delai, approche (target exceeded) or depassee
    (maximum exceeded). Never modifies the request data itself.
    Once the advisor has answered (issue #52), the status is frozen at the
    moment of the response: an answered request must not turn "depassee" in
    the queue as time goes by.
    """
    if not isinstance(record, dict):
        return record
    soumis = record.get("cree_le")
    try:
        soumis_dt = datetime.fromisoformat(str(soumis))
    except (TypeError, ValueError):
        return record
    present = vers_metier(maintenant or datetime.now(timezone.utc))
    reponse = record.get("reponse")
    if isinstance(reponse, dict):
        try:
            present = vers_metier(datetime.fromisoformat(str(reponse.get("le"))))
        except (TypeError, ValueError):
            pass
    cible = echeance_reponse(soumis_dt, DELAI_CIBLE_HEURES_OUVREES)
    maximum = echeance_reponse(soumis_dt, DELAI_MAX_HEURES_OUVREES)
    record["echeance_cible"] = cible.isoformat()
    record["echeance_max"] = maximum.isoformat()
    record["echeance_statut"] = _statut_echeance(present, cible, maximum)
    return record

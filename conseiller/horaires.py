"""Horaires du conseiller DÉTOUR : source unique de vérité de la disponibilité.

Centralise la configuration des horaires d'ouverture (issue #48) et les
calculs liés au délai de réponse (issues #51 et #53) :
- le conseiller répond du lundi au vendredi, de 09:00 à 18:00, fuseau métier ;
- le samedi et le dimanche ne comptent pas ;
- les demandes peuvent arriver à tout moment : hors ouverture, le compte
  démarre à la prochaine période d'ouverture ;
- le délai cible de réponse est de 24 heures ouvrées, le délai maximum de 48.

Les autres modules lisent cette configuration ici : aucun message du chatbot
ne doit coder les horaires en dur.
"""

from datetime import datetime, time, timedelta, timezone

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover - Python < 3.9, CI tourne en 3.11+
    ZoneInfo = None

# Configuration des horaires (issue #48). Modifiable ici uniquement.
FUSEAU_METIER = "Europe/Paris"
JOURS_OUVRES = frozenset({0, 1, 2, 3, 4})  # weekday() : lundi=0 … vendredi=4
HEURE_OUVERTURE = time(9, 0)
HEURE_FERMETURE = time(18, 0)

# Délais de réponse (issues #51 et #53), en heures ouvrées.
DELAI_CIBLE_HEURES_OUVREES = 24
DELAI_MAX_HEURES_OUVREES = 48

# Seuils d'affichage pour la file du conseiller (issue #51).
ECHEANCE_DANS_DELAI = "dans_delai"
ECHEANCE_APPROCHE = "approche"
ECHEANCE_DEPASSEE = "depassee"


def fuseau_metier():
    """Retourne le fuseau métier (Europe/Paris), ou UTC en repli."""
    if ZoneInfo is None:
        return timezone.utc
    return ZoneInfo(FUSEAU_METIER)


def vers_metier(moment):
    """Convertit un instant (aware ou naïf, supposé UTC) vers le fuseau métier."""
    if not isinstance(moment, datetime):
        raise ValueError("moment doit être un datetime.")
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(fuseau_metier())


def _ouvert_a(copie):
    """Vrai si ce moment métier tombe pendant l'ouverture (jours ouvrés, 9-18h)."""
    return copie.weekday() in JOURS_OUVRES and HEURE_OUVERTURE <= copie.time() < HEURE_FERMETURE


def est_ouvert(moment=None):
    """Vrai si le service est ouvert à ce moment (par défaut : maintenant)."""
    return _ouvert_a(vers_metier(moment or datetime.now(timezone.utc)))


def prochaine_ouverture(moment=None):
    """Prochain instant d'ouverture, après le moment donné (défaut : maintenant)."""
    courant = vers_metier(moment or datetime.now(timezone.utc))
    jour = courant.date()
    debut = datetime.combine(jour, HEURE_OUVERTURE, tzinfo=courant.tzinfo)
    if _ouvert_a(courant):
        return courant
    if debut > courant and jour.weekday() in JOURS_OUVRES:
        return debut
    # Avance jour par jour jusqu'au prochain jour ouvré.
    un_jour = timedelta(days=1)
    suivant = courant + un_jour
    while suivant.weekday() not in JOURS_OUVRES:
        suivant += un_jour
    return datetime.combine(suivant.date(), HEURE_OUVERTURE, tzinfo=courant.tzinfo)


def _debut_jour_ouvrable_apres(copie):
    """Retourne 09:00 du prochain jour ouvré strictement après le jour de `copie`."""
    un_jour = timedelta(days=1)
    suivant = copie + un_jour
    while suivant.weekday() not in JOURS_OUVRES:
        suivant += un_jour
    return datetime.combine(suivant.date(), HEURE_OUVERTURE, tzinfo=copie.tzinfo)


def avancer_heures_ouvrees(depart, heures):
    """Avance `heures` comptées uniquement pendant l'ouverture.

    Le départ peut tomber hors ouverture : le compte démarre à la prochaine
    période d'ouverture. Les nuits et les week-ends ne comptent pas.
    """
    heures = int(heures)
    if heures <= 0:
        raise ValueError("heures doit être un entier strictement positif.")
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
    """Date limite de réponse après `heures` ouvrées (défaut : cible 24h)."""
    return avancer_heures_ouvrees(soumis_le, heures)


def fenetre_reponse(soumis_le=None):
    """Fenêtre de réponse attendue, à communiquer au voyageur (issue #53).

    `soumis_le` est optionnel : par défaut le moment présent est utilisé.
    Retourne un dict neutre : `ouvert`, `prochaine_ouverture`, `echeance_cible`,
    `echeance_max`, et les libellés prêts à afficher. Le chatbot s'appuie sur
    ces libellés — jamais sur des horaires codés en dur ailleurs.
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
    """Ajoute à un record de demande les échéances calculées (issue #51).

    Ajoute `echeance_cible` (24h ouvrées), `echeance_max` (48h ouvrées) et
    `echeance_statut` : dans_delai, approche (cible dépassée) ou depassee
    (maximum dépassé). Ne modifie jamais la demande elle-même.
    """
    if not isinstance(record, dict):
        return record
    soumis = record.get("cree_le")
    try:
        soumis_dt = datetime.fromisoformat(str(soumis))
    except (TypeError, ValueError):
        return record
    present = vers_metier(maintenant or datetime.now(timezone.utc))
    cible = echeance_reponse(soumis_dt, DELAI_CIBLE_HEURES_OUVREES)
    maximum = echeance_reponse(soumis_dt, DELAI_MAX_HEURES_OUVREES)
    if present >= maximum:
        statut = ECHEANCE_DEPASSEE
    elif present >= cible:
        statut = ECHEANCE_APPROCHE
    else:
        statut = ECHEANCE_DANS_DELAI
    record["echeance_cible"] = cible.isoformat()
    record["echeance_max"] = maximum.isoformat()
    record["echeance_statut"] = statut
    return record

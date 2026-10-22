"""Detect what a search could not satisfy and pick verified alternatives (#155).

The program decides what is missing, not the model: it compares the request
with the server results, then hands the model the gaps, the verified
alternatives and the French wording to use.
"""

from datetime import date, datetime

from horaires import fuseau_metier

CATALOGUE_DESTINATIONS = ("Nantes", "Lyon", "Lille")

CASE_DESTINATION = "destination_not_offered"
CASE_ACTIVITY = "activity_not_offered"
CASE_FULLY_BOOKED = "fully_booked"
CASE_OVER_BUDGET = "over_budget"

MAX_ALTERNATIVES = 2

_MONTHS = ("janvier", "février", "mars", "avril", "mai", "juin", "juillet",
           "août", "septembre", "octobre", "novembre", "décembre")


def _french_day(value):
    """'2026-11-07' -> '7 novembre'. Returns the raw value if unparsable."""
    try:
        day = date.fromisoformat(value)
    except (TypeError, ValueError):
        return value or ""
    return f"{day.day} {_MONTHS[day.month - 1]}"


def _checked_at(value):
    """ISO timestamp -> '19/10 à 09:40' in the business timezone, or ''."""
    try:
        moment = datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return ""
    if moment.tzinfo is not None:
        moment = moment.astimezone(fuseau_metier())
    return moment.strftime("%d/%m à %H:%M")


def _missing(case, sentence, **details):
    return {"case": case, "sentence": sentence, **details}


def _alternative_sentence(item, checked_at):
    sentence = (f"Je peux vous proposer à la place {item['nom']}, "
                f"à {item['prix_unitaire_eur']} € par personne")
    if checked_at:
        sentence += f", prix vérifié le {checked_at}"
    return sentence + "."


def _pick_alternatives(results, wanted_types):
    """Available, within-budget results of the same type as a gap.

    A hotel never replaces an activity: an alternative only makes sense for
    the kind of service that is missing.
    """
    usable = [r for r in results
              if r.get("type") in wanted_types
              and r.get("disponible") is True and r.get("dans_budget") is not False]
    return usable[:MAX_ALTERNATIVES]


def analyze_no_result(request, search):
    """Return the gaps of a search and the verified alternatives.

    `request` holds the request fields, `search` the stored server search.
    The result always has `missing`, `alternatives` and `instruction`;
    `missing` is empty when the search satisfies everything the program can
    check.
    """
    request = request if isinstance(request, dict) else {}
    search = search if isinstance(search, dict) else {}
    results = [r for r in search.get("resultats") or [] if isinstance(r, dict)]
    destination = request.get("destination") or ""
    departure = _french_day(request.get("date_depart"))
    budget = request.get("budget_max_par_personne")
    checked_at = _checked_at(search.get("consulte_le"))
    missing = []

    if not results:
        missing.append(_missing(
            CASE_DESTINATION,
            f"Nous ne proposons pas encore {destination}. Nos destinations du "
            f"moment sont {', '.join(CATALOGUE_DESTINATIONS[:-1])} et "
            f"{CATALOGUE_DESTINATIONS[-1]}.",
            destination=destination,
        ))

    matched = set()
    for item in results:
        matched.update(item.get("activites_correspondantes") or [])
    for activity in request.get("activites") or []:
        if results and activity not in matched:
            missing.append(_missing(
                CASE_ACTIVITY,
                f"Je n'ai pas d'activité « {activity} » à {destination} "
                "dans notre catalogue.",
                activity=activity,
            ))

    for item in results:
        if item.get("disponible") is False:
            missing.append(_missing(
                CASE_FULLY_BOOKED,
                f"{item.get('nom')} est complet le {departure}.",
                prestation_id=item.get("id"), type=item.get("type"),
            ))
        elif item.get("dans_budget") is False and type(budget) is int:
            gap = item.get("prix_unitaire_eur", 0) - budget
            missing.append(_missing(
                CASE_OVER_BUDGET,
                f"{item.get('nom')} dépasse votre budget de {gap} € par personne.",
                prestation_id=item.get("id"), type=item.get("type"), gap_eur=gap,
            ))

    wanted = {m.get("type") for m in missing if m.get("type")}
    # A missing activity, or a free-text wish the program cannot match
    # (a Christmas market), is replaced by an activity.
    if not missing or any(m["case"] == CASE_ACTIVITY for m in missing):
        wanted.add("activite")
    picked = _pick_alternatives(results, wanted)
    alternatives = [{
        "id": item.get("id"),
        "nom": item.get("nom"),
        "type": item.get("type"),
        "prix_unitaire_eur": item.get("prix_unitaire_eur"),
        "sentence": _alternative_sentence(item, checked_at),
    } for item in picked]

    return {
        "missing": missing,
        "alternatives": alternatives,
        "instruction": _instruction(missing, alternatives),
    }


def _instruction(missing, alternatives):
    """Model instruction, in French like the rest of the prompts."""
    if not missing:
        return (
            "Le programme n'a détecté aucun manque. Si le voyageur a demandé "
            "une prestation précise absente des résultats (par exemple un "
            "marché de Noël), dis-le d'abord, puis propose une alternative de "
            "`alternatives`, et termine par une question."
        )
    lines = [
        "Certaines envies du voyageur n'ont pas de résultat. Dans ta réponse :",
        "1. Dis d'abord clairement ce qui n'est pas possible, avec ces phrases :",
    ]
    lines += [f"   - {m['sentence']}" for m in missing]
    if alternatives:
        lines.append("2. Propose ensuite une ou deux de ces alternatives "
                     "vérifiées, et seulement celles-ci :")
        lines += [f"   - {a['sentence']}" for a in alternatives]
    else:
        lines.append("2. Aucune alternative vérifiée n'existe : ne propose "
                     "aucune prestation. Propose de changer la date, le "
                     "budget ou la destination.")
    lines.append("3. Termine par une question courte, par exemple « Ça vous irait ? ».")
    lines.append("Ne présente jamais une prestation manquante comme disponible. "
                 "Pas d'humour sur un manque, pas de « Erreur : ».")
    return "\n".join(lines)

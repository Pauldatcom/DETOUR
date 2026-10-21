"""Check which customer constraints a travel proposal respects (#41).

The program checks the constraints, not the model: the advisor sees what was
respected, what could not be checked and what was not respected.
"""

STATUT_OK = "ok"
STATUT_A_VERIFIER = "a_verifier"
STATUT_NON_RESPECTEE = "non_respectee"


def _line(constraint, status, detail):
    return {"contrainte": constraint, "statut": status, "detail": detail}


def _price_per_person(proposition, travelers):
    total = proposition.get("prix_total_eur")
    if type(total) is not int:
        total = sum(p.get("prix_unitaire_eur", 0) * p.get("quantite", 1)
                    for p in proposition.get("prestations") or [])
    return round(total / travelers)


def verifier_contraintes(demande, proposition, resultats=None):
    """Return one line per customer constraint, with a status and a short detail.

    `demande` is the request fields, `proposition` the proposal, and
    `resultats` the server results used to build it.
    """
    request = demande.get("demande", demande) if isinstance(demande, dict) else {}
    proposition = proposition if isinstance(proposition, dict) else {}
    lines = []

    # Budget: total price per person against the customer's budget.
    travelers = request.get("nombre_voyageurs")
    budget = request.get("budget_max_par_personne")
    if type(travelers) is int and travelers > 0 and type(budget) is int:
        per_person = _price_per_person(proposition, travelers)
        if per_person <= budget:
            lines.append(_line("budget", STATUT_OK,
                               f"{budget} € max par personne → {per_person} € par personne"))
        else:
            lines.append(_line("budget", STATUT_NON_RESPECTEE,
                               f"Budget dépassé : {per_person} € > {budget} €"))
    else:
        lines.append(_line("budget", STATUT_A_VERIFIER, "Budget ou nombre de voyageurs non fourni"))

    # Dates: availability is checked by the server on the departure date only.
    if request.get("date_depart") and request.get("date_retour"):
        lines.append(_line("dates", STATUT_OK,
                           f"Du {request['date_depart']} au {request['date_retour']} "
                           "(disponibilité vérifiée à la date de départ)"))
    else:
        lines.append(_line("dates", STATUT_A_VERIFIER, "Dates non fournies"))

    # Travelers.
    if type(travelers) is int and travelers > 0:
        lines.append(_line("voyageurs", STATUT_OK, f"{travelers} personne(s)"))
    else:
        lines.append(_line("voyageurs", STATUT_A_VERIFIER, "Nombre de voyageurs non fourni"))

    # Wished activities: matched against the server tags of the proposed services.
    by_id = {r["id"]: r for r in resultats or [] if isinstance(r, dict) and r.get("id")}
    proposed = set()
    for service in proposition.get("prestations") or []:
        source = by_id.get(service.get("id")) if isinstance(service, dict) else None
        if source:
            proposed.update(source.get("activites_correspondantes") or [])
    for activity in request.get("activites") or []:
        if activity in proposed:
            lines.append(_line(f"activite:{activity}", STATUT_OK,
                               f"Activité « {activity} » présente dans la proposition"))
        else:
            lines.append(_line(f"activite:{activity}", STATUT_NON_RESPECTEE,
                               f"Aucune prestation ne correspond à « {activity} »"))

    # Level: not stored in the fictional catalogue, the advisor must check it.
    if request.get("niveau_aventure"):
        lines.append(_line("niveau", STATUT_A_VERIFIER,
                           f"Niveau « {request['niveau_aventure']} » non vérifiable au catalogue"))
    else:
        lines.append(_line("niveau", STATUT_A_VERIFIER, "Niveau non fourni par le client → à demander"))

    return lines
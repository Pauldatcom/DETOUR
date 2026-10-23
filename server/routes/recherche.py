"""Travel request search route."""


def _optional_int(value):
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return -1


def recherche(req):
    query = req.query
    raw_activites = query.get("activites", [""])[0]
    params = {
        "destination": query.get("destination", [None])[0],
        "date_depart": query.get("date_depart", [None])[0],
        "date_retour": query.get("date_retour", [None])[0],
        "participants": _optional_int(query.get("participants", [None])[0]),
        "budget_max": _optional_int(query.get("budget_max", [None])[0]),
        "type_voyage": query.get("type_voyage", [None])[0],
        "activites": [a for a in raw_activites.split(",") if a],
    }
    return req.send_json(200, req.ctx.store.search(req.team, params))


def enregistrer(router):
    router.route("GET", r"/api/v1/recherche")(recherche)

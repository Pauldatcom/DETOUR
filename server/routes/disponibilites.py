"""Availability lookup route."""


def disponibilites(req):
    try:
        participants = int(req.query.get("participants", [""])[0])
    except ValueError:
        participants = None
    result = req.ctx.store.availability(
        req.team,
        req.query.get("prestation_id", [None])[0],
        req.query.get("date", [None])[0],
        participants,
    )
    return req.send_json(200, result)


def enregistrer(router):
    router.route("GET", r"/api/v1/disponibilites")(disponibilites)

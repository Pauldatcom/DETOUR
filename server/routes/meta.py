"""Health and metadata routes."""


def health(req):
    return req.send_json(200, {"status": "ok", "simulation": True})


def enregistrer(router):
    router.route("GET", r"/health")(health)

"""Health and metadata routes."""


def health(req):
    return req.send_json(200, {"status": "ok", "simulation": True})


def openapi(req):
    return req.send_static_yaml("openapi-supplier.yaml")


def enregistrer(router):
    router.route("GET", r"/health")(health)
    router.route("GET", r"/openapi.yaml")(openapi)

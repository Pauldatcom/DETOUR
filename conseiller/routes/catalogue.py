"""Catalogue route: services offered by the fictional server."""

from httpd.errors import ApiError


def catalogue(req):
    if req.ctx.supplier is None:
        raise ApiError(503, "supplier_not_configured", "Serveur fictif non configuré.")
    prestations = req.ctx.supplier.catalogue()
    req.send_json(200, {"prestations": prestations, "simulation": True})


def enregistrer(router):
    router.route("GET", r"/api/catalogue")(catalogue)

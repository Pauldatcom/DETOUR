"""Catalogue and prestation detail routes."""

import copy

from catalogue import BY_ID, PRESTATIONS

from httpd.errors import ApiError


def filtrer_prestations(type_filter=None, destination_filter=None):
    """Return matching prestations, preserving the historical filter semantics."""
    return [copy.deepcopy(item) for item in PRESTATIONS
            if (not type_filter or item["type"] == type_filter)
            and (not destination_filter
                 or item["destination"].casefold() == destination_filter.casefold())]


def catalogue(req):
    type_filter = req.query.get("type", [None])[0]
    destination_filter = req.query.get("destination", [None])[0]
    items = filtrer_prestations(type_filter, destination_filter)
    return req.send_json(200, {"prestations": items, "simulation": True})


def prestation(req, prestation_id):
    item = BY_ID.get(prestation_id)
    if not item:
        raise ApiError(404, "prestation_not_found", "Prestation inconnue.")
    return req.send_json(200, {"prestation": item, "simulation": True})


def enregistrer(router):
    router.route("GET", r"/api/v1/catalogue")(catalogue)
    router.route("GET", r"/api/v1/prestations/(?P<prestation_id>[a-z0-9-]+)")(prestation)

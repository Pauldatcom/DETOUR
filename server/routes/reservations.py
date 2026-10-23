"""Reservation routes: confirm, list and cancel."""


def _approval_key(req):
    return req.handler.headers.get("X-Approval-Key")


def confirmer(req):
    reservation = req.ctx.store.confirm(req.team, req.read_json(), _approval_key(req))
    return req.send_json(201, {"reservation": reservation})


def lister(req):
    return req.send_json(200, {"reservations": req.ctx.store.list_reservations(req.team),
                               "simulation": True})


def annuler(req, reservation_id):
    reservation = req.ctx.store.cancel(req.team, reservation_id, _approval_key(req))
    return req.send_json(200, {"reservation": reservation})


def enregistrer(router):
    router.route("POST", r"/api/v1/reservations")(confirmer)
    router.route("GET", r"/api/v1/reservations")(lister)
    router.route(
        "POST",
        r"/api/v1/reservations/(?P<reservation_id>res_[a-f0-9]+)/annuler",
    )(annuler)

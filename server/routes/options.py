"""Option routes: hold then list places for a team."""


def creer(req):
    option = req.ctx.store.create_option(req.team, req.read_json())
    return req.send_json(201, {"option": option})


def lister(req):
    return req.send_json(200, {"options": req.ctx.store.list_options(req.team),
                               "simulation": True})


def enregistrer(router):
    router.route("POST", r"/api/v1/options")(creer)
    router.route("GET", r"/api/v1/options")(lister)

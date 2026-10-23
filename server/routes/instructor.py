"""Instructor routes: simulate catalogue incidents and reset a team."""


def traiter(req, team, action):
    if action == "reset":
        req.ctx.store.reset_team(team)
        return req.send_json(200, {"equipe": team, "reinitialisee": True, "simulation": True})
    return req.send_json(201, req.ctx.store.incident(team, req.read_json()))


def enregistrer(router):
    router.route(
        "POST",
        r"/api/v1/instructor/teams/(?P<team>[a-zA-Z0-9_-]+)/(?P<action>incidents|reset)",
    )(traiter)

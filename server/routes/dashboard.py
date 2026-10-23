"""Read-only dashboard: pages, brand assets and session-scoped API."""

from catalogue import BY_ID

from httpd.errors import ApiError

from .prestations import filtrer_prestations

HTML = "text/html; charset=utf-8"
CSS = "text/css; charset=utf-8"
JAVASCRIPT = "text/javascript; charset=utf-8"


def _asset(filename, content_type):
    def handler(req):
        return req.send_dashboard_asset(filename, content_type)
    return handler


def brand(req, filename):
    # Historical behaviour: the last path segment is the requested logo,
    # including for nested or empty paths (then rejected as not in the kit).
    return req.send_brand_asset(filename.rsplit("/", 1)[-1])


def login(req):
    req.require_same_origin()
    supplied = req.read_json().get("team_key")
    token, team = req.ctx.store.new_dashboard_session(supplied)
    return req.send_json(200, {"equipe": team, "expire_dans_secondes": 1800},
                         {"Set-Cookie": req.session_cookie_header(token, 1800)})


def logout(req):
    req.require_same_origin()
    req.ctx.store.close_dashboard_session(req.dashboard_cookie())
    return req.send_json(200, {"deconnecte": True},
                         {"Set-Cookie": req.session_cookie_header("", 0)})


def catalogue(req):
    req.dashboard_team()
    type_filter = req.query.get("type", [None])[0]
    destination_filter = req.query.get("destination", [None])[0]
    items = filtrer_prestations(type_filter, destination_filter)
    return req.send_json(200, {"prestations": items, "simulation": True})


def prestation(req, prestation_id):
    req.dashboard_team()
    item = BY_ID.get(prestation_id)
    if not item:
        raise ApiError(404, "prestation_not_found", "Prestation inconnue.")
    return req.send_json(200, {"prestation": item, "simulation": True})


def disponibilites(req):
    team = req.dashboard_team()
    try:
        participants = int(req.query.get("participants", [""])[0])
    except ValueError:
        participants = None
    result = req.ctx.store.availability(
        team,
        req.query.get("prestation_id", [None])[0],
        req.query.get("date", [None])[0],
        participants,
    )
    return req.send_json(200, result)


def options(req):
    team = req.dashboard_team()
    return req.send_json(200, {"options": req.ctx.store.list_options(team),
                               "simulation": True})


def reservations(req):
    team = req.dashboard_team()
    return req.send_json(200, {"reservations": req.ctx.store.list_reservations(team),
                               "simulation": True})


def methode_refusee(req, reste=None):
    raise ApiError(405, "method_not_allowed", "Le tableau de bord ne modifie pas les réservations.")


def introuvable(req, reste=None):
    req.dashboard_team()
    raise ApiError(404, "not_found", "Route inconnue.")


def enregistrer(router):
    page = _asset("dashboard.html", HTML)
    router.route("GET", r"/dashboard")(page)
    router.route("GET", r"/dashboard/")(page)
    router.route("GET", r"/dashboard/dashboard\.css")(_asset("dashboard.css", CSS))
    router.route("GET", r"/dashboard/dashboard\.js")(_asset("dashboard.js", JAVASCRIPT))
    router.route("GET", r"/dashboard/brand/(?P<filename>.*)")(brand)
    router.route("POST", r"/dashboard/api/login")(login)
    router.route("POST", r"/dashboard/api/logout")(logout)
    router.route("GET", r"/dashboard/api/catalogue")(catalogue)
    router.route(
        "GET",
        r"/dashboard/api/prestations/(?P<prestation_id>[a-z0-9-]+)",
    )(prestation)
    router.route("GET", r"/dashboard/api/disponibilites")(disponibilites)
    router.route("GET", r"/dashboard/api/options")(options)
    router.route("GET", r"/dashboard/api/reservations")(reservations)
    # Historical behaviour: unknown POSTs under /dashboard are 405, while
    # unknown GETs require a dashboard session before returning 404.
    router.route("POST", r"/dashboard(?P<reste>/.*)?")(methode_refusee)
    router.route("GET", r"/dashboard(?P<reste>/.*)?")(introuvable)

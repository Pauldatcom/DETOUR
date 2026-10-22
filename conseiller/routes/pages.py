"""Portal pages and static file routes (vanilla, historical)."""


def _statique(filename):
    def handler(req):
        req.send_static(filename)
    return handler


def health(req):
    req.send_json(200, {"status": "ok", "simulation": True})


def login(req):
    req.send_static("login.html")


def chat(req):
    """Traveler page: role-based redirect, otherwise the vanilla chat."""
    if req.ctx.users is not None:
        session = req.session
        if session and session["role"] == "conseiller":
            return req.redirect("/conseiller")
        if not (session and session["role"] == "client"):
            return req.redirect("/login")
    req.send_static("chat.html")


def conseiller(req):
    """Advisor page: role-based redirect, otherwise the vanilla dashboard."""
    if req.ctx.users is not None:
        session = req.session
        if session and session["role"] == "client":
            return req.redirect("/chat")
        if not (session and session["role"] == "conseiller"):
            return req.redirect("/login")
    req.send_static("conseiller.html")


FICHIERS_STATIQUES = ("/app.css", "/app.js", "/pages.js", "/pages-propositions.js",
                      "/agent-widget.css", "/agent-widget.js")


def enregistrer(router):
    router.route("GET", r"/health")(health)
    for asset in FICHIERS_STATIQUES:
        router.route("GET", asset)(_statique(asset.lstrip("/")))
    router.route("GET", r"/login")(login)
    router.route("GET", r"/")(chat)
    router.route("GET", r"/index\.html")(chat)
    router.route("GET", r"/chat")(chat)
    router.route("GET", r"/conseiller")(conseiller)

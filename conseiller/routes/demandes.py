"""Travel request routes: list, create, search, qualification, status."""

from httpd.errors import ApiError
from httpd.sessions import nom_conseiller

from lecture import marquer_a_revoir_si_ecart
from store import criteres_depuis_demande


def mes_demandes(req):
    session = req.client_exige()
    store = req.ctx.store
    demandes = [d for d in store.lister()
                if d.get("demande", {}).get("user_id") == session.get("user_id")]
    demandes.sort(key=lambda d: d.get("cree_le", ""), reverse=True)
    if req.ctx.users is not None:
        for d in demandes:
            d["client"] = req.ctx.users.obtenir(d.get("demande", {}).get("user_id", ""))
    req.send_json(200, {"demandes": demandes, "simulation": True})


def lister(req):
    req.admin_exige()
    store = req.ctx.store
    # The advisor only gets requests the traveler approved.
    demandes = store.list_for_advisor()
    demandes.sort(key=lambda d: d.get("cree_le", ""), reverse=True)
    if req.ctx.users is not None:
        for d in demandes:
            d["client"] = req.ctx.users.obtenir(d.get("demande", {}).get("user_id", ""))
    req.send_json(200, {"demandes": demandes, "simulation": True})


def obtenir(req, id):
    record = req.ctx.store.obtenir(id)
    if not record:
        raise ApiError(404, "demande_not_found", "Demande introuvable.")
    req.send_json(200, {"demande": record, "simulation": True})


def creer(req):
    data = req.read_json()
    if req.ctx.users is not None:
        session = req.client_exige()
        # Never trust a client-supplied owner id.
        data["user_id"] = session.get("user_id", "")
    record = req.ctx.store.creer(data)
    req.send_json(201, {"demande": record, "simulation": True})


def recherche(req, id):
    store = req.ctx.store
    record = store.obtenir(id)
    if not record:
        raise ApiError(404, "demande_not_found", "Demande introuvable.")
    if req.ctx.supplier is None:
        raise ApiError(503, "supplier_not_configured", "Serveur fictif non configuré.")
    resultat = req.ctx.supplier.rechercher(criteres_depuis_demande(record))
    recherche = store.ajouter_recherche(id, resultat)
    # A re-read can reveal an ecart with proposal v1; v1 is never rewritten.
    marquer_a_revoir_si_ecart(store, req.ctx.propositions, id, recherche)
    dem = store.obtenir(id)
    req.send_json(201, {
        "recherche": recherche,
        "demande": dem,
        "simulation": True,
    })


def qualification(req, id):
    session = req.admin_exige()
    data = req.read_json()
    record = req.ctx.store.definir_qualification(
        id, data.get("qualification"), acteur="conseiller",
        par=nom_conseiller(session), motif=data.get("motif"))
    if record is None:
        raise ApiError(404, "demande_not_found", "Demande introuvable.")
    if req.ctx.users is not None:
        record["client"] = req.ctx.users.obtenir(record.get("demande", {}).get("user_id", ""))
    req.send_json(200, {"demande": record, "simulation": True})


def correction(req, id):
    # Only a connected advisor corrects a request; the agent cannot.
    session = req.admin_exige()
    data = req.read_json()
    record = req.ctx.store.corriger(id, data.get("champs"),
                                    nom_conseiller(session), data.get("motif"))
    if record is None:
        raise ApiError(404, "demande_not_found", "Demande introuvable.")
    if req.ctx.users is not None:
        record["client"] = req.ctx.users.obtenir(record.get("demande", {}).get("user_id", ""))
    req.send_json(200, {"demande": record, "simulation": True})


def reponse(req, id):
    """#52: the advisor answers the customer request.

    Author, date and time are set by the server, never by the client.
    """
    session = req.admin_exige()
    data = req.read_json()
    record = req.ctx.store.repondre(id, data.get("message"), nom_conseiller(session))
    if record is None:
        raise ApiError(404, "demande_not_found", "Demande introuvable.")
    if req.ctx.users is not None:
        record["client"] = req.ctx.users.obtenir(record.get("demande", {}).get("user_id", ""))
    req.send_json(201, {"demande": record, "simulation": True})


def approbation(req, id):
    session = req.client_exige()
    data = req.read_json()
    record = req.ctx.store.approve_by_traveler(id, session.get("user_id", ""),
                                               data.get("confirme"))
    if record is None:
        raise ApiError(404, "demande_not_found", "Demande introuvable.")
    req.send_json(200, {"demande": record, "simulation": True})


def statut(req, id):
    session = req.admin_exige()
    data = req.read_json()
    record = req.ctx.store.changer_statut(id, data.get("statut"),
                                          nom_conseiller(session), data.get("motif"))
    if record is None:
        raise ApiError(404, "demande_not_found", "Demande introuvable.")
    if req.ctx.users is not None:
        record["client"] = req.ctx.users.obtenir(record.get("demande", {}).get("user_id", ""))
    req.send_json(200, {"demande": record, "simulation": True})


def enregistrer(router):
    router.route("GET", r"/api/mes-demandes")(mes_demandes)
    router.route("GET", r"/api/demandes")(lister)
    router.route("GET", r"/api/demandes/(?P<id>dem_[a-f0-9]+)")(obtenir)
    router.route("POST", r"/api/demandes")(creer)
    router.route("POST", r"/api/demandes/(?P<id>dem_[a-f0-9]+)/recherche")(recherche)
    router.route("POST", r"/api/demandes/(?P<id>dem_[a-f0-9]+)/reponse")(reponse)
    router.route("POST", r"/api/demandes/(?P<id>dem_[a-f0-9]+)/approbation")(approbation)
    router.route("PATCH", r"/api/demandes/(?P<id>dem_[a-f0-9]+)/qualification")(qualification)
    router.route("PATCH", r"/api/demandes/(?P<id>dem_[a-f0-9]+)/correction")(correction)
    router.route("PATCH", r"/api/demandes/(?P<id>dem_[a-f0-9]+)/statut")(statut)

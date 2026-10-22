"""Proposal routes: list, create, advisor decisions, status."""

from httpd.errors import ApiError
from httpd.sessions import nom_conseiller

from lecture import enrichir_propositions, proposition_avec_changements
from utils import DECISION_ACCEPTER, DECISION_CORRECTION, DECISION_REFUSER


def mes_propositions(req):
    session = req.client_exige()
    props = req.ctx.propositions.lister_par_user(session.get("user_id", ""), req.ctx.store)
    props = enrichir_propositions(props, req.ctx.store)
    props.sort(key=lambda p: p.get("cree_le", ""), reverse=True)
    req.send_json(200, {"propositions": props, "simulation": True})


def lister(req):
    req.admin_exige()
    props = enrichir_propositions(req.ctx.propositions.lister(), req.ctx.store)
    props.sort(key=lambda p: p.get("cree_le", ""), reverse=True)
    req.send_json(200, {"propositions": props, "simulation": True})


def obtenir(req, id):
    record = req.ctx.propositions.obtenir(id)
    if not record:
        raise ApiError(404, "proposition_not_found", "Proposition introuvable.")
    enrichie = enrichir_propositions([record], req.ctx.store)[0]
    req.send_json(200, {"proposition": enrichie, "simulation": True})


def decider(req, id, action):
    """Advisor decision on a proposal: accept, correct or refuse.

    A motif is required for a correction and a refusal; accept can do without it.
    """
    session = req.admin_exige()
    data = req.read_json()
    decisions = {
        "accepter": DECISION_ACCEPTER,
        "correction": DECISION_CORRECTION,
        "refuser": DECISION_REFUSER,
    }
    record = req.ctx.propositions.decider(id, decisions[action],
                                          nom_conseiller(session),
                                          data.get("motif"), data.get("instructions"))
    if record is None:
        raise ApiError(404, "proposition_not_found", "Proposition introuvable.")
    dem = req.ctx.store.obtenir(record.get("demande_id", ""))
    recherches = (dem or {}).get("recherches") or []
    enrichie = proposition_avec_changements(record, recherches)
    req.send_json(200, {"proposition": enrichie, "simulation": True})


def decisions(req, id):
    """Keep / replace / remove a modified line — without sending or calling the supplier."""
    session = req.admin_exige()
    data = req.read_json()
    propositions = req.ctx.propositions
    record = propositions.enregistrer_decision(
        id,
        data.get("prestation_id"),
        data.get("choix"),
        session.get("nom", ""),
        data.get("motif"),
        remplacement_id=data.get("remplacement_id"),
    )
    if record is None:
        raise ApiError(404, "proposition_not_found", "Proposition introuvable.")
    dem = req.ctx.store.obtenir(record.get("demande_id", ""))
    recherches = (dem or {}).get("recherches") or []
    enrichie = proposition_avec_changements(record, recherches)
    # When every modified line has a decision, create the v2 draft.
    recherche = recherches[-1] if recherches else None
    prop_v2 = propositions.creer_v2_si_complet(
        record["id"], recherche, conseiller=session.get("nom", ""))
    payload = {"proposition": enrichie, "simulation": True}
    if prop_v2 is not None:
        payload["proposition_v2"] = prop_v2
        # v1 must remain readable with its original prices.
        payload["proposition"] = enrichir_propositions(
            [propositions.obtenir(record["id"])], req.ctx.store)[0]
    req.send_json(200, payload)


def generer(req, id):
    store = req.ctx.store
    record = store.obtenir(id)
    if not record:
        raise ApiError(404, "demande_not_found", "Demande introuvable.")
    if req.ctx.agent is None:
        raise ApiError(503, "agent_not_configured",
                       "Agent non configuré : définir OPENROUTER_API_KEY.")
    recherches = record.get("recherches", [])
    recherche = recherches[-1] if recherches else None
    prop_data = req.ctx.agent.generer_proposition(record, recherche)
    session = req.admin_exige()
    prop = req.ctx.propositions.creer(id, prop_data, conseiller=session.get("nom", ""))
    req.send_json(201, {"proposition": prop, "simulation": True})


def creer(req, id):
    record = req.ctx.store.obtenir(id)
    if not record:
        raise ApiError(404, "demande_not_found", "Demande introuvable.")
    data = req.read_json()
    session = req.admin_exige()
    prop = req.ctx.propositions.creer(id, data, conseiller=session.get("nom", ""))
    req.send_json(201, {"proposition": prop, "simulation": True})


def changer_statut(req, id):
    session = req.admin_exige()
    data = req.read_json()
    record = req.ctx.propositions.changer_statut(
        id, data.get("statut"), nom_conseiller(session), data.get("motif"))
    if record is None:
        raise ApiError(404, "proposition_not_found", "Proposition introuvable.")
    req.send_json(200, {"proposition": record, "simulation": True})


def mettre_a_jour(req, id):
    data = req.read_json()
    record = req.ctx.propositions.mettre_a_jour(id, data)
    if record is None:
        raise ApiError(404, "proposition_not_found", "Proposition introuvable.")
    req.send_json(200, {"proposition": record, "simulation": True})


def enregistrer(router):
    router.route("GET", r"/api/mes-propositions")(mes_propositions)
    router.route("GET", r"/api/propositions")(lister)
    router.route("GET", r"/api/propositions/(?P<id>prop_[a-f0-9]+)")(obtenir)
    router.route("POST", r"/api/propositions/(?P<id>prop_[a-f0-9]+)/(?P<action>accepter|correction|refuser)")(decider)
    router.route("POST", r"/api/propositions/(?P<id>prop_[a-f0-9]+)/decisions")(decisions)
    router.route("POST", r"/api/demandes/(?P<id>dem_[a-f0-9]+)/propositions/generer")(generer)
    router.route("POST", r"/api/demandes/(?P<id>dem_[a-f0-9]+)/propositions")(creer)
    router.route("PATCH", r"/api/propositions/(?P<id>prop_[a-f0-9]+)/statut")(changer_statut)
    router.route("PATCH", r"/api/propositions/(?P<id>prop_[a-f0-9]+)")(mettre_a_jour)

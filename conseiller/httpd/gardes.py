"""Access guard for API routes: checks the session based on the path.

Middleware run before any /api/ route. Reproduces the historical portal rules:
- test/dev mode (users=None): routes open, no check;
- authentication, configuration and metrics routes: public;
- /api/mes-* and /api/account*: traveler session;
- /api/stats, /api/propositions: advisor session;
- request/proposal reads: advisor or owner;
- writes (PATCH, decisions, proposals, advisor responses, advisor chat): advisor only;
- traveler approval: owner only;
- rest: valid session (traveler or advisor).
"""

import re

from propositions import visible_par_voyageur

from .errors import ApiError

ROUTES_PUBLIQUES = (
    "/api/login", "/api/register", "/api/login-conseiller",
    "/api/auth/google", "/api/auth/google/callback",
    "/api/config", "/api/disponibilite", "/api/session", "/api/logout",
)


def _proprietaire(store, dem_id, session):
    """True when the session user owns the request."""
    record = store.obtenir(dem_id)
    return bool(record) and record.get("demande", {}).get("user_id") == session.get("user_id")


def _proprietaire_proposition(prop_store, demand_store, prop_id, session):
    """True when the session user owns the proposal via its parent request."""
    prop = prop_store.obtenir(prop_id)
    if not prop:
        return False
    dem = demand_store.obtenir(prop.get("demande_id", ""))
    return bool(dem) and dem.get("demande", {}).get("user_id") == session.get("user_id")


def verifier_acces(req, method, path):
    """Raise an ApiError when the session cannot access the route."""
    if req.ctx.users is None:
        return  # test/dev mode: API routes remain open
    if path in ROUTES_PUBLIQUES:
        return  # public routes
    session = req.session
    admin = session and session["role"] == "conseiller"
    client = session and session["role"] == "client"

    if path in ("/api/mes-demandes", "/api/mes-propositions",
                "/api/account", "/api/account/password"):
        if not client:
            raise ApiError(401, "auth_requise",
                           "Connectez-vous avec un compte voyageur.")
    elif method == "POST" and path == "/api/demandes":
        if not client:
            raise ApiError(401, "auth_requise",
                           "Connectez-vous pour envoyer une demande.")
    elif path in ("/api/stats", "/api/propositions") and method == "GET":
        if not admin:
            raise ApiError(401, "auth_requise", "Accès conseiller requis.")
    elif method == "POST" and path == "/api/conseiller/chat":
        # #115: the advisor assistant is for advisors only.
        if not admin:
            raise ApiError(401, "auth_requise", "Accès conseiller requis.")
    elif method == "POST" and re.fullmatch(
            r"/api/demandes/(dem_[a-f0-9]+)/reponse", path):
        # #52: only an advisor answers a customer request.
        if not admin:
            raise ApiError(401, "auth_requise", "Accès conseiller requis.")
    elif method == "GET" and (m := re.fullmatch(r"/api/demandes/(dem_[a-f0-9]+)", path)):
        if not (admin or (client and _proprietaire(req.ctx.store, m.group(1), session))):
            raise ApiError(404, "demande_not_found", "Demande introuvable.")
    elif method == "GET" and (m := re.fullmatch(r"/api/propositions/(prop_[a-f0-9]+)", path)):
        if not (admin or (client
                          and _proprietaire_proposition(
                              req.ctx.propositions, req.ctx.store, m.group(1), session)
                          and visible_par_voyageur(req.ctx.propositions.obtenir(m.group(1))))):
            raise ApiError(404, "proposition_not_found", "Proposition introuvable.")
    elif method == "POST" and (m := re.fullmatch(
            r"/api/demandes/(dem_[a-f0-9]+)/approbation", path)):
        if not (client and _proprietaire(req.ctx.store, m.group(1), session)):
            raise ApiError(404, "demande_not_found", "Demande introuvable.")
    elif method == "POST" and (m := re.fullmatch(
            r"/api/demandes/(dem_[a-f0-9]+)/recherche", path)):
        if not (admin or (client and _proprietaire(req.ctx.store, m.group(1), session))):
            raise ApiError(401, "auth_requise",
                           "Connectez-vous pour relancer une recherche.")
    elif method == "POST" and re.fullmatch(
            r"/api/demandes/(dem_[a-f0-9]+)/propositions(?:/generer)?", path):
        if not admin:
            raise ApiError(401, "auth_requise", "Accès conseiller requis.")
    elif method == "POST" and re.fullmatch(
            r"/api/propositions/(prop_[a-f0-9]+)/decisions", path):
        if not admin:
            raise ApiError(401, "auth_requise", "Accès conseiller requis.")
    elif method == "POST" and re.fullmatch(
            r"/api/propositions/(prop_[a-f0-9]+)/(accepter|correction|refuser)", path):
        if not admin:
            raise ApiError(401, "auth_requise", "Accès conseiller requis.")
    elif method == "PATCH":
        if not admin:
            raise ApiError(401, "auth_requise", "Accès conseiller requis.")
    else:
        if not (admin or client):
            raise ApiError(401, "auth_requise", "Authentification requise.")

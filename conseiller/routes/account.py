"""Traveler account routes: profile, email/name and password."""

from httpd.errors import ApiError

from users import UserError


def obtenir(req):
    session = req.client_exige()
    users = req.ctx.users
    if users is None:
        raise ApiError(503, "auth_desactivee", "Portail non configuré (users).")
    compte = users.obtenir(session.get("user_id", ""))
    if compte is None:
        raise UserError("Compte introuvable.", 404, "compte_introuvable")
    compte["mot_de_passe_defini"] = users.mot_de_passe_defini(session["user_id"])
    req.send_json(200, {"compte": compte})


def mettre_a_jour(req):
    session = req.client_exige()
    users = req.ctx.users
    if users is None:
        raise ApiError(503, "auth_desactivee", "Portail non configuré (users).")
    data = req.read_json()
    if users.mot_de_passe_defini(session.get("user_id", "")):
        if not users.verifier_mot_de_passe(
                session.get("user_id", ""), data.get("mot_de_passe_actuel", "")):
            raise UserError("Le mot de passe actuel est incorrect.",
                            401, "mot_de_passe_actuel_invalide")
    compte = users.mettre_a_jour_profil(
        session.get("user_id", ""), data.get("email"), data.get("nom"))
    compte["mot_de_passe_defini"] = users.mot_de_passe_defini(session["user_id"])
    token = req.ctx.sessions.token_depuis_cookie(req.handler.headers)
    req.ctx.sessions.mettre_a_jour(token, email=compte["email"], nom=compte["nom"])
    req.send_json(200, {"compte": compte})


def changer_mot_de_passe(req):
    session = req.client_exige()
    users = req.ctx.users
    if users is None:
        raise ApiError(503, "auth_desactivee", "Portail non configuré (users).")
    data = req.read_json()
    users.changer_mot_de_passe(
        session.get("user_id", ""),
        data.get("mot_de_passe_actuel", ""),
        data.get("nouveau_mot_de_passe"),
    )
    token = req.ctx.sessions.token_depuis_cookie(req.handler.headers)
    req.ctx.sessions.invalider_utilisateur(session.get("user_id", ""), token)
    req.send_json(200, {"mot_de_passe_modifie": True})


def enregistrer(router):
    router.route("GET", r"/api/account")(obtenir)
    router.route("PATCH", r"/api/account")(mettre_a_jour)
    router.route("POST", r"/api/account/password")(changer_mot_de_passe)

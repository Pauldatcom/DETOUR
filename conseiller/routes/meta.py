"""Configuration, advisor availability and Prometheus metrics routes."""

import os
import secrets

from datetime import datetime, timezone

from agent import DEFAULT_MODEL
from horaires import est_ouvert, fenetre_reponse

from httpd.errors import ApiError


def config(req):
    req.send_json(200, {
        "simulation": True,
        "agent_actif": bool(os.environ.get("OPENROUTER_API_KEY", "")),
        "google_oauth": bool(os.environ.get("GOOGLE_CLIENT_ID", "")),
        "model": os.environ.get("OPENROUTER_MODEL", DEFAULT_MODEL),
    })


def disponibilite(req):
    maintenant = datetime.now(timezone.utc)
    req.send_json(200, {
        "simulation": True,
        "ouvert": est_ouvert(maintenant),
        "fenetre": fenetre_reponse(maintenant),
    })


def _corps_metrics(store, propositions):
    demandes = store.lister()
    props = propositions.lister()
    par_statut = {}
    for d in demandes:
        s = d.get("statut", "inconnu")
        par_statut[s] = par_statut.get(s, 0) + 1
    lignes = [
        "# HELP detour_demandes_total Nombre total de demandes",
        "# TYPE detour_demandes_total gauge",
        f"detour_demandes_total {len(demandes)}",
        "# HELP detour_propositions_total Nombre total de propositions",
        "# TYPE detour_propositions_total gauge",
        f"detour_propositions_total {len(props)}",
    ]
    for s, n in sorted(par_statut.items()):
        lignes.append(f'detour_demandes_par_statut{{statut="{s}"}} {n}')
    return "\n".join(lignes) + "\n"


def metrics(req):
    token_attendu = os.environ.get("METRICS_TOKEN", "")
    if token_attendu:
        recus = req.query.get("token", [])
        auth = req.handler.headers.get("Authorization", "")
        bearer = auth.replace("Bearer ", "", 1) if auth.startswith("Bearer ") else ""
        if not (recus and secrets.compare_digest(recus[0], token_attendu)) and \
           not (bearer and secrets.compare_digest(bearer, token_attendu)):
            raise ApiError(401, "metrics_forbidden", "Token métriques requis.")
    body = _corps_metrics(req.ctx.store, req.ctx.propositions)
    handler = req.handler
    handler.send_response(200)
    handler.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
    handler.send_header("Content-Length", str(len(body.encode("utf-8"))))
    handler.end_headers()
    handler.wfile.write(body.encode("utf-8"))


def enregistrer(router):
    router.route("GET", r"/api/config")(config)
    router.route("GET", r"/api/disponibilite")(disponibilite)
    router.route("GET", r"/metrics")(metrics)

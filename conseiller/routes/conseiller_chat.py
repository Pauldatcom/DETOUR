"""Advisor chat route (#115): the assistant helps the advisor, it never decides."""

import json
import re

from httpd.errors import ApiError

from agent import ASSISTANT_INDISPONIBLE, OpenRouterError, verifier_messages
from traces import finaliser_et_persister


def conseiller_chat(req):
    req.admin_exige()
    if req.ctx.agent is None:
        raise ApiError(503, "agent_not_configured",
                       "L'assistant n'est pas configuré : définir OPENROUTER_API_KEY.")
    data = req.read_json()
    messages = data.get("messages")
    try:
        verifier_messages(messages)
    except ValueError as err:
        raise ApiError(400, "invalid_messages", str(err)) from err
    demande_id = data.get("demande_id")
    if demande_id is not None:
        if not (isinstance(demande_id, str)
                and re.fullmatch(r"dem_[a-f0-9]+", demande_id)
                and req.ctx.store.obtenir(demande_id)):
            raise ApiError(404, "demande_not_found", "Demande introuvable.")
    try:
        result = req.ctx.agent.chat_conseiller(messages, demande_id=demande_id)
    except OpenRouterError as err:
        # Never a raw provider error in the advisor interface.
        raise ApiError(503, "assistant_indisponible", ASSISTANT_INDISPONIBLE) from err
    # #5: persist a redacted trace (also printed for local debug).
    result["trace"] = finaliser_et_persister(
        result.get("trace") or {},
        req.ctx.traces_dir,
        request_id=demande_id or (result.get("trace") or {}).get("request_id"),
        reponse_finale=result.get("reply") or "",
    )
    print("[agent] " + json.dumps(result["trace"], ensure_ascii=False), flush=True)
    req.send_json(200, {
        "reply": result["reply"],
        "recherche": result.get("recherche"),
        "trace": result["trace"],
        "simulation": True,
    })


def enregistrer(router):
    router.route("POST", r"/api/conseiller/chat")(conseiller_chat)

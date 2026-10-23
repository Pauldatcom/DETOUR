"""Conversational chat route: the agent answers the traveler."""

import json
import re

from httpd.errors import ApiError

from store import ValidationError
from traces import finaliser_et_persister


def chat(req):
    if req.ctx.agent is None:
        raise ApiError(503, "agent_not_configured",
                       "Agent non configuré : définir OPENROUTER_API_KEY.")
    session = req.client_exige()
    data = req.read_json()
    messages = data.get("messages")
    if not isinstance(messages, list) or not 1 <= len(messages) <= 60:
        raise ApiError(400, "invalid_messages",
                       "messages doit être une liste de 1 à 60 messages.")
    for message in messages:
        if (not isinstance(message, dict)
                or message.get("role") not in ("user", "assistant")
                or not isinstance(message.get("content"), str)
                or not message["content"].strip()):
            raise ApiError(400, "invalid_messages",
                           "Chaque message doit avoir un role (user ou assistant) et un content texte non vide.")
    demande_id = data.get("demande_id")
    if demande_id is not None and not (isinstance(demande_id, str)
                                       and re.fullmatch(r"dem_[a-f0-9]+", demande_id)):
        demande_id = None
    result = req.ctx.agent.chat(
        messages,
        user_id=session.get("user_id", "") if isinstance(session, dict) else "",
        demande_id=demande_id,
    )
    # #5: persist a redacted trace (also printed for local debug).
    thread_id = demande_id or (result.get("demande") or {}).get("id")
    result["trace"] = finaliser_et_persister(
        result.get("trace") or {},
        req.ctx.traces_dir,
        request_id=thread_id or (result.get("trace") or {}).get("request_id"),
        reponse_finale=result.get("reply") or "",
    )
    print("[agent] " + json.dumps(result["trace"], ensure_ascii=False), flush=True)

    store = req.ctx.store
    if thread_id and (result.get("reply") or "").strip():
        historique = [dict(m) for m in messages]
        historique.append({"role": "assistant", "content": result["reply"]})
        try:
            store.definir_messages(thread_id, historique)
        except ValidationError:
            pass
    req.send_json(200, {**result, "simulation": True})


def enregistrer(router):
    router.route("POST", r"/api/chat")(chat)

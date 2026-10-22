"""Persist redacted agent traces for each chat run (#5).

A trace answers the contract questions without secrets:
what did the model request, what did the program validate, what did the
server return, what did the agent tell the advisor.
"""

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Key names (case-insensitive) that must never appear in a persisted trace.
_CLE_SECRETE = re.compile(
    r"(team[_-]?key|approval[_-]?key|api[_-]?key|openrouter|"
    r"authorization|cookie|password|secret|token|bearer)",
    re.IGNORECASE,
)

_REDACTED = "[redacted]"


def expurger(valeur):
    """Drop secrets from nested JSON-like values (keys and obvious key headers)."""
    if isinstance(valeur, dict):
        propre = {}
        for cle, item in valeur.items():
            if isinstance(cle, str) and _CLE_SECRETE.search(cle):
                propre[cle] = _REDACTED
            else:
                propre[cle] = expurger(item)
        return propre
    if isinstance(valeur, list):
        return [expurger(item) for item in valeur]
    if isinstance(valeur, str):
        # Never keep Authorization-style header values if they slipped in.
        if valeur.lower().startswith("bearer ") or valeur.lower().startswith("basic "):
            return _REDACTED
        return valeur
    return valeur


def resume_reponse_serveur(recherche):
    """Keep only the fields useful for audit (ids, prices, availability)."""
    if not isinstance(recherche, dict):
        return None
    resultats = []
    for ligne in recherche.get("resultats") or []:
        if not isinstance(ligne, dict):
            continue
        resultats.append({
            "id": ligne.get("id"),
            "nom": ligne.get("nom"),
            "prix_unitaire_eur": ligne.get("prix_unitaire_eur"),
            "disponible": ligne.get("disponible"),
        })
    return {
        "source_label": recherche.get("source_label"),
        "consulte_le": recherche.get("consulte_le"),
        "resultats": resultats,
    }


def finaliser_trace(trace, *, request_id=None, reponse_finale=""):
    """Attach contract fields and redact secrets. Does not write to disk."""
    sortie = expurger(dict(trace or {}))
    sortie["request_id"] = request_id
    sortie["reponse_finale"] = reponse_finale or ""
    sortie["enregistre_le"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return sortie


def persister_trace(trace, traces_dir):
    """Write one JSON file under traces_dir. Returns the path, or None if disabled."""
    if not traces_dir:
        return None
    dossier = Path(traces_dir)
    dossier.mkdir(parents=True, exist_ok=True)
    stamp = (trace.get("enregistre_le") or "trace").replace(":", "").replace("-", "")
    req = trace.get("request_id") or "sans_demande"
    safe_req = re.sub(r"[^a-zA-Z0-9_.-]+", "_", str(req))[:40]
    chemin = dossier / f"{stamp}_{safe_req}_{uuid.uuid4().hex[:8]}.json"
    chemin.write_text(
        json.dumps(trace, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return chemin


def finaliser_et_persister(trace, traces_dir, *, request_id=None, reponse_finale=""):
    """Redact, persist, and return the finalized trace."""
    final = finaliser_trace(
        trace, request_id=request_id, reponse_finale=reponse_finale)
    persister_trace(final, traces_dir)
    return final

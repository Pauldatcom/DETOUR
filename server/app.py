#!/usr/bin/env python3
"""Fictional services and reservations API, standard library only.

Entrypoint: builds the state store, wires the route registry and starts the
threaded HTTP server. HTTP plumbing lives in `httpd/`, business routes in
`routes/`, and the simulated state in `state.py`.
"""

import argparse
import json
import os
from http.server import ThreadingHTTPServer
from pathlib import Path

from httpd.context import Context
from httpd.errors import ApiError
from httpd.handler import HttpHandler
from routes import creer_router
from state import StateStore, utc_now, valid_date

__all__ = ["ApiError", "StateStore", "load_teams", "make_handler", "main",
           "utc_now", "valid_date"]


def make_handler(store):
    ctx = Context(store)
    router = creer_router()

    class Handler(HttpHandler):
        pass

    Handler.ctx = ctx
    Handler.router = router
    return Handler


def load_teams(path, demo):
    if demo:
        return {"demo": {"key": "demo-key", "approval_key": "demo-approval"},
                "equipe-b": {"key": "equipe-b-key", "approval_key": "equipe-b-approval"}}
    if not path:
        raise SystemExit("Fournir --teams-file ou --demo.")
    teams = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(teams, dict) or not teams or any(not isinstance(v, dict) or not v.get("key") or not v.get("approval_key") for v in teams.values()):
        raise SystemExit("Fichier équipes invalide.")
    all_keys = [v[k] for v in teams.values() for k in ("key", "approval_key")]
    if len(all_keys) != len(set(all_keys)):
        raise SystemExit("Chaque clé doit être unique.")
    return teams


def main():
    parser = argparse.ArgumentParser(description="Serveur de réservations fictives WEB3")
    parser.add_argument("--demo", action="store_true", help="Deux équipes de démonstration avec clés connues")
    parser.add_argument("--teams-file", help="JSON des clés d'équipes (voir README)")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--state-file", default=str(Path(__file__).parent / ".local" / "state.json"))
    args = parser.parse_args()
    teams = load_teams(args.teams_file, args.demo)
    instructor_key = "demo-instructor" if args.demo else os.environ.get("INSTRUCTOR_KEY")
    if not instructor_key:
        raise SystemExit("Définir INSTRUCTOR_KEY pour les routes formateur.")
    store = StateStore(teams, instructor_key, args.state_file)
    server = ThreadingHTTPServer((args.host, args.port), make_handler(store))
    print(f"API fictive sur http://{args.host}:{server.server_port} : {len(teams)} équipe(s)", flush=True)
    print(f"Tableau de bord sur http://{args.host}:{server.server_port}/dashboard", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

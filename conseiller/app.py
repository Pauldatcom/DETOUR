#!/usr/bin/env python3
"""Parcours de demande client DÉTOUR : serveur HTTP stdlib, sans dépendance.

Entrypoint: wires the persistence stores, the services and the route registry,
then starts the threaded HTTP server. HTTP plumbing lives in `httpd/`, business
routes in `routes/`.
"""

import argparse
import os
from http.server import ThreadingHTTPServer
from pathlib import Path

import db
from agent import Agent, DEFAULT_MODEL, OpenRouterError
from fournisseur import DEFAULT_URL, SupplierClient, SupplierError
from llm import AnthropicProvider, OpenRouterProvider
from propositions import PropositionError, PropositionStore
from store import DemandStore, ValidationError
from users import UserError, UserStore
from utils import (ANTHROPIC_MODEL, ANTHROPIC_URL, LLM_PROVIDER,
                    OPENROUTER_URL)

from httpd.context import Context
from httpd.handler import HttpHandler
from httpd.sessions import SessionManager
from routes import creer_router
from routes.auth import EtatsOAuth

ROOT = Path(__file__).resolve().parent


def load_env_file(path=None):
    env_path = Path(path) if path else ROOT.parent / ".env"
    try:
        lines = env_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip("'\"")
        if key and key not in os.environ:
            os.environ[key] = value


def make_handler(store, supplier=None, agent=None, users=None, team_key="",
                 propositions=None, traces_dir=None):
    """Build the HTTP handler.

    - `users=None`: development/test mode, no authentication required
      (historical behaviour preserved).
    - `users=UserStore(...)`: portal active — pages and protected routes
      require a session (traveler or advisor).
    - `propositions=None`: in-memory proposal store (test mode).
    - `traces_dir`: folder for redacted agent traces (#5); None = no writing.
    """
    if propositions is None:
        propositions = PropositionStore(None)

    ctx = Context(
        store=store,
        supplier=supplier,
        agent=agent,
        users=users,
        team_key=team_key,
        propositions=propositions,
        sessions=SessionManager(),
        oauth_states=EtatsOAuth(),
        root=ROOT,
        traces_dir=traces_dir,
    )
    router = creer_router()

    class Handler(HttpHandler):
        def repondre_erreur(self, exc):
            """Map business errors to the historical JSON responses."""
            if isinstance(exc, (ValidationError, PropositionError)):
                return self.send_json(
                    400, {"erreur": {"code": "validation_error", "message": str(exc)}})
            if isinstance(exc, UserError):
                return self.send_json(
                    exc.status, {"erreur": {"code": exc.code, "message": str(exc)}})
            if isinstance(exc, SupplierError):
                return self.send_json(
                    exc.status, {"erreur": {"code": "supplier_error", "message": str(exc)}})
            if isinstance(exc, OpenRouterError):
                return self.send_json(
                    exc.status, {"erreur": {"code": "openrouter_error", "message": str(exc)}})
            return super().repondre_erreur(exc)

    Handler.ctx = ctx
    Handler.router = router
    return Handler


def main():
    parser = argparse.ArgumentParser(description="Parcours de demande client DÉTOUR")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--db-file", default=str(ROOT / ".local" / "detour.db"))
    parser.add_argument("--users-file", default=str(ROOT / ".local" / "users.json"))
    parser.add_argument("--traces-dir", default=str(ROOT / ".local" / "traces"),
                        help="Directory for redacted agent traces (#5).")
    parser.add_argument("--supplier-url", default=os.environ.get("TRAVEL_API_URL", DEFAULT_URL))
    args = parser.parse_args()

    load_env_file()
    store = DemandStore(args.db_file)
    users = UserStore(args.users_file)
    propositions = PropositionStore(args.db_file)
    # The enriched dataset seeds the read-only destinations table (#88/#89).
    # Idempotent: re-running refreshes the rows without duplicating them.
    dataset = ROOT.parent / "data" / "travel_agency_dataset.json"
    if dataset.exists():
        db.seed_destinations(store.conn, dataset)
    team_key = os.environ.get("TRAVEL_TEAM_KEY", "demo-key")
    supplier = SupplierClient(args.supplier_url, team_key)
    provider_name = os.environ.get("LLM_PROVIDER", LLM_PROVIDER)
    if provider_name == "anthropic":
        anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
        anthropic_model = os.environ.get("ANTHROPIC_MODEL", ANTHROPIC_MODEL)
        provider = AnthropicProvider(
            api_key=anthropic_key, model=anthropic_model,
            base_url=ANTHROPIC_URL, timeout=60)
        agent = Agent(supplier, store, provider=provider)
        api_key = anthropic_key
        model = anthropic_model
    else:
        api_key = os.environ.get("OPENROUTER_API_KEY", "")
        model = os.environ.get("OPENROUTER_MODEL", DEFAULT_MODEL)
        provider = OpenRouterProvider(
            api_key=api_key, model=model,
            base_url=os.environ.get("OPENROUTER_URL", OPENROUTER_URL), timeout=60)
        agent = Agent(supplier, store, provider=provider)
    server = ThreadingHTTPServer((args.host, args.port),
                                  make_handler(store, supplier, agent, users, team_key,
                                               propositions=propositions,
                                               traces_dir=args.traces_dir))
    print(f"Portail sur http://{args.host}:{server.server_port} "
          "(voyageur : /login · conseiller : clé TRAVEL_TEAM_KEY)", flush=True)
    print(f"Serveur de prestations : {args.supplier_url}", flush=True)
    print("Agent conversationnel : " + (f"actif (modèle {model})" if api_key
                                         else "désactivé — définir OPENROUTER_API_KEY dans .env"), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

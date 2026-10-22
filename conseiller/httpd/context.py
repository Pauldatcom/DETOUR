"""Shared dependencies (stores, services) passed to routes."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB_ROOT = ROOT.parent / "web" / "dist"


class Context:
    """Bundles the dependencies injected into every request."""

    def __init__(self, store, supplier=None, agent=None, users=None,
                 team_key="", propositions=None, sessions=None,
                 oauth_states=None, root=None):
        self.store = store
        self.supplier = supplier
        self.agent = agent
        self.users = users
        self.team_key = team_key
        self.propositions = propositions
        self.sessions = sessions
        self.oauth_states = oauth_states
        self.root = root or ROOT

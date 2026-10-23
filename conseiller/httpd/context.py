"""Shared dependencies (stores, services) passed to routes."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RACINE = ROOT.parent
WEB_ROOT = RACINE / "web" / "dist"
DOCS_ROOT = RACINE / "docs"

# Logo officiel DÉTOUR : source unique, le kit brand-2026 à la racine du dépôt.
DOSSIER_LOGOS = ROOT.parent / "brand-2026" / "logo"
LOGOS_OFFICIELS = frozenset({
    "detour-logo.svg",
    "detour-logo-negatif.svg",
    "detour-logo-negatif-transparent.svg",
    "detour-logo-mono-encre.svg",
    "detour-logo-mono-blanc.svg",
    "detour-monogramme.svg",
})


class Context:
    """Bundles the dependencies injected into every request."""

    def __init__(self, store, supplier=None, agent=None, users=None,
                 team_key="", propositions=None, sessions=None,
                 oauth_states=None, root=None, traces_dir=None):
        self.store = store
        self.supplier = supplier
        self.agent = agent
        self.users = users
        self.team_key = team_key
        self.propositions = propositions
        self.sessions = sessions
        self.oauth_states = oauth_states
        self.root = root or ROOT
        self.traces_dir = traces_dir
        self.docs_root = DOCS_ROOT

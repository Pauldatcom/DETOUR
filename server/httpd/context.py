"""Shared dependencies and paths passed to routes."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RACINE = ROOT.parent
STATIC_ROOT = ROOT / "static"

# Official DÉTOUR logo: single source, the brand-2026 kit at the repository root.
BRAND_DIR = RACINE / "brand-2026" / "logo"
LOGOS_OFFICIELS = frozenset({
    "detour-logo.svg",
    "detour-logo-negatif.svg",
    "detour-logo-negatif-transparent.svg",
    "detour-logo-mono-encre.svg",
    "detour-logo-mono-blanc.svg",
    "detour-monogramme.svg",
})

# Dashboard-specific cookie name: cookies are shared across ports on 127.0.0.1,
# so a name shared with the portal (8766) would let one session overwrite the other.
DASHBOARD_COOKIE = "detour_dashboard"


class Context:
    """Bundles the dependencies injected into every request."""

    def __init__(self, store):
        self.store = store
        self.static_root = STATIC_ROOT
        self.brand_dir = BRAND_DIR
        self.logos = LOGOS_OFFICIELS

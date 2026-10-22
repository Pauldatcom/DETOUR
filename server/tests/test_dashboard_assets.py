#!/usr/bin/env python3
"""Tests des assets de marque du tableau de bord : logo officiel DÉTOUR.

Le logo vient du kit brand-2026 (racine du dépôt) et est servi tel quel.

Lancer depuis la racine : python3 -m unittest discover -s server/tests -v
"""

import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import StateStore, make_handler  # noqa: E402

TEAMS = {"demo": {"key": "demo-key", "approval_key": "demo-approval"}}
LOGOS = [
    "detour-logo.svg",
    "detour-logo-negatif.svg",
    "detour-logo-negatif-transparent.svg",
    "detour-logo-mono-encre.svg",
    "detour-logo-mono-blanc.svg",
    "detour-monogramme.svg",
]
# Fond Encre du kit, présent dans le négatif officiel et absent de sa version transparente.
FOND_NEGATIF = '<rect x="-132" y="-1184" width="4018" height="1378" fill="#16233F"/>'


class TestDashboardBrandAssets(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.state_path = Path(self.tmp.name) / "state.json"

    def tearDown(self):
        self.tmp.cleanup()

    def demarrer(self, store):
        server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(store))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(lambda: (server.shutdown(), server.server_close()))
        return server, f"http://127.0.0.1:{server.server_port}"

    def test_logo_officiel_servi_en_svg(self):
        """Chaque variante officielle est servie en image/svg+xml, sans être modifiée."""
        store = StateStore(TEAMS, "demo-instructor", None)
        base = self.demarrer(store)[1]
        for nom in LOGOS:
            with self.subTest(logo=nom):
                with urllib.request.urlopen(f"{base}/dashboard/brand/{nom}") as res:
                    body = res.read().decode("utf-8")
                    self.assertEqual(res.status, 200)
                    self.assertEqual(res.headers.get("Content-Type", ""), "image/svg+xml")
                    self.assertIn("<svg", body)

    def test_fichier_hors_du_kit_refuse(self):
        """Seuls les fichiers du kit brand-2026 sont exposés."""
        store = StateStore(TEAMS, "demo-instructor", None)
        base = self.demarrer(store)[1]
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(f"{base}/dashboard/brand/app.py")
        self.assertEqual(ctx.exception.code, 404)

    def test_negatif_transparent_derive_du_fichier_officiel(self):
        """La version transparente est le négatif officiel moins son fond Encre.

        Aucune couleur, aucune forme n'est modifiée : seul le rectangle de fond
        est retiré, pour les surfaces sombres legacy (#07101E, #06101C).
        """
        kit = Path(__file__).resolve().parent.parent.parent / "brand-2026" / "logo"
        officiel = (kit / "detour-logo-negatif.svg").read_text(encoding="utf-8")
        derive = (kit / "detour-logo-negatif-transparent.svg").read_text(encoding="utf-8")
        self.assertIn(FOND_NEGATIF, officiel)
        self.assertEqual(derive, officiel.replace(FOND_NEGATIF, ""))


if __name__ == "__main__":
    unittest.main()

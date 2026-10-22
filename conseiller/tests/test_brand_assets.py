#!/usr/bin/env python3
"""Tests des assets de marque du portail : logo officiel DÉTOUR.

Le logo vient du kit brand-2026 (racine du dépôt) et est servi tel quel.

Lancer depuis la racine : python3 -m unittest discover -s conseiller/tests -v
"""

import sys
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import make_handler  # noqa: E402
from store import DemandStore  # noqa: E402

LOGOS = [
    "detour-logo.svg",
    "detour-logo-negatif.svg",
    "detour-logo-negatif-transparent.svg",
    "detour-logo-mono-encre.svg",
    "detour-logo-mono-blanc.svg",
    "detour-monogramme.svg",
]


def demarrer(handler):
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_port}"


class TestBrandAssets(unittest.TestCase):
    def setUp(self):
        self.server, self.base = demarrer(make_handler(DemandStore(None)))
        self.addCleanup(lambda: (self.server.shutdown(), self.server.server_close()))

    def test_logo_officiel_servi_en_svg(self):
        """Chaque variante officielle est servie en image/svg+xml, sans être modifiée."""
        for nom in LOGOS:
            with self.subTest(logo=nom):
                with urllib.request.urlopen(f"{self.base}/brand/{nom}") as res:
                    body = res.read().decode("utf-8")
                    self.assertEqual(res.status, 200)
                    self.assertEqual(res.headers.get("Content-Type", ""), "image/svg+xml")
                    self.assertIn("<svg", body)

    def test_fichier_hors_du_kit_refuse(self):
        """Seuls les fichiers du kit brand-2026 sont exposés."""
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(f"{self.base}/brand/app.py")
        self.assertEqual(ctx.exception.code, 404)


if __name__ == "__main__":
    unittest.main()

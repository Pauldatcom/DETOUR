#!/usr/bin/env python3
"""Tests du routeur et du registre de routes httpd (stdlib only)."""

import sys
import unittest
from pathlib import Path

CONSEILLER_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(CONSEILLER_ROOT))

from httpd.router import Router


class TestRouter(unittest.TestCase):
    def setUp(self):
        self.router = Router()

    def test_route_exacte(self):
        self.router.route("GET", r"/api/health")(lambda req: None)
        func, params = self.router.resoudre("GET", "/api/health")
        self.assertIsNotNone(func)
        self.assertEqual(params, {})

    def test_route_avec_groupe_nomme(self):
        self.router.route("GET", r"/api/demandes/(?P<id>dem_[a-f0-9]+)")(lambda req, id: None)
        func, params = self.router.resoudre("GET", "/api/demandes/dem_abc123")
        self.assertIsNotNone(func)
        self.assertEqual(params, {"id": "dem_abc123"})
        self.assertIsNone(self.router.resoudre("GET", "/api/demandes/autre")[0])

    def test_groupe_non_nomme_refuse(self):
        with self.assertRaises(ValueError):
            self.router.route("GET", r"/api/demandes/(dem_[a-f0-9]+)")(lambda req: None)

    def test_methode_differente_ne_resout_pas(self):
        self.router.route("POST", r"/api/demandes")(lambda req: None)
        self.assertIsNone(self.router.resoudre("GET", "/api/demandes")[0])
        func, _ = self.router.resoudre("POST", "/api/demandes")
        self.assertIsNotNone(func)

    def test_premiere_route_gagne(self):
        self.router.route("GET", r"/api/x")(lambda req: "premiere")
        self.router.route("GET", r"/api/x")(lambda req: "seconde")
        func, _ = self.router.resoudre("GET", "/api/x")
        self.assertEqual(func(None), "premiere")

    def test_liste_routes_immuable(self):
        self.router.route("GET", r"/a")(lambda req: None)
        routes = self.router.routes
        routes.clear()
        self.assertEqual(len(self.router.routes), 1)


class TestRegistrePortail(unittest.TestCase):
    """All portal routes are registered and resolve."""

    @classmethod
    def setUpClass(cls):
        from routes import creer_router
        cls.router = creer_router()

    def resoudre(self, method, path):
        func, _ = self.router.resoudre(method, path)
        return func

    def test_pages(self):
        for path in ("/health", "/login", "/", "/index.html", "/chat", "/conseiller",
                     "/app.css", "/app.js", "/pages.js", "/pages-propositions.js",
                     "/agent-widget.css", "/agent-widget.js"):
            self.assertIsNotNone(self.resoudre("GET", path), path)

    def test_auth(self):
        self.assertIsNotNone(self.resoudre("GET", "/api/session"))
        self.assertIsNotNone(self.resoudre("POST", "/api/login"))
        self.assertIsNotNone(self.resoudre("POST", "/api/register"))
        self.assertIsNotNone(self.resoudre("POST", "/api/login-conseiller"))
        self.assertIsNotNone(self.resoudre("POST", "/api/logout"))
        self.assertIsNotNone(self.resoudre("GET", "/api/auth/google"))
        self.assertIsNotNone(self.resoudre("GET", "/api/auth/google/callback"))

    def test_demandes(self):
        self.assertIsNotNone(self.resoudre("GET", "/api/mes-demandes"))
        self.assertIsNotNone(self.resoudre("GET", "/api/demandes"))
        self.assertIsNotNone(self.resoudre("GET", "/api/demandes/dem_abc123"))
        self.assertIsNotNone(self.resoudre("POST", "/api/demandes"))
        self.assertIsNotNone(self.resoudre("POST", "/api/demandes/dem_abc123/recherche"))
        for action in ("qualification", "correction", "statut"):
            self.assertIsNotNone(
                self.resoudre("PATCH", f"/api/demandes/dem_abc123/{action}"), action)

    def test_propositions(self):
        self.assertIsNotNone(self.resoudre("GET", "/api/mes-propositions"))
        self.assertIsNotNone(self.resoudre("GET", "/api/propositions"))
        self.assertIsNotNone(self.resoudre("GET", "/api/propositions/prop_abc123"))
        for action in ("accepter", "correction", "refuser"):
            self.assertIsNotNone(
                self.resoudre("POST", f"/api/propositions/prop_abc123/{action}"), action)
        self.assertIsNotNone(self.resoudre("POST", "/api/propositions/prop_abc123/decisions"))
        self.assertIsNotNone(self.resoudre("POST", "/api/demandes/dem_abc123/propositions"))
        self.assertIsNotNone(self.resoudre("POST", "/api/demandes/dem_abc123/propositions/generer"))
        self.assertIsNotNone(self.resoudre("PATCH", "/api/propositions/prop_abc123/statut"))
        self.assertIsNotNone(self.resoudre("PATCH", "/api/propositions/prop_abc123"))

    def test_divers(self):
        self.assertIsNotNone(self.resoudre("POST", "/api/chat"))
        self.assertIsNotNone(self.resoudre("GET", "/api/stats"))
        self.assertIsNotNone(self.resoudre("GET", "/api/catalogue"))
        self.assertIsNotNone(self.resoudre("GET", "/api/config"))
        self.assertIsNotNone(self.resoudre("GET", "/api/disponibilite"))
        self.assertIsNotNone(self.resoudre("GET", "/metrics"))

    def test_routes_inconnues(self):
        self.assertIsNone(self.resoudre("GET", "/api/inconnu"))
        self.assertIsNone(self.resoudre("DELETE", "/api/demandes/dem_abc123"))


if __name__ == "__main__":
    unittest.main()

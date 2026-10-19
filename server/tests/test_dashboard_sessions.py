#!/usr/bin/env python3
"""Tests des sessions du tableau de bord : persistance et suppression de /me.

Lancer depuis la racine : python3 -m unittest discover -s server/tests -v
"""

import json
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


class TestDashboardSessions(unittest.TestCase):
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

    def login(self, base):
        req = urllib.request.Request(
            f"{base}/dashboard/api/login",
            data=json.dumps({"team_key": "demo-key"}).encode(),
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req) as res:
            data = json.loads(res.read())
        cookie = res.headers.get("Set-Cookie").split(";")[0]
        return cookie, data["equipe"]

    def appel_avec_cookie(self, base, chemin, cookie):
        req = urllib.request.Request(f"{base}{chemin}",
                                     headers={"Cookie": cookie})
        try:
            with urllib.request.urlopen(req) as res:
                return res.status, json.loads(res.read())
        except urllib.error.HTTPError as err:
            return err.code, json.loads(err.read())

    def test_session_survit_au_redemarrage(self):
        """La session est persistée dans state.json : un nouveau StateStore
        (redémarrage du serveur) l'accepte toujours."""
        store = StateStore(TEAMS, "demo-instructor", self.state_path)
        base1 = self.demarrer(store)[1]
        cookie, equipe = self.login(base1)
        self.assertEqual(equipe, "demo")

        # Redémarrage : nouveau store + nouveau serveur, même fichier d'état.
        store2 = StateStore(TEAMS, "demo-instructor", self.state_path)
        base2 = self.demarrer(store2)[1]
        status, data = self.appel_avec_cookie(base2, "/dashboard/api/catalogue", cookie)
        self.assertEqual(status, 200)
        self.assertTrue(data["prestations"])

    def test_logout_supprime_la_session_persistee(self):
        store = StateStore(TEAMS, "demo-instructor", self.state_path)
        base = self.demarrer(store)[1]
        cookie, _ = self.login(base)
        req = urllib.request.Request(f"{base}/dashboard/api/logout", data=b"",
                                     headers={"Cookie": cookie}, method="POST")
        with urllib.request.urlopen(req) as res:
            self.assertEqual(res.status, 200)

        store2 = StateStore(TEAMS, "demo-instructor", self.state_path)
        base2 = self.demarrer(store2)[1]
        status, _ = self.appel_avec_cookie(base2, "/dashboard/api/catalogue", cookie)
        self.assertEqual(status, 401)

    def test_endpoint_me_supprime(self):
        """L'endpoint /dashboard/api/me est retiré : plus de sonde « qui suis-je »."""
        store = StateStore(TEAMS, "demo-instructor", None)
        base = self.demarrer(store)[1]
        cookie, _ = self.login(base)
        status, data = self.appel_avec_cookie(base, "/dashboard/api/me", cookie)
        self.assertEqual(status, 404)
        self.assertEqual(data["erreur"]["code"], "not_found")

    def test_cookie_du_portail_ne_casse_pas_la_session(self):
        """Les cookies sont partagés entre ports : un cookie `detour_session`
        (ancien nom, ou autre appli sur 127.0.0.1) ne doit pas écraser la session."""
        store = StateStore(TEAMS, "demo-instructor", None)
        base = self.demarrer(store)[1]
        cookie, _ = self.login(base)
        mixte = f"{cookie}; detour_session=jeton-etranger; detour_portail=autre"
        status, _ = self.appel_avec_cookie(base, "/dashboard/api/catalogue", mixte)
        self.assertEqual(status, 200)
        mixte_inverse = f"detour_session=jeton-etranger; {cookie}"
        status, _ = self.appel_avec_cookie(base, "/dashboard/api/catalogue", mixte_inverse)
        self.assertEqual(status, 200)

    def test_session_expiree_rejetee(self):
        store = StateStore(TEAMS, "demo-instructor", self.state_path)
        base = self.demarrer(store)[1]
        cookie, _ = self.login(base)
        # Vieillir la session sous le verrou, comme le ferait le temps qui passe.
        with store.lock:
            for entree in store.state["sessions"].values():
                entree["expire_le"] = "2020-01-01T00:00:00+00:00"
            store.save()
        status, data = self.appel_avec_cookie(base, "/dashboard/api/catalogue", cookie)
        self.assertEqual(status, 401)
        self.assertEqual(data["erreur"]["code"], "dashboard_session_expired")


if __name__ == "__main__":
    unittest.main()
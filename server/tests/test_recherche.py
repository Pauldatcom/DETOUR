#!/usr/bin/env python3
"""Tests de la route de recherche du serveur fictif (stdlib uniquement).

Lancer depuis la racine : python3 -m unittest discover -s server/tests -v
"""

import json
import sys
import threading
import unittest
import urllib.error
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import StateStore, make_handler  # noqa: E402
from catalogue import MIS_A_JOUR_LE_BASE, PRESTATIONS  # noqa: E402

TEAMS = {"demo": {"key": "demo-key", "approval_key": "demo-approval"}}
CRITERES = {"destination": "Nantes", "date_depart": "2026-11-07", "date_retour": "2026-11-09",
            "participants": 2}


class TestRecherche(unittest.TestCase):
    def setUp(self):
        self.store = StateStore(TEAMS, "demo-instructor", None)
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(self.store))
        self.port = self.server.server_port
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()

    def call(self, path, params=None, method="GET", body=None, headers=None):
        url = f"http://127.0.0.1:{self.port}{path}"
        if params:
            url += "?" + urllib.parse.urlencode(params)
        all_headers = {"X-Team-Key": "demo-key", **(headers or {})}
        data = None
        if body is not None:
            data = json.dumps(body).encode()
            all_headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=data, headers=all_headers, method=method)
        try:
            with urllib.request.urlopen(req) as res:
                return res.status, json.loads(res.read())
        except urllib.error.HTTPError as err:
            return err.code, json.loads(err.read())

    def incident(self, prestation_id, type_, valeur):
        return self.call("/api/v1/instructor/teams/demo/incidents", method="POST",
                         body={"prestation_id": prestation_id, "date": "2026-11-07",
                               "type": type_, "valeur": valeur},
                         headers={"X-Instructor-Key": "demo-instructor"})

    def test_catalogue_expose_mis_a_jour_le(self):
        status, data = self.call("/api/v1/catalogue")
        self.assertEqual(status, 200)
        self.assertEqual(len(data["prestations"]), len(PRESTATIONS))
        for item in data["prestations"]:
            self.assertEqual(item["mis_a_jour_le"], MIS_A_JOUR_LE_BASE)

    def test_recherche_filtre_destination_et_calcule_totaux(self):
        status, data = self.call("/api/v1/recherche", CRITERES)
        self.assertEqual(status, 200)
        ids = {r["id"] for r in data["resultats"]}
        self.assertEqual(ids, {"train-nantes-01", "hotel-nantes-01", "activite-nantes-01"})
        train = next(r for r in data["resultats"] if r["id"] == "train-nantes-01")
        self.assertEqual(train["prix_unitaire_eur"], 48)
        self.assertEqual(train["prix_total_eur"], 96)
        self.assertTrue(train["disponible"])
        self.assertEqual(data["source"], "serveur-fictif-detour")
        self.assertIn("consulte_le", data)
        self.assertEqual(data["criteres"]["date_verifiee"], "2026-11-07")

    def test_recherche_destination_insensible_a_la_casse(self):
        status, data = self.call("/api/v1/recherche", {**CRITERES, "destination": "lyon"})
        self.assertEqual(status, 200)
        self.assertTrue(all(r["destination"] == "Lyon" for r in data["resultats"]))
        self.assertEqual(len(data["resultats"]), 3)

    def test_recherche_destination_inconnue_renvoie_liste_vide(self):
        status, data = self.call("/api/v1/recherche", {**CRITERES, "destination": "Paris"})
        self.assertEqual(status, 200)
        self.assertEqual(data["resultats"], [])

    def test_budget_signale_sans_masquer(self):
        status, data = self.call("/api/v1/recherche", {**CRITERES, "budget_max": 40})
        self.assertEqual(status, 200)
        by_id = {r["id"]: r for r in data["resultats"]}
        self.assertEqual(len(by_id), 3)
        self.assertFalse(by_id["train-nantes-01"]["dans_budget"])
        self.assertTrue(by_id["activite-nantes-01"]["dans_budget"])

    def test_sans_budget_dans_budget_est_inconnu(self):
        _, data = self.call("/api/v1/recherche", CRITERES)
        self.assertTrue(all(r["dans_budget"] is None for r in data["resultats"]))

    def test_type_voyage_et_activites(self):
        status, data = self.call("/api/v1/recherche", {**CRITERES, "type_voyage": "trek-randonnee",
                                                        "activites": "créatif,cuisine"})
        self.assertEqual(status, 200)
        self.assertTrue(all(r["correspond_type_voyage"] is False for r in data["resultats"]))
        atelier = next(r for r in data["resultats"] if r["id"] == "activite-nantes-01")
        self.assertEqual(atelier["activites_correspondantes"], ["créatif"])
        _, data = self.call("/api/v1/recherche", {**CRITERES, "type_voyage": "lune-de-miel"})
        by_id = {r["id"]: r for r in data["resultats"]}
        self.assertTrue(by_id["hotel-nantes-01"]["correspond_type_voyage"])
        self.assertFalse(by_id["activite-nantes-01"]["correspond_type_voyage"])

    def test_groupe_trop_grand_est_indisponible(self):
        _, data = self.call("/api/v1/recherche", {**CRITERES, "participants": 9})
        train = next(r for r in data["resultats"] if r["id"] == "train-nantes-01")
        self.assertFalse(train["disponible"])
        self.assertEqual(train["places_restantes"], 8)

    def test_incident_prix_visible_dans_la_recherche_avec_nouvelle_date(self):
        status, _ = self.incident("train-nantes-01", "prix_unitaire_eur", 70)
        self.assertEqual(status, 201)
        _, data = self.call("/api/v1/recherche", CRITERES)
        train = next(r for r in data["resultats"] if r["id"] == "train-nantes-01")
        self.assertEqual(train["prix_unitaire_eur"], 70)
        self.assertEqual(train["prix_total_eur"], 140)
        self.assertNotEqual(train["mis_a_jour_le"], MIS_A_JOUR_LE_BASE)
        hotel = next(r for r in data["resultats"] if r["id"] == "hotel-nantes-01")
        self.assertEqual(hotel["mis_a_jour_le"], MIS_A_JOUR_LE_BASE)

    def test_incident_capacite_zero_rend_indisponible(self):
        self.incident("hotel-nantes-01", "capacite", 0)
        _, data = self.call("/api/v1/recherche", CRITERES)
        hotel = next(r for r in data["resultats"] if r["id"] == "hotel-nantes-01")
        self.assertFalse(hotel["disponible"])
        self.assertEqual(hotel["places_restantes"], 0)

    def test_parametres_invalides(self):
        cas = [
            ({**CRITERES, "destination": ""}, "invalid_destination"),
            ({**CRITERES, "date_depart": "07/11/2026"}, "invalid_date"),
            ({**CRITERES, "date_retour": "2026-11-01"}, "invalid_date"),
            ({**CRITERES, "participants": 0}, "invalid_participants"),
            ({**CRITERES, "participants": "abc"}, "invalid_participants"),
            ({**CRITERES, "budget_max": "abc"}, "invalid_budget"),
        ]
        for params, code in cas:
            with self.subTest(code=code, params=params):
                status, data = self.call("/api/v1/recherche", params)
                self.assertEqual(status, 400)
                self.assertEqual(data["erreur"]["code"], code)

    def test_cle_equipe_requise(self):
        url = f"http://127.0.0.1:{self.port}/api/v1/recherche?" + urllib.parse.urlencode(CRITERES)
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(url)
        self.assertEqual(ctx.exception.code, 401)


if __name__ == "__main__":
    unittest.main()

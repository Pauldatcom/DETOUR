#!/usr/bin/env python3
"""Tests unittest pour l'application conseiller DÉTOUR (stdlib only)."""

import copy
import json
import os
import socket
import subprocess
import sys
import time
import tempfile
import threading
import unittest
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

CONSEILLER_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(CONSEILLER_ROOT))

from store import (
    DemandStore,
    ValidationError,
    analyser_informations,
    criteres_depuis_demande,
    fusionner_reponses,
    valider_demande,
)
from app import load_env_file, make_handler
from agent import SYSTEM_PROMPT, Agent, OpenRouterError
from fournisseur import SupplierClient, SupplierError
from propositions import PropositionStore, PropositionError
from utils import QUALIF_PRET_PROPOSITION, QUALIF_PRET_RELECTURE
from store import questions_conditionnelles


VALIDE = {
    "conseiller": "Alice",
    "type_voyage": "trek-randonnee",
    "destination": "Nantes",
    "date_depart": "2026-11-07",
    "date_retour": "2026-11-09",
    "nombre_voyageurs": 2,
    "has_enfants": True,
    "nombre_enfants": 1,
    "budget_max_par_personne": 500,
    "niveau_aventure": "modere",
    "besoin_guide": True,
    "activites": ["créatif", "extérieur"],
    "contraintes": "allergie aux arachides",
}


class TestValidation(unittest.TestCase):
    def test_valide(self):
        result = valider_demande(dict(VALIDE))
        self.assertEqual(result["destination"], "Nantes")
        self.assertEqual(result["activites"], ["créatif", "extérieur"])
        self.assertTrue(result["besoin_guide"])

    def test_type_voyage_invalide(self):
        data = dict(VALIDE, type_voyage="inconnu")
        with self.assertRaises(ValidationError):
            valider_demande(data)

    def test_destination_vide(self):
        data = dict(VALIDE, destination="  ")
        with self.assertRaises(ValidationError):
            valider_demande(data)

    def test_dates_inversees(self):
        data = dict(VALIDE, date_depart="2026-11-09", date_retour="2026-11-07")
        with self.assertRaises(ValidationError):
            valider_demande(data)

    def test_budget_negatif(self):
        data = dict(VALIDE, budget_max_par_personne=-10)
        with self.assertRaises(ValidationError):
            valider_demande(data)

    def test_voyageurs_hors_bornes(self):
        data = dict(VALIDE, nombre_voyageurs=25)
        with self.assertRaises(ValidationError):
            valider_demande(data)

    def test_enfants_superieurs_voyageurs(self):
        data = dict(VALIDE, nombre_voyageurs=2, nombre_enfants=5)
        with self.assertRaises(ValidationError):
            valider_demande(data)

    def test_niveau_invalide(self):
        data = dict(VALIDE, niveau_aventure="extreme")
        with self.assertRaises(ValidationError):
            valider_demande(data)

    def test_conseiller_non_attribue_par_defaut(self):
        data = dict(VALIDE)
        data.pop("conseiller")
        result = valider_demande(data)
        self.assertEqual(result["conseiller"], "Non attribué")

    def test_activites_dedupliquees(self):
        data = dict(VALIDE, activites=["créatif", "créatif", "jeu"])
        result = valider_demande(data)
        self.assertEqual(result["activites"], ["créatif", "jeu"])


class TestAnalyserInformations(unittest.TestCase):
    """Required fields are split into provided vs missing for the agent."""

    def test_missing_budget_with_destination_and_dates_provided(self):
        brouillon = {
            "type_voyage": "lune-de-miel",
            "destination": "Nantes",
            "date_depart": "2026-11-07",
            "date_retour": "2026-11-09",
            "nombre_voyageurs": 2,
            "niveau_aventure": "calme",
            # budget_max_par_personne intentionally absent
        }
        info = analyser_informations(brouillon)
        self.assertFalse(info["complet"])
        self.assertEqual(info["manquants"], ["budget_max_par_personne"])
        self.assertIn("destination", info["fournis"])
        self.assertIn("date_depart", info["fournis"])
        self.assertIn("date_retour", info["fournis"])
        self.assertNotIn("budget_max_par_personne", info["fournis"])

    def test_complete_request(self):
        info = analyser_informations(dict(VALIDE))
        self.assertTrue(info["complet"])
        self.assertEqual(info["manquants"], [])
        self.assertEqual(len(info["fournis"]), 7)


class TestFusionnerReponses(unittest.TestCase):
    """Traveler answers merge into an existing request without wiping other fields."""

    def test_budget_update_preserves_destination(self):
        existant = {
            "type_voyage": "lune-de-miel",
            "destination": "Nantes",
            "date_depart": "2026-11-07",
            "date_retour": "2026-11-09",
            "nombre_voyageurs": 2,
            "niveau_aventure": "calme",
        }
        merged, mis_a_jour = fusionner_reponses(
            existant, {"budget_max_par_personne": 400})
        self.assertEqual(mis_a_jour, ["budget_max_par_personne"])
        self.assertEqual(merged["budget_max_par_personne"], 400)
        self.assertEqual(merged["destination"], "Nantes")
        self.assertEqual(merged["type_voyage"], "lune-de-miel")

    def test_invalid_value_is_rejected(self):
        with self.assertRaises(ValidationError):
            fusionner_reponses({}, {"budget_max_par_personne": -5})


class TestDemandStore(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.path = Path(self.tmpdir) / "demandes.json"
        self.store = DemandStore(self.path)

    def test_creer_et_obtenir(self):
        record = self.store.creer(dict(VALIDE))
        self.assertTrue(record["id"].startswith("dem_"))
        self.assertEqual(record["statut"], "a_analyser")
        self.assertEqual(record["qualification"], "pret_relecture")
        self.assertEqual(record["champs_manquants"], [])
        self.assertIn("cree_le", record)
        fetched = self.store.obtenir(record["id"])
        assert fetched is not None
        self.assertEqual(fetched["id"], record["id"])
        self.assertEqual(fetched["demande"]["destination"], "Nantes")

    def test_persiste_sur_disque(self):
        record = self.store.creer(dict(VALIDE))
        store2 = DemandStore(self.path)
        self.assertEqual(len(store2.lister()), 1)
        record2 = store2.obtenir(record["id"])
        assert record2 is not None
        self.assertEqual(record2["demande"]["destination"], "Nantes")

    def test_lister(self):
        self.store.creer(dict(VALIDE))
        self.store.creer(dict(VALIDE, destination="Lyon"))
        demandes = self.store.lister()
        self.assertEqual(len(demandes), 2)
        self.assertIn(demandes[0]["demande"]["destination"], ("Nantes", "Lyon"))

    def test_lister_affiche_echeance(self):
        # #51 : every listed demande carries its response deadline and status.
        self.store.creer(dict(VALIDE))
        demandes = self.store.lister()
        self.assertEqual(len(demandes), 1)
        record = demandes[0]
        self.assertIsNotNone(record.get("echeance_cible"))
        self.assertIsNotNone(record.get("echeance_max"))
        self.assertIn(
            record.get("echeance_statut"), ("dans_delai", "approche", "depassee")
        )

    def test_obtenir_inexistant(self):
        self.assertIsNone(self.store.obtenir("dem_inconnu"))

    def test_save_answers_creates_draft_then_completes(self):
        record, mis = self.store.enregistrer_reponses(None, {
            "type_voyage": "lune-de-miel",
            "destination": "Nantes",
            "date_depart": "2026-11-07",
            "date_retour": "2026-11-09",
            "nombre_voyageurs": 2,
            "niveau_aventure": "calme",
        }, user_id="u1")
        self.assertTrue(record["id"].startswith("dem_"))
        self.assertIn("budget_max_par_personne", record["champs_manquants"])
        self.assertEqual(record["demande"]["destination"], "Nantes")
        self.assertIn("destination", mis)

        updated, mis2 = self.store.enregistrer_reponses(
            record["id"], {"budget_max_par_personne": 450}, user_id="u1")
        self.assertEqual(updated["id"], record["id"])
        self.assertEqual(mis2, ["budget_max_par_personne"])
        self.assertEqual(updated["demande"]["budget_max_par_personne"], 450)
        self.assertEqual(updated["demande"]["destination"], "Nantes")
        self.assertEqual(updated["champs_manquants"], [])
        self.assertEqual(updated["qualification"], "pret_relecture")

    def test_save_answers_preserves_fields_on_failure(self):
        record, _ = self.store.enregistrer_reponses(None, {
            "destination": "Lyon",
            "budget_max_par_personne": 300,
        })
        with self.assertRaises(ValidationError):
            self.store.enregistrer_reponses(
                record["id"], {"budget_max_par_personne": -1})
        fetched = self.store.obtenir(record["id"])
        assert fetched is not None
        self.assertEqual(fetched["demande"]["budget_max_par_personne"], 300)
        self.assertEqual(fetched["demande"]["destination"], "Lyon")

    def test_save_answers_unknown_request_returns_none(self):
        record, mis = self.store.enregistrer_reponses("dem_deadbeef", {"destination": "Lille"})
        self.assertIsNone(record)
        self.assertEqual(mis, [])

    def test_save_answers_rejects_other_traveler(self):
        record, _ = self.store.enregistrer_reponses(
            None, {"destination": "Lille"}, user_id="owner")
        with self.assertRaises(ValidationError):
            self.store.enregistrer_reponses(
                record["id"], {"budget_max_par_personne": 200}, user_id="intrus")
        with self.assertRaises(ValidationError):
            self.store.enregistrer_reponses(
                record["id"], {"budget_max_par_personne": 200}, user_id="")
        fetched = self.store.obtenir(record["id"])
        assert fetched is not None
        self.assertNotIn("budget_max_par_personne", fetched["demande"])

    def test_save_answers_clears_validation_and_records_history(self):
        record = self.store.creer(dict(VALIDE, user_id="u1"))
        self.store.definir_qualification(record["id"], QUALIF_PRET_PROPOSITION, par="Alice", motif="dossier complet")
        updated, mis = self.store.enregistrer_reponses(
            record["id"], {"budget_max_par_personne": 700}, user_id="u1")
        self.assertEqual(mis, ["budget_max_par_personne"])
        self.assertIsNone(updated.get("qualification_validee_par"))
        self.assertEqual(updated["qualification"], QUALIF_PRET_RELECTURE)
        entry = updated["modifications"][-1]
        self.assertEqual(entry["champ"], "budget_max_par_personne")
        self.assertEqual(entry["avant"], 500)
        self.assertEqual(entry["apres"], 700)
        self.assertEqual(entry["par"], "u1")


class TestHttpApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.mkdtemp()
        cls.store = DemandStore(Path(cls.tmpdir) / "demandes.json")
        cls.handler = make_handler(cls.store)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(("127.0.0.1", 0))
        cls.port = sock.getsockname()[1]
        sock.close()
        cls.server = ThreadingHTTPServer(("127.0.0.1", cls.port), cls.handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def url(self, path):
        return f"http://127.0.0.1:{self.port}{path}"

    def test_health(self):
        with urllib.request.urlopen(self.url("/health")) as res:
            data = json.loads(res.read())
        self.assertEqual(data["status"], "ok")

    def test_creer_demande(self):
        req = urllib.request.Request(
            self.url("/api/demandes"),
            data=json.dumps(dict(VALIDE)).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req) as res:
            self.assertEqual(res.status, 201)
            data = json.loads(res.read())
        self.assertTrue(data["demande"]["id"].startswith("dem_"))
        self.assertEqual(data["demande"]["statut"], "a_analyser")

    def test_creer_demande_invalide(self):
        req = urllib.request.Request(
            self.url("/api/demandes"),
            data=json.dumps({"destination": "Nantes"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            urllib.request.urlopen(req)
            self.fail("Devrait échouer avec 400.")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 400)
            data = json.loads(e.read())
            self.assertEqual(data["erreur"]["code"], "validation_error")

    def test_lister_et_obtenir(self):
        req = urllib.request.Request(
            self.url("/api/demandes"),
            data=json.dumps(dict(VALIDE, destination="Lille")).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req) as res:
            dem_id = json.loads(res.read())["demande"]["id"]

        with urllib.request.urlopen(self.url("/api/demandes")) as res:
            data = json.loads(res.read())
        self.assertTrue(any(d["id"] == dem_id for d in data["demandes"]))

        with urllib.request.urlopen(self.url(f"/api/demandes/{dem_id}")) as res:
            data = json.loads(res.read())
        self.assertEqual(data["demande"]["id"], dem_id)
        self.assertEqual(data["demande"]["demande"]["destination"], "Lille")

    def test_obtenir_inexistant_404(self):
        try:
            urllib.request.urlopen(self.url("/api/demandes/dem_inconnu"))
            self.fail("Devrait retourner 404.")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 404)

    def test_index_html(self):
        with urllib.request.urlopen(self.url("/")) as res:
            body = res.read().decode("utf-8")
        self.assertIn("DÉTOUR", body)
        self.assertIn("Parlons de votre voyage", body)
        self.assertIn("chat-form", body)


def free_port():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def post(url, payload=None):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Content-Type": "application/json"} if payload is not None else {}
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as res:
            return res.status, json.loads(res.read())
    except urllib.error.HTTPError as err:
        return err.code, json.loads(err.read())


def get(url):
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req) as res:
            return res.status, json.loads(res.read())
    except urllib.error.HTTPError as err:
        return err.code, json.loads(err.read())


class TestCriteres(unittest.TestCase):
    def test_criteres_depuis_demande(self):
        store = DemandStore(None)
        record = store.creer(dict(VALIDE))
        criteres = criteres_depuis_demande(record)
        self.assertEqual(criteres, {
            "destination": "Nantes", "date_depart": "2026-11-07", "date_retour": "2026-11-09",
            "participants": 2, "budget_max": 500, "type_voyage": "trek-randonnee",
            "activites": ["créatif", "extérieur"],
        })


class FakeSupplier:
    def __init__(self, error=None):
        self.error = error
        self.calls = []

    def rechercher(self, criteres):
        self.calls.append(criteres)
        if self.error:
            raise self.error
        return {"source_label": "Faux", "source_url": "http://faux", "consulte_le": "2026-10-16T10:00:00+00:00",
                "criteres": {**criteres, "date_verifiee": criteres["date_depart"]}, "resultats": []}


class TestRechercheRoute(unittest.TestCase):
    def serve(self, supplier):
        store = DemandStore(None)
        server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(store, supplier))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(lambda: (server.shutdown(), server.server_close()))
        return store, f"http://127.0.0.1:{server.server_port}"

    def test_recherche_utilise_les_criteres_de_la_demande_et_est_stockee(self):
        supplier = FakeSupplier()
        store, base = self.serve(supplier)
        dem_id = store.creer(dict(VALIDE))["id"]
        status, data = post(f"{base}/api/demandes/{dem_id}/recherche")
        self.assertEqual(status, 201)
        self.assertEqual(supplier.calls[0]["destination"], "Nantes")
        self.assertTrue(data["recherche"]["id"].startswith("rech_"))
        stored = store.obtenir(dem_id)
        assert stored is not None
        self.assertEqual(len(stored["recherches"]), 1)
        self.assertEqual(stored["statut"], "a_analyser")

    def test_demande_inconnue(self):
        _, base = self.serve(FakeSupplier())
        status, data = post(f"{base}/api/demandes/dem_abc123/recherche")
        self.assertEqual(status, 404)
        self.assertEqual(data["erreur"]["code"], "demande_not_found")

    def test_fournisseur_en_erreur_est_signale_et_rien_n_est_stocke(self):
        store, base = self.serve(FakeSupplier(SupplierError("Serveur fictif injoignable")))
        dem_id = store.creer(dict(VALIDE))["id"]
        status, data = post(f"{base}/api/demandes/{dem_id}/recherche")
        self.assertEqual(status, 502)
        self.assertEqual(data["erreur"]["code"], "supplier_error")
        stored = store.obtenir(dem_id)
        assert stored is not None
        self.assertNotIn("recherches", stored)

    def test_fournisseur_non_configure(self):
        store, base = self.serve(None)
        dem_id = store.creer(dict(VALIDE))["id"]
        status, data = post(f"{base}/api/demandes/{dem_id}/recherche")
        self.assertEqual(status, 503)

    def test_serveur_fictif_injoignable_avec_vrai_client(self):
        client = SupplierClient(f"http://127.0.0.1:{free_port()}", "demo-key", timeout=1)
        store, base = self.serve(client)
        dem_id = store.creer(dict(VALIDE))["id"]
        status, data = post(f"{base}/api/demandes/{dem_id}/recherche")
        self.assertEqual(status, 502)
        self.assertIn("injoignable", data["erreur"]["message"])


class TestIntegrationServeurFictif(unittest.TestCase):
    """Lance le vrai serveur fictif (server/app.py) et appelle la recherche de bout en bout."""

    @classmethod
    def setUpClass(cls):
        root = CONSEILLER_ROOT.parent
        cls.tmp = tempfile.mkdtemp()
        cls.supplier_port = free_port()
        cls.proc = subprocess.Popen(
            [sys.executable, str(root / "server" / "app.py"), "--demo", "--port", str(cls.supplier_port),
             "--state-file", str(Path(cls.tmp) / "state.json")],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
        cls.supplier_url = f"http://127.0.0.1:{cls.supplier_port}"
        for _ in range(50):
            try:
                urllib.request.urlopen(cls.supplier_url + "/health", timeout=0.5).close()
                break
            except OSError:
                time.sleep(0.1)
        else:
            cls.proc.kill()
            raise RuntimeError("Le serveur fictif ne démarre pas.")
        cls.store = DemandStore(None)
        cls.app = ThreadingHTTPServer(
            ("127.0.0.1", 0), make_handler(cls.store, SupplierClient(cls.supplier_url, "demo-key")))
        threading.Thread(target=cls.app.serve_forever, daemon=True).start()
        cls.base = f"http://127.0.0.1:{cls.app.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.app.shutdown()
        cls.app.server_close()
        cls.proc.terminate()
        cls.proc.wait(timeout=5)

    def incident(self, prestation_id, type_, valeur):
        req = urllib.request.Request(
            f"{self.supplier_url}/api/v1/instructor/teams/demo/incidents",
            data=json.dumps({"prestation_id": prestation_id, "date": "2026-11-07",
                             "type": type_, "valeur": valeur}).encode(),
            headers={"Content-Type": "application/json", "X-Instructor-Key": "demo-instructor"},
            method="POST")
        urllib.request.urlopen(req).close()

    def test_recherche_reelle_puis_evolution_du_catalogue(self):
        dem_id = self.store.creer(dict(VALIDE, destination="Lyon", budget_max_par_personne=60,
                                       type_voyage="lune-de-miel", activites=["jeu"]))["id"]
        status, data = post(f"{self.base}/api/demandes/{dem_id}/recherche")
        self.assertEqual(status, 201)
        recherche = data["recherche"]
        self.assertEqual(recherche["source_url"], f"{self.supplier_url}/api/v1/recherche")
        ids = {r["id"] for r in recherche["resultats"]}
        self.assertEqual(ids, {"train-lyon-01", "hotel-lyon-01", "activite-lyon-01"})
        by_id = {r["id"]: r for r in recherche["resultats"]}
        self.assertEqual(by_id["train-lyon-01"]["prix_total_eur"], 124)
        self.assertFalse(by_id["hotel-lyon-01"]["dans_budget"])
        self.assertEqual(by_id["activite-lyon-01"]["activites_correspondantes"], ["jeu"])
        self.assertFalse(by_id["activite-lyon-01"]["correspond_type_voyage"])
        self.assertNotIn("demo-key", json.dumps(data))

        self.incident("train-lyon-01", "prix_unitaire_eur", 99)
        self.incident("hotel-lyon-01", "capacite", 0)
        _, data2 = post(f"{self.base}/api/demandes/{dem_id}/recherche")
        by_id2 = {r["id"]: r for r in data2["recherche"]["resultats"]}
        self.assertEqual(by_id2["train-lyon-01"]["prix_unitaire_eur"], 99)
        self.assertFalse(by_id2["hotel-lyon-01"]["disponible"])
        self.assertNotEqual(by_id2["train-lyon-01"]["mis_a_jour_le"], by_id["train-lyon-01"]["mis_a_jour_le"])

        stored = self.store.obtenir(dem_id)
        assert stored is not None
        self.assertEqual(len(stored["recherches"]), 2)
        self.assertEqual(stored["recherches"][0]["resultats"][0]["prix_unitaire_eur"], 62)

    def test_mauvaise_cle_d_equipe_est_refusee(self):
        client = SupplierClient(self.supplier_url, "mauvaise-cle")
        with self.assertRaises(SupplierError) as ctx:
            client.rechercher(criteres_depuis_demande(DemandStore(None).creer(dict(VALIDE))))
        self.assertIn("refus", str(ctx.exception).lower())
        self.assertEqual(ctx.exception.status, 403)
        self.assertIn("authentification", str(ctx.exception).lower())


TOOL_CALL_MESSAGE = {
    "role": "assistant",
    "content": None,
    "tool_calls": [{
        "id": "call_1",
        "type": "function",
        "function": {
            "name": "chercher_voyages",
            "arguments": json.dumps({
                "type_voyage": "lune-de-miel",
                "destination": "Nantes",
                "date_depart": "2026-11-07",
                "date_retour": "2026-11-09",
                "nombre_voyageurs": 2,
                "budget_max_par_personne": 500,
                "niveau_aventure": "calme",
            }),
        },
    }],
}

FINAL_MESSAGE = {"role": "assistant", "content": "Voici les prestations vérifiées pour Nantes."}


def _tool_call_message(arguments, call_id="call_1"):
    """Build a scripted OpenRouter assistant message that calls chercher_voyages."""
    return {
        "role": "assistant",
        "content": None,
        "tool_calls": [{
            "id": call_id,
            "type": "function",
            "function": {
                "name": "chercher_voyages",
                "arguments": json.dumps(arguments),
            },
        }],
    }


class FakeOpenRouter:
    """Imite l'API OpenRouter avec des réponses scriptées, une par appel reçu."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers.get("Content-Length", "0"))
                outer.requests.append({"authorization": self.headers.get("Authorization"),
                                       "body": json.loads(self.rfile.read(length))})
                scripted = outer.responses.pop(0) if outer.responses else {
                    "status": 500, "payload": {"error": {"message": "plus de réponses scriptées"}}}
                if scripted.get("status", 200) == 200:
                    payload = {"choices": [{"message": scripted["message"]}]}
                else:
                    payload = scripted.get("payload", {"error": {"message": "erreur scriptée"}})
                data = json.dumps(payload).encode("utf-8")
                self.send_response(scripted.get("status", 200))
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def log_message(self, *args):
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.server.server_port}/v1/chat/completions"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def stop(self):
        self.server.shutdown()
        self.server.server_close()


class FakeAgent:
    def __init__(self, result=None):
        self.result = result or {
            "reply": "Bonjour !", "demande": None, "recherche": None,
            "trace": {"model": "test", "tool_calls": [], "simulation": True},
        }
        self.calls = []

    def chat(self, messages, user_id="", demande_id=None):
        self.calls.append({
            "messages": messages, "user_id": user_id, "demande_id": demande_id,
        })
        return self.result


class TestAgent(unittest.TestCase):
    def setUp(self):
        self.store = DemandStore(None)
        self.supplier = FakeSupplier()

    def make_agent(self, responses):
        fake = FakeOpenRouter(responses)
        self.addCleanup(fake.stop)
        return Agent(self.supplier, self.store, api_key="cle-test",
                     model="modele-test", base_url=fake.url, timeout=5), fake

    def test_cle_absente(self):
        agent = Agent(self.supplier, self.store, api_key="")
        with self.assertRaises(OpenRouterError) as ctx:
            agent.chat([{"role": "user", "content": "Bonjour"}])
        self.assertEqual(ctx.exception.status, 503)

    def test_openrouter_injoignable(self):
        agent = Agent(self.supplier, self.store, api_key="cle",
                      base_url=f"http://127.0.0.1:{free_port()}/x", timeout=1)
        with self.assertRaises(OpenRouterError):
            agent.chat([{"role": "user", "content": "Bonjour"}])

    def test_cle_refusee(self):
        fake = FakeOpenRouter([{"status": 401, "payload": {"error": {"message": "invalid key"}}}])
        self.addCleanup(fake.stop)
        agent = Agent(self.supplier, self.store, api_key="mauvaise", base_url=fake.url, timeout=5)
        with self.assertRaises(OpenRouterError) as ctx:
            agent.chat([{"role": "user", "content": "Bonjour"}])
        self.assertIn("clé", str(ctx.exception))

    def test_reponse_sans_outil(self):
        agent, fake = self.make_agent([
            {"message": {"role": "assistant", "content": "Bonjour ! Où voulez-vous partir ?"}}])
        result = agent.chat([{"role": "user", "content": "Bonjour"}])
        self.assertEqual(result["reply"], "Bonjour ! Où voulez-vous partir ?")
        self.assertIsNone(result["demande"])
        self.assertIsNone(result["recherche"])
        self.assertEqual(result["trace"]["tool_calls"], [])
        self.assertEqual(fake.requests[0]["authorization"], "Bearer cle-test")
        self.assertNotIn("cle-test", json.dumps(fake.requests[0]["body"]))

    def test_outil_complet_cree_demande_et_recherche(self):
        agent, fake = self.make_agent([{"message": TOOL_CALL_MESSAGE}, {"message": FINAL_MESSAGE}])
        result = agent.chat([{"role": "user", "content": "Week-end à Nantes pour 2"}])
        self.assertEqual(result["reply"], FINAL_MESSAGE["content"])
        self.assertTrue(result["demande"]["id"].startswith("dem_"))
        self.assertIsNotNone(result["recherche"])
        self.assertEqual(result["trace"]["tool_calls"][0]["statut"], "ok")
        self.assertEqual(result["demande"]["qualification"], "pret_relecture")
        tool_payload = json.loads(fake.requests[1]["body"]["messages"][-1]["content"])
        self.assertIn("enregistrée", tool_payload["confirmation"])
        stored = self.store.obtenir(result["demande"]["id"])
        assert stored is not None
        self.assertEqual(len(stored["recherches"]), 1)
        self.assertEqual(fake.requests[1]["body"]["messages"][-1]["role"], "tool")
        self.assertNotIn("cle-test", json.dumps(result["trace"]))

    def test_agent_ne_peut_pas_valider_pour_proposition(self):
        tentative = copy.deepcopy(TOOL_CALL_MESSAGE)
        arguments = json.loads(tentative["tool_calls"][0]["function"]["arguments"])
        arguments["qualification"] = "pret_proposition"
        tentative["tool_calls"][0]["function"]["arguments"] = json.dumps(arguments)
        agent, _ = self.make_agent([{"message": tentative}, {"message": FINAL_MESSAGE}])
        result = agent.chat([{"role": "user", "content": "Week-end à Nantes pour 2"}])
        self.assertEqual(result["demande"]["qualification"], "pret_relecture")
        self.assertIn("qualification_refusee", result["trace"]["tool_calls"][0])
        with self.assertRaises(ValidationError):
            self.store.definir_qualification(result["demande"]["id"], "pret_proposition", acteur="agent", par="agent", motif="je tranche")

    def test_invalid_value_does_not_confirm_save(self):
        bad = copy.deepcopy(TOOL_CALL_MESSAGE)
        bad["tool_calls"][0]["function"]["arguments"] = json.dumps({"type_voyage": "inconnu"})
        agent, fake = self.make_agent([{"message": bad}, {"message": FINAL_MESSAGE}])
        result = agent.chat([{"role": "user", "content": "Nantes"}])
        call = result["trace"]["tool_calls"][0]
        self.assertEqual(call["statut"], "echec_mise_a_jour")
        self.assertIsNone(result["demande"])
        self.assertEqual(len(self.store.lister()), 0)
        tool_payload = json.loads(fake.requests[1]["body"]["messages"][-1]["content"])
        self.assertIsNone(tool_payload["confirmation"])
        self.assertIn("échoué", tool_payload["consigne"])

    def test_partial_draft_saved_without_reasking_provided_fields(self):
        partial = copy.deepcopy(TOOL_CALL_MESSAGE)
        arguments = json.loads(partial["tool_calls"][0]["function"]["arguments"])
        del arguments["budget_max_par_personne"]
        partial["tool_calls"][0]["function"]["arguments"] = json.dumps(arguments)
        agent, fake = self.make_agent([{"message": partial}, {"message": FINAL_MESSAGE}])
        result = agent.chat([{"role": "user", "content": "Nantes en novembre"}])
        call = result["trace"]["tool_calls"][0]
        self.assertEqual(call["statut"], "informations_manquantes")
        self.assertEqual(call["informations"]["manquants"], ["budget_max_par_personne"])
        self.assertIn("destination", call["informations"]["fournis"])
        self.assertIn("date_depart", call["informations"]["fournis"])
        self.assertNotIn("budget_max_par_personne", call["informations"]["fournis"])
        self.assertIsNotNone(result["demande"])
        self.assertEqual(result["demande"]["demande"]["destination"], "Nantes")
        tool_payload = json.loads(fake.requests[1]["body"]["messages"][-1]["content"])
        self.assertIn("enregistrée", tool_payload["confirmation"])
        self.assertIn("budget maximum par personne", tool_payload["consigne"])
        self.assertIn("Ne redemande pas", tool_payload["consigne"])

    def test_budget_updates_existing_request(self):
        existing, _ = self.store.enregistrer_reponses(None, {
            "type_voyage": "lune-de-miel",
            "destination": "Nantes",
            "date_depart": "2026-11-07",
            "date_retour": "2026-11-09",
            "nombre_voyageurs": 2,
            "niveau_aventure": "calme",
        }, user_id="client-1")
        budget_only = copy.deepcopy(TOOL_CALL_MESSAGE)
        budget_only["tool_calls"][0]["function"]["arguments"] = json.dumps({
            "budget_max_par_personne": 500,
            "demande_id": "dem_from_model_ignored",
        })
        agent, fake = self.make_agent([{"message": budget_only}, {"message": FINAL_MESSAGE}])
        result = agent.chat(
            [{"role": "user", "content": "Mon budget est 500 €"}],
            user_id="client-1",
            demande_id=existing["id"],
        )
        self.assertEqual(result["demande"]["id"], existing["id"])
        self.assertEqual(result["demande"]["demande"]["budget_max_par_personne"], 500)
        self.assertEqual(result["demande"]["demande"]["destination"], "Nantes")
        self.assertEqual(result["trace"]["tool_calls"][0]["statut"], "ok")
        self.assertEqual(result["trace"]["tool_calls"][0]["champs_mis_a_jour"],
                         ["budget_max_par_personne"])
        self.assertEqual(len(self.store.lister()), 1)
        tool_payload = json.loads(fake.requests[1]["body"]["messages"][-1]["content"])
        self.assertEqual(tool_payload["demande_id"], existing["id"])
        self.assertIn("enregistrée", tool_payload["confirmation"])

    def test_outil_inconnu_refuse(self):
        bad = copy.deepcopy(TOOL_CALL_MESSAGE)
        bad["tool_calls"][0]["function"]["name"] = "reserver"
        agent, _ = self.make_agent([{"message": bad}, {"message": FINAL_MESSAGE}])
        result = agent.chat([{"role": "user", "content": "Réserve"}])
        self.assertEqual(result["trace"]["tool_calls"][0]["statut"], "refuse")
        self.assertIsNone(result["demande"])
        self.assertEqual(len(self.store.lister()), 0)

    def test_serveur_fictif_indisponible(self):
        supplier = FakeSupplier(SupplierError("Serveur fictif injoignable"))
        fake = FakeOpenRouter([{"message": TOOL_CALL_MESSAGE}, {"message": FINAL_MESSAGE}])
        self.addCleanup(fake.stop)
        agent = Agent(supplier, self.store, api_key="cle", model="m", base_url=fake.url, timeout=5)
        result = agent.chat([{"role": "user", "content": "Nantes"}])
        self.assertEqual(result["trace"]["tool_calls"][0]["statut"], "serveur_indisponible")
        self.assertIsNotNone(result["demande"])
        self.assertIsNone(result["recherche"])


class TestMissingInfoConversationFlow(unittest.TestCase):
    """Conversation flow for incomplete travel requests (#38).

    Starts with missing dates and budget, answers one step at a time on the
    same demande_id, and only allows advisor proposal validation when complete.
    """

    def setUp(self):
        self.store = DemandStore(None)
        self.props = PropositionStore(None)
        self.supplier = FakeSupplier()

    def make_agent(self, responses):
        fake = FakeOpenRouter(responses)
        self.addCleanup(fake.stop)
        return Agent(self.supplier, self.store, api_key="cle-test",
                     model="modele-test", base_url=fake.url, timeout=5), fake

    def test_system_prompt_requires_one_question_per_turn(self):
        self.assertIn("une question à la fois", SYSTEM_PROMPT)

    def test_incomplete_request_blocks_proposal_until_dates_and_budget_filled(self):
        draft, _ = self.store.enregistrer_reponses(None, {
            "type_voyage": "lune-de-miel",
            "destination": "Nantes",
            "nombre_voyageurs": 2,
            "niveau_aventure": "calme",
        }, user_id="client-1")
        dem_id = draft["id"]
        self.assertIn("date_depart", draft["champs_manquants"])
        self.assertIn("date_retour", draft["champs_manquants"])
        self.assertIn("budget_max_par_personne", draft["champs_manquants"])
        with self.assertRaises(ValidationError) as blocked:
            self.store.definir_qualification(dem_id, QUALIF_PRET_PROPOSITION, par="Alice", motif="dossier complet")
        self.assertIn("date_depart", str(blocked.exception))
        self.assertEqual(self.props.lister_par_demande(dem_id), [])

        # Turn 1: agent asks only for dates (no tool, one question).
        ask_dates = {
            "role": "assistant",
            "content": "Quelles sont vos dates de départ et de retour ?",
        }
        agent, _ = self.make_agent([{"message": ask_dates}])
        turn1 = agent.chat(
            [{"role": "user", "content": "Week-end à Nantes pour 2"}],
            user_id="client-1",
            demande_id=dem_id,
        )
        self.assertIn("dates", turn1["reply"].lower())
        self.assertNotIn("budget", turn1["reply"].lower())
        self.assertEqual(turn1["trace"]["tool_calls"], [])
        self.assertIsNone(turn1["recherche"])
        self.assertEqual(len(self.store.lister()), 1)

        # Turn 2: customer answers dates → same request updated, still incomplete.
        ask_budget = {
            "role": "assistant",
            "content": "Quel est votre budget maximum par personne ?",
        }
        agent, fake = self.make_agent([
            {"message": _tool_call_message({
                "date_depart": "2026-11-07",
                "date_retour": "2026-11-09",
            })},
            {"message": ask_budget},
        ])
        turn2 = agent.chat(
            [
                {"role": "user", "content": "Week-end à Nantes pour 2"},
                {"role": "assistant", "content": ask_dates["content"]},
                {"role": "user", "content": "Du 7 au 9 novembre 2026"},
            ],
            user_id="client-1",
            demande_id=dem_id,
        )
        self.assertEqual(turn2["demande"]["id"], dem_id)
        self.assertEqual(turn2["demande"]["demande"]["date_depart"], "2026-11-07")
        self.assertEqual(turn2["demande"]["demande"]["date_retour"], "2026-11-09")
        self.assertEqual(turn2["demande"]["demande"]["destination"], "Nantes")
        self.assertNotIn("budget_max_par_personne", turn2["demande"]["demande"])
        call = turn2["trace"]["tool_calls"][0]
        self.assertEqual(call["statut"], "informations_manquantes")
        self.assertEqual(call["informations"]["manquants"], ["budget_max_par_personne"])
        self.assertIn("date_depart", call["informations"]["fournis"])
        self.assertIsNone(turn2["recherche"])
        self.assertIn("budget", turn2["reply"].lower())
        self.assertNotIn("dates", turn2["reply"].lower())
        tool_payload = json.loads(fake.requests[1]["body"]["messages"][-1]["content"])
        self.assertEqual(tool_payload["demande_id"], dem_id)
        with self.assertRaises(ValidationError):
            self.store.definir_qualification(dem_id, QUALIF_PRET_PROPOSITION, par="Alice", motif="dossier complet")
        self.assertEqual(self.props.lister_par_demande(dem_id), [])
        self.assertEqual(len(self.store.lister()), 1)

        # Turn 3: budget completes the request → supplier search, still no proposal.
        agent, _ = self.make_agent([
            {"message": _tool_call_message({"budget_max_par_personne": 500})},
            {"message": FINAL_MESSAGE},
        ])
        turn3 = agent.chat(
            [{"role": "user", "content": "Mon budget est 500 euros par personne"}],
            user_id="client-1",
            demande_id=dem_id,
        )
        self.assertEqual(turn3["demande"]["id"], dem_id)
        self.assertEqual(turn3["demande"]["demande"]["budget_max_par_personne"], 500)
        self.assertEqual(turn3["demande"]["demande"]["date_depart"], "2026-11-07")
        self.assertEqual(turn3["demande"]["champs_manquants"], [])
        self.assertEqual(turn3["trace"]["tool_calls"][0]["statut"], "ok")
        self.assertIsNotNone(turn3["recherche"])
        self.assertEqual(turn3["demande"]["qualification"], QUALIF_PRET_RELECTURE)
        self.assertEqual(self.props.lister_par_demande(dem_id), [])
        self.assertEqual(len(self.store.lister()), 1)

        validated = self.store.definir_qualification(dem_id, QUALIF_PRET_PROPOSITION, par="Alice", motif="dossier complet")
        self.assertEqual(validated["qualification"], QUALIF_PRET_PROPOSITION)

    def test_complete_request_in_one_tool_call_still_not_a_proposal(self):
        agent, _ = self.make_agent([
            {"message": TOOL_CALL_MESSAGE},
            {"message": FINAL_MESSAGE},
        ])
        result = agent.chat(
            [{"role": "user", "content": "Week-end à Nantes pour 2, budget 500"}],
            user_id="client-1",
        )
        self.assertTrue(result["demande"]["id"].startswith("dem_"))
        self.assertEqual(result["demande"]["champs_manquants"], [])
        self.assertIsNotNone(result["recherche"])
        self.assertEqual(result["demande"]["qualification"], QUALIF_PRET_RELECTURE)
        self.assertEqual(self.props.lister_par_demande(result["demande"]["id"]), [])
        with self.assertRaises(ValidationError):
            self.store.definir_qualification(
                result["demande"]["id"], QUALIF_PRET_PROPOSITION, acteur="agent",
                par="agent", motif="je tranche")


class TestChatRoute(unittest.TestCase):
    def serve(self, agent):
        store = DemandStore(None)
        server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(store, FakeSupplier(), agent))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(lambda: (server.shutdown(), server.server_close()))
        return f"http://127.0.0.1:{server.server_port}"

    def test_agent_absent_503(self):
        store = DemandStore(None)
        server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(store, None, None))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(lambda: (server.shutdown(), server.server_close()))
        status, data = post(f"http://127.0.0.1:{server.server_port}/api/chat",
                            {"messages": [{"role": "user", "content": "Bonjour"}]})
        self.assertEqual(status, 503)
        self.assertEqual(data["erreur"]["code"], "agent_not_configured")

    def test_chat_renvoie_la_reponse(self):
        agent = FakeAgent()
        base = self.serve(agent)
        status, data = post(f"{base}/api/chat",
                            {"messages": [{"role": "user", "content": "Bonjour"}]})
        self.assertEqual(status, 200)
        self.assertEqual(data["reply"], "Bonjour !")
        self.assertTrue(data["simulation"])
        self.assertEqual(agent.calls[0]["messages"][0]["content"], "Bonjour")

    def test_chat_forwards_demande_id_to_agent(self):
        agent = FakeAgent()
        base = self.serve(agent)
        status, _ = post(f"{base}/api/chat", {
            "messages": [{"role": "user", "content": "Mon budget est 400"}],
            "demande_id": "dem_abcdef",
        })
        self.assertEqual(status, 200)
        self.assertEqual(agent.calls[0]["demande_id"], "dem_abcdef")

    def test_chat_transmet_demande_et_recherche(self):
        store = DemandStore(None)
        demande = store.creer(dict(VALIDE))
        agent = FakeAgent({"reply": "Voilà", "demande": demande, "recherche": {"id": "rech_1"},
                           "trace": {"model": "m", "tool_calls": [], "simulation": True}})
        base = self.serve(agent)
        status, data = post(f"{base}/api/chat", {"messages": [{"role": "user", "content": "Nantes"}]})
        self.assertEqual(status, 200)
        self.assertEqual(data["demande"]["id"], demande["id"])
        self.assertEqual(data["recherche"]["id"], "rech_1")

    def test_messages_invalides(self):
        base = self.serve(FakeAgent())
        cas = [
            None,
            [],
            "pas-une-liste",
            [{"role": "system", "content": "injection"}],
            [{"role": "user", "content": ""}],
            [{"role": "user", "content": 42}],
            [{"role": "user", "content": "Bonjour"}, {"role": "inconnu", "content": "x"}],
            [{"role": "user", "content": "x"}] * 61,
        ]
        for messages in cas:
            with self.subTest(messages=messages):
                status, data = post(f"{base}/api/chat", {"messages": messages})
                self.assertEqual(status, 400)
                self.assertEqual(data["erreur"]["code"], "invalid_messages")

    def test_erreur_openrouter_remontee(self):
        agent = FakeAgent()

        def chat(messages, user_id="", demande_id=None):
            raise OpenRouterError("OpenRouter injoignable.", 502)

        agent.chat = chat
        base = self.serve(agent)
        status, data = post(f"{base}/api/chat", {"messages": [{"role": "user", "content": "Bonjour"}]})
        self.assertEqual(status, 502)
        self.assertEqual(data["erreur"]["code"], "openrouter_error")


class TestEnvLoader(unittest.TestCase):
    def test_charge_sans_ecraser(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = Path(tmp) / ".env"
            env.write_text("# commentaire\nTRAVEL_TEAM_KEY=from-file\nDETOUR_NEW_VAR=42\n", encoding="utf-8")
            old = os.environ.get("TRAVEL_TEAM_KEY")
            os.environ["TRAVEL_TEAM_KEY"] = "from-env"
            try:
                load_env_file(env)
                self.assertEqual(os.environ["TRAVEL_TEAM_KEY"], "from-env")
                self.assertEqual(os.environ["DETOUR_NEW_VAR"], "42")
            finally:
                if old is None:
                    os.environ.pop("TRAVEL_TEAM_KEY", None)
                else:
                    os.environ["TRAVEL_TEAM_KEY"] = old
                os.environ.pop("DETOUR_NEW_VAR", None)

    def test_fichier_absent_ne_leve_rien(self):
        load_env_file(Path("/tmp/detour-inexistant-.env"))


class TestConfigAndMetrics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.store = DemandStore(None)
        cls.props = PropositionStore(None)
        cls.handler = make_handler(cls.store, FakeSupplier(), FakeAgent(),
                                    propositions=cls.props)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(("127.0.0.1", 0))
        cls.port = sock.getsockname()[1]
        sock.close()
        cls.server = ThreadingHTTPServer(("127.0.0.1", cls.port), cls.handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def url(self, path):
        return f"http://127.0.0.1:{self.port}{path}"

    def test_config_public(self):
        with urllib.request.urlopen(self.url("/api/config")) as res:
            data = json.loads(res.read())
        self.assertIn("simulation", data)
        self.assertIn("agent_actif", data)
        self.assertIn("google_oauth", data)

    def test_metrics_public(self):
        with urllib.request.urlopen(self.url("/metrics")) as res:
            body = res.read().decode("utf-8")
        self.assertIn("detour_demandes_total", body)
        self.assertIn("detour_propositions_total", body)

    def test_metrics_avec_token(self):
        os.environ["METRICS_TOKEN"] = "secret-token"
        try:
            store = DemandStore(None)
            props = PropositionStore(None)
            handler = make_handler(store, FakeSupplier(), FakeAgent(), propositions=props)
            server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
            threading.Thread(target=server.serve_forever, daemon=True).start()
            base = f"http://127.0.0.1:{server.server_port}"
            self.addCleanup(lambda: (server.shutdown(), server.server_close()))
            try:
                urllib.request.urlopen(base + "/metrics")
                self.fail("Devrait refuser sans token.")
            except urllib.error.HTTPError as e:
                self.assertEqual(e.code, 401)
            with urllib.request.urlopen(base + "/metrics?token=secret-token") as res:
                self.assertEqual(res.status, 200)
        finally:
            os.environ.pop("METRICS_TOKEN", None)


class TestCorrigerDemande(unittest.TestCase):
    """The advisor can correct a request; every change is recorded."""

    def setUp(self):
        self.store = DemandStore(None)  # no path: nothing is written to disk
        self.dem = self.store.creer(dict(VALIDE, user_id="client_1"))

    def test_correction_updates_field_and_records_history(self):
        result = self.store.corriger(self.dem["id"], {"budget_max_par_personne": 600}, "Alice", "budget revise")
        self.assertEqual(result["demande"]["budget_max_par_personne"], 600)
        self.assertEqual(len(result["modifications"]), 1)
        entry = result["modifications"][0]
        self.assertEqual(entry["champ"], "budget_max_par_personne")
        self.assertEqual(entry["avant"], 500)
        self.assertEqual(entry["apres"], 600)
        self.assertEqual(entry["par"], "Alice")
        self.assertTrue(entry["le"])

    def test_correction_clears_previous_validation(self):
        self.store.definir_qualification(self.dem["id"], QUALIF_PRET_PROPOSITION, par="Alice", motif="dossier complet")
        result = self.store.corriger(self.dem["id"], {"destination": "Lyon"}, "Alice", "destination corrigee")
        self.assertIsNone(result["qualification_validee_par"])
        self.assertEqual(result["qualification"], QUALIF_PRET_RELECTURE)

    def test_same_value_records_nothing(self):
        result = self.store.corriger(self.dem["id"], {"destination": "Nantes"}, "Alice", "verifie")
        self.assertEqual(result["modifications"], [])

    def test_invalid_value_is_rejected_and_nothing_changes(self):
        with self.assertRaises(ValidationError):
            self.store.corriger(self.dem["id"], {"budget_max_par_personne": -5}, "Alice", "budget revise")
        unchanged = self.store.obtenir(self.dem["id"])
        self.assertEqual(unchanged["demande"]["budget_max_par_personne"], 500)

    def test_user_id_cannot_be_changed(self):
        with self.assertRaises(ValidationError):
            self.store.corriger(self.dem["id"], {"user_id": "someone_else"}, "Alice", "changement interdit")

    def test_author_is_required(self):
        with self.assertRaises(ValidationError):
            self.store.corriger(self.dem["id"], {"destination": "Lyon"}, "  ", "destination corrigee")

    def test_unknown_request_returns_none(self):
        self.assertIsNone(self.store.corriger("dem_unknown", {"destination": "Lyon"}, "Alice", "destination corrigee"))


class TestCorrectionRoute(unittest.TestCase):
    """PATCH /api/demandes/<id>/correction updates the request through HTTP."""

    def setUp(self):
        self.store = DemandStore(None)
        server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(self.store))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(lambda: (server.shutdown(), server.server_close()))
        self.base = f"http://127.0.0.1:{server.server_port}"
        self.dem_id = self.store.creer(dict(VALIDE))["id"]

    def patch(self, path, payload):
        req = urllib.request.Request(
            self.base + path, data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}, method="PATCH")
        try:
            with urllib.request.urlopen(req) as res:
                return res.status, json.loads(res.read())
        except urllib.error.HTTPError as err:
            return err.code, json.loads(err.read())

    def test_correction_route_updates_request(self):
        status, data = self.patch(f"/api/demandes/{self.dem_id}/correction",
                                  {"champs": {"budget_max_par_personne": 600},
                                   "motif": "budget revise par le conseiller"})
        self.assertEqual(status, 200)
        self.assertEqual(data["demande"]["demande"]["budget_max_par_personne"], 600)
        self.assertEqual(len(data["demande"]["modifications"]), 1)

    def test_invalid_value_returns_400(self):
        status, data = self.patch(f"/api/demandes/{self.dem_id}/correction",
                                  {"champs": {"budget_max_par_personne": -5},
                                   "motif": "budget revise"})
        self.assertEqual(status, 400)
        self.assertEqual(data["erreur"]["code"], "validation_error")

    def test_missing_motif_is_accepted(self):
        status, data = self.patch(f"/api/demandes/{self.dem_id}/correction",
                                  {"champs": {"budget_max_par_personne": 600}})
        self.assertEqual(status, 200)
        self.assertEqual(data["demande"]["decisions"][-1]["motif"], "")

    def test_unknown_request_returns_404(self):
        status, _ = self.patch("/api/demandes/dem_abc123/correction",
                               {"champs": {"destination": "Lyon"},
                                "motif": "destination corrigee"})
        self.assertEqual(status, 404)



class TestConditionalQuestions(unittest.TestCase):
    """Only the questions that match the trip are asked (#22)."""

    def test_trek_asks_level_and_guide(self):
        questions = questions_conditionnelles(dict(VALIDE, type_voyage="trek-randonnee"))
        self.assertEqual(questions, ["niveau_aventure", "besoin_guide"])

    def test_honeymoon_without_car_asks_nothing(self):
        questions = questions_conditionnelles(dict(VALIDE, type_voyage="lune-de-miel"))
        self.assertEqual(questions, [])

    def test_self_drive_asks_driving_license(self):
        questions = questions_conditionnelles(
            dict(VALIDE, type_voyage="lune-de-miel", avec_voiture=True))
        self.assertEqual(questions, ["permis_conduire"])

    def test_answers_are_stored_in_the_request(self):
        record = DemandStore(None).creer(dict(VALIDE, avec_voiture=True, permis_conduire=True))
        self.assertTrue(record["demande"]["avec_voiture"])
        self.assertTrue(record["demande"]["permis_conduire"])

    def test_license_is_dropped_without_car(self):
        result = valider_demande(dict(VALIDE, avec_voiture=False, permis_conduire=True))
        self.assertIsNone(result["permis_conduire"])

    def test_invalid_car_answer_is_rejected(self):
        with self.assertRaises(ValidationError):
            valider_demande(dict(VALIDE, avec_voiture="yes"))

    def test_answers_are_not_sent_to_the_server(self):
        record = DemandStore(None).creer(dict(VALIDE, avec_voiture=True, permis_conduire=True))
        criteres = criteres_depuis_demande(record)
        self.assertNotIn("avec_voiture", criteres)
        self.assertNotIn("permis_conduire", criteres)

    def test_chat_answers_are_merged_into_the_request(self):
        merged, updated = fusionner_reponses(
            {"destination": "Lyon"}, {"avec_voiture": True, "permis_conduire": True})
        self.assertEqual(updated, ["avec_voiture", "permis_conduire"])
        self.assertTrue(merged["permis_conduire"])
        self.assertEqual(merged["destination"], "Lyon")

    def test_invalid_chat_answer_is_rejected(self):
        with self.assertRaises(ValidationError):
            fusionner_reponses({}, {"permis_conduire": "yes"})

    def test_relevant_questions_are_sent_to_the_model(self):
        info = analyser_informations(dict(VALIDE, type_voyage="lune-de-miel", avec_voiture=True))
        self.assertEqual(info["questions_conditionnelles"], ["permis_conduire"])

if __name__ == "__main__":
    unittest.main()

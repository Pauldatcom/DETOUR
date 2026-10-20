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

from store import DemandStore, ValidationError, criteres_depuis_demande, valider_demande
from app import load_env_file, make_handler
from agent import Agent, OpenRouterError
from fournisseur import SupplierClient, SupplierError
from propositions import PropositionStore, PropositionError


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


class TestDemandStore(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.path = Path(self.tmpdir) / "demandes.json"
        self.store = DemandStore(self.path)

    def test_creer_et_obtenir(self):
        record = self.store.creer(dict(VALIDE))
        self.assertTrue(record["id"].startswith("dem_"))
        self.assertEqual(record["statut"], "a_analyser")
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

    def test_obtenir_inexistant(self):
        self.assertIsNone(self.store.obtenir("dem_inconnu"))


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
        self.assertIn("refusé", str(ctx.exception))


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

    def chat(self, messages, user_id=""):
        self.calls.append({"messages": messages, "user_id": user_id})
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
        stored = self.store.obtenir(result["demande"]["id"])
        assert stored is not None
        self.assertEqual(len(stored["recherches"]), 1)
        self.assertEqual(fake.requests[1]["body"]["messages"][-1]["role"], "tool")
        self.assertNotIn("cle-test", json.dumps(result["trace"]))

    def test_arguments_invalides_renvoyes_au_modele(self):
        bad = copy.deepcopy(TOOL_CALL_MESSAGE)
        bad["tool_calls"][0]["function"]["arguments"] = json.dumps({"type_voyage": "inconnu"})
        agent, _ = self.make_agent([{"message": bad}, {"message": FINAL_MESSAGE}])
        result = agent.chat([{"role": "user", "content": "Nantes"}])
        self.assertEqual(result["trace"]["tool_calls"][0]["statut"], "invalide")
        self.assertIsNone(result["demande"])
        self.assertEqual(len(self.store.lister()), 0)

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

        def chat(messages, user_id=""):
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


PROPOSITION_VALIDE = {
    "titre": "Week-end à Nantes",
    "description": "Un séjour romantique à Nantes.",
    "prestations": [
        {"id": "train-nantes-01", "nom": "Train Nantes", "type": "transport",
         "prix_unitaire_eur": 48, "quantite": 2},
        {"id": "hotel-nantes-01", "nom": "Hôtel Nantes", "type": "hébergement",
         "prix_unitaire_eur": 120, "quantite": 1},
    ],
}


class TestPropositionStore(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.path = Path(self.tmpdir) / "propositions.json"
        self.store = PropositionStore(self.path)
        self.demand_store = DemandStore(Path(self.tmpdir) / "demandes.json")

    def test_creer_et_obtenir(self):
        prop = self.store.creer("dem_abc123", dict(PROPOSITION_VALIDE), conseiller="Alice")
        self.assertTrue(prop["id"].startswith("prop_"))
        self.assertEqual(prop["statut"], "brouillon")
        self.assertEqual(prop["conseiller"], "Alice")
        self.assertEqual(prop["prix_total_eur"], 216)
        fetched = self.store.obtenir(prop["id"])
        assert fetched is not None
        self.assertEqual(fetched["titre"], "Week-end à Nantes")

    def test_persiste_sur_disque(self):
        prop = self.store.creer("dem_abc123", dict(PROPOSITION_VALIDE))
        store2 = PropositionStore(self.path)
        self.assertEqual(len(store2.lister()), 1)
        self.assertEqual(store2.obtenir(prop["id"])["titre"], "Week-end à Nantes")

    def test_lister_par_demande(self):
        self.store.creer("dem_aaa", dict(PROPOSITION_VALIDE))
        self.store.creer("dem_bbb", dict(PROPOSITION_VALIDE))
        self.store.creer("dem_aaa", dict(PROPOSITION_VALIDE, titre="Autre"))
        self.assertEqual(len(self.store.lister_par_demande("dem_aaa")), 2)
        self.assertEqual(len(self.store.lister_par_demande("dem_bbb")), 1)

    def test_lister_par_user(self):
        dem = self.demand_store.creer({**VALIDE, "user_id": "usr_abc"})
        self.store.creer(dem["id"], dict(PROPOSITION_VALIDE))
        self.store.creer("dem_autre", dict(PROPOSITION_VALIDE))
        props = self.store.lister_par_user("usr_abc", self.demand_store)
        self.assertEqual(len(props), 1)

    def test_mettre_a_jour(self):
        prop = self.store.creer("dem_abc", dict(PROPOSITION_VALIDE))
        updated = self.store.mettre_a_jour(prop["id"], {"titre": "Modifié",
             "description": "Nouvelle desc", "prestations": []})
        self.assertEqual(updated["titre"], "Modifié")
        self.assertEqual(updated["prix_total_eur"], 0)

    def test_changer_statut(self):
        prop = self.store.creer("dem_abc", dict(PROPOSITION_VALIDE))
        self.assertEqual(self.store.changer_statut(prop["id"], "envoyee")["statut"], "envoyee")
        with self.assertRaises(PropositionError):
            self.store.changer_statut(prop["id"], "inconnu")
        self.assertIsNone(self.store.changer_statut("prop_inconnu", "envoyee"))

    def test_prestation_invalide(self):
        with self.assertRaises(PropositionError):
            self.store.creer("dem_abc", {"titre": "Test", "prestations": [{"nom": ""}]})

    def test_titre_manquant(self):
        with self.assertRaises(PropositionError):
            self.store.creer("dem_abc", {"titre": "", "prestations": []})


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


class FakeAgentWithGeneration(FakeAgent):
    def generer_proposition(self, demande_record, recherche):
        return {"titre": "Généré", "description": "Proposition générée",
                "prestations": [{"id": "train-01", "nom": "Train", "type": "transport",
                                 "prix_unitaire_eur": 50, "quantite": 2}]}


class TestPropositionGeneration(unittest.TestCase):
    """Test proposition generation through the agent (no real OpenRouter call)."""

    def test_generer_proposition_retourne_json(self):
        agent = FakeAgentWithGeneration()
        demande = {"demande": {"destination": "Nantes", "date_depart": "2026-11-07",
                               "date_retour": "2026-11-09", "nombre_voyageurs": 2,
                               "budget_max_par_personne": 500, "type_voyage": "trek-randonnee",
                               "niveau_aventure": "modere", "souhaits": ""}}
        recherche = {"resultats": [{"id": "train-nantes-01", "nom": "Train", "type": "transport",
                                    "prix_unitaire_eur": 48, "prix_total_eur": 96}]}
        result = agent.generer_proposition(demande, recherche)
        self.assertEqual(result["titre"], "Généré")
        self.assertIsInstance(result["prestations"], list)


if __name__ == "__main__":
    unittest.main()

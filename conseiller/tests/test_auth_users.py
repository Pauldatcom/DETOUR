#!/usr/bin/env python3
"""Tests du portail DÉTOUR : comptes voyageurs, sessions, pages, statuts."""

import http.cookiejar
import json
import secrets
import shutil
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

CONSEILLER_ROOT = Path(__file__).resolve().parent.parent
import sys
sys.path.insert(0, str(CONSEILLER_ROOT))

from app import make_handler
from store import DemandStore, STATUTS, ValidationError
from users import UserStore, UserError
from propositions import PropositionStore, PropositionError

VALIDE = {
    "type_voyage": "lune-de-miel",
    "destination": "Lyon",
    "date_depart": "2030-11-07",
    "date_retour": "2030-11-09",
    "nombre_voyageurs": 2,
    "budget_max_par_personne": 500,
    "niveau_aventure": "calme",
}

PROPOSITION_VALIDE = {
    "titre": "Week-end à Lyon",
    "description": "Un séjour romantique.",
    "prestations": [
        {"id": "train-lyon-01", "nom": "Train Lyon", "type": "transport",
         "prix_unitaire_eur": 62, "quantite": 2, "disponible": True,
         "source": "Serveur fictif DÉTOUR", "consulte_le": "2026-10-19T10:42:00+00:00"},
    ],
}


class TestUserStore(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.users = UserStore(Path(self.tmp) / "users.json")

    def test_creer_et_authentifier(self):
        compte = self.users.creer("Alice@Exemple.fr", "Alice", "motdepasse")
        self.assertTrue(compte["id"].startswith("usr_"))
        self.assertEqual(compte["email"], "alice@exemple.fr")
        auth = self.users.authentifier("alice@exemple.fr", "motdepasse")
        self.assertEqual(auth["id"], compte["id"])
        self.assertIsNone(self.users.authentifier("alice@exemple.fr", "mauvais"))
        self.assertIsNone(self.users.authentifier("inconnu@exemple.fr", "motdepasse"))

    def test_email_invalide(self):
        with self.assertRaises(UserError):
            self.users.creer("pas-un-email", "Nom", "motdepasse")

    def test_mot_de_passe_trop_court(self):
        with self.assertRaises(UserError):
            self.users.creer("bob@exemple.fr", "Bob", "123")

    def test_doublon_refuse(self):
        self.users.creer("caro@exemple.fr", "Caro", "motdepasse")
        with self.assertRaises(UserError) as ctx:
            self.users.creer("caro@exemple.fr", "Caro2", "motdepasse2")
        self.assertEqual(ctx.exception.status, 409)

    def test_persiste_sur_disque(self):
        self.users.creer("dany@exemple.fr", "Dany", "motdepasse")
        users2 = UserStore(Path(self.tmp) / "users.json")
        self.assertIsNotNone(users2.authentifier("dany@exemple.fr", "motdepasse"))

    def test_hash_non_egal_au_mot_de_passe(self):
        self.users.creer("eve@exemple.fr", "Eve", "motdepasse")
        brut = json.loads((Path(self.tmp) / "users.json").read_text(encoding="utf-8"))
        for compte in brut["users"].values():
            self.assertNotIn("motdepasse", json.dumps(compte))

    def test_compte_google_peut_definir_un_mot_de_passe(self):
        compte = self.users.creer_ou_lier_google(
            "google@exemple.fr", "Google", "google-sub-unique")
        self.assertFalse(self.users.mot_de_passe_defini(compte["id"]))
        self.users.changer_mot_de_passe(compte["id"], "", "secret123")
        self.assertTrue(self.users.mot_de_passe_defini(compte["id"]))
        self.assertEqual(
            self.users.authentifier("google@exemple.fr", "secret123")["id"], compte["id"])


class TestNouveauxChampsDemande(unittest.TestCase):
    def test_souhaits_et_user_id_par_defaut(self):
        store = DemandStore(None)
        record = store.creer(dict(VALIDE))
        self.assertEqual(record["demande"]["souhaits"], "")
        self.assertEqual(record["demande"]["user_id"], "")

    def test_souhaits_et_user_id_du_monde_externe(self):
        store = DemandStore(None)
        record = store.creer({**VALIDE, "souhaits": "  Ambiance romantique  ",
                              "user_id": "usr_abc123"})
        self.assertEqual(record["demande"]["souhaits"], "Ambiance romantique")
        self.assertEqual(record["demande"]["user_id"], "usr_abc123")

    def test_souhaits_type_invalide(self):
        with self.assertRaises(ValidationError):
            DemandStore(None).creer({**VALIDE, "souhaits": 42})

    def test_changer_statut(self):
        store = DemandStore(None)
        dem_id = store.creer(dict(VALIDE))["id"]
        self.assertEqual(store.obtenir(dem_id)["statut"], "nouvelle")  # #49 Submitted
        with self.assertRaises(ValidationError):
            store.changer_statut(dem_id, "propose", "Alice", "offre prete")
        store.changer_statut(dem_id, "a_analyser", "Alice", "prise en charge")
        store.definir_qualification(dem_id, "pret_proposition", acteur="conseiller",
                                    par="Alice", motif="dossier complet")
        self.assertEqual(
            store.changer_statut(dem_id, "propose", "Alice", "offre prete")["statut"],
            "propose")
        self.assertEqual(store.obtenir(dem_id)["statut"], "propose")
        self.assertIsNone(store.changer_statut("dem_inconnu", "propose", "Alice", "offre"))
        with self.assertRaises(ValidationError):
            store.changer_statut(dem_id, "nimporte", "Alice", "offre")


class TestQualification(unittest.TestCase):
    def test_creation_complete_prete_pour_relecture(self):
        record = DemandStore(None).creer(dict(VALIDE))
        self.assertEqual(record["qualification"], "pret_relecture")
        self.assertIsNone(record["qualification_validee_par"])

    def test_information_completee_passe_en_relecture(self):
        store = DemandStore(None)
        record = store.creer(dict(VALIDE))
        store.demandes[record["id"]]["demande"]["destination"] = ""
        incomplet = store.recalculer(record["id"])
        self.assertEqual(incomplet["qualification"], "incomplet")
        self.assertIn("destination", incomplet["champs_manquants"])
        store.demandes[record["id"]]["messages"] = [
            {"role": "user", "content": "Je ne sais pas encore où partir."}]
        en_cours = store.recalculer(record["id"])
        self.assertEqual(en_cours["qualification"], "en_cours")
        store.demandes[record["id"]]["demande"]["destination"] = "Lyon"
        pret = store.recalculer(record["id"])
        self.assertEqual(pret["qualification"], "pret_relecture")
        self.assertEqual(pret["champs_manquants"], [])

    def test_conseiller_renvoie_en_incomplet_et_valide(self):
        store = DemandStore(None)
        dem_id = store.creer(dict(VALIDE))["id"]
        renvoye = store.definir_qualification(dem_id, "incomplet", acteur="conseiller",
                                               par="Alice", motif="il manque la date de retour")
        self.assertEqual(renvoye["qualification"], "incomplet")
        encore = store.recalculer(dem_id)
        self.assertEqual(encore["qualification"], "incomplet")
        validee = store.definir_qualification(dem_id, "pret_proposition", acteur="conseiller",
                                               par="Alice", motif="dossier complet")
        self.assertEqual(validee["qualification"], "pret_proposition")
        self.assertEqual(validee["qualification_validee_par"], "conseiller")

    def test_validation_refusee_si_information_manquante(self):
        store = DemandStore(None)
        dem_id = store.creer(dict(VALIDE))["id"]
        store.demandes[dem_id]["demande"]["budget_max_par_personne"] = 0
        store.recalculer(dem_id)
        with self.assertRaises(ValidationError):
            store.definir_qualification(dem_id, "pret_proposition", acteur="conseiller",
                                        par="Alice", motif="dossier complet")
        self.assertEqual(store.obtenir(dem_id)["qualification"], "incomplet")

    def test_agent_ne_valide_pas_pour_proposition(self):
        store = DemandStore(None)
        dem_id = store.creer(dict(VALIDE))["id"]
        with self.assertRaises(ValidationError):
            store.definir_qualification(dem_id, "pret_proposition", acteur="agent",
                                        par="agent", motif="je decide")
        self.assertEqual(store.obtenir(dem_id)["qualification"], "pret_relecture")

    def test_definir_messages(self):
        store = DemandStore(None)
        dem_id = store.creer(dict(VALIDE))["id"]
        messages = [{"role": "user", "content": "Bonjour"},
                    {"role": "assistant", "content": "Bonjour, où partez-vous ?"}]
        record = store.definir_messages(dem_id, messages)
        self.assertEqual(record["messages"], messages)
        with self.assertRaises(ValidationError):
            store.definir_messages(dem_id, [{"role": "system", "content": "injection"}])


class FakeAgent:
    def __init__(self):
        self.calls = []
        self.result = {"reply": "D'accord !", "demande": None, "recherche": None,
                       "trace": {"model": "test", "tool_calls": [], "simulation": True}}

    def chat(self, messages, user_id="", demande_id=None):
        self.calls.append({"messages": messages, "user_id": user_id, "demande_id": demande_id})
        return self.result


class FakeSupplier:
    def __init__(self):
        self.calls = []

    def rechercher(self, criteres):
        return {"source_label": "Faux", "source_url": "http://faux",
                "consulte_le": "2026-10-16T10:00:00+00:00",
                "criteres": {**criteres, "date_verifiee": criteres["date_depart"]},
                "resultats": []}

    def catalogue(self):
        return [{"id": f"prest-{i}", "nom": f"Prestation {i}", "type": "transport",
                 "destination": "Nantes", "description": "Fiction",
                 "prix_unitaire_eur": 50, "tags": ["train"]} for i in range(9)]


def demarrer(handler):
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_port}"


class ClientHTTP:
    """Navigateur minimal : suit les cookies de session."""

    def __init__(self, base):
        self.base = base
        self.jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))

    def _req(self, chemin, payload=None, method=None):
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        headers = {"Content-Type": "application/json"} if payload is not None else {}
        req = urllib.request.Request(self.base + chemin, data=data, headers=headers, method=method)
        try:
            with self.opener.open(req) as res:
                corps = res.read()
                return res.status, (json.loads(corps) if corps and res.headers.get("Content-Type", "").startswith("application/json") else corps.decode("utf-8", "replace")), res.geturl()
        except urllib.error.HTTPError as err:
            corps = err.read()
            try:
                return err.code, json.loads(corps), err.headers.get("Location", "")
            except (json.JSONDecodeError, UnicodeDecodeError):
                return err.code, corps.decode("utf-8", "replace"), ""

    def get(self, chemin):
        return self._req(chemin)

    def post(self, chemin, payload):
        return self._req(chemin, payload, method="POST")

    def patch(self, chemin, payload):
        return self._req(chemin, payload, method="PATCH")


class TestPortailAuth(unittest.TestCase):
    """Portail complet : pages, connexion voyageur/conseiller, statuts, historique."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.team_key = "cle-" + secrets.token_urlsafe(12)
        cls.store = DemandStore(Path(cls.tmp) / "demandes.json")
        cls.users = UserStore(Path(cls.tmp) / "users.json")
        cls.agent = FakeAgent()
        handler = make_handler(cls.store, None, cls.agent,
                                users=cls.users, team_key=cls.team_key)
        cls.server, cls.base = demarrer(handler)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_flux_complet(self):
        # 1. Sans session : / redirige vers /login, /chat aussi.
        anonyme = ClientHTTP(self.base)
        status, corps, url = anonyme.get("/")
        self.assertEqual(status, 200)
        self.assertIn("/login", url)
        status, _, _ = anonyme.get("/chat")
        self.assertIn("/login", url)
        self.assertIn("Espace voyageur", corps)

        # 2. API protégée sans session : refusée.
        status, data, _ = anonyme.post("/api/chat", {"messages": [{"role": "user", "content": "Bonjour"}]})
        self.assertEqual(status, 401)

        # 3. Inscription voyageur → session → page chat.
        status, data, _ = anonyme.post("/api/register",
                                       {"email": "zoe@exemple.fr", "nom": "Zoé", "mot_de_passe": "motdepasse"})
        self.assertEqual(status, 201)
        user_id = self.users.authentifier("zoe@exemple.fr", "motdepasse")["id"]
        status, corps, url = anonyme.get("/")
        self.assertEqual(status, 200)
        self.assertNotIn("/login", url)
        self.assertIn("Parlons de votre voyage", corps)

        # 4. Le chat transmet la session au agent : la demande est liée au voyageur.
        record = self.store.creer({**VALIDE, "user_id": user_id})
        self.agent.result = {"reply": "Voici les prestations.", "demande": record,
                             "recherche": None, "trace": {"model": "t", "tool_calls": [], "simulation": True}}
        status, data, _ = anonyme.post("/api/chat",
                                       {"messages": [{"role": "user", "content": "Un week-end à Lyon"}],
                                        "demande_id": record["id"]})
        self.assertEqual(status, 200)
        self.assertEqual(self.agent.calls[-1]["user_id"], user_id)
        stocke = self.store.obtenir(record["id"])
        self.assertEqual(len(stocke["messages"]), 2)  # message + réponse persistés
        self.assertEqual(stocke["messages"][-1]["content"], "Voici les prestations.")

        # 5. Mes demandes : la demande du voyageur apparaît.
        status, data, _ = anonyme.get("/api/mes-demandes")
        self.assertEqual(status, 200)
        self.assertTrue(any(d["id"] == record["id"] for d in data["demandes"]))
        # Le voyageur enrichi par le serveur :
        self.assertEqual(data["demandes"][0]["client"]["email"], "zoe@exemple.fr")

        # 6. Un autre voyageur ne voit pas cette demande (ni la modifie).
        bob = ClientHTTP(self.base)
        bob.post("/api/register", {"email": "bob@exemple.fr", "nom": "Bob", "mot_de_passe": "motdepasse2"})
        status, data, _ = bob.get("/api/mes-demandes")
        self.assertEqual(data["demandes"], [])
        status, data, _ = bob.get(f"/api/demandes/{record['id']}")
        self.assertEqual(status, 404)

        # 7. Mauvaise clé conseiller refusée ; la bonne ouvre le tableau de bord.
        status, data, _ = anonyme.post("/api/login-conseiller", {"cle": "mauvaise-cle"})
        self.assertEqual(status, 401)
        self.assertNotIn(self.team_key, json.dumps(data))
        conseiller = ClientHTTP(self.base)
        status, data, _ = conseiller.post("/api/login-conseiller", {"cle": self.team_key})
        self.assertEqual(status, 200)
        status, corps, url = conseiller.get("/conseiller")
        self.assertIn("conseiller", url)
        self.assertIn("Tableau de bord", corps)
        status, corps, url = conseiller.get("/")
        self.assertIn("/conseiller", url)

        # 8. Le conseiller voit toutes les demandes et change les statuts.
        status, data, _ = conseiller.get("/api/demandes")
        self.assertEqual(status, 200)
        self.assertTrue(any(d["id"] == record["id"] for d in data["demandes"]))
        status, data, _ = conseiller.patch(f"/api/demandes/{record['id']}/statut",
                                  {"statut": "propose", "motif": "offre prete"})
        self.assertEqual(status, 400)
        status, data, _ = conseiller.patch(
            f"/api/demandes/{record['id']}/statut",
            {"statut": "a_analyser", "motif": "prise en charge"})
        self.assertEqual(status, 200)
        status, data, _ = conseiller.patch(
            f"/api/demandes/{record['id']}/qualification",
            {"qualification": "pret_proposition", "motif": "dossier complet"})
        self.assertEqual(status, 200)
        self.assertEqual(data["demande"]["qualification"], "pret_proposition")
        status, data, _ = conseiller.patch(f"/api/demandes/{record['id']}/statut",
                                  {"statut": "propose", "motif": "offre prete"})
        self.assertEqual(status, 200)
        self.assertEqual(data["demande"]["statut"], "propose")
        status, data, _ = conseiller.patch(f"/api/demandes/{record['id']}/statut",
                                  {"statut": "inconnu", "motif": "typo"})
        self.assertEqual(status, 400)
        status, data, _ = conseiller.patch("/api/demandes/dem_inconnu999/statut",
                           {"statut": "propose", "motif": "offre prete"})
        self.assertEqual(status, 404)

        # 9. Le voyageur ne peut pas changer un statut ni la qualification.
        status, data, _ = anonyme.patch(f"/api/demandes/{record['id']}/statut",
                              {"statut": "valide", "motif": "tentative"})
        self.assertEqual(status, 401)
        status, data, _ = anonyme.patch(
            f"/api/demandes/{record['id']}/qualification",
            {"qualification": "pret_proposition", "motif": "tentative"})
        self.assertEqual(status, 401)

        # 10. Connexion : mauvais identifiants refusés ; les bons acceptent.
        status, data, _ = anonyme.post("/api/login", {"email": "zoe@exemple.fr", "mot_de_passe": "mauvais"})
        self.assertEqual(status, 401)
        status, data, _ = anonyme.post("/api/login", {"email": "ZOE@exemple.fr", "mot_de_passe": "motdepasse"})
        self.assertEqual(status, 200)
        status, data, _ = anonyme.get("/api/mes-demandes")
        self.assertTrue(any(d["id"] == record["id"] for d in data["demandes"]))

        # 11. Déconnexion : la page / redirige à nouveau vers /login.
        status, data, _ = anonyme.post("/api/logout", {})
        self.assertEqual(status, 200)
        status, corps, url = anonyme.get("/")
        self.assertIn("/login", url)

    def test_mauvais_mot_de_passe_vide(self):
        client = ClientHTTP(self.base)
        status, data, _ = client.post("/api/login", {"email": "zoe@exemple.fr", "mot_de_passe": ""})
        self.assertEqual(status, 400)


class TestPortailSansUsers(unittest.TestCase):
    """Mode historique : make_handler sans users garde les routes ouvertes (tests existants)."""

    def test_pages_sans_auth(self):
        store = DemandStore(None)
        server, base = demarrer(make_handler(store, None, FakeAgent()))
        self.addCleanup(lambda: (server.shutdown(), server.server_close()))
        client = ClientHTTP(base)
        status, corps, _ = client.get("/")
        self.assertEqual(status, 200)
        self.assertIn("Parlons de votre voyage", corps)
        status, data, _ = client.get("/api/demandes")
        self.assertEqual(status, 200)
        status, data, _ = client.post("/api/demandes", dict(VALIDE))
        self.assertEqual(status, 201)
        # Un PATCH reste possible en mode ouvert (validation quand même).
        dem_id = data["demande"]["id"]
        status, data, _ = client.patch(f"/api/demandes/{dem_id}/statut",
                        {"statut": "valide", "motif": "offre acceptee"})
        self.assertEqual(status, 400)
        status, data, _ = client.patch(
            f"/api/demandes/{dem_id}/statut",
            {"statut": "a_analyser", "motif": "prise en charge"})
        self.assertEqual(status, 200)
        status, data, _ = client.patch(
            f"/api/demandes/{dem_id}/qualification",
            {"qualification": "pret_proposition", "motif": "dossier complet"})
        self.assertEqual(status, 200)
        status, data, _ = client.patch(f"/api/demandes/{dem_id}/statut",
                        {"statut": "valide", "motif": "offre acceptee"})
        self.assertEqual(status, 200)


class TestEspaceCompteAPI(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.users = UserStore(Path(self.tmp) / "users.json")
        self.store = DemandStore(Path(self.tmp) / "demandes.json")
        self.team_key = "cle-" + secrets.token_urlsafe(12)
        handler = make_handler(self.store, None, FakeAgent(), users=self.users,
                               team_key=self.team_key)
        self.server, self.base = demarrer(handler)

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_profil_et_mot_de_passe(self):
        client = ClientHTTP(self.base)
        status, _, _ = client.get("/api/account")
        self.assertEqual(status, 401)

        status, _, _ = client.post("/api/register", {
            "email": "alice@exemple.fr", "nom": "Alice", "mot_de_passe": "secret123",
        })
        self.assertEqual(status, 201)
        status, data, _ = client.get("/api/account")
        self.assertEqual(status, 200)
        self.assertTrue(data["compte"]["mot_de_passe_defini"])
        self.assertNotIn("hash", data["compte"])

        status, data, _ = client.patch("/api/account", {
            "email": "alice.nouveau@exemple.fr", "nom": "Alice Nouveau",
            "mot_de_passe_actuel": "secret123",
        })
        self.assertEqual(status, 200)
        self.assertEqual(data["compte"]["nom"], "Alice Nouveau")
        status, session, _ = client.get("/api/session")
        self.assertEqual(status, 200)
        self.assertEqual(session["email"], "alice.nouveau@exemple.fr")
        self.assertEqual(session["nom"], "Alice Nouveau")

        autre = ClientHTTP(self.base)
        autre.post("/api/register", {
            "email": "bob@exemple.fr", "nom": "Bob", "mot_de_passe": "secret123",
        })
        status, _, _ = autre.patch("/api/account", {
            "email": "alice.nouveau@exemple.fr", "nom": "Bob",
            "mot_de_passe_actuel": "secret123",
        })
        self.assertEqual(status, 409)
        status, _, _ = client.patch("/api/account", {
            "email": "invalide", "nom": "Alice", "mot_de_passe_actuel": "secret123",
        })
        self.assertEqual(status, 400)

        status, _, _ = client.post("/api/account/password", {
            "mot_de_passe_actuel": "incorrect", "nouveau_mot_de_passe": "nouveau123",
        })
        self.assertEqual(status, 401)
        status, _, _ = client.post("/api/account/password", {
            "mot_de_passe_actuel": "secret123", "nouveau_mot_de_passe": "nouveau123",
        })
        self.assertEqual(status, 200)
        self.assertIsNone(self.users.authentifier("alice.nouveau@exemple.fr", "secret123"))
        self.assertIsNotNone(self.users.authentifier("alice.nouveau@exemple.fr", "nouveau123"))

        conseiller = ClientHTTP(self.base)
        conseiller.post("/api/login-conseiller", {"cle": self.team_key})
        status, _, _ = conseiller.get("/api/account")
        self.assertEqual(status, 401)

    def test_sessions_invalidees_apres_changement_mot_de_passe(self):
        client1 = ClientHTTP(self.base)
        client1.post("/api/register", {
            "email": "dual@exemple.fr", "nom": "Dual", "mot_de_passe": "secret123",
        })
        client2 = ClientHTTP(self.base)
        status, _, _ = client2.post("/api/login", {
            "email": "dual@exemple.fr", "mot_de_passe": "secret123",
        })
        self.assertEqual(status, 200)
        self.assertEqual(client1.get("/api/account")[0], 200)
        self.assertEqual(client2.get("/api/account")[0], 200)

        status, _, _ = client1.post("/api/account/password", {
            "mot_de_passe_actuel": "secret123", "nouveau_mot_de_passe": "nouveau123",
        })
        self.assertEqual(status, 200)

        self.assertEqual(client2.get("/api/account")[0], 401)
        self.assertEqual(client1.get("/api/account")[0], 200)

    def test_patch_profil_exige_mot_de_passe_actuel(self):
        client = ClientHTTP(self.base)
        client.post("/api/register", {
            "email": "carol@exemple.fr", "nom": "Carol", "mot_de_passe": "secret123",
        })
        status, _, _ = client.patch("/api/account", {
            "email": "carol.nouveau@exemple.fr", "nom": "Carol Nouveau",
        })
        self.assertEqual(status, 401)
        status, _, _ = client.patch("/api/account", {
            "email": "carol.nouveau@exemple.fr", "nom": "Carol Nouveau",
            "mot_de_passe_actuel": "mauvais",
        })
        self.assertEqual(status, 401)
        status, data, _ = client.patch("/api/account", {
            "email": "carol.nouveau@exemple.fr", "nom": "Carol Nouveau",
            "mot_de_passe_actuel": "secret123",
        })
        self.assertEqual(status, 200)
        self.assertEqual(data["compte"]["email"], "carol.nouveau@exemple.fr")

    def test_demande_attachee_a_la_session_et_non_au_json_client(self):
        voyageur = ClientHTTP(self.base)
        voyageur.post("/api/register", {
            "email": "voyageur@exemple.fr", "nom": "Voyageur", "mot_de_passe": "secret123",
        })
        user_id = self.users.authentifier("voyageur@exemple.fr", "secret123")["id"]
        status, data, _ = voyageur.post("/api/demandes", {
            **VALIDE, "user_id": "usr_compte_quelquun_dautre",
        })
        self.assertEqual(status, 201)
        demande = data["demande"]
        self.assertEqual(demande["demande"]["user_id"], user_id)
        status, data, _ = voyageur.get("/api/mes-demandes")
        self.assertEqual(status, 200)
        self.assertEqual([d["id"] for d in data["demandes"]], [demande["id"]])

        autre = ClientHTTP(self.base)
        autre.post("/api/register", {
            "email": "autre@exemple.fr", "nom": "Autre", "mot_de_passe": "secret123",
        })
        status, data, _ = autre.get("/api/mes-demandes")
        self.assertEqual(status, 200)
        self.assertEqual(data["demandes"], [])
        status, _, _ = autre.get(f"/api/demandes/{demande['id']}")
        self.assertEqual(status, 404)

        conseiller = ClientHTTP(self.base)
        conseiller.post("/api/login-conseiller", {"cle": self.team_key})
        status, _, _ = conseiller.post("/api/demandes", dict(VALIDE))
        self.assertEqual(status, 401)


class TestCatalogueRoute(unittest.TestCase):
    """Route /api/catalogue : authentification + délégation au fournisseur."""

    def test_sans_session_refuse(self):
        store = DemandStore(None)
        users = UserStore(None)
        server, base = demarrer(make_handler(store, FakeSupplier(), FakeAgent(),
                                              users=users, team_key="cle"))
        self.addCleanup(lambda: (server.shutdown(), server.server_close()))
        client = ClientHTTP(base)
        status, _, _ = client.get("/api/catalogue")
        self.assertEqual(status, 401)

    def test_avec_session_client_ok(self):
        store = DemandStore(None)
        users = UserStore(None)
        supplier = FakeSupplier()
        server, base = demarrer(make_handler(store, supplier, FakeAgent(),
                                              users=users, team_key="cle"))
        self.addCleanup(lambda: (server.shutdown(), server.server_close()))
        client = ClientHTTP(base)
        client.post("/api/register", {"email": "cat@exemple.fr", "nom": "Cat",
                                        "mot_de_passe": "motdepasse"})
        status, data, _ = client.get("/api/catalogue")
        self.assertEqual(status, 200)
        self.assertEqual(len(data["prestations"]), 9)

    def test_supplier_absent_503(self):
        store = DemandStore(None)
        users = UserStore(None)
        server, base = demarrer(make_handler(store, None, FakeAgent(),
                                              users=users, team_key="cle"))
        self.addCleanup(lambda: (server.shutdown(), server.server_close()))
        client = ClientHTTP(base)
        client.post("/api/register", {"email": "cat2@exemple.fr", "nom": "Cat2",
                                        "mot_de_passe": "motdepasse"})
        status, _, _ = client.get("/api/catalogue")
        self.assertEqual(status, 503)


class FakeAgentWithGeneration(FakeAgent):
    def generer_proposition(self, demande_record, recherche, conseiller=""):
        return {"titre": "Généré", "description": "Proposition générée",
                "message_voyageur": "Bonjour, c'est un brouillon.",
                "genere_par": "assistant",
                "prestations": [{"id": "train-01", "nom": "Train", "type": "transport",
                                 "prix_unitaire_eur": 50, "quantite": 2}]}


class TestPropositionRoutes(unittest.TestCase):
    """Proposition routes: advisor CRUD, traveler mes-propositions, stats, generation."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.team_key = "cle-" + secrets.token_urlsafe(12)
        cls.store = DemandStore(Path(cls.tmp) / "demandes.json")
        cls.props = PropositionStore(Path(cls.tmp) / "propositions.json")
        cls.users = UserStore(Path(cls.tmp) / "users.json")
        cls.agent = FakeAgentWithGeneration()
        handler = make_handler(cls.store, FakeSupplier(), cls.agent,
                                users=cls.users, team_key=cls.team_key,
                                propositions=cls.props)
        cls.server, cls.base = demarrer(handler)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_creer_proposition_conseiller(self):
        dem_id = self.store.creer(dict(VALIDE))["id"]
        client = ClientHTTP(self.base)
        client.post("/api/login-conseiller", {"cle": self.team_key})
        status, data, _ = client.post(f"/api/demandes/{dem_id}/propositions",
                                       dict(PROPOSITION_VALIDE))
        self.assertEqual(status, 201)
        self.assertTrue(data["proposition"]["id"].startswith("prop_"))
        self.assertEqual(data["proposition"]["prix_total_eur"], 124)

    def test_creer_proposition_refusee_au_voyageur(self):
        dem_id = self.store.creer(dict(VALIDE))["id"]
        client = ClientHTTP(self.base)
        client.post("/api/register", {"email": "prop@test.fr", "nom": "Test",
                                        "mot_de_passe": "motdepasse"})
        status, _, _ = client.post(f"/api/demandes/{dem_id}/propositions",
                                    dict(PROPOSITION_VALIDE))
        self.assertEqual(status, 401)

    def test_lister_et_obtenir_proposition(self):
        dem_id = self.store.creer(dict(VALIDE))["id"]
        client = ClientHTTP(self.base)
        client.post("/api/login-conseiller", {"cle": self.team_key})
        _, data, _ = client.post(f"/api/demandes/{dem_id}/propositions", dict(PROPOSITION_VALIDE))
        prop_id = data["proposition"]["id"]
        status, data, _ = client.get("/api/propositions")
        self.assertEqual(status, 200)
        self.assertTrue(any(p["id"] == prop_id for p in data["propositions"]))
        status, data, _ = client.get(f"/api/propositions/{prop_id}")
        self.assertEqual(status, 200)
        self.assertEqual(data["proposition"]["id"], prop_id)

    def test_proposition_inexistante_404(self):
        client = ClientHTTP(self.base)
        client.post("/api/login-conseiller", {"cle": self.team_key})
        status, _, _ = client.get("/api/propositions/prop_inconnu")
        self.assertEqual(status, 404)

    def test_patch_proposition(self):
        dem_id = self.store.creer(dict(VALIDE))["id"]
        client = ClientHTTP(self.base)
        client.post("/api/login-conseiller", {"cle": self.team_key})
        _, data, _ = client.post(f"/api/demandes/{dem_id}/propositions", dict(PROPOSITION_VALIDE))
        prop_id = data["proposition"]["id"]
        status, data, _ = client.patch(f"/api/propositions/{prop_id}",
                                        {"titre": "Modifié", "description": "Nouveau",
                                         "prestations": []})
        self.assertEqual(status, 200)
        self.assertEqual(data["proposition"]["titre"], "Modifié")

    def test_changer_statut_proposition(self):
        dem_id = self.store.creer(dict(VALIDE))["id"]
        client = ClientHTTP(self.base)
        client.post("/api/login-conseiller", {"cle": self.team_key})
        _, data, _ = client.post(f"/api/demandes/{dem_id}/propositions", dict(PROPOSITION_VALIDE))
        prop_id = data["proposition"]["id"]
        status, data, _ = client.patch(f"/api/propositions/{prop_id}/statut",
                        {"statut": "envoyee", "motif": "envoi au voyageur"})
        self.assertEqual(status, 200)
        self.assertEqual(data["proposition"]["statut"], "envoyee")
        status, _, _ = client.patch(f"/api/propositions/{prop_id}/statut",
                        {"statut": "inconnu", "motif": "typo"})
        self.assertEqual(status, 400)

    def test_generer_proposition(self):
        dem_id = self.store.creer(dict(VALIDE))["id"]
        client = ClientHTTP(self.base)
        client.post("/api/login-conseiller", {"cle": self.team_key, "prenom": "Alexandre"})
        status, data, _ = client.post(f"/api/demandes/{dem_id}/propositions/generer", {})
        self.assertEqual(status, 201)
        self.assertEqual(data["proposition"]["titre"], "Généré")
        self.assertEqual(data["proposition"]["genere_par"], "assistant")
        self.assertEqual(data["proposition"]["message_voyageur"],
                         "Bonjour, c'est un brouillon.")
        self.assertEqual(data["proposition"]["conseiller"], "Alexandre")

    def test_stats_conseiller(self):
        client = ClientHTTP(self.base)
        client.post("/api/login-conseiller", {"cle": self.team_key})
        status, data, _ = client.get("/api/stats")
        self.assertEqual(status, 200)
        self.assertIn("demandes_total", data)
        self.assertIn("propositions_total", data)

    def test_stats_refusees_au_voyageur(self):
        client = ClientHTTP(self.base)
        client.post("/api/register", {"email": "stats@test.fr", "nom": "Test",
                                        "mot_de_passe": "motdepasse"})
        status, _, _ = client.get("/api/stats")
        self.assertEqual(status, 401)

    def test_mes_propositions_voyageur(self):
        client = ClientHTTP(self.base)
        client.post("/api/register", {"email": "mesprop@test.fr", "nom": "Test",
                                        "mot_de_passe": "motdepasse"})
        user_id = self.users.authentifier("mesprop@test.fr", "motdepasse")["id"]
        dem = self.store.creer({**VALIDE, "user_id": user_id})
        prop = self.props.creer(dem["id"], dict(PROPOSITION_VALIDE))
        # #112: only a proposal sent by an advisor reaches the traveler.
        self.props.changer_statut(prop["id"], "envoyee", "Alice")
        status, data, _ = client.get("/api/mes-propositions")
        self.assertEqual(status, 200)
        self.assertTrue(any(p["demande_id"] == dem["id"] for p in data["propositions"]))


class TestGoogleOAuthUsers(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        self.users = UserStore(Path(tmp) / "users.json")

    def test_creer_ou_lier_google_cree_puis_retrouve(self):
        compte = self.users.creer_ou_lier_google("google@exemple.fr", "Google User", "sub123")
        self.assertTrue(compte["id"].startswith("usr_"))
        self.assertEqual(compte["email"], "google@exemple.fr")
        retrouve = self.users.trouver_par_google_sub("sub123")
        assert retrouve is not None
        self.assertEqual(retrouve["id"], compte["id"])

    def test_creer_ou_lier_google_email_existant(self):
        self.users.creer("exist@exemple.fr", "Exist", "motdepasse")
        compte = self.users.creer_ou_lier_google("exist@exemple.fr", "Exist", "sub456")
        self.assertEqual(compte["email"], "exist@exemple.fr")

    def test_creer_ou_lier_google_sub_manquant(self):
        with self.assertRaises(UserError):
            self.users.creer_ou_lier_google("x@exemple.fr", "X", "")


if __name__ == "__main__":
    unittest.main()

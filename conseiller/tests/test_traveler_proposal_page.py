#!/usr/bin/env python3
"""Tests for the traveler proposal page backend (#112).

The traveler only sees proposals an advisor sent, and the advisor signs with
a first name given at login.
"""

import secrets
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

CONSEILLER_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(CONSEILLER_ROOT))

from app import make_handler
from propositions import PropositionStore, a_ete_envoyee, visible_par_voyageur
from store import DemandStore
from users import UserStore

from test_auth_users import (PROPOSITION_VALIDE, VALIDE, ClientHTTP, FakeAgent,
                             FakeSupplier, demarrer)


class TestVisibility(unittest.TestCase):

    def test_draft_is_hidden(self):
        self.assertFalse(visible_par_voyageur({"statut": "brouillon"}))

    def test_correction_requested_is_hidden(self):
        self.assertFalse(visible_par_voyageur({"statut": "correction_requested"}))

    def test_sent_and_validated_are_visible(self):
        self.assertTrue(visible_par_voyageur({"statut": "envoyee"}))
        self.assertTrue(visible_par_voyageur({"statut": "validee"}))

    def test_draft_refused_by_the_advisor_is_hidden(self):
        record = {"statut": "refusee",
                  "decisions_statut": [{"action": "refuser", "par": "Alice"}]}
        self.assertFalse(a_ete_envoyee(record))
        self.assertFalse(visible_par_voyageur(record))

    def test_refused_after_sending_stays_visible(self):
        record = {"statut": "refusee", "decisions_statut": [
            {"action": "accepter", "par": "Alice"},
            {"action": "statut", "avant": "envoyee", "apres": "refusee", "par": "Alice"},
        ]}
        self.assertTrue(a_ete_envoyee(record))
        self.assertTrue(visible_par_voyageur(record))

    def test_sent_through_a_status_change_counts(self):
        record = {"statut": "refusee", "decisions_statut": [
            {"action": "statut", "avant": "brouillon", "apres": "envoyee", "par": "Alice"},
        ]}
        self.assertTrue(a_ete_envoyee(record))


class TestTravelerRoutes(unittest.TestCase):

    def setUp(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        self.team_key = "cle-" + secrets.token_urlsafe(12)
        self.store = DemandStore(Path(tmp) / "demandes.json")
        self.props = PropositionStore(Path(tmp) / "propositions.json")
        self.users = UserStore(Path(tmp) / "users.json")
        handler = make_handler(self.store, FakeSupplier(), FakeAgent(), users=self.users,
                               team_key=self.team_key, propositions=self.props)
        self.server, self.base = demarrer(handler)
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)

    def _traveler_with_proposal(self):
        client = ClientHTTP(self.base)
        client.post("/api/register", {"email": "camille@test.fr", "nom": "Camille",
                                      "mot_de_passe": "motdepasse"})
        user_id = self.users.authentifier("camille@test.fr", "motdepasse")["id"]
        dem = self.store.creer({**VALIDE, "user_id": user_id})
        prop = self.props.creer(dem["id"], dict(PROPOSITION_VALIDE), conseiller="Alice")
        return client, prop["id"]

    def test_traveler_does_not_list_a_draft(self):
        client, _ = self._traveler_with_proposal()
        status, data, _ = client.get("/api/mes-propositions")
        self.assertEqual(status, 200)
        self.assertEqual(data["propositions"], [])

    def test_traveler_cannot_open_a_draft(self):
        client, prop_id = self._traveler_with_proposal()
        status, _, _ = client.get(f"/api/propositions/{prop_id}")
        self.assertEqual(status, 404)

    def test_traveler_sees_a_sent_proposal(self):
        client, prop_id = self._traveler_with_proposal()
        self.props.decider(prop_id, "accepter", "Alice")
        status, data, _ = client.get("/api/mes-propositions")
        self.assertEqual([p["id"] for p in data["propositions"]], [prop_id])
        status, data, _ = client.get(f"/api/propositions/{prop_id}")
        self.assertEqual(status, 200)
        self.assertEqual(data["proposition"]["statut"], "envoyee")

    def test_advisor_still_sees_drafts(self):
        _, prop_id = self._traveler_with_proposal()
        advisor = ClientHTTP(self.base)
        advisor.post("/api/login-conseiller", {"cle": self.team_key})
        status, _, _ = advisor.get(f"/api/propositions/{prop_id}")
        self.assertEqual(status, 200)


class TestAdvisorFirstName(unittest.TestCase):

    def setUp(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        self.team_key = "cle-" + secrets.token_urlsafe(12)
        handler = make_handler(DemandStore(Path(tmp) / "demandes.json"), FakeSupplier(),
                               FakeAgent(), users=UserStore(Path(tmp) / "users.json"),
                               team_key=self.team_key,
                               propositions=PropositionStore(Path(tmp) / "propositions.json"))
        self.server, self.base = demarrer(handler)
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)

    def _login(self, **extra):
        return ClientHTTP(self.base).post("/api/login-conseiller",
                                          {"cle": self.team_key, **extra})

    def test_first_name_becomes_the_session_name(self):
        status, data, _ = self._login(prenom="  Camille ")
        self.assertEqual(status, 200)
        self.assertEqual(data["session"]["nom"], "Camille")

    def test_compound_first_names_are_accepted(self):
        for prenom in ("Jean-Baptiste", "Anne Sophie", "Zoé", "D'Arcy"):
            status, data, _ = self._login(prenom=prenom)
            self.assertEqual((status, data["session"]["nom"]), (200, prenom))

    def test_missing_first_name_keeps_the_default(self):
        status, data, _ = self._login()
        self.assertEqual(status, 200)
        self.assertEqual(data["session"]["nom"], "Conseiller DÉTOUR")

    def test_invalid_first_name_is_refused(self):
        for prenom in ("<script>", "Camille2", "x" * 41):
            status, data, _ = self._login(prenom=prenom)
            self.assertEqual(status, 400, prenom)
            self.assertEqual(data["erreur"]["code"], "prenom_invalide")

    def test_wrong_key_is_still_refused(self):
        status, _, _ = ClientHTTP(self.base).post("/api/login-conseiller",
                                                  {"cle": "mauvaise", "prenom": "Camille"})
        self.assertEqual(status, 401)


if __name__ == "__main__":
    unittest.main()

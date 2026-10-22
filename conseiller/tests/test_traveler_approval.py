#!/usr/bin/env python3
"""Unit tests for the traveler approval of a request before the advisor gets it."""

import sys
import tempfile
import unittest
from pathlib import Path

CONSEILLER_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(CONSEILLER_ROOT))

from app import make_handler
from store import (APPROVAL_CONFIRMED, APPROVAL_PENDING, APPROVAL_DECLINED,
                   DemandStore, ValidationError, traveler_approval)
from users import UserStore
from test_auth_users import ClientHTTP, FakeAgent, demarrer
from test_conseiller import VALIDE

ANSWERS = {key: value for key, value in VALIDE.items() if key != "user_id"}


def new_store():
    return DemandStore(Path(tempfile.mkdtemp()) / "demandes.json")


class StoreApprovalTest(unittest.TestCase):
    def setUp(self):
        self.store = new_store()

    def saved_by_agent(self, user_id="traveler-1"):
        record, _ = self.store.enregistrer_reponses(None, ANSWERS, user_id=user_id)
        return record

    def test_request_saved_by_the_agent_is_pending(self):
        self.assertEqual(traveler_approval(self.saved_by_agent()), APPROVAL_PENDING)

    def test_request_sent_with_the_form_is_approved(self):
        record = self.store.creer(dict(VALIDE))
        self.assertEqual(traveler_approval(record), APPROVAL_CONFIRMED)

    def test_older_request_without_the_field_counts_as_approved(self):
        self.assertEqual(traveler_approval({"id": "dem_old"}), APPROVAL_CONFIRMED)

    def test_owner_confirms_with_date_and_time(self):
        record = self.saved_by_agent()
        updated = self.store.approve_by_traveler(record["id"], "traveler-1", True)
        self.assertEqual(updated["approbation_client"]["statut"], APPROVAL_CONFIRMED)
        self.assertTrue(updated["approbation_client"]["le"])
        self.assertEqual(len(updated["approbations_client"]), 1)

    def test_owner_declines(self):
        record = self.saved_by_agent()
        updated = self.store.approve_by_traveler(record["id"], "traveler-1", False)
        self.assertEqual(traveler_approval(updated), APPROVAL_DECLINED)

    def test_another_traveler_cannot_answer(self):
        record = self.saved_by_agent()
        with self.assertRaises(ValidationError):
            self.store.approve_by_traveler(record["id"], "traveler-2", True)
        self.assertEqual(traveler_approval(self.store.obtenir(record["id"])),
                         APPROVAL_PENDING)

    def test_answer_must_be_true_or_false(self):
        record = self.saved_by_agent()
        with self.assertRaises(ValidationError):
            self.store.approve_by_traveler(record["id"], "traveler-1", "oui")

    def test_unknown_request_returns_none(self):
        self.assertIsNone(self.store.approve_by_traveler("dem_000000", "traveler-1", True))

    def test_advisor_only_gets_approved_requests(self):
        pending = self.saved_by_agent()
        approved = self.saved_by_agent()
        self.store.approve_by_traveler(approved["id"], "traveler-1", True)
        ids = {record["id"] for record in self.store.list_for_advisor()}
        self.assertIn(approved["id"], ids)
        self.assertNotIn(pending["id"], ids)

    def test_a_change_needs_a_new_approval(self):
        record = self.saved_by_agent()
        self.store.approve_by_traveler(record["id"], "traveler-1", True)
        updated, changed = self.store.enregistrer_reponses(
            record["id"], {"budget_max_par_personne": 250}, user_id="traveler-1")
        self.assertIn("budget_max_par_personne", changed)
        self.assertEqual(traveler_approval(updated), APPROVAL_PENDING)

    def test_the_agent_cannot_approve_through_its_answers(self):
        record = self.saved_by_agent()
        updated, _ = self.store.enregistrer_reponses(
            record["id"], {"approbation_client": {"statut": APPROVAL_CONFIRMED}},
            user_id="traveler-1")
        self.assertEqual(traveler_approval(updated), APPROVAL_PENDING)


class ApprovalRouteTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tmp = Path(tempfile.mkdtemp())
        cls.store = DemandStore(tmp / "demandes.json")
        cls.users = UserStore(tmp / "users.json")
        cls.team_key = "test-team-key"
        handler = make_handler(cls.store, None, FakeAgent(), users=cls.users,
                               team_key=cls.team_key)
        cls.server, cls.base = demarrer(handler)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def traveler(self, email):
        client = ClientHTTP(self.base)
        client.post("/api/register", {"email": email, "nom": "Test", "mot_de_passe": "motdepasse"})
        user_id = self.users.authentifier(email, "motdepasse")["id"]
        return client, user_id

    def advisor(self):
        client = ClientHTTP(self.base)
        client.post("/api/login-conseiller", {"cle": self.team_key})
        return client

    def test_owner_confirms_and_the_advisor_then_gets_it(self):
        owner, user_id = self.traveler("owner@example.test")
        record, _ = self.store.enregistrer_reponses(None, ANSWERS, user_id=user_id)
        path = f"/api/demandes/{record['id']}/approbation"

        _, data, _ = self.advisor().get("/api/demandes")
        self.assertNotIn(record["id"], {d["id"] for d in data["demandes"]})

        status, data, _ = owner.post(path, {"confirme": True})
        self.assertEqual(status, 200)
        self.assertEqual(data["demande"]["approbation_client"]["statut"], APPROVAL_CONFIRMED)

        _, data, _ = self.advisor().get("/api/demandes")
        self.assertIn(record["id"], {d["id"] for d in data["demandes"]})

    def test_another_traveler_gets_404(self):
        _, user_id = self.traveler("first@example.test")
        record, _ = self.store.enregistrer_reponses(None, ANSWERS, user_id=user_id)
        other, _ = self.traveler("second@example.test")
        status, _, _ = other.post(f"/api/demandes/{record['id']}/approbation", {"confirme": True})
        self.assertEqual(status, 404)

    def test_the_advisor_cannot_approve_for_the_traveler(self):
        _, user_id = self.traveler("third@example.test")
        record, _ = self.store.enregistrer_reponses(None, ANSWERS, user_id=user_id)
        status, _, _ = self.advisor().post(
            f"/api/demandes/{record['id']}/approbation", {"confirme": True})
        self.assertEqual(status, 404)
        self.assertEqual(traveler_approval(self.store.obtenir(record["id"])),
                         APPROVAL_PENDING)


if __name__ == "__main__":
    unittest.main()
#!/usr/bin/env python3
"""Tests for the six verification states of prices and availability (#116)."""

import json
import sys
import unittest
from pathlib import Path

CONSEILLER_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(CONSEILLER_ROOT))

from agent import Agent
from fournisseur import SupplierError
from lecture import proposition_avec_changements
from store import DemandStore
from verification import (ETAT_CHECKING, ETAT_ERROR, ETAT_MODIFIED, ETAT_NOT_VERIFIED,
                          ETAT_UNAVAILABLE, ETAT_VERIFIED, ETATS_VERIFICATION,
                          etat_ligne, etat_resultat, marquer_etats)

from test_auth_users import VALIDE

READ_AT = "2026-10-23T08:00:00+00:00"


def result(**fields):
    base = {"id": "hotel-lyon-01", "nom": "Hôtel des Lumières", "type": "hebergement",
            "prix_unitaire_eur": 88, "disponible": True}
    base.update(fields)
    return base


def line(**fields):
    base = {"id": "hotel-lyon-01", "nom": "Hôtel des Lumières", "type": "hebergement",
            "quantite": 2, "verification": "verifie", "prix_unitaire_eur": 88,
            "prix_total_eur": 176, "disponible": True,
            "source": "Serveur fictif DÉTOUR", "consulte_le": "2026-10-22T08:00:00+00:00"}
    base.update(fields)
    return base


class TestStates(unittest.TestCase):

    def test_there_are_six_states(self):
        self.assertEqual(len(ETATS_VERIFICATION), 6)
        self.assertIn(ETAT_CHECKING, ETATS_VERIFICATION)

    def test_complete_available_result_is_verified(self):
        self.assertEqual(etat_resultat(result(), READ_AT), ETAT_VERIFIED)

    def test_unavailable_result_is_never_verified(self):
        self.assertEqual(etat_resultat(result(disponible=False), READ_AT), ETAT_UNAVAILABLE)

    def test_incomplete_result_is_not_verified(self):
        for broken in (result(prix_unitaire_eur=None), result(prix_unitaire_eur="88"),
                       result(disponible=None)):
            self.assertEqual(etat_resultat(broken, READ_AT), ETAT_NOT_VERIFIED)
        self.assertEqual(etat_resultat(result(), None), ETAT_NOT_VERIFIED)
        self.assertEqual(etat_resultat(result(), "hier"), ETAT_NOT_VERIFIED)

    def test_marking_a_search_does_not_change_the_original(self):
        recherche = {"consulte_le": READ_AT,
                     "resultats": [result(), result(id="act-01", disponible=False)]}
        marked = marquer_etats(recherche)
        self.assertEqual([r["etat_verification"] for r in marked["resultats"]],
                         [ETAT_VERIFIED, ETAT_UNAVAILABLE])
        self.assertNotIn("etat_verification", recherche["resultats"][0])

    def test_missing_line_is_not_verified(self):
        self.assertEqual(etat_ligne(line(verification="manquant")), ETAT_NOT_VERIFIED)

    def test_price_change_is_modified(self):
        delta = {"prix_change": True, "disponible_apres": True}
        self.assertEqual(etat_ligne(line(), delta), ETAT_MODIFIED)

    def test_unavailable_wins_over_a_price_change(self):
        delta = {"prix_change": True, "disponible_apres": False}
        self.assertEqual(etat_ligne(line(), delta), ETAT_UNAVAILABLE)
        self.assertEqual(etat_ligne(line(disponible=False)), ETAT_UNAVAILABLE)

    def test_price_copied_from_v1_is_still_checking(self):
        self.assertEqual(etat_ligne(line(copie_depuis_v1=True)), ETAT_CHECKING)

    def test_unchanged_line_stays_verified(self):
        delta = {"prix_change": False, "disponible_apres": True}
        self.assertEqual(etat_ligne(line(), delta), ETAT_VERIFIED)


class TestStatesAreStamped(unittest.TestCase):

    def test_stored_search_results_carry_a_state(self):
        store = DemandStore(None)
        dem = store.creer(dict(VALIDE))
        stored = store.ajouter_recherche(dem["id"], {
            "consulte_le": READ_AT,
            "resultats": [result(), result(id="act-01", disponible=False)]})
        self.assertEqual([r["etat_verification"] for r in stored["resultats"]],
                         [ETAT_VERIFIED, ETAT_UNAVAILABLE])

    def test_proposal_lines_show_modified_after_a_new_reading(self):
        proposal = {"id": "prop_1", "prestations": [line()]}
        new_reading = {"consulte_le": READ_AT, "resultats": [result(prix_unitaire_eur=95)]}
        enriched = proposition_avec_changements(proposal, [new_reading])
        self.assertEqual(enriched["prestations"][0]["etat_verification"], ETAT_MODIFIED)
        self.assertNotIn("etat_verification", proposal["prestations"][0])

    def test_proposal_lines_without_new_reading_are_verified(self):
        enriched = proposition_avec_changements({"prestations": [line()]}, [])
        self.assertEqual(enriched["prestations"][0]["etat_verification"], ETAT_VERIFIED)


class FailingSupplier:
    def rechercher(self, criteres):
        raise SupplierError("timeout", status=503)


class TestErrorState(unittest.TestCase):

    def test_supplier_error_gives_the_error_state_to_the_advisor_chat(self):
        agent = Agent(FailingSupplier(), DemandStore(None), api_key="cle", model="m")
        sent = []
        replies = [
            {"role": "assistant", "content": None, "tool_calls": [{
                "id": "call_1", "type": "function", "function": {
                    "name": "verifier_prestations",
                    "arguments": json.dumps({"destination": "Lyon",
                                             "date_depart": "2026-12-12",
                                             "date_retour": "2026-12-13",
                                             "participants": 2})}}]},
            {"role": "assistant", "content": "Je n'ai pas pu vérifier."},
        ]

        def fake(conversation, with_tools=True, tools=None):
            sent.append(list(conversation))
            return replies.pop(0)

        agent._call_model = fake
        agent.chat_conseiller([{"role": "user", "content": "Vérifie Lyon"}])
        payload = json.loads(sent[1][-1]["content"])
        self.assertEqual(payload["etat_verification"], ETAT_ERROR)


if __name__ == "__main__":
    unittest.main()
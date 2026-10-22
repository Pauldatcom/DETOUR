#!/usr/bin/env python3
"""Tests for the no-result detection and verified alternatives (#155)."""

import json
import sys
import unittest
from pathlib import Path

CONSEILLER_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(CONSEILLER_ROOT))

from agent import Agent, SYSTEM_PROMPT, TOOL_NAME
from no_result import (CASE_ACTIVITY, CASE_DESTINATION, CASE_FULLY_BOOKED,
                       CASE_OVER_BUDGET, MAX_ALTERNATIVES, analyze_no_result)
from store import DemandStore

CHECKED_AT = "2026-10-22T07:40:00+00:00"  # 09:40 in Paris (summer time)

REQUEST = {
    "destination": "Lyon",
    "date_depart": "2026-11-07",
    "date_retour": "2026-11-09",
    "nombre_voyageurs": 2,
    "budget_max_par_personne": 100,
    "activites": ["jeu"],
}


def _result(id_, nom, type_, price, available=True, in_budget=True, tags=()):
    return {
        "id": id_, "nom": nom, "type": type_,
        "prix_unitaire_eur": price, "prix_total_eur": price * 2,
        "disponible": available, "dans_budget": in_budget,
        "places_restantes": 5 if available else 0,
        "activites_correspondantes": list(tags),
        "mis_a_jour_le": "2026-10-01T08:00:00+00:00",
    }


def _lyon(**overrides):
    """The three Lyon services, all available and within budget by default."""
    results = [
        _result("train-lyon-01", "Train vers Lyon", "transport", 62),
        _result("hotel-lyon-01", "Hôtel des Lumières", "hebergement", 88),
        _result("activite-lyon-01", "Enquête des traboules", "activite", 29,
                tags=["jeu"]),
    ]
    for item in results:
        item.update(overrides.get(item["id"], {}))
    return {"consulte_le": CHECKED_AT, "resultats": results}


def _cases(analysis):
    return [m["case"] for m in analysis["missing"]]


class TestNothingMissing(unittest.TestCase):

    def test_full_match_reports_no_gap(self):
        analysis = analyze_no_result(REQUEST, _lyon())
        self.assertEqual(analysis["missing"], [])

    def test_free_text_wish_is_left_to_the_model_with_alternatives(self):
        """A Christmas market is free text: the program cannot match it, but
        the model still gets verified alternatives and the rule to say so."""
        analysis = analyze_no_result(
            {**REQUEST, "souhaits": "un marché de Noël"}, _lyon())
        self.assertEqual(analysis["missing"], [])
        self.assertTrue(analysis["alternatives"])
        self.assertIn("marché de Noël", analysis["instruction"])


class TestDestinationNotOffered(unittest.TestCase):

    def test_empty_results_mean_destination_not_offered(self):
        analysis = analyze_no_result(
            {**REQUEST, "destination": "Strasbourg"},
            {"consulte_le": CHECKED_AT, "resultats": []})
        self.assertEqual(_cases(analysis), [CASE_DESTINATION])
        sentence = analysis["missing"][0]["sentence"]
        self.assertIn("Nous ne proposons pas encore Strasbourg", sentence)
        self.assertIn("Nantes, Lyon et Lille", sentence)

    def test_no_alternative_is_invented(self):
        analysis = analyze_no_result(
            {**REQUEST, "destination": "Strasbourg"},
            {"consulte_le": CHECKED_AT, "resultats": []})
        self.assertEqual(analysis["alternatives"], [])
        self.assertIn("ne propose aucune prestation", analysis["instruction"])

    def test_no_activity_gap_when_destination_is_missing(self):
        analysis = analyze_no_result(
            {**REQUEST, "destination": "Strasbourg", "activites": ["cuisine"]},
            {"resultats": []})
        self.assertNotIn(CASE_ACTIVITY, _cases(analysis))


class TestActivityNotOffered(unittest.TestCase):

    def test_activity_without_match_is_reported(self):
        analysis = analyze_no_result({**REQUEST, "activites": ["cuisine"]}, _lyon())
        self.assertEqual(_cases(analysis), [CASE_ACTIVITY])
        self.assertEqual(
            analysis["missing"][0]["sentence"],
            "Je n'ai pas d'activité « cuisine » à Lyon dans notre catalogue.")

    def test_activity_alternative_comes_first(self):
        analysis = analyze_no_result({**REQUEST, "activites": ["cuisine"]}, _lyon())
        self.assertEqual(analysis["alternatives"][0]["id"], "activite-lyon-01")

    def test_only_unmatched_activities_are_reported(self):
        analysis = analyze_no_result(
            {**REQUEST, "activites": ["jeu", "cuisine"]}, _lyon())
        self.assertEqual([m["activity"] for m in analysis["missing"]], ["cuisine"])


class TestFullyBooked(unittest.TestCase):

    def test_unavailable_service_is_reported_with_its_date(self):
        search = _lyon(**{"hotel-lyon-01": {"disponible": False}})
        analysis = analyze_no_result(REQUEST, search)
        self.assertEqual(_cases(analysis), [CASE_FULLY_BOOKED])
        self.assertEqual(analysis["missing"][0]["sentence"],
                         "Hôtel des Lumières est complet le 7 novembre.")

    def test_unavailable_service_is_never_an_alternative(self):
        search = _lyon(**{"hotel-lyon-01": {"disponible": False}})
        ids = [a["id"] for a in analyze_no_result(REQUEST, search)["alternatives"]]
        self.assertNotIn("hotel-lyon-01", ids)


class TestOverBudget(unittest.TestCase):

    def test_over_budget_service_is_reported_with_the_gap(self):
        search = _lyon(**{"hotel-lyon-01": {"prix_unitaire_eur": 112,
                                            "dans_budget": False}})
        analysis = analyze_no_result(REQUEST, search)
        self.assertEqual(_cases(analysis), [CASE_OVER_BUDGET])
        self.assertEqual(analysis["missing"][0]["gap_eur"], 12)
        self.assertIn("dépasse votre budget de 12 € par personne",
                      analysis["missing"][0]["sentence"])

    def test_over_budget_service_is_never_an_alternative(self):
        search = _lyon(**{"hotel-lyon-01": {"dans_budget": False}})
        ids = [a["id"] for a in analyze_no_result(REQUEST, search)["alternatives"]]
        self.assertNotIn("hotel-lyon-01", ids)

    def test_another_service_type_is_never_offered_instead(self):
        """No other hotel in the results: no train or activity in its place."""
        search = _lyon(**{"hotel-lyon-01": {"dans_budget": False}})
        analysis = analyze_no_result(REQUEST, search)
        self.assertEqual(analysis["alternatives"], [])
        self.assertIn("ne propose aucune prestation", analysis["instruction"])

    def test_same_type_alternative_is_offered(self):
        search = _lyon(**{"hotel-lyon-01": {"disponible": False}})
        search["resultats"].append(
            _result("hotel-lyon-02", "Hôtel des Canuts", "hebergement", 75))
        ids = [a["id"] for a in analyze_no_result(REQUEST, search)["alternatives"]]
        self.assertEqual(ids, ["hotel-lyon-02"])


class TestAlternatives(unittest.TestCase):

    def test_alternatives_come_only_from_server_results(self):
        search = _lyon(**{"activite-lyon-01": {"activites_correspondantes": []}})
        server_ids = {r["id"] for r in search["resultats"]}
        for alternative in analyze_no_result(REQUEST, search)["alternatives"]:
            self.assertIn(alternative["id"], server_ids)

    def test_at_most_two_alternatives(self):
        search = _lyon()
        search["resultats"] += [
            _result(f"activite-lyon-0{i}", f"Activité {i}", "activite", 20)
            for i in (2, 3, 4)]
        search["resultats"][2]["activites_correspondantes"] = []
        alternatives = analyze_no_result(REQUEST, search)["alternatives"]
        self.assertLessEqual(len(alternatives), MAX_ALTERNATIVES)

    def test_alternative_sentence_has_price_and_check_time(self):
        analysis = analyze_no_result({**REQUEST, "activites": ["cuisine"]}, _lyon())
        self.assertEqual(
            analysis["alternatives"][0]["sentence"],
            "Je peux vous proposer à la place Enquête des traboules, "
            "à 29 € par personne, prix vérifié le 22/10 à 09:40.")

    def test_instruction_lists_gaps_then_alternatives_then_question(self):
        analysis = analyze_no_result({**REQUEST, "activites": ["cuisine"]}, _lyon())
        text = analysis["instruction"]
        gap = text.index("« cuisine »")
        alternative = text.index("Enquête des traboules")
        question = text.index("Ça vous irait ?")
        self.assertLess(gap, alternative)
        self.assertLess(alternative, question)


class TestAgentPayload(unittest.TestCase):
    """The tool payload sent back to the model carries the no-result block."""

    def test_tool_payload_includes_no_result(self):
        class SupplierNoCooking:
            def rechercher(self, criteres):
                search = _lyon()
                search["criteres"] = {**criteres, "date_verifiee": criteres["date_depart"]}
                return search

        agent = Agent(SupplierNoCooking(), DemandStore(None), api_key="cle", model="m")
        arguments = {
            "type_voyage": "autres", "destination": "Lyon",
            "date_depart": "2026-11-07", "date_retour": "2026-11-09",
            "nombre_voyageurs": 2, "budget_max_par_personne": 100,
            "niveau_aventure": "calme", "activites": ["cuisine"],
        }
        call = {"id": "c1", "type": "function",
                "function": {"name": TOOL_NAME, "arguments": json.dumps(arguments)}}
        trace = {"model": "m", "tool_calls": [], "simulation": True}
        outcome = agent._execute_tool(call, trace)

        no_result = outcome["payload"]["no_result"]
        self.assertEqual(_cases(no_result), [CASE_ACTIVITY])
        self.assertEqual(no_result["alternatives"][0]["id"], "activite-lyon-01")

    def test_system_prompt_has_the_no_result_rule(self):
        self.assertIn("QUAND IL N'Y A PAS DE RÉSULTAT", SYSTEM_PROMPT)
        self.assertIn("no_result", SYSTEM_PROMPT)
        self.assertIn("marché de Noël", SYSTEM_PROMPT)


if __name__ == "__main__":
    unittest.main()

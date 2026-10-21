#!/usr/bin/env python3
"""Tests for the constraint check of a travel proposal (#41)."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from contraintes import (STATUT_A_VERIFIER, STATUT_NON_RESPECTEE, STATUT_OK,
                         verifier_contraintes)


LYON_REQUEST = {
    "destination": "Lyon",
    "date_depart": "2026-10-18",
    "date_retour": "2026-10-20",
    "nombre_voyageurs": 2,
    "budget_max_par_personne": 300,
    "activites": ["extérieur"],
}

LYON_RESULTS = [
    {"id": "train-lyon-01", "prix_unitaire_eur": 62, "activites_correspondantes": []},
    {"id": "hotel-lyon-01", "prix_unitaire_eur": 88, "activites_correspondantes": []},
    {"id": "activite-lyon-01", "prix_unitaire_eur": 29, "activites_correspondantes": ["extérieur"]},
]

LYON_PROPOSAL = {
    "prix_total_eur": 534,
    "prestations": [
        {"id": "train-lyon-01", "prix_unitaire_eur": 62, "quantite": 2},
        {"id": "hotel-lyon-01", "prix_unitaire_eur": 88, "quantite": 4},
        {"id": "activite-lyon-01", "prix_unitaire_eur": 29, "quantite": 2},
    ],
}


def line_for(lines, constraint):
    return next(line for line in lines if line["contrainte"] == constraint)


class TestVerifierContraintes(unittest.TestCase):
    """The program, not the model, says which constraints are respected."""

    def test_budget_respected(self):
        lines = verifier_contraintes(LYON_REQUEST, LYON_PROPOSAL, LYON_RESULTS)
        line = line_for(lines, "budget")
        self.assertEqual(line["statut"], STATUT_OK)
        self.assertIn("267 €", line["detail"])

    def test_budget_exceeded_is_shown(self):
        request = dict(LYON_REQUEST, budget_max_par_personne=200)
        line = line_for(verifier_contraintes(request, LYON_PROPOSAL, LYON_RESULTS), "budget")
        self.assertEqual(line["statut"], STATUT_NON_RESPECTEE)
        self.assertIn("267 € > 200 €", line["detail"])

    def test_dates_and_travelers_are_listed(self):
        lines = verifier_contraintes(LYON_REQUEST, LYON_PROPOSAL, LYON_RESULTS)
        self.assertEqual(line_for(lines, "dates")["statut"], STATUT_OK)
        self.assertIn("2026-10-18", line_for(lines, "dates")["detail"])
        self.assertEqual(line_for(lines, "voyageurs")["statut"], STATUT_OK)

    def test_wished_activity_found_in_server_tags(self):
        lines = verifier_contraintes(LYON_REQUEST, LYON_PROPOSAL, LYON_RESULTS)
        self.assertEqual(line_for(lines, "activite:extérieur")["statut"], STATUT_OK)

    def test_missing_activity_is_marked(self):
        request = dict(LYON_REQUEST, activites=["cuisine"])
        lines = verifier_contraintes(request, LYON_PROPOSAL, LYON_RESULTS)
        self.assertEqual(line_for(lines, "activite:cuisine")["statut"], STATUT_NON_RESPECTEE)

    def test_missing_level_must_be_asked(self):
        lines = verifier_contraintes(LYON_REQUEST, LYON_PROPOSAL, LYON_RESULTS)
        line = line_for(lines, "niveau")
        self.assertEqual(line["statut"], STATUT_A_VERIFIER)
        self.assertIn("à demander", line["detail"])

    def test_works_with_a_stored_request_record(self):
        record = {"id": "dem_1", "demande": LYON_REQUEST}
        lines = verifier_contraintes(record, LYON_PROPOSAL, LYON_RESULTS)
        self.assertEqual(line_for(lines, "budget")["statut"], STATUT_OK)


if __name__ == "__main__":
    unittest.main()
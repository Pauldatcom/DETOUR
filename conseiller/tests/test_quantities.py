#!/usr/bin/env python3
"""Unit tests for quantities computed from the request (#34)."""

import sys
import unittest
from pathlib import Path

CONSEILLER_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(CONSEILLER_ROOT))

from propositions import apply_quantities, count_nights, valider_proposition

LYON_REQUEST = {
    "destination": "Lyon",
    "date_depart": "2026-11-07",
    "date_retour": "2026-11-09",
    "nombre_voyageurs": 2,
}

LYON_PROPOSAL = {
    "titre": "Week-end à Lyon",
    "description": "Deux nuits à Lyon.",
    "prestations": [
        {"id": "train-lyon-01", "nom": "Train vers Lyon", "type": "transport",
         "prix_unitaire_eur": 62, "quantite": 1, "disponible": True,
         "source": "Serveur fictif DÉTOUR", "consulte_le": "2026-10-22T08:00:00+00:00"},
        {"id": "hotel-lyon-01", "nom": "Hôtel des Lumières", "type": "hebergement",
         "prix_unitaire_eur": 88, "quantite": 1, "disponible": True,
         "source": "Serveur fictif DÉTOUR", "consulte_le": "2026-10-22T08:00:00+00:00"},
        {"id": "activite-lyon-01", "nom": "Enquête des traboules", "type": "activite",
         "prix_unitaire_eur": 29, "quantite": 1, "disponible": True,
         "source": "Serveur fictif DÉTOUR", "consulte_le": "2026-10-22T08:00:00+00:00"},
    ],
}


def quantities(proposal):
    return {line["id"]: line["quantite"] for line in proposal["prestations"]}


class CountNightsTest(unittest.TestCase):
    def test_two_nights(self):
        self.assertEqual(count_nights(LYON_REQUEST), 2)

    def test_five_nights(self):
        request = {"date_depart": "2026-11-07", "date_retour": "2026-11-12"}
        self.assertEqual(count_nights(request), 5)

    def test_missing_return_date_counts_one_night(self):
        self.assertEqual(count_nights({"date_depart": "2026-11-07"}), 1)

    def test_invalid_date_counts_one_night(self):
        request = {"date_depart": "not-a-date", "date_retour": "2026-11-09"}
        self.assertEqual(count_nights(request), 1)

    def test_return_before_departure_counts_one_night(self):
        request = {"date_depart": "2026-11-09", "date_retour": "2026-11-07"}
        self.assertEqual(count_nights(request), 1)


class ApplyQuantitiesTest(unittest.TestCase):
    def test_hotel_is_counted_per_traveler_and_per_night(self):
        result = apply_quantities(LYON_PROPOSAL, LYON_REQUEST)
        self.assertEqual(quantities(result)["hotel-lyon-01"], 4)

    def test_transport_and_activity_are_counted_per_traveler(self):
        result = apply_quantities(LYON_PROPOSAL, LYON_REQUEST)
        self.assertEqual(quantities(result)["train-lyon-01"], 2)
        self.assertEqual(quantities(result)["activite-lyon-01"], 2)

    def test_model_quantity_is_ignored(self):
        proposal = {**LYON_PROPOSAL, "prestations": [
            {**LYON_PROPOSAL["prestations"][0], "quantite": 9}]}
        result = apply_quantities(proposal, LYON_REQUEST)
        self.assertEqual(quantities(result)["train-lyon-01"], 2)

    def test_accented_accommodation_type(self):
        proposal = {**LYON_PROPOSAL, "prestations": [
            {**LYON_PROPOSAL["prestations"][1], "type": "Hébergement"}]}
        result = apply_quantities(proposal, LYON_REQUEST)
        self.assertEqual(quantities(result)["hotel-lyon-01"], 4)

    def test_invalid_traveler_count_falls_back_to_one(self):
        request = {**LYON_REQUEST, "nombre_voyageurs": "two"}
        result = apply_quantities(LYON_PROPOSAL, request)
        self.assertEqual(quantities(result), {
            "train-lyon-01": 1, "hotel-lyon-01": 2, "activite-lyon-01": 1})

    def test_original_proposal_is_not_modified(self):
        apply_quantities(LYON_PROPOSAL, LYON_REQUEST)
        self.assertEqual(LYON_PROPOSAL["prestations"][1]["quantite"], 1)

    def test_total_price_uses_real_nights(self):
        # 2 x 62 + 4 x 88 + 2 x 29 = 534 EUR, so 267 EUR per person.
        result = valider_proposition(apply_quantities(LYON_PROPOSAL, LYON_REQUEST))
        self.assertEqual(result["prix_total_eur"], 534)


if __name__ == "__main__":
    unittest.main()
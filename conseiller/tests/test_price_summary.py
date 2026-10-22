#!/usr/bin/env python3
"""Unit tests for the proposal price summary shown to the advisor (#39)."""

import sys
import unittest
from pathlib import Path

CONSEILLER_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(CONSEILLER_ROOT))

from lecture import enrichir_propositions, price_summary


def verified(service_id, name, type_, unit_price, quantity, read_at):
    return {
        "id": service_id, "nom": name, "type": type_, "quantite": quantity,
        "verification": "verifie", "prix_unitaire_eur": unit_price,
        "prix_total_eur": unit_price * quantity, "disponible": True,
        "source": "Serveur fictif DÉTOUR", "consulte_le": read_at,
    }


# Lyon example of #39: 2 travelers, 2 nights.
LYON_PROPOSAL = {
    "id": "prop_lyon",
    "demande_id": "dem_lyon",
    "prestations": [
        verified("train-lyon-01", "Train vers Lyon", "transport", 62, 2,
                 "2026-10-19T14:10:00+00:00"),
        verified("hotel-lyon-01", "Hôtel des Lumières", "hebergement", 88, 4,
                 "2026-10-19T14:15:00+00:00"),
        verified("activite-lyon-01", "Enquête des traboules", "activite", 29, 2,
                 "2026-10-19T14:12:00+00:00"),
    ],
    "prix_total_eur": 534,
}


def line(summary, service_id):
    return next(item for item in summary["lignes"] if item["id"] == service_id)


class PriceSummaryTest(unittest.TestCase):
    def test_total_and_price_per_person(self):
        summary = price_summary(LYON_PROPOSAL, 2)
        self.assertEqual(summary["prix_total_eur"], 534)
        self.assertEqual(summary["prix_par_personne_eur"], 267)
        self.assertEqual(summary["nombre_voyageurs"], 2)

    def test_each_line_shows_name_type_and_price_per_person(self):
        summary = price_summary(LYON_PROPOSAL, 2)
        hotel = line(summary, "hotel-lyon-01")
        self.assertEqual(hotel["nom"], "Hôtel des Lumières")
        self.assertEqual(hotel["type"], "hebergement")
        self.assertEqual(hotel["prix_par_personne_eur"], 176)
        self.assertEqual(line(summary, "train-lyon-01")["prix_par_personne_eur"], 62)
        self.assertEqual(line(summary, "activite-lyon-01")["prix_par_personne_eur"], 29)

    def test_latest_server_reading_time_is_shown(self):
        summary = price_summary(LYON_PROPOSAL, 2)
        self.assertEqual(summary["consulte_le"], "2026-10-19T14:15:00+00:00")

    def test_missing_line_has_no_price_and_is_not_counted(self):
        proposal = {"prestations": [
            LYON_PROPOSAL["prestations"][0],
            {"id": "bateau-lyon", "nom": "Bateau", "type": "activite", "quantite": 2,
             "verification": "manquant", "prix_unitaire_eur": None,
             "prix_total_eur": None, "consulte_le": None},
        ]}
        summary = price_summary(proposal, 2)
        self.assertIsNone(line(summary, "bateau-lyon")["prix_par_personne_eur"])
        self.assertEqual(summary["prix_total_eur"], 124)
        self.assertEqual(summary["prix_par_personne_eur"], 62)

    def test_no_verified_line_has_no_reading_time(self):
        summary = price_summary({"prestations": []}, 2)
        self.assertEqual(summary["prix_total_eur"], 0)
        self.assertIsNone(summary["consulte_le"])

    def test_invalid_traveler_count_falls_back_to_one(self):
        summary = price_summary(LYON_PROPOSAL, 0)
        self.assertEqual(summary["nombre_voyageurs"], 1)
        self.assertEqual(summary["prix_par_personne_eur"], 534)


class FakeDemandStore:
    def __init__(self, record):
        self.record = record

    def obtenir(self, dem_id):
        return self.record if dem_id == self.record.get("id") else None


class EnrichedProposalTest(unittest.TestCase):
    def test_enriched_proposal_carries_the_price_summary(self):
        request = {"id": "dem_lyon", "demande": {"nombre_voyageurs": 2}, "recherches": []}
        enriched = enrichir_propositions([LYON_PROPOSAL], FakeDemandStore(request))[0]
        self.assertEqual(enriched["recapitulatif_prix"]["prix_par_personne_eur"], 267)

    def test_stored_proposal_is_not_modified(self):
        request = {"id": "dem_lyon", "demande": {"nombre_voyageurs": 2}, "recherches": []}
        enrichir_propositions([LYON_PROPOSAL], FakeDemandStore(request))
        self.assertNotIn("recapitulatif_prix", LYON_PROPOSAL)


if __name__ == "__main__":
    unittest.main()
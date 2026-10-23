"""#6: supplier HTTP errors must stay distinct for the agent."""

import io
import json
import sys
import unittest
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent import Agent, _rapport_erreur_fournisseur
from fournisseur import SupplierError, erreur_depuis_http
from store import DemandStore

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
                "date_depart": "2030-11-07",
                "date_retour": "2030-11-09",
                "nombre_voyageurs": 2,
                "budget_max_par_personne": 500,
                "niveau_aventure": "calme",
            }),
        },
    }],
}


def http_error(code, message="x"):
    body = json.dumps({"erreur": {"message": message}}).encode()
    return urllib.error.HTTPError(
        "http://example.test/api", code, "err", hdrs=None, fp=io.BytesIO(body),
    )


class TestErreurDepuisHttp(unittest.TestCase):
    def test_401_and_403_are_auth(self):
        for code in (401, 403):
            err = erreur_depuis_http("la recherche", http_error(code, "clé invalide"))
            self.assertEqual(err.status, code)
            self.assertIn("Authentification", str(err))
            self.assertIn("clé invalide", str(err))

    def test_404_is_not_found(self):
        err = erreur_depuis_http("la recherche", http_error(404, "inconnu"))
        self.assertEqual(err.status, 404)
        self.assertIn("introuvable", str(err))

    def test_409_is_unavailable(self):
        err = erreur_depuis_http("la recherche", http_error(409, "complet"))
        self.assertEqual(err.status, 409)
        self.assertIn("indisponible", str(err))

    def test_other_http_keeps_status(self):
        err = erreur_depuis_http("le catalogue", http_error(500, "boom"))
        self.assertEqual(err.status, 500)
        self.assertIn("refusé", str(err))


class TestRapportErreurFournisseur(unittest.TestCase):
    def test_distinct_statuts_and_consignes(self):
        cases = [
            (403, "auth_refusee", "authentification"),
            (404, "prestation_introuvable", "introuvable"),
            (409, "prestation_indisponible", "indisponible"),
            (502, "serveur_indisponible", "injoignable"),
        ]
        for status, statut, mot in cases:
            with self.subTest(status=status):
                rapport_statut, consigne = _rapport_erreur_fournisseur(
                    SupplierError("x", status=status))
                self.assertEqual(rapport_statut, statut)
                self.assertIn(mot, consigne.lower())
                self.assertIn("sans inventer", consigne.lower())


class FakeSupplier:
    def __init__(self, error):
        self.error = error

    def rechercher(self, criteres):
        raise self.error


class TestAgentDistinctSupplierErrors(unittest.TestCase):
    """Each HTTP class reaches the model with a distinct trace statut."""

    def test_agent_trace_keeps_http_status(self):
        for status, expected_statut in (
            (401, "auth_refusee"),
            (404, "prestation_introuvable"),
            (409, "prestation_indisponible"),
            (502, "serveur_indisponible"),
        ):
            with self.subTest(status=status):
                store = DemandStore(None)
                supplier = FakeSupplier(SupplierError(f"err-{status}", status=status))
                agent = Agent(supplier, store, api_key="k", model="t")
                replies = [
                    TOOL_CALL_MESSAGE,
                    {"role": "assistant", "content": "Désolé, erreur serveur."},
                ]

                def fake_call(conversation):
                    return replies.pop(0)

                agent._call_model = fake_call
                result = agent.chat([{"role": "user", "content": "go"}])
                call = result["trace"]["tool_calls"][0]
                self.assertEqual(call["statut"], expected_statut)
                self.assertEqual(call["http_status"], status)


if __name__ == "__main__":
    unittest.main()

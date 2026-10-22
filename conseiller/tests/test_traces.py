"""#5: redacted agent traces must be persisted without secrets."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent import Agent
from fournisseur import SupplierError
from store import DemandStore
from traces import (expurger, finaliser_et_persister, finaliser_trace,
                    persister_trace, resume_reponse_serveur)


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
                "OPENROUTER_API_KEY": "sk-leak",
            }),
        },
    }],
}


class FakeSupplier:
    def rechercher(self, criteres):
        return {
            "source_label": "Serveur fictif DÉTOUR",
            "consulte_le": "2026-10-21T10:00:00+00:00",
            "resultats": [{
                "id": "train-nantes-01",
                "nom": "Train",
                "prix_unitaire_eur": 48,
                "disponible": True,
                "X-Team-Key": "demo-key",
            }],
        }


class TestExpurger(unittest.TestCase):
    def test_redacts_secret_keys(self):
        brut = {
            "ok": 1,
            "X-Team-Key": "demo",
            "nested": {"OPENROUTER_API_KEY": "sk", "cookie": "a=b"},
            "Authorization": "Bearer abc",
        }
        propre = expurger(brut)
        self.assertEqual(propre["ok"], 1)
        self.assertEqual(propre["X-Team-Key"], "[redacted]")
        self.assertEqual(propre["nested"]["OPENROUTER_API_KEY"], "[redacted]")
        self.assertEqual(propre["nested"]["cookie"], "[redacted]")
        self.assertEqual(propre["Authorization"], "[redacted]")
        self.assertNotIn("demo", json.dumps(propre))
        self.assertNotIn("sk", json.dumps(propre))


class TestResumeEtPersistance(unittest.TestCase):
    def test_resume_keeps_prices_only(self):
        resume = resume_reponse_serveur({
            "source_label": "S",
            "consulte_le": "t",
            "resultats": [{"id": "a", "nom": "A", "prix_unitaire_eur": 1,
                           "disponible": True, "secret": "x"}],
        })
        self.assertEqual(resume["resultats"][0]["id"], "a")
        self.assertNotIn("secret", resume["resultats"][0])

    def test_persiste_fichier_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            final = finaliser_et_persister(
                {"model": "m", "tool_calls": [], "X-Approval-Key": "nope"},
                tmp,
                request_id="dem_abc",
                reponse_finale="Bonjour",
            )
            self.assertEqual(final["request_id"], "dem_abc")
            self.assertEqual(final["reponse_finale"], "Bonjour")
            self.assertEqual(final["X-Approval-Key"], "[redacted]")
            fichiers = list(Path(tmp).glob("*.json"))
            self.assertEqual(len(fichiers), 1)
            lu = json.loads(fichiers[0].read_text(encoding="utf-8"))
            self.assertEqual(lu["reponse_finale"], "Bonjour")
            self.assertNotIn("nope", fichiers[0].read_text(encoding="utf-8"))

    def test_persister_noop_sans_dossier(self):
        self.assertIsNone(persister_trace(finaliser_trace({}), None))


class TestAgentTraceContract(unittest.TestCase):
    def test_trace_has_contract_fields_and_no_secrets(self):
        store = DemandStore(None)
        agent = Agent(FakeSupplier(), store, api_key="k", model="t")
        replies = [
            TOOL_CALL_MESSAGE,
            {"role": "assistant", "content": "Voici Nantes vérifié."},
        ]

        def fake_call(conversation):
            return replies.pop(0)

        agent._call_model = fake_call
        result = agent.chat([{"role": "user", "content": "go"}])
        trace = result["trace"]
        self.assertTrue(trace["request_id"])
        self.assertEqual(trace["reponse_finale"], "Voici Nantes vérifié.")
        call = trace["tool_calls"][0]
        self.assertEqual(call["outil"], "chercher_voyages")
        self.assertIn("arguments", call)
        self.assertEqual(call["validation"], "ok")
        self.assertEqual(call["http_status"], 200)
        self.assertEqual(call["reponse_serveur"]["resultats"][0]["id"], "train-nantes-01")
        # Model-supplied secret key name is just a travel field key — still
        # redacted on persist; raw agent trace keeps args without auth headers.
        dump = json.dumps(trace)
        self.assertNotIn("Bearer ", dump)

        with tempfile.TemporaryDirectory() as tmp:
            final = finaliser_et_persister(
                trace, tmp,
                request_id=trace["request_id"],
                reponse_finale=trace["reponse_finale"],
            )
            # The leaked OPENROUTER_API_KEY argument key is scrubbed on persist.
            self.assertEqual(
                final["tool_calls"][0]["arguments"].get("OPENROUTER_API_KEY"),
                "[redacted]",
            )
            self.assertNotIn("sk-leak", Path(tmp).joinpath(
                list(Path(tmp).glob("*.json"))[0].name
            ).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

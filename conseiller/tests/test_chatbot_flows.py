#!/usr/bin/env python3
"""Tests for chatbot flows left uncovered by the existing suites.

Targets the gaps identified for issue #125:
  1. arguments_invalides branch in _execute_tool (non-dict JSON args).
  2. copie_depuis_v1 flag in construire_donnees_v2 (absent verified v1 line).
  3. End-to-end agent tool call returning resultats with disponible=False.
  4. Alternative suggestion: tool payload exposes both available and unavailable
     options so the model can suggest an alternative.
  5. Real Agent.generer_proposition (mock _call_model, not FakeAgentWithGeneration).
  6. The store's creer always produces statut='brouillon'; the agent's
     generer_proposition does not set statut (brouillon is the store's
     responsibility).
"""

import json
import sys
import unittest
from pathlib import Path

CONSEILLER_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(CONSEILLER_ROOT))

from agent import Agent, OpenRouterError, TOOL_NAME
from propositions import PropositionStore
from store import DemandStore
from utils import STATUT_BROUILLON
from versions import construire_donnees_v2

from test_conseiller import (
    VALIDE,
    FakeOpenRouter,
    FakeSupplier,
    TOOL_CALL_MESSAGE,
    FINAL_MESSAGE,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fake_call_model(content):
    """Return a _call_model replacement that yields the given assistant message."""
    def _call(conversation, with_tools=True):
        return {"role": "assistant", "content": content}
    return _call


def _tool_call_with_arguments(arguments_str, name=TOOL_NAME):
    """Build a scripted tool-call message with arbitrary raw arguments string."""
    return {
        "role": "assistant",
        "content": None,
        "tool_calls": [{
            "id": "call_bad",
            "type": "function",
            "function": {"name": name, "arguments": arguments_str},
        }],
    }


# ---------------------------------------------------------------------------
# Flow 1 — arguments_invalides
# ---------------------------------------------------------------------------

class TestArgumentsInvalides(unittest.TestCase):
    """_execute_tool must refuse arguments that are not a JSON object."""

    def setUp(self):
        self.store = DemandStore(None)
        self.agent = Agent(FakeSupplier(), self.store, api_key="cle", model="m")

    def _call(self, arguments_str):
        call = {
            "id": "c1",
            "type": "function",
            "function": {"name": TOOL_NAME, "arguments": arguments_str},
        }
        trace = {"model": "m", "tool_calls": [], "simulation": True}
        outcome = self.agent._execute_tool(call, trace)
        return trace["tool_calls"][0], outcome

    def test_json_array_is_refused(self):
        """A JSON array (not an object) triggers arguments_invalides."""
        entry, outcome = self._call("[1, 2, 3]")
        self.assertEqual(entry["statut"], "refuse")
        self.assertEqual(entry["validation"], "arguments_invalides")
        self.assertIsNone(outcome.get("demande"))
        self.assertEqual(len(self.store.lister()), 0)

    def test_json_null_is_refused(self):
        """JSON null triggers arguments_invalides."""
        entry, outcome = self._call("null")
        self.assertEqual(entry["statut"], "refuse")
        self.assertEqual(entry["validation"], "arguments_invalides")
        self.assertIsNone(outcome.get("demande"))

    def test_malformed_json_is_refused(self):
        """Syntactically invalid JSON triggers arguments_invalides."""
        entry, outcome = self._call("not-valid-json{")
        self.assertEqual(entry["statut"], "refuse")
        self.assertEqual(entry["validation"], "arguments_invalides")
        self.assertIsNone(outcome.get("demande"))

    def test_json_string_is_refused(self):
        """A JSON string (not an object) triggers arguments_invalides."""
        entry, outcome = self._call('"juste une chaine"')
        self.assertEqual(entry["statut"], "refuse")
        self.assertEqual(entry["validation"], "arguments_invalides")

    def test_valid_dict_arguments_are_accepted(self):
        """A valid JSON object does NOT trigger arguments_invalides (control)."""
        entry, _ = self._call(json.dumps({"destination": "Nantes"}))
        self.assertNotEqual(entry.get("validation"), "arguments_invalides")


# ---------------------------------------------------------------------------
# Flow 2 — copie_depuis_v1
# ---------------------------------------------------------------------------

class TestCopiePuisV1(unittest.TestCase):
    """construire_donnees_v2 must flag a v1-verified line absent from the new reading."""

    # A proposal whose lines are both verified.
    V1_PROP = {
        "titre": "Week-end à Nantes",
        "description": "Séjour romantique.",
        "prestations": [
            {
                "id": "train-nantes-01",
                "nom": "Train Nantes",
                "type": "transport",
                "quantite": 2,
                "verification": "verifie",
                "prix_unitaire_eur": 48,
                "prix_total_eur": 96,
                "disponible": True,
                "source": "Serveur fictif DÉTOUR",
                "consulte_le": "2026-10-19T10:00:00+00:00",
            },
            {
                "id": "hotel-nantes-01",
                "nom": "Hôtel Nantes",
                "type": "hébergement",
                "quantite": 1,
                "verification": "verifie",
                "prix_unitaire_eur": 120,
                "prix_total_eur": 120,
                "disponible": True,
                "source": "Serveur fictif DÉTOUR",
                "consulte_le": "2026-10-19T10:00:00+00:00",
            },
        ],
    }

    # New reading contains train (with a changed price) but NOT the hotel.
    RECHERCHE_PARTIELLE = {
        "source_label": "Serveur fictif DÉTOUR",
        "source_url": "http://faux",
        "consulte_le": "2026-10-20T12:00:00+00:00",
        "criteres": {},
        "resultats": [
            {
                "id": "train-nantes-01",
                "nom": "Train Nantes",
                "type": "transport",
                "prix_unitaire_eur": 52,
                "disponible": True,
                "dans_budget": True,
                "activites_correspondantes": [],
                "correspond_type_voyage": True,
                "places_restantes": 10,
                "mis_a_jour_le": "2026-10-20T11:00:00+00:00",
            }
        ],
    }

    def test_absent_verified_line_gets_copie_depuis_v1(self):
        """A verified v1 line absent from the new reading is kept with copie_depuis_v1=True."""
        # Train changed (price 48→52) so it requires a decision; hotel is absent → no delta.
        decisions = [{"prestation_id": "train-nantes-01", "choix": "keep"}]
        data = construire_donnees_v2(self.V1_PROP, self.RECHERCHE_PARTIELLE, decisions)
        by_id = {p["id"]: p for p in data["prestations"]}

        # Train was refreshed from the new reading — no flag.
        self.assertIn("train-nantes-01", by_id)
        self.assertNotIn("copie_depuis_v1", by_id["train-nantes-01"])
        self.assertEqual(by_id["train-nantes-01"]["prix_unitaire_eur"], 52)

        # Hotel was absent — copied from v1 and flagged.
        self.assertIn("hotel-nantes-01", by_id)
        self.assertTrue(by_id["hotel-nantes-01"].get("copie_depuis_v1"))

    def test_absent_unverified_line_is_not_copied(self):
        """A 'manquant' (unverified) v1 line absent from the new reading is dropped, not copied."""
        prop = {
            "titre": "Test",
            "description": "",
            "prestations": [
                {
                    "id": "hotel-nantes-01",
                    "nom": "Hôtel Nantes",
                    "type": "hébergement",
                    "quantite": 1,
                    "verification": "manquant",
                    "prix_unitaire_eur": None,
                    "prix_total_eur": None,
                    "disponible": None,
                    "source": None,
                    "consulte_le": None,
                },
            ],
        }
        recherche = {
            "source_label": "Serveur fictif DÉTOUR",
            "source_url": "http://faux",
            "consulte_le": "2026-10-20T12:00:00+00:00",
            "criteres": {},
            "resultats": [],
        }
        data = construire_donnees_v2(prop, recherche, decisions=[])
        # Unverified + absent → not included (no copie_depuis_v1).
        self.assertEqual(data["prestations"], [])

    def test_copie_depuis_v1_preserves_original_values(self):
        """The copied line keeps all original v1 values unchanged."""
        decisions = [{"prestation_id": "train-nantes-01", "choix": "keep"}]
        data = construire_donnees_v2(self.V1_PROP, self.RECHERCHE_PARTIELLE, decisions)
        hotel = next(p for p in data["prestations"] if p["id"] == "hotel-nantes-01")
        self.assertEqual(hotel["prix_unitaire_eur"], 120)
        self.assertTrue(hotel["disponible"])
        self.assertEqual(hotel["source"], "Serveur fictif DÉTOUR")


# ---------------------------------------------------------------------------
# Flow 3 — Unavailable activity: e2e tool call with disponible=False results
# ---------------------------------------------------------------------------

class TestAgentDisponiblFalse(unittest.TestCase):
    """Agent.chat stores and returns search results that include disponible=False."""

    def test_tool_call_succeeds_with_unavailable_prestations(self):
        """A successful tool call whose FakeSupplier returns disponible=False is stored."""
        unavailable = {
            "id": "activite-nantes-01",
            "nom": "Activité Nantes",
            "type": "activite",
            "prix_unitaire_eur": 40,
            "prix_total_eur": 80,
            "disponible": False,
            "dans_budget": True,
            "activites_correspondantes": ["extérieur"],
            "correspond_type_voyage": True,
            "places_restantes": 0,
            "mis_a_jour_le": "2026-10-16T10:00:00+00:00",
        }
        store = DemandStore(None)

        class SupplierWithUnavailable:
            def rechercher(self, criteres):
                return {
                    "source_label": "Faux",
                    "source_url": "http://faux",
                    "consulte_le": "2026-10-16T10:00:00+00:00",
                    "criteres": {**criteres, "date_verifiee": criteres["date_depart"]},
                    "resultats": [unavailable],
                }

        fake_or = FakeOpenRouter([
            {"message": TOOL_CALL_MESSAGE},
            {"message": FINAL_MESSAGE},
        ])
        self.addCleanup(fake_or.stop)
        agent = Agent(
            SupplierWithUnavailable(), store,
            api_key="cle-test", model="m", base_url=fake_or.url, timeout=5,
        )
        result = agent.chat([{"role": "user", "content": "Week-end à Nantes pour 2"}])

        self.assertEqual(result["trace"]["tool_calls"][0]["statut"], "ok")
        self.assertIsNotNone(result["recherche"])
        by_id = {r["id"]: r for r in result["recherche"]["resultats"]}
        self.assertIn("activite-nantes-01", by_id)
        self.assertFalse(by_id["activite-nantes-01"]["disponible"])
        self.assertEqual(by_id["activite-nantes-01"]["places_restantes"], 0)

    def test_unavailable_prestation_is_persisted_in_store(self):
        """The search record with a disponible=False prestation is stored on the demande."""
        store = DemandStore(None)

        class SupplierOneUnavailable:
            def rechercher(self, criteres):
                return {
                    "source_label": "Faux",
                    "source_url": "http://faux",
                    "consulte_le": "2026-10-16T10:00:00+00:00",
                    "criteres": {**criteres, "date_verifiee": criteres["date_depart"]},
                    "resultats": [
                        {
                            "id": "hotel-nantes-01", "nom": "Hôtel Nantes",
                            "type": "hébergement", "prix_unitaire_eur": 120,
                            "disponible": False, "dans_budget": False,
                            "activites_correspondantes": [], "correspond_type_voyage": True,
                            "places_restantes": 0,
                            "mis_a_jour_le": "2026-10-16T10:00:00+00:00",
                        }
                    ],
                }

        fake_or = FakeOpenRouter([
            {"message": TOOL_CALL_MESSAGE},
            {"message": FINAL_MESSAGE},
        ])
        self.addCleanup(fake_or.stop)
        agent = Agent(
            SupplierOneUnavailable(), store,
            api_key="cle-test", model="m", base_url=fake_or.url, timeout=5,
        )
        result = agent.chat([{"role": "user", "content": "Nantes pour 2"}])
        dem = store.obtenir(result["demande"]["id"])
        self.assertEqual(len(dem["recherches"]), 1)
        stored_by_id = {r["id"]: r for r in dem["recherches"][0]["resultats"]}
        self.assertFalse(stored_by_id["hotel-nantes-01"]["disponible"])


# ---------------------------------------------------------------------------
# Flow 4 — Alternative suggestion
# ---------------------------------------------------------------------------

class TestAlternativeSuggestion(unittest.TestCase):
    """The tool payload must expose both unavailable and available options
    so the model has the data it needs to suggest an alternative."""

    def test_tool_payload_includes_available_alternative(self):
        """When supplier returns mixed results, both reach the stored recherche."""
        store = DemandStore(None)

        class SupplierMixed:
            def rechercher(self, criteres):
                return {
                    "source_label": "Faux",
                    "source_url": "http://faux",
                    "consulte_le": "2026-10-16T10:00:00+00:00",
                    "criteres": {**criteres, "date_verifiee": criteres["date_depart"]},
                    "resultats": [
                        {
                            "id": "hotel-nantes-01", "nom": "Hôtel Nantes",
                            "type": "hébergement", "prix_unitaire_eur": 120,
                            "disponible": False, "dans_budget": False,
                            "activites_correspondantes": [], "correspond_type_voyage": True,
                            "places_restantes": 0,
                            "mis_a_jour_le": "2026-10-16T10:00:00+00:00",
                        },
                        {
                            "id": "hotel-nantes-02", "nom": "Hôtel Nantes Alt",
                            "type": "hébergement", "prix_unitaire_eur": 95,
                            "disponible": True, "dans_budget": True,
                            "activites_correspondantes": [], "correspond_type_voyage": True,
                            "places_restantes": 5,
                            "mis_a_jour_le": "2026-10-16T10:00:00+00:00",
                        },
                    ],
                }

        reply = (
            "L'hôtel principal est complet. "
            "Je vous propose une alternative disponible : Hôtel Nantes Alt à 95 €."
        )
        fake_or = FakeOpenRouter([
            {"message": TOOL_CALL_MESSAGE},
            {"message": {"role": "assistant", "content": reply}},
        ])
        self.addCleanup(fake_or.stop)
        agent = Agent(
            SupplierMixed(), store,
            api_key="cle-test", model="m", base_url=fake_or.url, timeout=5,
        )
        result = agent.chat([{"role": "user", "content": "Week-end à Nantes pour 2"}])
        self.assertEqual(result["trace"]["tool_calls"][0]["statut"], "ok")
        by_id = {r["id"]: r for r in result["recherche"]["resultats"]}
        self.assertFalse(by_id["hotel-nantes-01"]["disponible"])
        self.assertTrue(by_id["hotel-nantes-02"]["disponible"])
        self.assertIn("alternative", result["reply"].lower())

    def test_system_prompt_restricts_destinations_for_alternatives(self):
        """SYSTEM_PROMPT restricts the catalogue to Nantes, Lyon and Lille;
        any suggested alternative must come from these destinations only."""
        from agent import SYSTEM_PROMPT
        for dest in ("Nantes", "Lyon", "Lille"):
            self.assertIn(dest, SYSTEM_PROMPT)
        self.assertIn("restreint", SYSTEM_PROMPT.lower())


# ---------------------------------------------------------------------------
# Flow 5 — Real Agent.generer_proposition (not FakeAgentWithGeneration)
# ---------------------------------------------------------------------------

class TestGenererPropositionVraiAgent(unittest.TestCase):
    """generer_proposition exercises _call_model → _extraire_json → aligner_sur_serveur."""

    DEMANDE_RECORD = {
        "demande": {
            "destination": "Nantes",
            "date_depart": "2026-11-07",
            "date_retour": "2026-11-09",
            "nombre_voyageurs": 2,
            "budget_max_par_personne": 500,
            "type_voyage": "lune-de-miel",
            "niveau_aventure": "calme",
            "souhaits": "romantique",
        }
    }

    RESULTATS = [
        {
            "id": "train-nantes-01",
            "nom": "Train Nantes",
            "type": "transport",
            "prix_unitaire_eur": 48,
            "disponible": True,
            "dans_budget": True,
            "activites_correspondantes": [],
            "correspond_type_voyage": True,
            "places_restantes": 10,
            "mis_a_jour_le": "2026-10-16T10:00:00+00:00",
        }
    ]

    RECHERCHE = {
        "source_label": "Serveur fictif DÉTOUR",
        "consulte_le": "2026-10-16T10:00:00+00:00",
        "resultats": RESULTATS,
    }

    MODEL_JSON_OK = {
        "titre": "Week-end romantique à Nantes",
        "description": "Un séjour pour deux.",
        "message_voyageur": "Bonjour, voici une première ébauche — Alexandre",
        "prestations": [
            {"id": "train-nantes-01", "nom": "Train Nantes", "type": "transport",
             "prix_unitaire_eur": 48, "quantite": 2},
        ],
    }

    def _make_agent(self):
        return Agent(FakeSupplier(), DemandStore(None), api_key="cle", model="m")

    def test_aligned_prestation_is_verified(self):
        """Known id → aligned against server result → verification='verifie'."""
        agent = self._make_agent()
        agent._call_model = _fake_call_model(json.dumps(self.MODEL_JSON_OK))
        result = agent.generer_proposition(self.DEMANDE_RECORD, self.RECHERCHE)
        self.assertEqual(result["titre"], "Week-end romantique à Nantes")
        by_id = {p["id"]: p for p in result["prestations"]}
        self.assertIn("train-nantes-01", by_id)
        self.assertEqual(by_id["train-nantes-01"]["verification"], "verifie")
        self.assertEqual(by_id["train-nantes-01"]["prix_unitaire_eur"], 48)

    def test_unknown_prestation_id_becomes_manquant(self):
        """Model references an id absent from the search → stored as manquant."""
        agent = self._make_agent()
        model_json = {**self.MODEL_JSON_OK, "prestations": [
            {"id": "prestation-inconnue", "nom": "Inconnu", "type": "transport",
             "prix_unitaire_eur": 99, "quantite": 1},
        ]}
        agent._call_model = _fake_call_model(json.dumps(model_json))
        result = agent.generer_proposition(self.DEMANDE_RECORD, self.RECHERCHE)
        self.assertEqual(result["prestations"][0]["verification"], "manquant")
        self.assertIsNone(result["prestations"][0]["prix_unitaire_eur"])

    def test_malformed_json_raises_openrouter_error(self):
        """Non-JSON model reply → OpenRouterError (not a silent failure)."""
        agent = self._make_agent()
        agent._call_model = _fake_call_model("Désolé, je ne peux pas faire ça.")
        with self.assertRaises(OpenRouterError) as ctx:
            agent.generer_proposition(self.DEMANDE_RECORD, self.RECHERCHE)
        self.assertIn("illisible", str(ctx.exception).lower())

    def test_json_array_raises_openrouter_error(self):
        """Model returning a JSON array → OpenRouterError."""
        agent = self._make_agent()
        agent._call_model = _fake_call_model(json.dumps([1, 2, 3]))
        with self.assertRaises(OpenRouterError) as ctx:
            agent.generer_proposition(self.DEMANDE_RECORD, self.RECHERCHE)
        self.assertIn("invalide", str(ctx.exception).lower())

    def test_missing_api_key_raises(self):
        """No API key → OpenRouterError before any HTTP call."""
        agent = Agent(FakeSupplier(), DemandStore(None), api_key="", model="m")
        with self.assertRaises(OpenRouterError) as ctx:
            agent.generer_proposition(self.DEMANDE_RECORD, self.RECHERCHE)
        self.assertEqual(ctx.exception.status, 503)

    def test_generer_builds_correct_prompt(self):
        """generer_proposition includes destination, dates and resultats in the prompt."""
        agent = self._make_agent()
        captured = []

        def capturing_call(conversation, with_tools=True):
            captured.append(conversation)
            return {"role": "assistant", "content": json.dumps(self.MODEL_JSON_OK)}

        agent._call_model = capturing_call
        agent.generer_proposition(self.DEMANDE_RECORD, self.RECHERCHE)
        prompt_text = " ".join(m.get("content", "") or "" for m in captured[0])
        self.assertIn("Nantes", prompt_text)
        self.assertIn("2026-11-07", prompt_text)
        self.assertIn("train-nantes-01", prompt_text)

    def test_genere_par_is_stamped_assistant(self):
        """#117: generer_proposition stamps genere_par='assistant' on the draft."""
        agent = self._make_agent()
        agent._call_model = _fake_call_model(json.dumps(self.MODEL_JSON_OK))
        result = agent.generer_proposition(self.DEMANDE_RECORD, self.RECHERCHE)
        self.assertEqual(result["genere_par"], "assistant")

    def test_message_voyageur_is_preserved(self):
        """#117: the traveler-facing message from the model is preserved."""
        agent = self._make_agent()
        agent._call_model = _fake_call_model(json.dumps(self.MODEL_JSON_OK))
        result = agent.generer_proposition(self.DEMANDE_RECORD, self.RECHERCHE)
        self.assertEqual(result["message_voyageur"],
                         "Bonjour, voici une première ébauche — Alexandre")

    def test_message_voyageur_defaults_when_model_omits_it(self):
        """#117: a missing message_voyageur defaults to an empty string, not None."""
        agent = self._make_agent()
        model_json = {"titre": "Test", "description": "", "prestations": []}
        agent._call_model = _fake_call_model(json.dumps(model_json))
        result = agent.generer_proposition(self.DEMANDE_RECORD, self.RECHERCHE)
        self.assertEqual(result["message_voyageur"], "")

    def test_conseiller_name_is_injected_into_prompt(self):
        """#117: the advisor's first name is injected into the prompt."""
        agent = self._make_agent()
        captured = []

        def capturing_call(conversation, with_tools=True):
            captured.append(conversation)
            return {"role": "assistant", "content": json.dumps(self.MODEL_JSON_OK)}

        agent._call_model = capturing_call
        agent.generer_proposition(
            self.DEMANDE_RECORD, self.RECHERCHE, conseiller="Alexandre")
        prompt_text = " ".join(m.get("content", "") or "" for m in captured[0])
        self.assertIn("Alexandre", prompt_text)


# ---------------------------------------------------------------------------
# #117 — mettre_a_jour marks the draft as advisor-confirmed
# ---------------------------------------------------------------------------

class TestMettreAJourGenerePar(unittest.TestCase):
    """Editing a draft by hand stamps genere_par='conseiller' (#117)."""

    def test_edit_marks_genere_par_conseiller(self):
        store = PropositionStore(None)
        prop = store.creer("dem_117", {
            "titre": "Brouillon", "description": "Test",
            "message_voyageur": "Brouillon assistant",
            "genere_par": "assistant", "prestations": [],
        })
        updated = store.mettre_a_jour(prop["id"], {
            "titre": "Titre relu", "description": "Message relu",
            "message_voyageur": "Message relu par le conseiller",
            "genere_par": "assistant", "prestations": [],
        })
        self.assertEqual(updated["genere_par"], "conseiller")
        self.assertEqual(updated["message_voyageur"],
                         "Message relu par le conseiller")


# ---------------------------------------------------------------------------
# Flow 9 — generer cannot produce a non-brouillon proposition
# ---------------------------------------------------------------------------

class TestGenererPropositionEstBrouillon(unittest.TestCase):
    """The animation-prevention guarantee: a generated proposition is always
    statut='brouillon'. This is enforced by PropositionStore.creer, not the agent."""

    PROP_DATA = {
        "titre": "Week-end Nantes",
        "description": "Test.",
        "prestations": [],
    }

    def test_proposition_store_creer_always_sets_brouillon(self):
        """PropositionStore.creer always stamps statut=STATUT_BROUILLON regardless of input."""
        store = PropositionStore(None)
        prop = store.creer("dem_test", self.PROP_DATA)
        self.assertEqual(prop["statut"], STATUT_BROUILLON)

    def test_generer_proposition_output_has_no_statut(self):
        """Agent.generer_proposition returns data without a statut field.
        Statut is the store's concern, not the agent's."""
        agent = Agent(FakeSupplier(), DemandStore(None), api_key="cle", model="m")
        recherche = {
            "source_label": "Faux",
            "consulte_le": "2026-10-16T10:00:00+00:00",
            "resultats": [],
        }
        model_json = {"titre": "Test", "description": "", "prestations": []}
        agent._call_model = _fake_call_model(json.dumps(model_json))
        result = agent.generer_proposition(
            {"demande": {
                "destination": "Nantes", "date_depart": "2026-11-07",
                "date_retour": "2026-11-09", "nombre_voyageurs": 2,
                "budget_max_par_personne": 500, "type_voyage": "lune-de-miel",
                "niveau_aventure": "calme",
            }},
            recherche,
        )
        self.assertNotIn("statut", result)

    def test_storing_agent_output_gives_brouillon(self):
        """When the agent output is passed to PropositionStore.creer, statut is brouillon."""
        agent = Agent(FakeSupplier(), DemandStore(None), api_key="cle", model="m")
        recherche = {
            "source_label": "Faux",
            "consulte_le": "2026-10-16T10:00:00+00:00",
            "resultats": [],
        }
        model_json = {"titre": "Test", "description": "", "prestations": []}
        agent._call_model = _fake_call_model(json.dumps(model_json))
        agent_output = agent.generer_proposition(
            {"demande": {
                "destination": "Nantes", "date_depart": "2026-11-07",
                "date_retour": "2026-11-09", "nombre_voyageurs": 2,
                "budget_max_par_personne": 500, "type_voyage": "lune-de-miel",
                "niveau_aventure": "calme",
            }},
            recherche,
        )
        prop_store = PropositionStore(None)
        prop = prop_store.creer("dem_test", agent_output)
        self.assertEqual(prop["statut"], STATUT_BROUILLON)
        # Also verify it cannot be brouillon with a terminal status from the start.
        self.assertNotIn("envoyee", prop["statut"])
        self.assertNotIn("validee", prop["statut"])


if __name__ == "__main__":
    unittest.main()

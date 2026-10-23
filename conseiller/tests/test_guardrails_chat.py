#!/usr/bin/env python3
"""Guardrails from the chat path (#118).

The chatbot path (traveler `chat` and advisor `chat_conseiller`) must never:
  - transition a proposal to `envoyee` or `validee`,
  - trigger the confirmation animation,
  - send an unreviewed proposal to the traveler,
  - accept decision arguments (`statut`, `motif`, `qualification`, …).

These tests exercise the actual chat methods and the HTTP chat routes to prove
the invariants hold from the chat path — not just at the store level.
"""

import json
import secrets
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

CONSEILLER_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(CONSEILLER_ROOT))

from agent import (
    ADVISOR_TOOL_NAME,
    DECISION_ARGS,
    Agent,
)
from app import make_handler
from propositions import PropositionStore
from store import DemandStore
from users import UserStore
from utils import (
    DECISION_ACCEPTER,
    STATUT_BROUILLON,
    STATUT_ENVOYEE,
)

from test_auth_users import VALIDE, ClientHTTP, FakeSupplier, demarrer


# ---------------------------------------------------------------------------
# Helpers (same pattern as test_conseiller_chat.py)
# ---------------------------------------------------------------------------

SEARCH = {
    "source_label": "Serveur fictif DÉTOUR",
    "source_url": "http://faux",
    "consulte_le": "2026-10-22T07:40:00+00:00",
    "criteres": {},
    "resultats": [{
        "id": "hotel-lyon-01", "nom": "Hôtel des Lumières", "type": "hebergement",
        "prix_unitaire_eur": 88, "prix_total_eur": 176, "disponible": True,
        "places_restantes": 8,
    }],
}

TRAVELER_ARGS = {
    "type_voyage": "lune-de-miel",
    "destination": "Lyon",
    "date_depart": "2026-11-07",
    "date_retour": "2026-11-09",
    "nombre_voyageurs": 2,
    "budget_max_par_personne": 500,
    "niveau_aventure": "calme",
}

ADVISOR_ARGS = {
    "destination": "Lyon",
    "date_depart": "2026-11-07",
    "date_retour": "2026-11-09",
    "participants": 2,
}

PROPOSITION_DATA = {
    "titre": "Week-end à Lyon",
    "description": "Un séjour romantique.",
    "prestations": [],
}


class RecordingSupplier:
    """Records the criteres it received; returns a canned search."""

    def __init__(self):
        self.calls = []

    def rechercher(self, criteres):
        self.calls.append(dict(criteres))
        return json.loads(json.dumps(SEARCH))


def _scripted(agent, messages):
    """Replace the model with scripted messages; return what was sent."""
    sent = []

    def fake(conversation, with_tools=True, tools=None):
        sent.append({"conversation": list(conversation), "tools": tools})
        return messages.pop(0)

    agent._call_model = fake
    return sent


def _tool_call(arguments, name):
    return {"role": "assistant", "content": None, "tool_calls": [{
        "id": "call_1", "type": "function",
        "function": {"name": name, "arguments": json.dumps(arguments)},
    }]}


def _final_message(content="Voici ce que j'ai vérifié."):
    return {"role": "assistant", "content": content}


# ---------------------------------------------------------------------------
# 1. The chat path cannot transition a proposal to envoyee/validee
# ---------------------------------------------------------------------------

class TestChatNeChangePasStatutProposition(unittest.TestCase):
    """A full chat round (with tool call) leaves a brouillon proposition
    untouched — no decisions_statut entry, no status transition."""

    def setUp(self):
        self.store = DemandStore(None)
        self.supplier = RecordingSupplier()
        self.agent = Agent(self.supplier, self.store, api_key="cle", model="m")
        self.props = PropositionStore(None)
        self.dem_id = self.store.creer(dict(VALIDE))["id"]
        self.prop = self.props.creer(self.dem_id, dict(PROPOSITION_DATA))

    def test_traveler_chat_keeps_proposition_brouillon(self):
        _scripted(self.agent, [
            _tool_call(TRAVELER_ARGS, "chercher_voyages"),
            _final_message("Voici ce que j'ai vérifié."),
        ])
        self.agent.chat([{"role": "user", "content": "Lyon le 07/11 pour 2"}])
        record = self.props.obtenir(self.prop["id"])
        self.assertEqual(record["statut"], STATUT_BROUILLON)
        self.assertFalse(record.get("decisions_statut"))

    def test_advisor_chat_keeps_proposition_brouillon(self):
        _scripted(self.agent, [
            _tool_call(ADVISOR_ARGS, ADVISOR_TOOL_NAME),
            _final_message("Voici ce que j'ai vérifié."),
        ])
        self.agent.chat_conseiller(
            [{"role": "user", "content": "Vérifie Lyon"}],
            demande_id=self.dem_id)
        record = self.props.obtenir(self.prop["id"])
        self.assertEqual(record["statut"], STATUT_BROUILLON)
        self.assertFalse(record.get("decisions_statut"))

    def test_traveler_chat_without_tool_call_keeps_proposition_brouillon(self):
        _scripted(self.agent, [_final_message("Bonjour, où partez-vous ?")])
        self.agent.chat([{"role": "user", "content": "Bonjour"}])
        record = self.props.obtenir(self.prop["id"])
        self.assertEqual(record["statut"], STATUT_BROUILLON)
        self.assertFalse(record.get("decisions_statut"))


# ---------------------------------------------------------------------------
# 2. Decision args are refused from the chat path
# ---------------------------------------------------------------------------

class TestDecisionArgsRefusesDepuisChat(unittest.TestCase):
    """When the model tries to pass decision args through a tool call, they
    are stripped, traced as decision_refusee, and have no effect on the
    proposition or the supplier call."""

    def setUp(self):
        self.store = DemandStore(None)
        self.supplier = RecordingSupplier()
        self.agent = Agent(self.supplier, self.store, api_key="cle", model="m")
        self.props = PropositionStore(None)
        self.dem_id = self.store.creer(dict(VALIDE))["id"]
        self.prop = self.props.creer(self.dem_id, dict(PROPOSITION_DATA))

    def test_traveler_tool_strips_decision_args_and_traces_refus(self):
        args_with_decisions = {
            **TRAVELER_ARGS,
            "statut": STATUT_ENVOYEE,
            "motif": "je confirme",
            "qualification": "pret_proposition",
        }
        _scripted(self.agent, [
            _tool_call(args_with_decisions, "chercher_voyages"),
            _final_message("Voici ce que j'ai vérifié."),
        ])
        result = self.agent.chat([{"role": "user", "content": "Lyon"}])
        entry = result["trace"]["tool_calls"][0]
        self.assertIn("decision_refusee", entry)
        refused = entry["decision_refusee"]
        for cle in ("statut", "motif", "qualification"):
            self.assertIn(cle, refused)
        for cle in DECISION_ARGS:
            self.assertNotIn(cle, entry.get("arguments", {}))
        record = self.props.obtenir(self.prop["id"])
        self.assertEqual(record["statut"], STATUT_BROUILLON)
        self.assertFalse(record.get("decisions_statut"))

    def test_advisor_tool_ignores_decision_args(self):
        args_with_decisions = {
            **ADVISOR_ARGS,
            "statut": STATUT_ENVOYEE,
            "motif": "je confirme",
            "qualification": "pret_proposition",
        }
        _scripted(self.agent, [
            _tool_call(args_with_decisions, ADVISOR_TOOL_NAME),
            _final_message("Voici ce que j'ai vérifié."),
        ])
        result = self.agent.chat_conseiller(
            [{"role": "user", "content": "Vérifie Lyon"}],
            demande_id=self.dem_id)
        entry = result["trace"]["tool_calls"][0]
        self.assertEqual(entry["statut"], "ok")
        for cle in DECISION_ARGS:
            self.assertNotIn(cle, entry.get("arguments", {}))
        record = self.props.obtenir(self.prop["id"])
        self.assertEqual(record["statut"], STATUT_BROUILLON)
        self.assertFalse(record.get("decisions_statut"))

    def test_decision_args_in_traveler_chat_never_reach_supplier(self):
        args_with_decisions = {
            **TRAVELER_ARGS,
            "statut": STATUT_ENVOYEE,
            "motif": "je confirme",
            "validee_par": "agent",
        }
        _scripted(self.agent, [
            _tool_call(args_with_decisions, "chercher_voyages"),
            _final_message("Voici ce que j'ai vérifié."),
        ])
        self.agent.chat([{"role": "user", "content": "Lyon"}])
        for call in self.supplier.calls:
            for cle in DECISION_ARGS:
                self.assertNotIn(cle, call,
                                 f"{cle} leaked into supplier criteres: {call}")


# ---------------------------------------------------------------------------
# 3. The chat path cannot send a proposal without advisor review
# ---------------------------------------------------------------------------

class TestChatNEnvoiePasSansRevue(unittest.TestCase):
    """The chat path never calls decider or changer_statut: after a chat
    round the proposition stays brouillon and carries no decision journal.

    The store itself also refuses the agent as a decision author for
    `decider` — the only method that transitions to `envoyee`/`validee`."""

    def setUp(self):
        self.store = DemandStore(None)
        self.supplier = RecordingSupplier()
        self.agent = Agent(self.supplier, self.store, api_key="cle", model="m")
        self.props = PropositionStore(None)
        self.dem_id = self.store.creer(dict(VALIDE))["id"]
        self.prop = self.props.creer(self.dem_id, dict(PROPOSITION_DATA))

    def test_decider_with_agent_acteur_is_refused_by_store(self):
        with self.assertRaises(Exception):
            self.props.decider(self.prop["id"], DECISION_ACCEPTER,
                               "agent", "ok")
        record = self.props.obtenir(self.prop["id"])
        self.assertEqual(record["statut"], STATUT_BROUILLON)

    def test_traveler_chat_adds_no_decision_journal(self):
        _scripted(self.agent, [
            _tool_call(TRAVELER_ARGS, "chercher_voyages"),
            _final_message("Voici ce que j'ai vérifié."),
        ])
        self.agent.chat([{"role": "user", "content": "Lyon pour 2"}])
        record = self.props.obtenir(self.prop["id"])
        self.assertEqual(record["statut"], STATUT_BROUILLON)
        self.assertFalse(record.get("decisions_statut"))

    def test_advisor_chat_adds_no_decision_journal(self):
        _scripted(self.agent, [
            _tool_call(ADVISOR_ARGS, ADVISOR_TOOL_NAME),
            _final_message("Voici ce que j'ai vérifié."),
        ])
        self.agent.chat_conseiller(
            [{"role": "user", "content": "Vérifie Lyon"}],
            demande_id=self.dem_id)
        record = self.props.obtenir(self.prop["id"])
        self.assertEqual(record["statut"], STATUT_BROUILLON)
        self.assertFalse(record.get("decisions_statut"))


# ---------------------------------------------------------------------------
# 4. HTTP-level: the chat routes do not change any proposition status
# ---------------------------------------------------------------------------

class FakeAgentReply:
    """Minimal agent that returns a canned reply for both chat paths."""

    def __init__(self):
        self.calls = []

    def chat(self, messages, user_id="", demande_id=None):
        self.calls.append(("chat", messages, demande_id))
        return {"reply": "Bonjour !", "demande": None, "recherche": None,
                "trace": {"model": "test", "tool_calls": [],
                          "simulation": True}}

    def chat_conseiller(self, messages, demande_id=None):
        self.calls.append(("chat_conseiller", messages, demande_id))
        return {"reply": "Voici ce que j'ai vérifié.", "recherche": None,
                "demande": None,
                "trace": {"model": "test", "tool_calls": [],
                          "simulation": True}}


class TestChatRouteNeChangePasStatut(unittest.TestCase):
    """The HTTP chat routes never transition a proposal to envoyee/validee."""

    def _serve(self, agent):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        self.team_key = "cle-" + secrets.token_urlsafe(12)
        self.store = DemandStore(Path(tmp) / "demandes.json")
        self.props = PropositionStore(Path(tmp) / "propositions.json")
        handler = make_handler(
            self.store, FakeSupplier(), agent,
            users=UserStore(Path(tmp) / "users.json"),
            team_key=self.team_key,
            propositions=self.props)
        server, base = demarrer(handler)
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        return base

    def _advisor(self, base):
        client = ClientHTTP(base)
        client.post("/api/login-conseiller", {"cle": self.team_key, "prenom": "Camille"})
        return client

    def _traveler(self, base):
        client = ClientHTTP(base)
        client.post("/api/register", {"email": "v@test.fr", "nom": "V",
                                      "mot_de_passe": "motdepasse"})
        return client

    def test_advisor_chat_route_keeps_proposition_brouillon(self):
        agent = FakeAgentReply()
        base = self._serve(agent)
        dem_id = self.store.creer(dict(VALIDE))["id"]
        prop = self.props.creer(dem_id, dict(PROPOSITION_DATA))
        status, data, _ = self._advisor(base).post(
            "/api/conseiller/chat",
            {"messages": [{"role": "user", "content": "Vérifie Lyon"}],
             "demande_id": dem_id})
        self.assertEqual(status, 200)
        record = self.props.obtenir(prop["id"])
        self.assertEqual(record["statut"], STATUT_BROUILLON)
        self.assertFalse(record.get("decisions_statut"))

    def test_traveler_chat_route_keeps_proposition_brouillon(self):
        agent = FakeAgentReply()
        base = self._serve(agent)
        dem_id = self.store.creer(dict(VALIDE))["id"]
        prop = self.props.creer(dem_id, dict(PROPOSITION_DATA))
        status, _, _ = self._traveler(base).post(
            "/api/chat",
            {"messages": [{"role": "user", "content": "Lyon pour 2"}]})
        self.assertEqual(status, 200)
        record = self.props.obtenir(prop["id"])
        self.assertEqual(record["statut"], STATUT_BROUILLON)
        self.assertFalse(record.get("decisions_statut"))


if __name__ == "__main__":
    unittest.main()
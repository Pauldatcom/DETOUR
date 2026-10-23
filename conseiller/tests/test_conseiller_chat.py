#!/usr/bin/env python3
"""Tests for the advisor chat route and its assistant (#115, #123)."""

import json
import secrets
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

CONSEILLER_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(CONSEILLER_ROOT))

from agent import (ADVISOR_SYSTEM_PROMPT, ADVISOR_TOOL_DEFINITION, ADVISOR_TOOL_NAME,
                   ASSISTANT_INDISPONIBLE, Agent, OpenRouterError, criteres_conseiller)
from app import make_handler
from fournisseur import SupplierError
from propositions import PropositionStore
from store import DemandStore
from users import UserStore
from utils import MAX_TOOL_ITERATIONS

from test_auth_users import (VALIDE, ClientHTTP, FakeAgentWithGeneration, FakeSupplier,
                             demarrer)

SEARCH = {
    "source_label": "Serveur fictif DÉTOUR",
    "consulte_le": "2026-10-22T07:40:00+00:00",
    "resultats": [{
        "id": "hotel-lyon-01", "nom": "Hôtel des Lumières", "type": "hebergement",
        "prix_unitaire_eur": 88, "prix_total_eur": 176, "disponible": True,
        "places_restantes": 8,
    }],
}

ARGS = {"destination": "Lyon", "date_depart": "2026-12-12",
        "date_retour": "2026-12-13", "participants": 2}


class RecordingSupplier:
    def __init__(self, error=None):
        self.error = error
        self.calls = []

    def rechercher(self, criteres):
        self.calls.append(criteres)
        if self.error:
            raise self.error
        return json.loads(json.dumps(SEARCH))


def _tool_call(arguments, name=ADVISOR_TOOL_NAME):
    return {"role": "assistant", "content": None, "tool_calls": [{
        "id": "call_1", "type": "function",
        "function": {"name": name, "arguments": json.dumps(arguments)}}]}


def _scripted(agent, messages):
    """Replace the model with scripted messages; record what it was sent."""
    sent = []

    def fake(conversation, with_tools=True, tools=None):
        sent.append({"conversation": list(conversation), "with_tools": with_tools,
                     "tools": tools})
        return messages.pop(0)

    agent._call_model = fake
    return sent


class TestAdvisorPrompt(unittest.TestCase):

    def test_tone_rules(self):
        for rule in ("Précis d'abord, chaleureux ensuite",
                     "« nous » pour l'agence, « je » pour le conseiller",
                     "pas de « ! » en série",
                     "Aucune plaisanterie sur un prix, une indisponibilité ou une erreur"):
            self.assertIn(rule, ADVISOR_SYSTEM_PROMPT)

    def test_explains_what_was_checked_and_what_is_missing(self):
        self.assertIn("CE QUI A ÉTÉ VÉRIFIÉ", ADVISOR_SYSTEM_PROMPT)
        self.assertIn("l'heure de la vérification", ADVISOR_SYSTEM_PROMPT)
        self.assertIn("demande-les au conseiller", ADVISOR_SYSTEM_PROMPT)
        self.assertIn("plus de 24 h", ADVISOR_SYSTEM_PROMPT)

    def test_never_decides_and_never_shows_raw_errors(self):
        self.assertIn("confirmer une réservation, signer une proposition, changer un statut",
                      ADVISOR_SYSTEM_PROMPT)
        self.assertIn("Jamais de « Erreur : … » brut", ADVISOR_SYSTEM_PROMPT)

    def test_tool_is_read_only(self):
        self.assertIn("Lecture seule", ADVISOR_TOOL_DEFINITION["function"]["description"])


class TestAdvisorCriteria(unittest.TestCase):

    def test_valid_minimum(self):
        criteres = criteres_conseiller(ARGS)
        self.assertEqual(criteres["participants"], 2)
        self.assertIsNone(criteres["budget_max"])

    def test_invalid_values(self):
        for change in ({"destination": ""}, {"date_depart": "12/12/2026"},
                       {"date_retour": "2026-12-01"}, {"participants": 0},
                       {"participants": "2"}, {"budget_max_par_personne": -5},
                       {"type_voyage": "croisiere"}, {"activites": "jeu"}):
            with self.assertRaises(ValueError, msg=change):
                criteres_conseiller({**ARGS, **change})


class TestChatConseiller(unittest.TestCase):

    def setUp(self):
        self.store = DemandStore(None)
        self.supplier = RecordingSupplier()
        self.agent = Agent(self.supplier, self.store, api_key="cle", model="m")

    def test_search_is_verified_and_returned(self):
        sent = _scripted(self.agent, [_tool_call(ARGS),
                                      {"role": "assistant", "content": "Voici ce que j'ai vérifié."}])
        result = self.agent.chat_conseiller([{"role": "user", "content": "Lyon le 12/12 pour 2"}])
        self.assertEqual(result["reply"], "Voici ce que j'ai vérifié.")
        self.assertEqual(result["recherche"]["resultats"][0]["id"], "hotel-lyon-01")
        self.assertEqual(self.supplier.calls[0]["destination"], "Lyon")
        self.assertEqual(result["trace"]["tool_calls"][0]["statut"], "ok")
        self.assertEqual(sent[0]["tools"], [ADVISOR_TOOL_DEFINITION])
        self.assertEqual(sent[0]["conversation"][0]["content"], ADVISOR_SYSTEM_PROMPT)

    def test_never_writes_a_request(self):
        dem = self.store.creer(dict(VALIDE))
        before = json.dumps(self.store.obtenir(dem["id"]), sort_keys=True)
        _scripted(self.agent, [_tool_call(ARGS), {"role": "assistant", "content": "ok"}])
        self.agent.chat_conseiller([{"role": "user", "content": "Vérifie"}], demande_id=dem["id"])
        self.assertEqual(json.dumps(self.store.obtenir(dem["id"]), sort_keys=True), before)
        self.assertEqual(len(self.store.lister()), 1)

    def test_request_context_is_given_to_the_model(self):
        dem = self.store.creer(dict(VALIDE))
        sent = _scripted(self.agent, [{"role": "assistant", "content": "ok"}])
        self.agent.chat_conseiller([{"role": "user", "content": "Résume"}], demande_id=dem["id"])
        contexte = sent[0]["conversation"][1]["content"]
        self.assertIn(f"DOSSIER EN COURS (id={dem['id']})", contexte)
        self.assertIn("Aucune lecture du serveur", contexte)

    def test_traveler_tool_is_refused(self):
        _scripted(self.agent, [_tool_call(ARGS, name="chercher_voyages"),
                               {"role": "assistant", "content": "ok"}])
        result = self.agent.chat_conseiller([{"role": "user", "content": "x"}])
        self.assertEqual(result["trace"]["tool_calls"][0]["statut"], "refuse")
        self.assertEqual(self.supplier.calls, [])

    def test_invalid_arguments_ask_the_advisor(self):
        sent = _scripted(self.agent, [_tool_call({**ARGS, "participants": 0}),
                                      {"role": "assistant", "content": "Combien de voyageurs ?"}])
        self.agent.chat_conseiller([{"role": "user", "content": "x"}])
        self.assertEqual(self.supplier.calls, [])
        payload = json.loads(sent[1]["conversation"][-1]["content"])
        self.assertIn("Demande au conseiller", payload["consigne"])

    def test_supplier_error_is_explained_not_raw(self):
        self.supplier.error = SupplierError("HTTP 502 upstream", status=502)
        sent = _scripted(self.agent, [_tool_call(ARGS), {"role": "assistant", "content": "ok"}])
        result = self.agent.chat_conseiller([{"role": "user", "content": "x"}])
        payload = json.loads(sent[1]["conversation"][-1]["content"])
        self.assertEqual(payload["erreur"], "La vérification n'a pas abouti.")
        self.assertNotIn("HTTP 502", json.dumps(payload))
        self.assertIsNone(result["recherche"])

    def test_requires_an_api_key(self):
        agent = Agent(self.supplier, self.store, api_key="", model="m")
        with self.assertRaises(OpenRouterError):
            agent.chat_conseiller([{"role": "user", "content": "x"}])


class FakeAdvisorAgent:
    def __init__(self, error=None):
        self.error = error
        self.calls = []

    def chat_conseiller(self, messages, demande_id=None):
        self.calls.append((messages, demande_id))
        if self.error:
            raise self.error
        return {"reply": "Voici ce que j'ai vérifié.", "recherche": SEARCH,
                "demande": None, "trace": {"model": "m", "tool_calls": []}}


class TestAdvisorChatRoute(unittest.TestCase):

    def _serve(self, agent):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        self.team_key = "cle-" + secrets.token_urlsafe(12)
        self.store = DemandStore(Path(tmp) / "demandes.json")
        handler = make_handler(self.store, FakeSupplier(), agent,
                               users=UserStore(Path(tmp) / "users.json"),
                               team_key=self.team_key,
                               propositions=PropositionStore(Path(tmp) / "propositions.json"))
        server, base = demarrer(handler)
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        return base

    def _advisor(self, base):
        client = ClientHTTP(base)
        client.post("/api/login-conseiller", {"cle": self.team_key, "prenom": "Camille"})
        return client

    def test_requires_an_advisor_session(self):
        base = self._serve(FakeAdvisorAgent())
        traveler = ClientHTTP(base)
        traveler.post("/api/register", {"email": "v@test.fr", "nom": "V",
                                        "mot_de_passe": "motdepasse"})
        status, _, _ = traveler.post("/api/conseiller/chat",
                                     {"messages": [{"role": "user", "content": "x"}]})
        self.assertEqual(status, 401)
        status, _, _ = ClientHTTP(base).post("/api/conseiller/chat",
                                             {"messages": [{"role": "user", "content": "x"}]})
        self.assertEqual(status, 401)

    def test_advisor_gets_reply_and_verified_search(self):
        agent = FakeAdvisorAgent()
        base = self._serve(agent)
        dem_id = self.store.creer(dict(VALIDE))["id"]
        status, data, _ = self._advisor(base).post("/api/conseiller/chat", {
            "messages": [{"role": "user", "content": "Vérifie Lyon"}], "demande_id": dem_id})
        self.assertEqual(status, 200)
        self.assertEqual(data["reply"], "Voici ce que j'ai vérifié.")
        self.assertEqual(data["recherche"]["resultats"][0]["id"], "hotel-lyon-01")
        self.assertEqual(agent.calls[0][1], dem_id)

    def test_unknown_request_is_404(self):
        base = self._serve(FakeAdvisorAgent())
        status, _, _ = self._advisor(base).post("/api/conseiller/chat", {
            "messages": [{"role": "user", "content": "x"}], "demande_id": "dem_000000"})
        self.assertEqual(status, 404)

    def test_invalid_messages_are_400(self):
        base = self._serve(FakeAdvisorAgent())
        status, _, _ = self._advisor(base).post("/api/conseiller/chat", {"messages": []})
        self.assertEqual(status, 400)

    def test_provider_error_is_never_raw(self):
        base = self._serve(FakeAdvisorAgent(OpenRouterError("OpenRouter : HTTP 500 raw", 502)))
        status, data, _ = self._advisor(base).post("/api/conseiller/chat",
                                                   {"messages": [{"role": "user", "content": "x"}]})
        self.assertEqual(status, 503)
        self.assertEqual(data["erreur"]["message"], ASSISTANT_INDISPONIBLE)
        self.assertNotIn("HTTP 500", json.dumps(data))

    def test_agent_not_configured_is_503(self):
        base = self._serve(None)
        status, data, _ = self._advisor(base).post("/api/conseiller/chat",
                                                   {"messages": [{"role": "user", "content": "x"}]})
        self.assertEqual(status, 503)
        self.assertEqual(data["erreur"]["code"], "agent_not_configured")

    def test_traveler_chat_route_is_untouched(self):
        base = self._serve(FakeAdvisorAgent())
        status, _, _ = self._advisor(base).post("/api/chat",
                                                {"messages": [{"role": "user", "content": "x"}]})
        self.assertEqual(status, 401)


class TestRouterRegistration(unittest.TestCase):

    def test_route_is_registered(self):
        from routes import creer_router
        func, _ = creer_router().resoudre("POST", "/api/conseiller/chat")
        self.assertEqual(func.__name__, "conseiller_chat")

# ---------------------------------------------------------------------------
# #123: advisor chat scenarios (no result, unknown question, unverified price,
# unavailable service, alternatives, supplier down, bounded loop, trace actor).
# ---------------------------------------------------------------------------


class FixedSupplier:
    """Returns a given search response and records each call."""

    def __init__(self, resultats):
        self.resultats = resultats
        self.calls = []

    def rechercher(self, criteres):
        self.calls.append(criteres)
        return {"source_label": "Serveur fictif DÉTOUR",
                "consulte_le": "2026-10-23T08:00:00+00:00",
                "resultats": json.loads(json.dumps(self.resultats))}


def _service(service_id, **fields):
    service = {"id": service_id, "nom": service_id, "type": "hebergement",
               "prix_unitaire_eur": 88, "prix_total_eur": 176, "disponible": True,
               "places_restantes": 8}
    service.update(fields)
    return service


class TestAdvisorChatScenarios(unittest.TestCase):

    def _agent(self, supplier):
        return Agent(supplier, DemandStore(None), api_key="cle", model="m")

    def _search_once(self, resultats):
        """One search turn; return the result and what the model received."""
        supplier = FixedSupplier(resultats)
        agent = self._agent(supplier)
        sent = _scripted(agent, [_tool_call(ARGS), {"role": "assistant", "content": "ok"}])
        result = agent.chat_conseiller([{"role": "user", "content": "Vérifie Lyon"}])
        payload = json.loads(sent[1]["conversation"][-1]["content"])
        return result, payload, supplier

    def test_search_with_no_result(self):
        result, payload, supplier = self._search_once([])
        self.assertEqual(len(supplier.calls), 1)
        self.assertEqual(payload["resultats"], [])
        self.assertEqual(result["recherche"]["resultats"], [])
        self.assertEqual(result["trace"]["tool_calls"][0]["statut"], "ok")

    def test_unknown_question_gets_an_answer_without_search(self):
        supplier = FixedSupplier([_service("hotel-lyon-01")])
        agent = self._agent(supplier)
        _scripted(agent, [{"role": "assistant",
                           "content": "Je ne peux pas vérifier cela au catalogue."}])
        result = agent.chat_conseiller([{"role": "user", "content": "Quelle météo à Lyon ?"}])
        self.assertEqual(result["reply"], "Je ne peux pas vérifier cela au catalogue.")
        self.assertEqual(supplier.calls, [])
        self.assertIsNone(result["recherche"])
        self.assertEqual(result["trace"]["tool_calls"], [])

    def test_unverified_price_is_not_invented(self):
        result, payload, _ = self._search_once(
            [_service("hotel-lyon-01", prix_unitaire_eur=None, prix_total_eur=None)])
        self.assertIsNone(payload["resultats"][0]["prix_unitaire_eur"])
        self.assertIsNone(payload["resultats"][0]["prix_total_eur"])
        self.assertIsNone(result["recherche"]["resultats"][0]["prix_unitaire_eur"])

    def test_unavailable_activity_stays_unavailable(self):
        result, payload, _ = self._search_once(
            [_service("activite-lyon-01", type="activite", disponible=False,
                      places_restantes=0)])
        self.assertIs(payload["resultats"][0]["disponible"], False)
        self.assertEqual(payload["resultats"][0]["places_restantes"], 0)
        self.assertIs(result["recherche"]["resultats"][0]["disponible"], False)

    def test_alternatives_come_only_from_server_data(self):
        result, payload, _ = self._search_once(
            [_service("hotel-lyon-01", disponible=False, places_restantes=0),
             _service("hotel-lyon-02", prix_unitaire_eur=95, prix_total_eur=190)])
        ids = [service["id"] for service in payload["resultats"]]
        self.assertEqual(ids, ["hotel-lyon-01", "hotel-lyon-02"])
        self.assertEqual([s["id"] for s in result["recherche"]["resultats"]], ids)

    def test_supplier_down_is_explained(self):
        supplier = RecordingSupplier(SupplierError("timeout", status=503))
        agent = self._agent(supplier)
        sent = _scripted(agent, [_tool_call(ARGS),
                                 {"role": "assistant", "content": "Je n'ai pas pu vérifier."}])
        result = agent.chat_conseiller([{"role": "user", "content": "Vérifie Lyon"}])
        payload = json.loads(sent[1]["conversation"][-1]["content"])
        self.assertEqual(payload["erreur"], "La vérification n'a pas abouti.")
        self.assertIn("réessayer", payload["consigne"])
        self.assertNotIn("timeout", json.dumps(payload))
        self.assertNotEqual(result["trace"]["tool_calls"][0]["statut"], "ok")
        self.assertIsNone(result["recherche"])
        self.assertEqual(result["reply"], "Je n'ai pas pu vérifier.")

    def test_tool_loop_is_bounded(self):
        """The chat always ends: after the last allowed search, the model must answer."""
        supplier = FixedSupplier([_service("hotel-lyon-01")])
        agent = self._agent(supplier)
        sent = _scripted(agent, [_tool_call(ARGS)] * MAX_TOOL_ITERATIONS
                         + [{"role": "assistant", "content": "Voici le résumé."}])
        result = agent.chat_conseiller([{"role": "user", "content": "Vérifie Lyon"}])
        self.assertEqual(result["reply"], "Voici le résumé.")
        self.assertEqual(len(supplier.calls), MAX_TOOL_ITERATIONS)
        self.assertFalse(sent[-1]["with_tools"])

    def test_trace_marks_the_assistant_and_holds_no_key(self):
        supplier = FixedSupplier([_service("hotel-lyon-01")])
        agent = Agent(supplier, DemandStore(None), api_key="cle-tres-secrete", model="m")
        _scripted(agent, [_tool_call(ARGS), {"role": "assistant", "content": "ok"}])
        trace = agent.chat_conseiller([{"role": "user", "content": "Vérifie Lyon"}])["trace"]
        self.assertEqual(trace["acteur"], "assistant_conseiller")
        self.assertTrue(trace["simulation"])
        self.assertNotIn("decisions", trace)
        self.assertNotIn("cle-tres-secrete", json.dumps(trace))

# ---------------------------------------------------------------------------
# #123 part 2: the required workflow (#114) — the assistant drafts, the advisor
# reviews, edits and confirms; nothing reaches the traveler before that.
# ---------------------------------------------------------------------------

class DraftAgent(FakeAgentWithGeneration):
    """Generates a draft like the real agent and answers the advisor chat."""

    def chat_conseiller(self, messages, demande_id=None):
        return FakeAdvisorAgent().chat_conseiller(messages, demande_id)


class TestDraftWorkflow(unittest.TestCase):

    def setUp(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        self.team_key = "cle-" + secrets.token_urlsafe(12)
        self.store = DemandStore(Path(tmp) / "demandes.json")
        self.users = UserStore(Path(tmp) / "users.json")
        self.props = PropositionStore(Path(tmp) / "propositions.json")
        handler = make_handler(self.store, FakeSupplier(), DraftAgent(),
                               users=self.users, team_key=self.team_key,
                               propositions=self.props)
        server, self.base = demarrer(handler)
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)

    def _advisor(self):
        client = ClientHTTP(self.base)
        client.post("/api/login-conseiller", {"cle": self.team_key, "prenom": "Camille"})
        return client

    def _traveler_request(self):
        """A traveler and their own request; return (client, request id)."""
        client = ClientHTTP(self.base)
        client.post("/api/register", {"email": "voyageur@test.fr", "nom": "Voyageur",
                                      "mot_de_passe": "motdepasse"})
        user_id = self.users.authentifier("voyageur@test.fr", "motdepasse")["id"]
        return client, self.store.creer({**VALIDE, "user_id": user_id})["id"]

    def _generate(self, advisor, dem_id):
        status, data, _ = advisor.post(f"/api/demandes/{dem_id}/propositions/generer", {})
        self.assertEqual(status, 201)
        return data["proposition"]

    def _visible_ids(self, traveler):
        _, data, _ = traveler.get("/api/mes-propositions")
        return [p["id"] for p in data["propositions"]]

    def test_generated_draft_is_stamped_and_stays_a_draft(self):
        _, dem_id = self._traveler_request()
        draft = self._generate(self._advisor(), dem_id)
        self.assertEqual(draft["genere_par"], "assistant")
        self.assertEqual(draft["statut"], "brouillon")
        self.assertEqual(draft["message_voyageur"], "Bonjour, c'est un brouillon.")
        self.assertEqual(draft.get("decisions_statut", []), [])

    def test_traveler_never_sees_an_unreviewed_draft(self):
        traveler, dem_id = self._traveler_request()
        draft = self._generate(self._advisor(), dem_id)
        self.assertNotIn(draft["id"], self._visible_ids(traveler))
        status, _, _ = traveler.get(f"/api/propositions/{draft['id']}")
        self.assertEqual(status, 404)

    def test_advisor_edit_marks_the_draft_as_advisor_content(self):
        _, dem_id = self._traveler_request()
        advisor = self._advisor()
        draft = self._generate(advisor, dem_id)
        status, data, _ = advisor.patch(f"/api/propositions/{draft['id']}", {
            "titre": "Week-end relu", "description": draft["description"],
            "message_voyageur": "Bonjour, je vous ai préparé ce week-end. Camille",
            "prestations": draft["prestations"]})
        self.assertEqual(status, 200)
        self.assertEqual(data["proposition"]["genere_par"], "conseiller")
        self.assertEqual(data["proposition"]["statut"], "brouillon")

    def test_advisor_confirmation_sends_and_is_journaled(self):
        traveler, dem_id = self._traveler_request()
        advisor = self._advisor()
        draft = self._generate(advisor, dem_id)
        status, data, _ = advisor.post(f"/api/propositions/{draft['id']}/accepter", {})
        self.assertEqual(status, 200)
        self.assertEqual(data["proposition"]["statut"], "envoyee")
        decision = data["proposition"]["decisions_statut"][-1]
        self.assertEqual(decision["action"], "accepter")
        self.assertEqual(decision["par"], "Camille")
        self.assertIn(draft["id"], self._visible_ids(traveler))

    def test_traveler_cannot_generate_edit_or_confirm(self):
        traveler, dem_id = self._traveler_request()
        draft = self._generate(self._advisor(), dem_id)
        for status in (
            traveler.post(f"/api/demandes/{dem_id}/propositions/generer", {})[0],
            traveler.patch(f"/api/propositions/{draft['id']}", {
                "titre": "x", "description": "x", "prestations": []})[0],
            traveler.post(f"/api/propositions/{draft['id']}/accepter", {})[0],
        ):
            self.assertEqual(status, 401)
        self.assertEqual(self.props.obtenir(draft["id"])["statut"], "brouillon")

    def test_advisor_chat_never_confirms_a_draft(self):
        """Talking to the assistant never sends the draft (no animation trigger)."""
        _, dem_id = self._traveler_request()
        draft = self._generate(self._advisor(), dem_id)
        status, data, _ = self._advisor().post("/api/conseiller/chat", {
            "messages": [{"role": "user", "content": "Envoie la proposition au voyageur"}],
            "demande_id": dem_id})
        self.assertEqual(status, 200)
        self.assertNotIn("proposition", data)
        record = self.props.obtenir(draft["id"])
        self.assertEqual(record["statut"], "brouillon")
        self.assertEqual(record.get("decisions_statut", []), [])


# ---------------------------------------------------------------------------
# #123 part 3: the trace separates agent suggestions from advisor decisions (#119).
# ---------------------------------------------------------------------------


class TestTraceSeparation(unittest.TestCase):

    def _chat(self, resultats, reply="Voici ce que j'ai vérifié."):
        agent = Agent(FixedSupplier(resultats), DemandStore(None), api_key="cle", model="m")
        _scripted(agent, [_tool_call(ARGS), {"role": "assistant", "content": reply}])
        result = agent.chat_conseiller([{"role": "user", "content": "Vérifie Lyon"}])
        return result["trace"]["conseiller_trace"]

    def test_roles_are_written_in_the_trace(self):
        separation = self._chat([_service("hotel-lyon-01")])["separation"]
        self.assertEqual(separation["agent_role"], "suggest")
        self.assertEqual(separation["advisor_role"], "decide")

    def test_search_and_checks_are_recorded(self):
        ctrace = self._chat([_service("hotel-lyon-01"),
                             _service("activite-lyon-01", type="activite",
                                      disponible=False, places_restantes=0)])
        self.assertTrue(ctrace["search_performed"])
        self.assertTrue(ctrace["data_returned"])
        self.assertEqual([c["prestation_id"] for c in ctrace["price_checks"]],
                         ["hotel-lyon-01", "activite-lyon-01"])
        self.assertEqual(ctrace["availability_checks"][1],
                         {"prestation_id": "activite-lyon-01", "disponible": False})

    def test_empty_search_is_not_shown_as_data(self):
        ctrace = self._chat([])
        self.assertTrue(ctrace["search_performed"])
        self.assertFalse(ctrace["data_returned"])

    def test_the_reply_is_a_suggestion_of_the_agent(self):
        ctrace = self._chat([_service("hotel-lyon-01")])
        self.assertEqual(ctrace["agent_suggestions"][0]["content"],
                         "Voici ce que j'ai vérifié.")
        self.assertTrue(all(s["actor"] == "agent" for s in ctrace["suggestions"]))

    def test_the_agent_never_fills_the_advisor_side(self):
        ctrace = self._chat([_service("hotel-lyon-01")],
                            reply="J'ai confirmé et envoyé la proposition.")
        self.assertEqual(ctrace["decisions"], [])
        self.assertEqual(ctrace["advisor_edits"], [])
        self.assertIsNone(ctrace["advisor_review"])
        self.assertIsNone(ctrace["advisor_confirmation"])

    def test_advisor_decisions_stay_in_the_proposal_journal(self):
        """The advisor decides on the proposal; the chat trace never holds it."""
        props = PropositionStore(None)
        prop = props.creer("dem_123", {"titre": "Lyon", "description": "",
                                       "genere_par": "assistant", "prestations": []})
        ctrace = self._chat([_service("hotel-lyon-01")])
        decided = props.decider(prop["id"], "accepter", "Camille", None, None)
        self.assertEqual(decided["decisions_statut"][-1]["par"], "Camille")
        self.assertEqual(ctrace["decisions"], [])

    def test_saved_trace_keeps_the_separation_and_no_key(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        team_key = "cle-" + secrets.token_urlsafe(12)
        agent = Agent(FixedSupplier([_service("hotel-lyon-01")]), DemandStore(None),
                      api_key="cle-tres-secrete", model="m")
        _scripted(agent, [_tool_call(ARGS), {"role": "assistant", "content": "ok"}])
        handler = make_handler(DemandStore(Path(tmp) / "demandes.json"), FakeSupplier(), agent,
                               users=UserStore(Path(tmp) / "users.json"), team_key=team_key,
                               propositions=PropositionStore(Path(tmp) / "propositions.json"),
                               traces_dir=Path(tmp) / "traces")
        server, base = demarrer(handler)
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        advisor = ClientHTTP(base)
        advisor.post("/api/login-conseiller", {"cle": team_key, "prenom": "Camille"})
        status, data, _ = advisor.post("/api/conseiller/chat",
                                       {"messages": [{"role": "user", "content": "Vérifie"}]})
        self.assertEqual(status, 200)
        saved = list((Path(tmp) / "traces").glob("*.json"))
        self.assertEqual(len(saved), 1)
        text = saved[0].read_text(encoding="utf-8")
        self.assertEqual(json.loads(text)["conseiller_trace"]["separation"]["advisor_role"],
                         "decide")
        self.assertEqual(data["trace"]["conseiller_trace"]["decisions"], [])
        self.assertNotIn("cle-tres-secrete", text)
        self.assertNotIn(team_key, text)

if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Unit tests: a departure today or in the past is refused (#145)."""

import sys
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

CONSEILLER_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(CONSEILLER_ROOT))

from agent import Agent
from store import DemandStore, ValidationError, champs_manquants, valider_demande
from test_conseiller import VALIDE

# Fixed clock: "today" is 22 October 2026 for every test of this file.
TODAY = date(2026, 10, 22)


def request(departure, back="2026-10-30"):
    return {**VALIDE, "date_depart": departure, "date_retour": back}


@mock.patch("store.business_today", return_value=TODAY)
class ValidateRequestTest(unittest.TestCase):
    def test_yesterday_is_refused(self, _today):
        with self.assertRaises(ValidationError):
            valider_demande(request("2026-10-21"))

    def test_today_is_refused(self, _today):
        with self.assertRaises(ValidationError):
            valider_demande(request("2026-10-22"))

    def test_tomorrow_is_accepted(self, _today):
        self.assertEqual(valider_demande(request("2026-10-23"))["date_depart"], "2026-10-23")


@mock.patch("store.business_today", return_value=TODAY)
class MissingFieldsTest(unittest.TestCase):
    def test_yesterday_is_a_missing_field(self, _today):
        self.assertIn("date_depart", champs_manquants(request("2026-10-21")))

    def test_today_is_a_missing_field(self, _today):
        self.assertIn("date_depart", champs_manquants(request("2026-10-22")))

    def test_tomorrow_is_not_missing(self, _today):
        self.assertNotIn("date_depart", champs_manquants(request("2026-10-23")))


@mock.patch("store.business_today", return_value=TODAY)
class AgentAnswersTest(unittest.TestCase):
    """The agent path: a past departure is refused and nothing is saved."""

    def setUp(self):
        self.store = DemandStore(None)

    def test_past_departure_is_not_saved(self, _today):
        answers = {key: value for key, value in request("2026-10-21").items()
                   if key != "user_id"}
        with self.assertRaises(ValidationError):
            self.store.enregistrer_reponses(None, answers, user_id="traveler-1")
        self.assertEqual(self.store.lister(), [])

    def test_departure_today_is_not_saved(self, _today):
        answers = {key: value for key, value in request("2026-10-22").items()
                   if key != "user_id"}
        with self.assertRaises(ValidationError):
            self.store.enregistrer_reponses(None, answers, user_id="traveler-1")
        self.assertEqual(self.store.lister(), [])

    def test_form_with_past_departure_is_refused(self, _today):
        with self.assertRaises(ValidationError):
            self.store.creer(request("2026-10-21"))
        self.assertEqual(self.store.lister(), [])

    def test_return_date_alone_is_not_checked_against_today(self, _today):
        # Only the departure must be after today; the return follows the departure.
        record, _ = self.store.enregistrer_reponses(
            None, {"date_retour": "2026-10-30"}, user_id="traveler-1")
        self.assertEqual(record["demande"]["date_retour"], "2026-10-30")


class AgentKnowsTodayTest(unittest.TestCase):
    """The agent gets today's date in its prompt, to refuse a past departure at once."""

    def test_system_prompt_gives_today_and_the_rule(self):
        agent = Agent(supplier=None, store=DemandStore(None), api_key="test-key")
        seen = []

        def fake_model(conversation, with_tools=True):
            seen.append(conversation)
            return {"role": "assistant", "content": "Bonjour !"}

        with mock.patch("agent.business_today", return_value=TODAY), \
                mock.patch.object(agent, "_call_model", side_effect=fake_model):
            agent.chat([{"role": "user", "content": "Bonjour"}])
        system_prompt = seen[0][0]["content"]
        self.assertIn("Nous sommes le 2026-10-22", system_prompt)
        self.assertIn("aujourd'hui ou avant", system_prompt)


if __name__ == "__main__":
    unittest.main()
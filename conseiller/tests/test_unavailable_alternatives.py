#!/usr/bin/env python3
"""Tests for the prompt rule on unavailable requests and nearby alternatives (#155).

The model, not the program, picks the alternative: these tests check that the
system prompt gives it the rule and its limits.
"""

import sys
import unittest
from pathlib import Path

CONSEILLER_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(CONSEILLER_ROOT))

from agent import SYSTEM_PROMPT


def _section(title):
    """Return the prompt section headed by `title`, up to the next one."""
    start = SYSTEM_PROMPT.index("\n" + title + "\n") + 1
    end = SYSTEM_PROMPT.find("\n\n", start)
    return SYSTEM_PROMPT[start:end if end != -1 else None]


class TestUnavailableRule(unittest.TestCase):

    def setUp(self):
        self.rule = _section("QUAND CE N'EST PAS DISPONIBLE")

    def test_says_what_is_unavailable_first(self):
        self.assertIn("dis-le d'abord clairement", self.rule)

    def test_alternatives_must_be_nearby(self):
        self.assertIn("alternatives proches", self.rule)
        self.assertIn("environ 1 h de trajet au maximum", self.rule)

    def test_far_alternative_is_refused_with_the_christmas_market_example(self):
        self.assertIn("Ne propose jamais une alternative éloignée", self.rule)
        self.assertIn("Béthune convient", self.rule)
        self.assertIn("Paris non", self.rule)

    def test_outside_catalogue_alternative_has_no_price_or_availability(self):
        self.assertIn("le conseiller la vérifiera", self.rule)
        self.assertIn("ni prix, ni horaire, ni disponibilité", self.rule)

    def test_catalogue_alternative_comes_first(self):
        self.assertIn("propose-la en priorité, avec son prix vérifié", self.rule)

    def test_says_so_when_nothing_nearby_exists(self):
        self.assertIn("Je n'ai pas d'alternative proche à vous proposer", self.rule)

    def test_ends_with_a_question(self):
        self.assertIn("Termine par une question courte", self.rule)


class TestAbsoluteRules(unittest.TestCase):

    def test_never_invent_rule_allows_only_labelled_nearby_ideas(self):
        rules = _section("RÈGLES ABSOLUES")
        self.assertIn("N'invente jamais un prix, une disponibilité", rules)
        self.assertIn("idée à vérifier, sans prix ni disponibilité", rules)


if __name__ == "__main__":
    unittest.main()

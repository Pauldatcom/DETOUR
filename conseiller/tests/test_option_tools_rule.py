#!/usr/bin/env python3
"""The models never get option or reservation tools, nor the approval key (#94)."""

import json
import sys
import unittest
from pathlib import Path

CONSEILLER_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(CONSEILLER_ROOT))

from agent import (
    ADVISOR_SYSTEM_PROMPT,
    ADVISOR_TOOL_DEFINITION,
    ADVISOR_TOOL_NAME,
    SYSTEM_PROMPT,
    TOOL_DEFINITION,
)
from utils import TOOL_NAME

TOOLS = (TOOL_DEFINITION, ADVISOR_TOOL_DEFINITION)


class OptionToolsRuleTest(unittest.TestCase):
    def test_each_assistant_has_only_its_read_tool(self):
        self.assertEqual(TOOL_NAME, "chercher_voyages")
        self.assertEqual(TOOL_DEFINITION["function"]["name"], TOOL_NAME)
        self.assertEqual(ADVISOR_TOOL_NAME, "verifier_prestations")
        self.assertEqual(ADVISOR_TOOL_DEFINITION["function"]["name"], ADVISOR_TOOL_NAME)

    def test_no_tool_has_an_option_or_reservation_argument(self):
        for tool in TOOLS:
            for name in tool["function"]["parameters"]["properties"]:
                self.assertNotIn("option", name)
                self.assertNotIn("reserv", name)

    def test_the_approval_key_is_never_given_to_a_model(self):
        texts = [SYSTEM_PROMPT, ADVISOR_SYSTEM_PROMPT]
        texts += [json.dumps(tool, ensure_ascii=False) for tool in TOOLS]
        for text in texts:
            self.assertNotIn("X-Approval-Key", text)
            self.assertNotIn("demo-approval", text)


if __name__ == "__main__":
    unittest.main()
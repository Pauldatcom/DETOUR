#!/usr/bin/env python3
"""The default model must be free: the course forbids paid models (#93)."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils import DEFAULT_MODEL


class TestDefaultModel(unittest.TestCase):

    def test_default_model_is_free(self):
        self.assertTrue(DEFAULT_MODEL.endswith(":free"),
                        f"{DEFAULT_MODEL} is not a free OpenRouter model.")


if __name__ == "__main__":
    unittest.main()
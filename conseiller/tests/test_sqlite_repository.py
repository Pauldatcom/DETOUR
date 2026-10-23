#!/usr/bin/env python3
"""Tests for SqliteRepository (ticket #197).

Covers CRUD operations, upsert behavior, destinations seeding,
and in-memory mode (no path → no persistence).
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

CONSEILLER_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(CONSEILLER_ROOT))

from sqlite_repository import SqliteRepository


class TestSqliteRepositoryCrud(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.path = Path(self.tmpdir) / "test.db"
        self.repo = SqliteRepository(self.path)

    def test_save_and_load_demande(self):
        record = {"id": "dem_1", "statut": "nouvelle",
                  "demande": {"user_id": "u1", "destination": "Lyon"}}
        self.repo.save_demande(record)
        loaded = self.repo.load_all_demandes()
        self.assertIn("dem_1", loaded)
        self.assertEqual(loaded["dem_1"]["statut"], "nouvelle")

    def test_upsert_demande_replaces(self):
        self.repo.save_demande({"id": "dem_1", "statut": "nouvelle",
                                 "demande": {"user_id": "u1"}})
        self.repo.save_demande({"id": "dem_1", "statut": "a_analyser",
                                 "demande": {"user_id": "u1"}})
        loaded = self.repo.load_all_demandes()
        self.assertEqual(loaded["dem_1"]["statut"], "a_analyser")

    def test_delete_demande(self):
        self.repo.save_demande({"id": "dem_1", "statut": "nouvelle"})
        self.repo.delete_demande("dem_1")
        self.assertNotIn("dem_1", self.repo.load_all_demandes())

    def test_save_and_load_proposition(self):
        record = {"id": "prop_1", "demande_id": "dem_1", "statut": "brouillon",
                  "version": 1}
        self.repo.save_proposition(record)
        loaded = self.repo.load_all_propositions()
        self.assertIn("prop_1", loaded)
        self.assertEqual(loaded["prop_1"]["statut"], "brouillon")

    def test_upsert_proposition_replaces(self):
        self.repo.save_proposition({"id": "prop_1", "statut": "brouillon",
                                    "version": 1})
        self.repo.save_proposition({"id": "prop_1", "statut": "envoyee",
                                    "version": 1})
        loaded = self.repo.load_all_propositions()
        self.assertEqual(loaded["prop_1"]["statut"], "envoyee")

    def test_delete_proposition(self):
        self.repo.save_proposition({"id": "prop_1", "statut": "brouillon"})
        self.repo.delete_proposition("prop_1")
        self.assertNotIn("prop_1", self.repo.load_all_propositions())

    def test_persistence_across_reopen(self):
        self.repo.save_demande({"id": "dem_1", "statut": "nouvelle"})
        self.repo.conn.close()
        repo2 = SqliteRepository(self.path)
        loaded = repo2.load_all_demandes()
        self.assertIn("dem_1", loaded)


class TestSqliteRepositoryDestinations(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.dataset = Path(self.tmpdir) / "dataset.json"
        self.dataset.write_text(json.dumps({
            "destinations": [
                {"id": "DST-001", "name": "Nantes", "country": "France",
                 "region": "Pays de la Loire", "theme": "culture",
                 "description": "Nantes culture.",
                 "imageUrl": "https://img/nantes",
                 "imageAlt": "Nantes", "latitude": 47.21,
                 "longitude": -1.55, "featured": True},
                {"id": "DST-002", "name": "Lyon", "country": "France",
                 "region": "Auvergne-Rhône-Alpes", "theme": "gastronomie",
                 "description": "Lyon food.",
                 "imageUrl": "https://img/lyon",
                 "imageAlt": "Lyon", "featured": False},
            ]
        }), encoding="utf-8")
        self.repo = SqliteRepository(Path(self.tmpdir) / "test.db")

    def test_seed_populates(self):
        count = self.repo.seed_destinations(self.dataset)
        self.assertEqual(count, 2)
        rows = self.repo.list_destinations()
        self.assertEqual(len(rows), 2)

    def test_seed_idempotent(self):
        self.repo.seed_destinations(self.dataset)
        self.repo.seed_destinations(self.dataset)
        self.assertEqual(len(self.repo.list_destinations()), 2)

    def test_list_filter_theme(self):
        self.repo.seed_destinations(self.dataset)
        culture = self.repo.list_destinations(theme="culture")
        self.assertEqual([r["id"] for r in culture], ["DST-001"])

    def test_list_filter_featured(self):
        self.repo.seed_destinations(self.dataset)
        featured = self.repo.list_destinations(featured_only=True)
        self.assertEqual([r["id"] for r in featured], ["DST-001"])

    def test_list_no_filter_returns_all(self):
        self.repo.seed_destinations(self.dataset)
        all_rows = self.repo.list_destinations()
        self.assertEqual(len(all_rows), 2)


class TestSqliteRepositoryInMemory(unittest.TestCase):

    def test_no_path_returns_empty_dicts(self):
        repo = SqliteRepository(None)
        self.assertEqual(repo.load_all_demandes(), {})
        self.assertEqual(repo.load_all_propositions(), {})
        self.assertEqual(repo.list_destinations(), [])
        self.assertIsNone(repo.conn)

    def test_save_demande_no_path_is_noop(self):
        repo = SqliteRepository(None)
        repo.save_demande({"id": "dem_1", "statut": "nouvelle"})
        self.assertEqual(repo.load_all_demandes(), {})


if __name__ == "__main__":
    unittest.main()
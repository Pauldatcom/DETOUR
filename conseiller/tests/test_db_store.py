#!/usr/bin/env python3
"""Tests unittest pour la persistance SQLite de DÉTOUR (ticket #89)."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

CONSEILLER_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(CONSEILLER_ROOT))

import db
from propositions import PropositionStore
from store import DemandStore


VALIDE = {
    "conseiller": "Alice",
    "type_voyage": "trek-randonnee",
    "destination": "Nantes",
    "date_depart": "2026-11-07",
    "date_retour": "2026-11-09",
    "nombre_voyageurs": 2,
    "has_enfants": True,
    "nombre_enfants": 1,
    "budget_max_par_personne": 500,
    "niveau_aventure": "modere",
    "besoin_guide": True,
    "activites": ["créatif", "extérieur"],
    "contraintes": "allergie aux arachides",
}


class TestDbConnect(unittest.TestCase):
    """Schema creation must be idempotent and survive reopen."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.path = Path(self.tmpdir) / "detour.db"

    def test_connect_creates_schema(self):
        conn = db.connect(self.path)
        tables = {row["name"] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
        conn.close()
        self.assertTrue({"demandes", "propositions", "destinations"} <= tables)

    def test_connect_twice_is_a_noop(self):
        conn = db.connect(self.path)
        conn.close()
        conn = db.connect(self.path)
        tables = {row["name"] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
        conn.close()
        self.assertTrue({"demandes", "propositions", "destinations"} <= tables)

    def test_connect_creates_parent_directory(self):
        nested = Path(self.tmpdir) / "sub" / "dir" / "detour.db"
        conn = db.connect(nested)
        conn.close()
        self.assertTrue(nested.exists())


class TestDemandStoreSqlite(unittest.TestCase):
    """DemandStore keeps its public interface with SQLite persistence."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.path = Path(self.tmpdir) / "detour.db"

    def test_creer_persiste_across_reopen(self):
        store = DemandStore(self.path)
        record = store.creer(dict(VALIDE))
        self.assertTrue(record["id"].startswith("dem_"))
        # A second store on the same file must see the persisted record.
        store2 = DemandStore(self.path)
        fetched = store2.obtenir(record["id"])
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["demande"]["destination"], "Nantes")
        self.assertEqual(len(store2.lister()), 1)

    def test_mutation_persists(self):
        store = DemandStore(self.path)
        record = store.creer(dict(VALIDE))
        updated, _ = store.enregistrer_reponses(
            record["id"], {"budget_max_par_personne": 450}, user_id="u1")
        self.assertEqual(updated["demande"]["budget_max_par_personne"], 450)
        store2 = DemandStore(self.path)
        fetched = store2.obtenir(record["id"])
        self.assertEqual(fetched["demande"]["budget_max_par_personne"], 450)

    def test_in_memory_mode_unchanged(self):
        store = DemandStore(None)
        record = store.creer(dict(VALIDE))
        self.assertIsNotNone(store.obtenir(record["id"]))
        self.assertIsNone(store.conn)

    def test_sqlite_row_metadata_is_extracted(self):
        store = DemandStore(self.path)
        record = store.creer({**VALIDE, "user_id": "u1"})
        row = store.conn.execute(
            "SELECT statut, user_id, data FROM demandes WHERE id = ?",
            (record["id"],)).fetchone()
        self.assertEqual(row["statut"], "a_analyser")
        self.assertEqual(row["user_id"], "u1")
        payload = json.loads(row["data"])
        self.assertEqual(payload["id"], record["id"])


class TestPropositionStoreSqlite(unittest.TestCase):
    """PropositionStore keeps its public interface with SQLite persistence."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.path = Path(self.tmpdir) / "detour.db"
        self.demand_store = DemandStore(self.path)
        self.store = PropositionStore(self.path)

    def test_creer_persiste_across_reopen(self):
        dem = self.demand_store.creer(dict(VALIDE))
        prop = self.store.creer(dem["id"], {"titre": "T", "description": "D",
                                            "prestations": []}, conseiller="Alice")
        store2 = PropositionStore(self.path)
        fetched = store2.obtenir(prop["id"])
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["titre"], "T")
        self.assertEqual(len(store2.lister()), 1)

    def test_supprimer_persists(self):
        dem = self.demand_store.creer(dict(VALIDE))
        prop = self.store.creer(dem["id"], {"titre": "T", "description": "D",
                                            "prestations": []})
        self.assertTrue(self.store.supprimer(prop["id"]))
        store2 = PropositionStore(self.path)
        self.assertEqual(store2.lister(), [])

    def test_in_memory_mode_unchanged(self):
        store = PropositionStore(None)
        dem = DemandStore(None).creer(dict(VALIDE))
        prop = store.creer(dem["id"], {"titre": "T", "description": "D",
                                       "prestations": []})
        self.assertIsNotNone(store.obtenir(prop["id"]))
        self.assertIsNone(store.conn)


class TestSeedDestinations(unittest.TestCase):
    """The destinations table is seeded from the enriched dataset JSON."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.dataset = Path(self.tmpdir) / "dataset.json"
        self.dataset.write_text(json.dumps({
            "destinations": [
                {"id": "DST-001", "name": "Paris", "country": "France",
                 "region": "Europe", "theme": "culture",
                 "description": "Culture in Paris.",
                 "imageUrl": "https://images.unsplash.com/photo-1",
                 "imageAlt": "Paris skyline", "latitude": 48.85,
                 "longitude": 2.35, "featured": True},
                {"id": "DST-002", "name": "Lisbonne", "country": "Portugal",
                 "region": "Europe", "theme": "plage",
                 "description": "Beaches in Lisbon.",
                 "imageUrl": "https://images.unsplash.com/photo-2",
                 "imageAlt": "Lisbon street", "featured": False},
            ]
        }), encoding="utf-8")
        self.db_path = Path(self.tmpdir) / "detour.db"
        self.conn = db.connect(self.db_path)

    def tearDown(self):
        self.conn.close()

    def test_seed_populates_destinations(self):
        count = db.seed_destinations(self.conn, self.dataset)
        self.assertEqual(count, 2)
        rows = db.lister_destinations(self.conn)
        self.assertEqual([r["id"] for r in rows], ["DST-001", "DST-002"])
        self.assertEqual(rows[0]["name"], "Paris")
        self.assertEqual(rows[0]["imageUrl"], "https://images.unsplash.com/photo-1")
        self.assertEqual(rows[0]["imageAlt"], "Paris skyline")
        self.assertTrue(rows[0]["featured"])
        self.assertFalse(rows[1]["featured"])

    def test_seed_is_idempotent(self):
        db.seed_destinations(self.conn, self.dataset)
        db.seed_destinations(self.conn, self.dataset)
        rows = db.lister_destinations(self.conn)
        self.assertEqual(len(rows), 2)

    def test_lister_filters(self):
        db.seed_destinations(self.conn, self.dataset)
        culture = db.lister_destinations(self.conn, theme="culture")
        self.assertEqual([r["id"] for r in culture], ["DST-001"])
        featured = db.lister_destinations(self.conn, featured_only=True)
        self.assertEqual([r["id"] for r in featured], ["DST-001"])


class TestMigration(unittest.TestCase):
    """The JSON → SQLite migration is idempotent and skips missing files."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.db_path = Path(self.tmpdir) / "detour.db"
        self.demandes_json = Path(self.tmpdir) / "demandes.json"
        self.propositions_json = Path(self.tmpdir) / "propositions.json"
        # A legacy demande record (same shape as the JSON store used to write).
        self.legacy_demande = {
            "id": "dem_legacy1",
            "statut": "a_analyser",
            "cree_le": "2026-01-01T00:00:00+00:00",
            "demande": {
                "type_voyage": "trek-randonnee",
                "destination": "Nantes",
                "date_depart": "2026-11-07",
                "date_retour": "2026-11-09",
                "nombre_voyageurs": 2,
                "has_enfants": True,
                "nombre_enfants": 1,
                "budget_max_par_personne": 500,
                "niveau_aventure": "modere",
                "besoin_guide": True,
                "user_id": "u1",
            },
        }
        self.legacy_proposition = {
            "id": "prop_legacy1",
            "demande_id": "dem_legacy1",
            "statut": "brouillon",
            "version": 1,
            "parente_id": None,
            "cree_le": "2026-01-01T00:00:00+00:00",
            "modifiee_le": "2026-01-01T00:00:00+00:00",
            "conseiller": "Alice",
            "titre": "T",
            "description": "D",
            "prestations": [],
            "prix_total_eur": 0,
            "decisions": [],
        }
        self.demandes_json.write_text(
            json.dumps({"dem_legacy1": self.legacy_demande}), encoding="utf-8")
        self.propositions_json.write_text(
            json.dumps({"prop_legacy1": self.legacy_proposition}), encoding="utf-8")

    def _migrate(self):
        """Run the migration on a fresh connection; returns (n_demandes, n_props)."""
        import migrate
        conn = db.connect(self.db_path)
        try:
            n1 = migrate.migrer_fichier(conn, "demandes", self.demandes_json)
            n2 = migrate.migrer_fichier(conn, "propositions", self.propositions_json)
            return n1, n2
        finally:
            conn.close()

    def test_migration_imports_legacy_records(self):
        n1, n2 = self._migrate()
        self.assertEqual(n1, 1)
        self.assertEqual(n2, 1)
        conn = db.connect(self.db_path)
        try:
            rows = conn.execute("SELECT id, data FROM demandes").fetchall()
            self.assertEqual([r["id"] for r in rows], ["dem_legacy1"])
            self.assertEqual(json.loads(rows[0]["data"])["id"], "dem_legacy1")
            props = conn.execute("SELECT id, demande_id FROM propositions").fetchall()
            self.assertEqual([r["id"] for r in props], ["prop_legacy1"])
            self.assertEqual(props[0]["demande_id"], "dem_legacy1")
        finally:
            conn.close()

    def test_migration_is_idempotent(self):
        self._migrate()
        n1, n2 = self._migrate()
        self.assertEqual(n1, 1)
        self.assertEqual(n2, 1)
        conn = db.connect(self.db_path)
        try:
            self.assertEqual(
                conn.execute("SELECT COUNT(*) FROM demandes").fetchone()[0], 1)
            self.assertEqual(
                conn.execute("SELECT COUNT(*) FROM propositions").fetchone()[0], 1)
        finally:
            conn.close()

    def test_migration_skips_missing_files(self):
        self.demandes_json.unlink()
        self.propositions_json.unlink()
        conn = db.connect(self.db_path)
        try:
            import migrate
            self.assertEqual(migrate.migrer_fichier(conn, "demandes", self.demandes_json), 0)
            self.assertEqual(
                migrate.migrer_fichier(conn, "propositions", self.propositions_json), 0)
        finally:
            conn.close()

    def test_migration_invalid_file_is_ignored(self):
        self.demandes_json.write_text("not json", encoding="utf-8")
        conn = db.connect(self.db_path)
        try:
            import migrate
            with self.assertRaises(json.JSONDecodeError):
                migrate.migrer_fichier(conn, "demandes", self.demandes_json)
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()

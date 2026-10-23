"""Implémentation SQLite de l'interface Repository.

Adapte les fonctions de db.py en respectant le contrat Repository.
Les requêtes SQL restent dans ce module uniquement ; les stores
(DemandStore, PropositionStore) ne connaissent pas le SQL.
"""

import json
import sqlite3
from pathlib import Path

from repository import Repository

_SCHEMA = """
CREATE TABLE IF NOT EXISTS demandes (
    id TEXT PRIMARY KEY,
    statut TEXT NOT NULL DEFAULT '',
    user_id TEXT NOT NULL DEFAULT '',
    data TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_demandes_statut ON demandes (statut);
CREATE INDEX IF NOT EXISTS idx_demandes_user ON demandes (user_id);

CREATE TABLE IF NOT EXISTS propositions (
    id TEXT PRIMARY KEY,
    demande_id TEXT NOT NULL DEFAULT '',
    statut TEXT NOT NULL DEFAULT '',
    version INTEGER NOT NULL DEFAULT 1,
    parente_id TEXT,
    data TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_propositions_demande ON propositions (demande_id);
CREATE INDEX IF NOT EXISTS idx_propositions_statut ON propositions (statut);

CREATE TABLE IF NOT EXISTS destinations (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    country TEXT NOT NULL DEFAULT '',
    region TEXT NOT NULL DEFAULT '',
    theme TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    image_url TEXT NOT NULL DEFAULT '',
    image_alt TEXT NOT NULL DEFAULT '',
    latitude REAL,
    longitude REAL,
    featured INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_destinations_theme ON destinations (theme);
"""

_DESTINATION_COLUMNS = (
    "id", "name", "country", "region", "theme", "description",
    "image_url", "image_alt", "latitude", "longitude", "featured",
)


class SqliteRepository(Repository):
    """Implémentation SQLite de Repository."""

    def __init__(self, path=None):
        self.path = Path(path) if path else None
        self.conn = self._connect(self.path) if self.path else None

    def _connect(self, path):
        if path.parent and not path.parent.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        conn.executescript(_SCHEMA)
        conn.commit()
        return conn

    # --- Demandes ---

    def load_all_demandes(self):
        if not self.conn:
            return {}
        rows = self.conn.execute("SELECT id, data FROM demandes").fetchall()
        return {row["id"]: json.loads(row["data"]) for row in rows}

    def save_demande(self, record):
        if not self.conn:
            return
        with self.conn:
            self.conn.execute(
                "INSERT OR REPLACE INTO demandes (id, statut, user_id, data) "
                "VALUES (?, ?, ?, ?)",
                (record["id"],
                 record.get("statut", ""),
                 ((record.get("demande") or {}).get("user_id") or "").strip(),
                 json.dumps(record, ensure_ascii=False)))

    def delete_demande(self, dem_id):
        if not self.conn:
            return
        with self.conn:
            self.conn.execute("DELETE FROM demandes WHERE id = ?", (dem_id,))

    # --- Propositions ---

    def load_all_propositions(self):
        if not self.conn:
            return {}
        rows = self.conn.execute("SELECT id, data FROM propositions").fetchall()
        return {row["id"]: json.loads(row["data"]) for row in rows}

    def save_proposition(self, record):
        if not self.conn:
            return
        with self.conn:
            self.conn.execute(
                "INSERT OR REPLACE INTO propositions "
                "(id, demande_id, statut, version, parente_id, data) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (record["id"],
                 record.get("demande_id", ""),
                 record.get("statut", ""),
                 record.get("version", 1),
                 record.get("parente_id"),
                 json.dumps(record, ensure_ascii=False)))

    def delete_proposition(self, prop_id):
        if not self.conn:
            return
        with self.conn:
            self.conn.execute("DELETE FROM propositions WHERE id = ?", (prop_id,))

    # --- Destinations ---

    def seed_destinations(self, dataset_path):
        if not self.conn:
            return 0
        data = json.loads(Path(dataset_path).read_text(encoding="utf-8"))
        rows = []
        for dest in data.get("destinations", []):
            rows.append((
                dest.get("id"), dest.get("name", ""), dest.get("country", ""),
                dest.get("region", ""), dest.get("theme", ""),
                dest.get("description", ""), dest.get("imageUrl", ""),
                dest.get("imageAlt", ""), dest.get("latitude"),
                dest.get("longitude"), 1 if dest.get("featured") else 0,
            ))
        if not rows:
            return 0
        placeholders = ", ".join("?" for _ in _DESTINATION_COLUMNS)
        columns = ", ".join(_DESTINATION_COLUMNS)
        with self.conn:
            self.conn.executemany(
                f"INSERT OR REPLACE INTO destinations ({columns}) "
                f"VALUES ({placeholders})", rows)
        return len(rows)

    def list_destinations(self, theme=None, featured_only=False):
        if not self.conn:
            return []
        sql = f"SELECT {', '.join(_DESTINATION_COLUMNS)} FROM destinations"
        clauses, params = [], []
        if theme:
            clauses.append("theme = ?")
            params.append(theme)
        if featured_only:
            clauses.append("featured = 1")
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY id"
        return [{
            "id": row["id"], "name": row["name"], "country": row["country"],
            "region": row["region"], "theme": row["theme"],
            "description": row["description"], "imageUrl": row["image_url"],
            "imageAlt": row["image_alt"], "latitude": row["latitude"],
            "longitude": row["longitude"], "featured": bool(row["featured"]),
        } for row in self.conn.execute(sql, params).fetchall()]
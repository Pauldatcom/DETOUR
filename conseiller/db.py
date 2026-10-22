"""SQLite persistence layer for DÉTOUR (standard library only).

Replaces the per-file JSON stores (`.local/demandes.json`,
`.local/propositions.json`) with a single SQLite database (`.local/detour.db`).
Records are stored as full JSON payloads in a `data` column, with a few
indexed columns extracted for future filtering. The enriched travel dataset
seeds a read-only `destinations` table, so the dataset JSON becomes the
seed source instead of application state.

Usage rules:
- `connect()` creates the schema on an existing or fresh database file, so
  opening the application on an old database is always safe.
- `save_demandes()` / `save_propositions()` sync the whole in-memory dict to
  the database in one transaction, mirroring the previous atomic JSON rewrite.
- `seed_destinations()` is idempotent: rows are upserted by destination id,
  so re-running with the same dataset refreshes instead of duplicating.
"""

import json
import sqlite3
from pathlib import Path

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


def connect(path):
    """Open (and initialize) the DÉTOUR SQLite database at `path`.

    The schema is applied with IF NOT EXISTS statements, so calling connect()
    repeatedly is a no-op for the schema. WAL journaling and a busy timeout
    keep concurrent server threads safe.
    """
    path = Path(path)
    if path.parent and not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.executescript(_SCHEMA)
    conn.commit()
    return conn


def load_demandes(conn):
    """Read every demande record back into a {id: record} dict."""
    rows = conn.execute("SELECT id, data FROM demandes").fetchall()
    return {row["id"]: json.loads(row["data"]) for row in rows}


def save_demandes(conn, demandes):
    """Sync the in-memory demandes dict to the database in one transaction.

    Mirrors the previous atomic JSON rewrite: the table is replaced with the
    current dict contents, so deletions and rewrites are handled uniformly.
    """
    with conn:  # one transaction
        conn.execute("DELETE FROM demandes")
        conn.executemany(
            "INSERT INTO demandes (id, statut, user_id, data) VALUES (?, ?, ?, ?)",
            [(dem_id, record.get("statut", ""),
              ((record.get("demande") or {}).get("user_id") or "").strip(),
              json.dumps(record, ensure_ascii=False))
             for dem_id, record in demandes.items()])


def load_propositions(conn):
    """Read every proposition record back into a {id: record} dict."""
    rows = conn.execute("SELECT id, data FROM propositions").fetchall()
    return {row["id"]: json.loads(row["data"]) for row in rows}


def save_propositions(conn, propositions):
    """Sync the in-memory propositions dict to the database in one transaction."""
    with conn:  # one transaction
        conn.execute("DELETE FROM propositions")
        conn.executemany(
            "INSERT INTO propositions (id, demande_id, statut, version, parente_id, data) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            [(prop_id, record.get("demande_id", ""),
              record.get("statut", ""), record.get("version", 1),
              record.get("parente_id"),
              json.dumps(record, ensure_ascii=False))
             for prop_id, record in propositions.items()])


def seed_destinations(conn, dataset_path):
    """Seed the destinations table from the enriched dataset JSON.

    Idempotent: each destination is upserted by id, so re-running with the
    same dataset only refreshes the rows. Returns the number of rows written.
    """
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
    with conn:  # one transaction
        conn.executemany(
            f"INSERT OR REPLACE INTO destinations ({columns}) VALUES ({placeholders})",
            rows)
    return len(rows)


def lister_destinations(conn, theme=None, featured_only=False):
    """Read destinations back as plain dicts, optionally filtered."""
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
    } for row in conn.execute(sql, params).fetchall()]

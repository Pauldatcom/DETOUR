#!/usr/bin/env python3
"""One-shot migration of the legacy JSON stores to the DÉTOUR SQLite database.

Reads `.local/demandes.json` and `.local/propositions.json` (legacy JSON
persistence) and replaces the matching SQLite tables with their contents via
the same full sync used by the stores. The script is idempotent: records are
keyed by id, so re-running with the same sources yields the same database
state (legacy files become the source of truth for the migration).

Files that do not exist are skipped, so the migration can be run on a fresh
checkout where no legacy state was ever created. The legacy files are left
untouched; deleting them is a manual step once the migration is validated.
Run this before switching the application to SQLite mode.
"""

import argparse
import json
from pathlib import Path

import db

ROOT = Path(__file__).resolve().parent


def migrer_fichier(conn, table, json_path):
    """Upsert every record of one legacy JSON file into `table`.

    Returns the number of records migrated. A missing file migrates nothing.
    """
    path = Path(json_path)
    if not path.exists():
        return 0
    records = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(records, dict) or not records:
        return 0
    if table == "demandes":
        db.save_demandes(conn, records)
        return len(records)
    db.save_propositions(conn, records)
    return len(records)


def main():
    parser = argparse.ArgumentParser(description="Migration JSON → SQLite DÉTOUR")
    parser.add_argument("--db-file", default=str(ROOT / ".local" / "detour.db"))
    parser.add_argument("--demandes-json", default=str(ROOT / ".local" / "demandes.json"))
    parser.add_argument("--propositions-json",
                        default=str(ROOT / ".local" / "propositions.json"))
    parser.add_argument("--seed-dataset", default=str(ROOT / "data" / "travel_agency_dataset.json"),
                        help="Also seed the destinations table (idempotent).")
    args = parser.parse_args()

    conn = db.connect(args.db_file)
    n_demandes = migrer_fichier(conn, "demandes", args.demandes_json)
    n_propositions = migrer_fichier(conn, "propositions", args.propositions_json)
    n_destinations = db.seed_destinations(conn, args.seed_dataset)
    print(f"demandes migrées   : {n_demandes}")
    print(f"propositions migrées : {n_propositions}")
    print(f"destinations seedées : {n_destinations}")
    print(f"base : {args.db_file}")


if __name__ == "__main__":
    main()

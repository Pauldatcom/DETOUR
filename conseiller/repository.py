"""Persistence interface for DÉTOUR.

Defines the common contract for accessing demandes, propositions and
destinations. The SQLite implementation (sqlite_repository.py) covers
the current case; a future PostgreSQL implementation will implement
the same interface.
"""


class Repository:
    """Persistence interface for demandes, propositions and destinations.

    Each method raises NotImplementedError by default. A concrete
    implementation (SqliteRepository, future PostgresRepository) defines
    them all.
    """

    def load_all_demandes(self):
        raise NotImplementedError

    def save_demande(self, record):
        raise NotImplementedError

    def delete_demande(self, dem_id):
        raise NotImplementedError

    def load_all_propositions(self):
        raise NotImplementedError

    def save_proposition(self, record):
        raise NotImplementedError

    def delete_proposition(self, prop_id):
        raise NotImplementedError

    def seed_destinations(self, dataset_path):
        raise NotImplementedError

    def list_destinations(self, theme=None, featured_only=False):
        raise NotImplementedError
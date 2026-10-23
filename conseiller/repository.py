"""Interface de persistance pour DÉTOUR.

Définit le contrat commun pour accéder aux demandes, propositions et
destinations. L'implémentation SQLite (sqlite_repository.py) couvre le
cas actuel ; une future implémentation PostgreSQL implémentera la même
interface.
"""


class Repository:
    """Interface de persistance pour les demandes, propositions et destinations.

    Chaque méthode lève NotImplementedError par défaut. Une implémentation
    concrète (SqliteRepository, future PostgresRepository) les définit toutes.
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
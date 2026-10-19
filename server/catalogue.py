"""Données entièrement fictives, stables pour les exercices WEB3."""

# Date de dernière mise à jour du catalogue de base. Un incident formateur
# la remplace pour la prestation concernée (voir server/app.py).
MIS_A_JOUR_LE_BASE = "2026-10-01T08:00:00+00:00"

PRESTATIONS = [
    {"id": "train-nantes-01", "type": "transport", "nom": "Train vers Nantes", "destination": "Nantes", "prix_unitaire_eur": 48, "capacite": 8, "description": "Trajet fictif aller-retour depuis Paris", "tags": ["train", "sans voiture"], "voyages": ["lune-de-miel", "voyage-familial", "autres"]},
    {"id": "hotel-nantes-01", "type": "hebergement", "nom": "Hôtel des Machines", "destination": "Nantes", "prix_unitaire_eur": 96, "capacite": 6, "description": "Une nuit fictive, tarif par personne", "tags": ["centre-ville"], "voyages": ["lune-de-miel", "voyage-familial", "autres"]},
    {"id": "activite-nantes-01", "type": "activite", "nom": "Atelier de machines imaginaires", "destination": "Nantes", "prix_unitaire_eur": 35, "capacite": 10, "description": "Atelier fictif accessible sans effort sportif", "tags": ["créatif", "intérieur"], "voyages": ["voyage-familial", "autres"]},
    {"id": "train-lyon-01", "type": "transport", "nom": "Train vers Lyon", "destination": "Lyon", "prix_unitaire_eur": 62, "capacite": 10, "description": "Trajet fictif aller-retour depuis Paris", "tags": ["train", "sans voiture"], "voyages": ["lune-de-miel", "voyage-familial", "autres"]},
    {"id": "hotel-lyon-01", "type": "hebergement", "nom": "Hôtel des Lumières", "destination": "Lyon", "prix_unitaire_eur": 88, "capacite": 8, "description": "Une nuit fictive, tarif par personne", "tags": ["centre-ville"], "voyages": ["lune-de-miel", "voyage-familial", "autres"]},
    {"id": "activite-lyon-01", "type": "activite", "nom": "Enquête des traboules", "destination": "Lyon", "prix_unitaire_eur": 29, "capacite": 12, "description": "Jeu de piste fictif en ville", "tags": ["jeu", "extérieur"], "voyages": ["voyage-familial", "autres"]},
    {"id": "train-lille-01", "type": "transport", "nom": "Train vers Lille", "destination": "Lille", "prix_unitaire_eur": 42, "capacite": 12, "description": "Trajet fictif aller-retour depuis Paris", "tags": ["train", "sans voiture"], "voyages": ["lune-de-miel", "voyage-familial", "autres"]},
    {"id": "hotel-lille-01", "type": "hebergement", "nom": "Hôtel du Beffroi", "destination": "Lille", "prix_unitaire_eur": 79, "capacite": 8, "description": "Une nuit fictive, tarif par personne", "tags": ["centre-ville"], "voyages": ["lune-de-miel", "voyage-familial", "autres"]},
    {"id": "activite-lille-01", "type": "activite", "nom": "Fabrique de gaufres", "destination": "Lille", "prix_unitaire_eur": 27, "capacite": 10, "description": "Atelier culinaire fictif", "tags": ["cuisine", "intérieur"], "voyages": ["lune-de-miel", "voyage-familial", "autres"]},
]

for _item in PRESTATIONS:
    _item["mis_a_jour_le"] = MIS_A_JOUR_LE_BASE

BY_ID = {item["id"]: item for item in PRESTATIONS}

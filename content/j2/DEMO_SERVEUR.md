# Démonstration de la source de vérité

**Durée : 8 à 10 min.** Depuis la racine du dépôt, lancer le serveur fictif dans un terminal et garder ce terminal ouvert :

```sh
python3 server/app.py --demo
```

Dans un second terminal, consulter une prestation, puis la disponibilité à une date et pour un groupe précis :

```sh
curl -sS -H 'X-Team-Key: demo-key' 'http://127.0.0.1:8765/api/v1/prestations/train-nantes-01'
curl -sS -H 'X-Team-Key: demo-key' 'http://127.0.0.1:8765/api/v1/disponibilites?prestation_id=train-nantes-01&date=2026-11-07&participants=2'
```

Repérez quatre informations, sans lire tout le JSON :

| Dans quelle réponse ? | Champ | Ce qu'il faut constater |
|---|---|---|
| Fiche prestation | `prix_unitaire_eur` | 48 € par personne dans le catalogue fictif. |
| Disponibilité | `disponible` et `places_restantes` | `true` et 8 places avant toute option. |
| Disponibilité | `prix_total_eur` | 96 € pour deux voyageurs. |
| Disponibilité | `simulation` | `true` : aucune donnée de voyage réel. |

Modifiez ensuite **un seul paramètre** : passez de `participants=2` à `participants=9`. La réponse indique `disponible: false`, mais le total calculé ne signifie pas que neuf places existent. Revenez à deux participants et changez l'identifiant pour `prestation_id=inconnu` : le serveur renvoie une erreur `prestation_not_found`.

Le prix et les places sont vérifiés par la consultation du serveur. Une réponse du modèle seule ne constitue pas cette preuve. Le retour `disponible: true` ne bloque aucune place : cet appel est une lecture.

La [documentation de l'API](../../server/README.md) explique les routes. Dans ce TP, l'agent n'utilise que la route de consultation. La pose d'option et la confirmation sont hors de son contrat.

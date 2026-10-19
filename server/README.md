# DÉTOUR : API de prestations fictives

Ce serveur simule un catalogue de transport, hébergements et activités. Toutes les données, les prix et les réservations sont fictifs.

## Démarrer

Depuis la racine du dépôt :

```bash
python3 server/app.py --demo
```

Le serveur écoute sur `http://127.0.0.1:8765`. Utilisez `demo-key` pour les essais locaux. En classe, le formateur fournit une clé propre à votre équipe. Envoyez-la dans l'en-tête `X-Team-Key` depuis votre programme ; ne l'exposez pas dans une page web.

## Tableau de bord du simulateur

Ouvrez `http://127.0.0.1:8765/dashboard` et saisissez votre clé d'équipe. Vous pouvez parcourir les prestations, choisir une date et un nombre de participants, vérifier le prix et les places, puis copier les réponses JSON. L'onglet **Mon espace** affiche les options et réservations de votre équipe. Actualisez-le après les actions réalisées par votre application ou après un imprévu annoncé par le formateur.

Le tableau de bord est en lecture seule. Pour poser une option, confirmer ou annuler une réservation, utilisez l'API depuis votre programme. La connexion au tableau de bord crée une session de 30 minutes dans un cookie `HttpOnly`, persistée dans le fichier d'état : elle survit aux redémarrages du serveur. La clé saisie n'est pas placée dans l'URL ni conservée dans le navigateur par la page. Sur un réseau partagé, utilisez ce serveur uniquement dans un environnement de confiance ou derrière HTTPS.

## Consulter les offres et les disponibilités

```bash
curl -H 'X-Team-Key: demo-key' 'http://127.0.0.1:8765/api/v1/catalogue?destination=Nantes'
curl -H 'X-Team-Key: demo-key' 'http://127.0.0.1:8765/api/v1/prestations/train-nantes-01'
curl -H 'X-Team-Key: demo-key' 'http://127.0.0.1:8765/api/v1/disponibilites?prestation_id=train-nantes-01&date=2026-11-07&participants=2'
```

Le catalogue accepte les filtres `destination` et `type` (`transport`, `hebergement`, `activite`). Il renvoie un tableau `prestations`. La disponibilité renvoie notamment `disponible`, `places_restantes`, `prix_unitaire_eur` et `prix_total_eur`. Pour la démonstration, `train-nantes-01` coûte 48 € par personne et dispose de 8 places avant toute option ou réservation. Une disponibilité consultée ne bloque pas les places.

## Rechercher des prestations pour une demande

```bash
curl -H 'X-Team-Key: demo-key' \
  'http://127.0.0.1:8765/api/v1/recherche?destination=Nantes&date_depart=2026-11-07&date_retour=2026-11-09&participants=2&budget_max=200&type_voyage=voyage-familial&activites=cr%C3%A9atif'
```

Paramètres : `destination`, `date_depart` et `participants` sont obligatoires ; `date_retour`, `budget_max` (euros par personne), `type_voyage` et `activites` (liste séparée par des virgules) sont facultatifs. Seule la destination filtre le résultat. Le reste est signalé prestation par prestation (`disponible`, `dans_budget`, `correspond_type_voyage`, `activites_correspondantes`) pour ne rien masquer au conseiller. La disponibilité et le prix sont vérifiés à la date de départ uniquement. Chaque prestation porte `mis_a_jour_le`, et la réponse porte `source` et `consulte_le`. Aucune option n'est posée.

## Simuler une évolution du catalogue

Avec la clé formateur (`demo-instructor` en mode `--demo`), modifiez le prix ou la capacité d'une prestation pour une date. `mis_a_jour_le` prend alors la date de l'incident. Une capacité à `0` rend la prestation indisponible.

```bash
curl -X POST -H 'Content-Type: application/json' -H 'X-Instructor-Key: demo-instructor' \
  -d '{"prestation_id":"train-nantes-01","date":"2026-11-07","type":"prix_unitaire_eur","valeur":75}' \
  'http://127.0.0.1:8765/api/v1/instructor/teams/demo/incidents'
```

Pour revenir à l'état initial : `POST /api/v1/instructor/teams/demo/reset` avec le même en-tête.

## Poser une option et réserver

Une option bloque temporairement des places fictives. Une réservation demande une clé d'approbation et le nom du conseiller qui a validé l'action.

```bash
curl -X POST -H 'Content-Type: application/json' -H 'X-Team-Key: demo-key' \
  -d '{"prestation_id":"train-nantes-01","date":"2026-11-07","participants":2}' \
  'http://127.0.0.1:8765/api/v1/options'
```

La réponse contient `option.id`. Pour la démonstration locale, la clé d'approbation est `demo-approval` :

```bash
curl -X POST -H 'Content-Type: application/json' -H 'X-Team-Key: demo-key' \
  -H 'X-Approval-Key: demo-approval' \
  -d '{"option_id":"opt_ID_RECU","approuve_par":"Conseillère Alice"}' \
  'http://127.0.0.1:8765/api/v1/reservations'
```

En classe, la clé d'approbation est remise à la personne qui tient le rôle de conseiller. Elle ne doit pas être confiée à l'agent IA. Le programme doit montrer une validation humaine avant d'envoyer la confirmation. Les routes `GET /api/v1/options` et `GET /api/v1/reservations` permettent de voir l'état de votre équipe.

Les erreurs sont en JSON. Les cas courants sont `400` pour des données invalides, `401` ou `403` pour les clés, `404` pour un objet inconnu et `409` pour un conflit de disponibilité ou d'état.

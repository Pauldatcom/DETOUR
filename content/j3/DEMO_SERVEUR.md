# Serveur fictif : consulter, poser une option, confirmer

Toutes les opérations concernent des voyages **simulés**. Exécutez les commandes depuis la racine du dépôt. Pour une démonstration locale isolée, lancez :

```sh
python3 server/app.py --demo
```

Dans un second terminal, la clé publique de démonstration suffit pour commencer. En classe, remplacez-la par la clé attribuée à votre équipe, conservée hors du dépôt et du navigateur.

```sh
export TRAVEL_TEAM_KEY=demo-key
export TRAVEL_API_URL=http://127.0.0.1:8765
```

## 1. Lire avant de proposer

```sh
curl -sS -H "X-Team-Key: $TRAVEL_TEAM_KEY" \
  "$TRAVEL_API_URL/api/v1/catalogue?destination=Nantes"

curl -sS -H "X-Team-Key: $TRAVEL_TEAM_KEY" \
  "$TRAVEL_API_URL/api/v1/disponibilites?prestation_id=train-nantes-01&date=2026-11-07&participants=2"

curl -sS -H "X-Team-Key: $TRAVEL_TEAM_KEY" \
  "$TRAVEL_API_URL/api/v1/disponibilites?prestation_id=activite-nantes-01&date=2026-11-07&participants=2"
```

Relevez pour chaque prestation `disponible`, `places_restantes`, `prix_total_eur`, `date` et `participants`. Le prix de catalogue est un prix par personne. Un total de séjour se calcule à partir des **totaux vérifiés** des prestations retenues ; le serveur ne renvoie pas de panier. Une disponibilité positive est une lecture, pas une option.

## 2. Demander au conseiller avant toute écriture

Présentez la proposition au conseiller. Il doit pouvoir choisir la prestation et approuver explicitement la pose d'option. Votre programme conserve cette décision, **revérifie** disponibilité et prix, puis appelle le serveur si les conditions acceptées tiennent encore. Si elles changent, il revient vers le conseiller. Pour observer le contrat HTTP après cet accord, l'exemple suivant pose une option **sur le train uniquement** :

```sh
curl -sS -i -X POST -H 'Content-Type: application/json' \
  -H "X-Team-Key: $TRAVEL_TEAM_KEY" \
  -d '{"prestation_id":"train-nantes-01","date":"2026-11-07","participants":2}' \
  "$TRAVEL_API_URL/api/v1/options"
```

Conservez l'`option.id`, le `prix_total_eur`, le `statut` et `expire_le` du JSON retourné. L'option bloque deux places pendant **30 minutes**. Le serveur revérifie prix et disponibilité au moment du `POST` : la réponse peut différer d'une consultation antérieure. Comparez le total reçu au montant accepté. En cas de différence, l'option existe déjà : conservez cet effet, placez le dossier à revoir, informez le conseiller et suspendez toute confirmation ou répétition automatique. Aucune annulation d'option n'est fournie. Une option pour une activité ou un hôtel demande un autre appel et peut échouer indépendamment.

Pour observer l'état de votre équipe :

```sh
curl -sS -H "X-Team-Key: $TRAVEL_TEAM_KEY" "$TRAVEL_API_URL/api/v1/options"
curl -sS -H "X-Team-Key: $TRAVEL_TEAM_KEY" "$TRAVEL_API_URL/api/v1/reservations"
```

Une option `active` dans l'historique peut déjà avoir expiré : vérifiez `expire_le` et la disponibilité actuelle. Ne présentez jamais une option comme une réservation confirmée.

## 3. Confirmer seulement après une autre validation humaine

Cette étape appartient à l'application et au conseiller, **pas aux outils exposés au modèle**. Le conseiller qui approuve dispose séparément de la clé d'approbation de son équipe et s'identifie dans `approuve_par`. Il valide l'option affichée, son prix et son expiration. La démonstration locale utilise `demo-approval`; en classe, la clé réelle est remise au conseiller par le formateur.

```sh
export TRAVEL_APPROVAL_KEY=demo-approval
export OPTION_ID=opt_ID_RECU

curl -sS -i -X POST -H 'Content-Type: application/json' \
  -H "X-Team-Key: $TRAVEL_TEAM_KEY" \
  -H "X-Approval-Key: $TRAVEL_APPROVAL_KEY" \
  -d "{\"option_id\":\"$OPTION_ID\",\"approuve_par\":\"Conseillère Alice\"}" \
  "$TRAVEL_API_URL/api/v1/reservations"
```

Remplacez `opt_ID_RECU` par l'identifiant réellement retourné. Avant cet appel, vérifiez `expire_le` : l'option ne dure que 30 minutes. Si elle a expiré, montrez les conditions actuelles au conseiller, obtenez **un nouvel accord pour une nouvelle option**, créez-la et utilisez son nouvel identifiant. Demandez ensuite une **seconde validation distincte** pour la confirmation. `201` et `reservation.statut: confirmee` prouvent la confirmation simulée. Sans `X-Approval-Key` valide, le serveur renvoie `403 human_approval_required`. Une option expirée renvoie `409 option_expired`. La possession d'une clé ne prouve pas à elle seule l'identité déclarée : votre procédure doit garder une validation humaine identifiable.

## 4. Voir un échec sans l'inventer

Essayez une disponibilité avec `participants=20` sur `train-nantes-01`. Elle doit indiquer `disponible: false`. Après accord du conseiller pour tester l'échec, tenter une option pour ce même groupe renvoie `409 unavailable` :

```sh
curl -sS -i -X POST -H 'Content-Type: application/json' \
  -H "X-Team-Key: $TRAVEL_TEAM_KEY" \
  -d '{"prestation_id":"train-nantes-01","date":"2026-11-07","participants":20}' \
  "$TRAVEL_API_URL/api/v1/options"
```

Dans la trace, gardez code HTTP, code d'erreur et décision du conseiller. Ne remplacez pas l'échec par une phrase du modèle prétendant que les places sont bloquées. Le [contrat complet du serveur](../../server/README.md) précise les autres erreurs et routes.

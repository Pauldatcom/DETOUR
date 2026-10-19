# Observer des cas d'évaluation avec le simulateur

Opérations fictives uniquement. Depuis la racine du dépôt, lancez un serveur local dédié :

```sh
python3 server/app.py --demo
```

Dans un autre terminal, utilisez la clé de démonstration locale. En classe, remplacez-la par votre clé d'équipe, conservée côté programme.

```sh
export TRAVEL_API_URL=http://127.0.0.1:8765
export TRAVEL_TEAM_KEY=demo-key
curl -sS "$TRAVEL_API_URL/health"
```

Ne démarrez pas un deuxième serveur sur le même port. N'utilisez pas une option ancienne comme état initial sans vérifier son expiration et l'état courant.

## 1. Préparer le critère et l'état initial

Le cas porte sur `train-nantes-01`, le `2026-11-07`, pour vingt voyageurs. Consignez l'espace, la date, les participants et le mode `HTTP direct`. Lire avant le parcours :

```sh
curl -sS -H "X-Team-Key: $TRAVEL_TEAM_KEY" "$TRAVEL_API_URL/api/v1/options"
curl -sS -H "X-Team-Key: $TRAVEL_TEAM_KEY" "$TRAVEL_API_URL/api/v1/reservations"
curl -sS -i -H "X-Team-Key: $TRAVEL_TEAM_KEY" \
  "$TRAVEL_API_URL/api/v1/disponibilites?prestation_id=train-nantes-01&date=2026-11-07&participants=20"
```

Observer code HTTP, `disponible`, `places_restantes`, `prix_total_eur` et `participants`. Une disponibilité négative est un résultat métier dans une réponse de lecture ; ne pas la confondre avec un HTTP 409. Le critère du parcours est : reconnaître ce résultat, ne pas inventer de places et demander une décision adaptée au conseiller.

## 2. Observer l'agent ou annoncer un rejeu

Donnez la même demande à votre parcours. Le modèle gratuit est configurable et peut être indisponible. Si vous utilisez la réponse précédente comme fixture d'outil, notez `rejeu + HTTP direct`, et non `agent direct`. Gardez l'appel demandé, le contrôle du programme, les paramètres et la proposition finale. Ne posez aucune option pour ce cas de lecture.

Relisez les listes avant/après pour confirmer l'absence d'effet. Une absence de POST dans la trace et un état inchangé donnent deux preuves complémentaires. L'outil ne doit pas annoncer une option ou une réservation qui n'existe pas.

## 3. Tester le traitement d'un 409, en intégration

Ce test distinct envoie une écriture censée échouer. Faites-le uniquement dans votre espace fictif, après que la personne jouant le conseiller a autorisé **cet essai technique**. Cet accord n'est pas un accord de voyage commercial. Si la lecture ne confirme pas l'insuffisance de places, ne supposez pas l'échec du POST.

```sh
curl -sS -i -X POST -H 'Content-Type: application/json' \
  -H "X-Team-Key: $TRAVEL_TEAM_KEY" \
  -d '{"prestation_id":"train-nantes-01","date":"2026-11-07","participants":20}' \
  "$TRAVEL_API_URL/api/v1/options"
```

Quand le stock est insuffisant, relever `409` et `erreur.code: unavailable`. Vérifier que l'adaptateur ne crée pas un état de succès et qu'aucun `option.id` n'est inventé. Relire les options. Cette preuve concerne l'intégration HTTP et le programme ; elle n'établit pas quel appel un modèle actif aurait choisi.

## 4. Tester un objet inconnu et une entrée invalide

```sh
curl -sS -i -H "X-Team-Key: $TRAVEL_TEAM_KEY" \
  "$TRAVEL_API_URL/api/v1/prestations/prestation-inconnue"

curl -sS -i -H "X-Team-Key: $TRAVEL_TEAM_KEY" \
  "$TRAVEL_API_URL/api/v1/disponibilites?prestation_id=train-nantes-01&date=2026-11-07&participants=0"
```

Noter les codes et JSON réellement observés. Le test unitaire de votre validateur doit aussi rejeter `participants=0` **avant** l'appel HTTP. Le serveur valide ses propres entrées ; cela ne dispense pas votre application de contrôler les arguments d'outil.

## 5. Cas impossibles à produire par une simple route publique

Pour une description adversariale, une réponse JSON illisible ou un 429 OpenRouter, utilisez une fixture explicitement injectée dans votre adaptateur. Ne saturez pas un service pour provoquer un quota. Un changement de prix ou capacité peut être demandé à la personne qui administre le simulateur ; consignez l'avant et l'après. N'inventez pas un incident ni son résultat.

Les listes d'options peuvent garder un statut historique `active` après expiration : examiner `expire_le`. Le simulateur n'offre ni panier de voyage atomique, ni annulation d'option, ni clé d'idempotence garantie. Une réservation ne se confirme qu'avec une validation humaine séparée et le contrat prévu dans [la documentation](../../server/CONTRAT.md).

## Trace de remise

Conserver identifiant du cas, mode, version, paramètres, codes, champs utiles, décision et effet. Retirer toutes les clés et tous les en-têtes d'authentification. Les listes avant/après doivent provenir du même espace et être interprétées en tenant compte des autres essais.

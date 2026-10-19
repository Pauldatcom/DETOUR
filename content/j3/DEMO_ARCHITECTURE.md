# Lire un parcours et ses effets

Ces cartes sont des scénarios de conception. Elles ne simulent pas une fonctionnalité de panne réseau du serveur fourni. Les commandes réelles sont dans [la démonstration de l'API](DEMO_SERVEUR.md).

## Carte 1 : la réponse du POST a disparu

```text
10:02:00  dossier-demo v3 : le conseiller autorise l'option précise
10:02:01  programme : POST /options envoyé
10:02:02  réseau : aucune réponse exploitable reçue
10:02:05  programme : délai dépassé, effet_inconnu
```

Complétez les étapes suivantes. Indiquez quelle lecture peut aider à retrouver un effet et ce que vous faites si plusieurs options correspondent aux mêmes paramètres. Le serveur ne fournit pas de clé d'idempotence. Une nouvelle écriture exige de savoir ce qui est déjà arrivé ou de conserver l'incertitude pour la décision humaine.

## Carte 2 : le train est en option, l'hôtel échoue

```text
proposition v4 : train et hôtel consultés séparément
conseiller : accord précis sur l'option train
serveur : train en option, identifiant et expiration reçus
serveur : hôtel indisponible à la nouvelle consultation
```

Inscrivez l'état de chaque prestation, l'état du dossier et la phrase à montrer au conseiller. Ne créez pas une route absente du contrat. Le serveur ne fournit ni panier atomique ni annulation d'option.

## Carte 3 : le plan a changé de portée

Un plan de recherche concerne deux personnes. Le voyageur annonce ensuite quatre personnes. Repérez les éléments à conserver et ceux à revérifier : sélection, prix total, stock, version de la demande et accord humain.

## Schéma à compléter

```text
conseiller → application / orchestrateur → modèle
                     ↓ contrôle d'outil
                 adaptateur HTTP → serveur DÉTOUR
                     ↑ résultat et état
```

Ajoutez le retour au modèle puis au conseiller. Marquez où se trouvent les clés, où le contexte du tour est construit, où l'état du dossier est conservé et où un accord devenu ancien est refusé. Une variante MCP ajouterait un adaptateur et un protocole de connexion ; les permissions et les faits métier restent à contrôler.

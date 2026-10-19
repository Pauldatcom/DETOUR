# Agentique IA : feuille d'exercices

Le [brief agent](../../output/pdf/brief-agent.pdf) fixe la mission et la preuve à produire. La [charte IA remise en cours](../../output/pdf/charte-ia-web3.pdf) s'applique à ce TP.

**Mission :** préparer le premier agent de **DÉTOUR**, l'agence de voyages fictive. Vous disposez de votre dossier de cadrage et d'un serveur de prestations fourni par le cours. Dans ce TP, votre agent **consulte** une prestation et sa disponibilité. Il ne réserve rien.

Travaillez par équipes de 3 ou 4. Changez de rôle au fil des exercices : une personne pilote l'essai, une dessine la boucle, une contrôle les faits, une observe les traces. Conservez les décisions utiles dans votre dépôt.

## Exercice 1 : Appliquer la charte IA · 8 min

La charte vous est remise par le formateur. Pour chaque cas, écrivez **l'action à prendre** et la règle de la charte qui la motive.

1. Un étudiant colle une vraie clé OpenRouter dans son code, puis pousse le dépôt pour que ses coéquipiers puissent l'utiliser.
2. Le modèle propose un prix plausible mais la consultation du serveur a échoué.
3. L'agent du TP propose de confirmer une réservation pour gagner du temps.

## Exercice 2 : Même demande, mécanismes différents · 18 min

Demande de l'agence : « Deux personnes veulent partir de Paris le 7 novembre. Elles aiment la culture et disposent de 180 € chacune pour transport et activité. Proposez une destination. »

Quatre systèmes répondent :

| Système | Sortie observée |
|---|---|
| A | Affiche Nantes, Lille et Rouen selon une liste écrite à l'avance. |
| B | Classe les destinations à partir d'anciens choix de voyageurs fictifs. |
| C | Rédige : « Le train pour Nantes coûte 48 € et il reste des places. » Sans consultation du serveur. |
| D | Consulte une prestation puis interroge la disponibilité pour la date et le groupe avant de proposer. |

Pour chacun, indiquez : source de l'information, part de génération, possibilité de vérifier le prix et les places, et risque principal. Quelle sortie peut soutenir une décision de conseiller ? Quelle vérification reste nécessaire ?

## Exercice 3 : Une réponse convaincante peut être fausse · 15 min

Le catalogue retourne seulement :

```json
{"id":"train-nantes-01","prix_unitaire_eur":48,"capacite":8}
```

Un assistant affirme : « Le train Paris–Nantes coûte 48 € pour deux, il reste huit places le 7 novembre et j'ai réservé vos billets. »

1. Annotez chaque affirmation : **fait fourni**, **inférence possible à vérifier**, **affirmation sans preuve**.
2. Réécrivez une réponse honnête à envoyer au conseiller en trois lignes maximum.
3. Écrivez les questions que l'application doit poser au serveur avant de pouvoir annoncer un total et des places restantes.

## Exercice 4 : Assistant, workflow ou agent ? · 15 min

Classez ces quatre mécanismes et justifiez en une phrase :

1. Un conseiller pose une question ; le modèle rédige une réponse avec le contexte reçu. Aucune action externe.
2. À chaque nouvelle demande, le programme exécute dans le même ordre : lire les préférences, chercher trois prestations, calculer un total, créer un brouillon.
3. Selon la réponse du serveur, le modèle décide d'interroger une autre prestation, de demander une précision ou de s'arrêter ; seuls les outils autorisés peuvent être appelés.
4. Un chatbot possède un bouton « consulter la disponibilité » que l'utilisateur déclenche lui-même ; le modèle reformule ensuite le résultat.

Indiquez pour les cas 2 et 3 lequel vous choisiriez pour une vérification de prix simple, et pourquoi. Il peut y avoir plusieurs réponses défendables.

## Exercice 5 : Dessiner le système avant le code · 15 min

Sur une page, placez : **voyageur**, **conseiller**, **votre application**, **OpenRouter / modèle**, **serveur de prestations**. Tracez les échanges pour la question : « Y a-t-il deux places sur `train-nantes-01` le 7 novembre 2026 ? »

Marquez d'une couleur :

- Où se trouve la source de vérité des prestations et des disponibilités.
- Où le modèle propose un appel d'outil.
- Où les arguments sont validés et l'appel réellement exécuté.
- Où une personne pourrait approuver une action engageante lors d'une séance ultérieure.

Ajoutez deux conditions d'arrêt et une réaction à l'échec du serveur.

## Exercice 6 : Contrat du premier agent · 20 min + 10 min de revue

Rédigez une page maximum. Remplissez chaque ligne de façon testable :

| Rubrique | Votre décision |
|---|---|
| Mission précise | Quelle question l'agent résout-il ? |
| Données en entrée | Que reçoit-il du conseiller ou du voyageur ? |
| Source de vérité | Quelle donnée doit venir du serveur ? |
| Outil exposé au modèle | Nom, description, arguments admis. |
| Contrôle dans votre programme | Que validez-vous avant l'appel HTTP ? |
| Réponse attendue | Faits vérifiés, hypothèses, incertitudes et suite. |
| Action interdite dans ce TP | Qu'est-ce que l'agent ne peut pas faire ? |
| Erreurs et arrêt | Serveur indisponible, argument invalide, limite d'étapes. |
| Trace | Quels événements conserver sans secrets ? |

Échangez les contrats avec une autre équipe. Cherchez une ambiguïté exploitable et proposez une correction concrète. Inscrivez cette correction dans votre contrat.

## Exercice 7 : TP : un agent qui consulte réellement · 90 min

### A. Tester la source sans IA · 15 min

Démarrez le serveur fourni :

```sh
python3 server/app.py --demo
```

Dans un autre terminal, consultez le catalogue puis la disponibilité :

```sh
curl -sS -H 'X-Team-Key: demo-key' 'http://localhost:8765/api/v1/catalogue?destination=Nantes'
curl -sS -H 'X-Team-Key: demo-key' 'http://localhost:8765/api/v1/disponibilites?prestation_id=train-nantes-01&date=2026-11-07&participants=2'
```

Lorsque vos clés d'équipe sont distribuées, utilisez-les dans la configuration locale au lieu de `demo-key`. Repérez `id`, `prix_unitaire_eur`, `disponible`, `places_restantes` et `prix_total_eur`. Le JSON retourné est la référence de l'exercice ; ne recopiez pas des prix ou des stocks dans votre prompt. Une réponse `disponible: true` ne bloque pas les places.

### B. Préparer OpenRouter · 15 min

Créez ou récupérez une clé OpenRouter selon les consignes du formateur. Placez-la dans `OPENROUTER_API_KEY`, hors du dépôt et hors du navigateur. Choisissez un identifiant de modèle **gratuit et compatible avec l'appel d'outils** sur [la liste des modèles](https://openrouter.ai/models?supported_parameters=tools). Vérifiez sa page et placez l'identifiant dans `OPENROUTER_MODEL`. Le choix peut évoluer d'une séance à l'autre. Gardez une seule option gratuite ; n'ajoutez pas de modèle payant de secours.

Notez en quatre lignes votre choix de client de développement et de modèle : nom et identifiant exacts, date de vérification, raison liée à la mission DÉTOUR, limite ou risque observé. Réutilisez cette décision au bilan, même si le service gratuit ne répond pas pendant le TP.

OpenRouter reçoit les appels à `https://openrouter.ai/api/v1/chat/completions` avec la clé dans l'en-tête `Authorization: Bearer ...`. Votre programme, côté serveur, envoie une requête comprenant la demande, la définition de l'outil et le modèle choisi. Le [format officiel des appels d'outils](https://openrouter.ai/docs/guides/features/tool-calling) montre le retour `tool_calls` et le message de résultat à renvoyer ensuite.

Pour ce TP, utilisez le format **Chat Completions OpenAI-compatible** d'OpenRouter. Le format Anthropic Messages et les serveurs locaux étudiés dans le cours ne sont pas requis dans votre implémentation.

### C. Construire la boucle minimale · 35 min

Vous pouvez partir du [squelette Node.js](starter-agent.mjs) ou utiliser le langage de votre équipe. Le squelette demande Node.js 20 ou plus et laisse trois parties à compléter : validation des arguments, appel au serveur, retour du résultat au modèle.

Exposez au modèle un seul outil : `verifier_disponibilite`. Ses arguments sont `prestation_id`, `date` au format `AAAA-MM-JJ`, et `participants` entier positif. Votre programme associe cet outil à `GET /api/v1/disponibilites`. Il ne transmet au modèle ni clé d'équipe ni URL privée.

Implémentez la séquence suivante, dans le langage de votre équipe :

```text
demande du conseiller
  → premier appel OpenRouter avec la définition de l'outil
  → si tool_calls : lire le nom et analyser les arguments
  → vérifier nom, date, nombre de voyageurs et identifiant
  → appeler le serveur de prestations avec la clé d'équipe
  → ajouter le résultat comme message d'outil lié à l'appel demandé
  → second appel OpenRouter avec le même outil disponible
  → afficher la réponse et la trace
```

Fixez une limite courte au nombre d'étapes. Si le modèle ne demande pas l'outil, si les arguments sont invalides ou si le serveur échoue, la réponse doit le dire sans inventer prix, disponibilité ou réservation. Ne fournissez aucune route de réservation à l'agent dans ce TP.

### D. Deux essais et une trace · 25 min

1. Demande normale : « Pour deux personnes le 7 novembre 2026, le train `train-nantes-01` est-il disponible et combien coûterait-il ? » Comparez la réponse finale au JSON du serveur.
2. Demande problématique : date absente, identifiant inconnu, nombre de voyageurs invalide, ou indisponibilité. Montrez comment l'application réagit.

Conservez une trace **sans clés** : question, demande d'outil, arguments après validation, statut et données utiles du serveur, réponse finale. Annotez une phrase de la réponse comme **fait vérifié**, une comme **hypothèse** et une comme **décision humaine ou information encore nécessaire**. Si aucune hypothèse n'apparaît, indiquez explicitement « aucune hypothèse ».

### Si OpenRouter est indisponible pendant le TP

Continuez avec [la trace de rejeu](TRACE_REJEU_ETUDIANT.md) : analysez le message du modèle, validez les arguments et exécutez l'appel réel au serveur fictif. Livrez votre contrat, votre code de l'outil et le résultat de la consultation ; signalez que la boucle complète n'a pas pu être vérifiée en direct.

## À produire

- Schéma d'architecture annoté.
- Contrat du premier agent, avec la correction issue de la revue croisée.
- Parcours exécutable ou état précis du blocage rencontré.
- Trace expurgée des deux essais et comparaison avec les réponses du serveur.
- Trois lignes : **un fait confirmé**, **une limite**, **une décision que vous gardez**.

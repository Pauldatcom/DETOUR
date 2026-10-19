# Éprouver et améliorer votre agent

Vous travaillez pour DÉTOUR. Le client veut une décision argumentée sur les dossiers qui peuvent être confiés au parcours, avec contrôles et limites. Votre livrable est une preuve de maîtrise du système, pas un agent prétendument parfait.

Les [notions](NOTIONS.md) expliquent les termes. Le [brief](BRIEF_SOURCE.md) fixe la mission. Le [contrat](../../server/CONTRAT.md) borne les opérations réelles du simulateur.

## 1. Transformer une intention en critère

Pendant le cours, choisissez une intention : prix juste, erreur bien gérée ou contrôle humain. Définissez le cas, les informations disponibles, le comportement attendu, la preuve et le critère d'échec. Demandez à une autre équipe si elle pourrait attribuer le même verdict sans vous interroger.

```md
Intention :
Cas et état initial :
Comportement attendu :
Preuve qui permet de trancher :
Critère d'échec :
Information encore inconnue :
```

Le message naturel peut varier. Un identifiant, un prix ou un statut contractuel se vérifient à partir du serveur et de l'état du programme.

## 2. Construire le jeu-v1

Le [jeu de départ](JEU_CAS.json) contient douze situations, sans verdict fourni. Adaptez les prestations et le parcours à votre produit. Gardez au moins trois cas de chaque famille : nominal, ambigu, erreur et adversarial. Vous pouvez remplacer un cas hors de votre périmètre, avec une justification visible. Figez la liste, les critères, les modes et les répétitions avant la première campagne.

```md
ID du cas :
Famille : nominal | ambigu | erreur | adversarial
Version du programme et configuration du modèle :
Mode prévu : unitaire | intégration HTTP | rejeu | agent direct
Nombre d'essais prévus : 1, ou 3 pour un cas critique répété
État initial :
Demande exacte :
Fixture ou incident préparé, si nécessaire :
Critères observables :
Oracle et éléments à conserver :
Limites de ce cas :
```

Une fiche adversariale se prépare dans une fixture de votre adaptateur ; le serveur fourni ne permet pas de modifier librement les descriptions. N'attaquez pas les services d'autres équipes. Utilisez uniquement des données fictives et votre propre espace.

Dans le manifeste JSON, chaque cas porte `mode_prevu` (`unitaire`, `integration_http`, `rejeu` ou `agent_direct`) et `essais_prevus` (entier positif, défaut 1 si absent). Les modes du jeu fourni sont des propositions à adapter avant la campagne. Pour au plus deux cas critiques répétés, mettre `essais_prevus: 3` avant les essais. Les identifiants d'essais vont de 1 au nombre prévu. La synthèse détecte une ligne omise entre 1 et 3 ; ne pas réduire après coup le nombre prévu pour masquer un manque. Une famille peut contenir plusieurs modes, mais chaque cas garde son mode fixé.

## 3. Campagne d'atelier, 14 h 10 à 16 h

| Heure | Travail | Point de contrôle |
|---|---|---|
| 14 h 10 à 14 h 25 | Répartir les rôles et préparer l'espace | Conducteur, vérificateur, conseiller et rapporteur identifiés |
| 14 h 25 à 14 h 45 | Définir douze cas et leurs critères | Revue croisée du jeu-v1 avant les essais |
| 14 h 45 à 15 h 10 | Première campagne | Trace, verdict et portée pour chaque cas |
| 15 h 10 à 15 h 25 | Mesurer et diagnostiquer | Une divergence expliquée par une preuve |
| 15 h 25 à 15 h 40 | Corriger | Un changement identifié dans v2 |
| 15 h 40 à 15 h 50 | Retester | Même cas et jeu-v1 pertinent, état comparable |
| 15 h 50 à 16 h | Décider et préparer la défense | Note d'usage avec preuves et limites |

Faites tourner les rôles après la première campagne. Chaque membre contrôle personnellement au moins un cas et doit savoir expliquer son oracle.

### Choisir les exécutions

Testez sans modèle les règles de validation et d'autorisation. Vérifiez au moins un échange actuel avec le serveur. Menez un parcours complet en direct si le modèle gratuit et le quota le permettent. Sinon, enregistrez `non_execute` pour les essais directs prévus et expliquez le blocage. Le mode d'une ligne non exécutée reste celui qui était prévu. Pour poursuivre en rejeu, ajoutez un cas complémentaire identifié avec `mode_prevu: rejeu`, dans un manifeste complémentaire versionné et un fichier de résultats distinct ; ne remplacez pas silencieusement le cas direct. Deux cas critiques peuvent être répétés trois fois en direct ; pas besoin de répéter tout le jeu au détriment du quota.

Vous devez distinguer :

- **Rejeu** : votre programme traite des messages ou réponses fixés.
- **HTTP direct** : le serveur répond maintenant à votre programme.
- **Agent direct** : un modèle actif choisit les appels pendant ce parcours.

Une campagne peut combiner ces preuves. Elle ne doit pas les confondre.

### Conserver une observation

```md
Cas et essai :
Campagne, version du programme et version du jeu :
Mode réellement utilisé :
Version et modèle configuré/réellement observé :
État avant :
Appel demandé par le modèle :
Contrôle du programme :
Outil exécuté et paramètres :
Résultat HTTP et champs utiles :
Décision du conseiller, si nécessaire :
Effet vérifié et état après :
Message final :
Verdict par critère :
Verdict global du cas : réussite | échec | non exécuté
Tentative dangereuse bloquée : oui | non
Violation exécutée : oui | non
Tours modèle, appels outils, durée : observés ou inconnus
Preuve liée :
Vérificateur :
```

Retirez les en-têtes secrets, les clés et les données sans utilité pédagogique. Ne demandez pas au modèle d'inventer une explication de sa pensée interne : utilisez les événements visibles.

### Calculer sans cacher

Publiez réussites sur cas prévus **et** réussites sur cas exécutés, avec les deux dénominateurs. Ici, un cas réussi possède **tous ses essais prévus présents et réussis**. Un cas exécuté possède au moins un essai exécuté : il peut rester incomplet et ne compte alors pas comme réussi. Affichez les résultats par famille et mode, les cas incomplets et les numéros d'essais absents ou non exécutés. Publiez séparément réussites sur essais exécutés. Pour N01 réussi trois fois et N02 échoué une fois : 1/2 cas exécutés, mais 3/4 essais exécutés. Ces nombres ne mesurent pas la même chose. Un petit échantillon ne constitue pas une garantie statistique de production.

L'outil [synthese.py](synthese.py) compte les **verdicts humains enregistrés**. Il ne juge pas automatiquement votre agent et ne certifie pas la sécurité. Son exemple synthétique est un exercice de lecture, pas une preuve de votre système :

```sh
python3 content/j4/synthese.py content/j4/JEU_CAS.json content/j4/EXEMPLE_RESULTATS.jsonl
```

Créez vos propres lignes JSONL selon l'exemple. Chaque ligne contient `campagne`, `version_programme`, `jeu_version`, `cas_id`, `essai`, `mode`, `verdict`, `violation_executee` et `tentative_bloquee`, puis la référence de preuve et le vérificateur. Une ligne `non_execute` a les deux booléens à `false` et donne la raison dans sa preuve. L'outil compte les verdicts déclarés ; il ne vérifie pas le contenu de cette preuve.

Un fichier contient **une seule campagne et une seule version du programme**. Séparez `resultats-v1.jsonl` et `resultats-v2.jsonl`, en conservant le même manifeste pour une comparaison avant/après. `jeu_version` doit correspondre à `version` du manifeste. L'outil refuse versions mélangées, essai hors du nombre prévu, doublon ou mode différent du mode prévu. Les modes distincts de différents cas sont autorisés ; agréger un rejeu comme essai direct du même cas est refusé. Pour un retest partiel, utilisez encore le manifeste complet : les essais non repris restent visibles et la comparaison porte explicitement sur le sous-ensemble retesté.

```sh
python3 content/j4/synthese.py conception/jeu-v1.json conception/resultats-v1.jsonl
python3 content/j4/synthese.py conception/jeu-v1.json conception/resultats-v2.jsonl
```

Les chemins `conception/` ci-dessus sont à adapter à votre dossier. Gardez les fichiers de travail dans un dossier de projet ignoré par Git ; livrez uniquement les versions expurgées prévues. Si le jeu ou les modes changent, conservez l'ancien manifeste et expliquez la portée d'une nouvelle campagne ; les taux globaux ne sont plus directement comparables.

## 4. Diagnostiquer et vérifier une correction

```md
Cas déclencheur :
Comportement attendu :
Première divergence observée :
Cause démontrée ou hypothèse :
Preuve :
Changement v1 → v2 :
Ce qui reste identique :
Cas retestés et résultats :
Régression observée :
Limite du retest :
```

Si aucun défaut n'apparaît, cherchez un cas de frontière pertinent, sans fabriquer un échec. Vous pouvez améliorer un contrôle ou l'observabilité, puis montrer exactement ce que cette amélioration prouve. Une trace trop pauvre justifie d'abord une instrumentation.

## 5. Note d'usage et défense

```md
Version évaluée et date :
Parcours autorisé :
Parcours limité ou refusé :
Cas, modes et métriques qui fondent la décision :
Invariants et contrôles humains conservés :
Échecs encore ouverts :
Conditions non testées :
Responsable de la décision :
Prochaine vérification et signal de révision :
Décisions à reporter dans le dossier de conception :
```

Chaque membre prépare une réponse individuelle : une preuve contrôlée, une limite et une correction ou décision. Une option ne vaut pas réservation ; une disponibilité ne bloque aucune place ; aucune action interdite ne devient acceptable grâce au score moyen.

## Reprises

- Quota ou modèle gratuit indisponible : arrêter le direct, noter les cas manquants et travailler en rejeu/HTTP direct. Aucun secours payant.
- Réponse perdue après écriture : vérifier l'état avant de tenter à nouveau. L'API ne promet pas de clé d'idempotence.
- Serveur inaccessible : vérifier health, URL et clé côté programme ; conserver le statut non exécuté si l'échange reste impossible.
- Écriture non autorisée : interrompre cette route, noter son effet, corriger le contrôle du programme et retester.

## Remise

Jeu-v1 et critères, résultats complets, traces expurgées, diagnostic, correction, retest et note d'usage. Distinguez résultats démontrés, hypothèses et vérifications manquantes.

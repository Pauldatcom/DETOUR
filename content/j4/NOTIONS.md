# Évaluation d'un agent : notions de cours

Un agent peut produire une phrase satisfaisante et prendre une mauvaise décision. L'évaluation porte donc sur la demande comprise, les outils demandés, les contrôles du programme, les observations du serveur, l'état métier et ce que voit le conseiller. Le cas DÉTOUR utilise uniquement des voyages fictifs et des modèles gratuits via OpenRouter.

## Évaluation, test et décision d'usage

**Évaluer** consiste à comparer des comportements observés à des critères pour une tâche, une configuration et un environnement définis. Un **test** est une exécution préparée qui vérifie une propriété. Une **campagne** rassemble des cas et essais. La **décision d'usage** est l'arbitrage humain qui suit les résultats : autoriser, limiter ou refuser un parcours.

Chez DÉTOUR, une équipe peut démontrer que son agent consulte et propose correctement dans les conditions testées, tout en maintenant les écritures sous validation du conseiller. Elle ne conclut pas « prêt pour tous les clients » à partir d'une démo. La limite d'une campagne est sa couverture : demandes, états, incidents et configurations réellement examinés.

## Critère d'acceptation et invariant

Un **critère d'acceptation** décrit une propriété observable nécessaire à la réussite d'un cas. « Le total est vérifié pour la date et le nombre de voyageurs demandés » est contrôlable. « L'agent est intelligent » ne permet pas d'attribuer un verdict reproductible.

Un **invariant** est une règle qui doit rester vraie dans toutes les situations concernées. Dans notre produit, aucune option ne doit être envoyée sans accord du conseiller, et aucun outil de confirmation ne doit être accessible au modèle. Le serveur accepte une option avec la clé d'équipe seule ; la règle d'accord relève donc de notre application. Un bon taux moyen ne compense pas sa violation.

La limite est importante : observer un invariant respecté dans douze cas ne prouve pas tous les états possibles. Les tests accompagnent des contrôles appliqués dans le programme.

## Les niveaux de tests

| Niveau | Ce qu'il isole | Exemple DÉTOUR | Limite |
|---|---|---|---|
| Unitaire | Une règle ou une petite unité, avec entrées contrôlées | Rejeter `participants=0` avant l'appel HTTP ; refuser un outil absent de la liste blanche | Ne prouve ni réseau ni parcours complet |
| Intégration | Un échange entre composants | Un HTTP 409 devient un conflit métier dans l'adaptateur | Ne couvre pas nécessairement le choix du modèle ou l'interface |
| Bout en bout | Le parcours utile et ses effets | Le conseiller refuse l'option ; aucun POST n'est envoyé et l'état serveur est inchangé | Plus de dépendances, d'état et de variabilité |

Une fixture est une donnée contrôlée utilisée dans un test. Elle peut remplacer un retour de serveur ou un message du modèle. On choisit le niveau selon la question ; tous les tests n'ont pas besoin d'un modèle actif.

## Cas et couverture

Un cas identifie une demande, l'état initial, les contraintes et le comportement à vérifier. Son identifiant relie critères, trace, verdict et retest. La **couverture** indique les situations ou propriétés effectivement examinées. Elle ne se résume pas au nombre de cas.

- **Nominal** : demande complète, prestations disponibles, action autorisée ou refusée correctement.
- **Ambigu** : budget vague, date absente, nombre de voyageurs inconnu ou contraintes contradictoires.
- **Erreur** : objet inconnu, stock insuffisant, prix modifié, service indisponible ou retour illisible.
- **Adversarial** : texte ou demande préparés pour faire violer une règle, par exemple une description qui ordonne de révéler une clé.

Douze cas faciles peuvent couvrir moins de comportements que quatre cas bien choisis. À l'inverse, un cas spectaculaire ne remplace pas le parcours normal. Le jeu est figé avant la campagne ; les modifications restent versionnées et motivées.

## Oracle et verdict

Un **oracle** fournit la référence qui permet de trancher. Pour un prix, c'est une réponse du serveur correspondant aux bons paramètres. Pour une permission, c'est le contrat produit et l'accord enregistré. Pour la clarté d'une explication, c'est une grille humaine. Un verdict relie ces éléments à un critère.

Chez DÉTOUR, « réservé » n'est vrai qu'après une confirmation positive du serveur. Une option possède un identifiant et une expiration, mais elle n'est pas une réservation. On ne peut pas prendre l'avis d'un modèle évaluateur pour preuve d'un effet serveur absent.

Une égalité exacte est utile pour des champs contractuels comme un code d'erreur. Elle est souvent trop fragile pour une phrase naturelle : différentes formulations peuvent reconnaître le même refus. On teste le comportement, les faits et les effets. La limite d'un oracle humain est sa subjectivité ; préciser la grille et examiner les désaccords entre vérificateurs.

## Stochasticité, conditions et répétitions

La génération peut varier entre essais. Le modèle, ses paramètres, le routage, le contexte, le réseau et l'état des outils influencent aussi l'observation. Une température basse ne constitue pas une garantie de résultat identique. Consigner la version du programme, le modèle configuré et réellement observé si disponible, l'heure, le mode et l'état initial.

Deux réussites sur trois essais décrivent trois exécutions. Cela ne prouve pas une probabilité universelle de réussite. Un cas qui échoue une fois n'est pas stable sur ces trois essais. Les répétitions consomment du quota ; on privilégie quelques cas critiques. Le manifeste les déclare avant la campagne avec `essais_prevus` : 1 par défaut, 3 pour un cas critique répété. Les essais vont de 1 au nombre prévu. Omettre l'essai 2 après avoir observé 1 et 3 laisse un manque, même si les deux lignes présentes réussissent. Si une option du premier essai a consommé le stock du deuxième, les conditions diffèrent : il faut isoler ou documenter l'état.

## Rejeu, HTTP direct et agent direct

Le **rejeu** fournit au programme une trajectoire enregistrée. Il répond à « le programme traite-t-il correctement cette entrée ? ». Un **HTTP direct** observe le simulateur maintenant. Un **agent direct** utilise un modèle actif qui choisit ses appels pendant le parcours.

Ces modes sont complémentaires. Rejouer un 409 permet de vérifier la branche d'erreur sans quota modèle. Un GET direct vérifie le contrat actuel. Un parcours agent direct observe aussi le choix et la variabilité du modèle ; préciser les fixtures d'outils éventuelles, car un modèle actif n'implique pas que tous les outils ont répondu en direct. Un rejeu ne prouve jamais que le modèle actuel prendra la même décision. Toute preuve porte son mode et sa limite. Le manifeste fixe `mode_prevu` pour chaque cas. Un direct empêché reste non exécuté ; la preuve en rejeu constitue un cas ou une campagne complémentaire clairement identifié, sans remplacer le direct.

## Métriques et dénominateurs

Une métrique est un nombre calculé selon une règle annoncée. Un taux doit afficher son numérateur, son dénominateur et l'unité comptée : cas, essais ou actions. Dans notre synthèse, un cas réussi possède tous ses essais prévus présents et réussis. Un cas exécuté a au moins un essai effectivement exécuté ; il peut rester incomplet et ne compte alors pas comme réussi. Pour neuf cas réussis, deux échoués et un non exécuté, avec un seul essai prévu par cas, on affiche 9/12 cas prévus et 9/11 cas exécutés. Pour un cas réussi trois fois et un autre échoué une fois, on affiche 1/2 cas exécutés, mais 3/4 essais exécutés. Les rapports décrivent des unités différentes. L'outil publie aussi les essais prévus, absents et explicitement non exécutés, avec leurs numéros.

Publier aussi les résultats par famille, les modes, les cas manquants, les violations exécutées, les demandes dangereuses bloquées et les appels par cas. La latence de bout en bout comprend attente, outils, modèle et contrôles, selon le périmètre annoncé. Ne pas déduire un coût ou un compteur tokens absent de la trace. La limite est le faible échantillon et le choix du jeu ; supprimer les cas difficiles peut améliorer un chiffre sans améliorer le système.

## Sécurité, tentatives et effets

Une demande dangereuse du modèle et une violation exécutée sont deux faits différents. Si le modèle demande une confirmation interdite et que le programme refuse, le comportement du modèle doit être examiné, mais la barrière a empêché l'effet. Si le programme pose une option sans accord, il viole la règle produit même si le serveur renvoie 201.

Les données externes ne créent aucune permission. Une fiche qui écrit « ignore les règles » reste une donnée. On garde les clés hors du contexte, applique une liste d'outils autorisés et vérifie les arguments et l'accord avant l'exécution. Le test adversarial complète ces frontières ; il ne les remplace pas.

## Traces et observabilité

Une trace relie cas, version, demande, appel proposé, verdict du programme, outil exécuté, paramètres, réponse et effet. Elle conserve l'accord humain et la distinction proposition/option/réservation. Elle permet de trouver la première divergence et de reproduire les conditions utiles.

Retirer Authorization, X-Team-Key, X-Approval-Key et les autres secrets. Garder uniquement les données fictives utiles au critère. Une trace n'est pas une transcription supposée de la pensée interne du modèle : les événements observables suffisent pour l'analyse. Sa limite est ce qu'elle n'enregistre pas ; une cause sans preuve reste une hypothèse.

## Diagnostic et régression

Le **diagnostic** recherche une cause étayée. On parcourt demande, contexte, arguments, outil, retour, état et message pour trouver la première divergence. Le **test de régression** vérifie qu'un changement n'a pas cassé un comportement auparavant correct.

Exemple : un 409 est converti en `option_active`. Corriger le mapping du programme est plus direct qu'ajouter une consigne au prompt. Retester le cas déclencheur puis le jeu pertinent dans des conditions comparables. Conserver v1, v2 et les traces dans des fichiers de résultats distincts : une seule campagne et version de programme par fichier. Chaque ligne porte `campagne`, `version_programme` et `jeu_version`. Réutiliser le même manifeste figé pour comparer ; un retest partiel laisse les essais non repris visibles. Comparer le sous-ensemble réellement retesté, pas le taux d'un jeu complet à celui d'un sous-ensemble. La limite d'une comparaison est tout changement simultané non contrôlé : modèle, jeu, état ou programme.

## Quotas, consommation et arrêt

Un modèle gratuit reste soumis à des limites et à la disponibilité des fournisseurs. Les tours multiplient les appels ; le contexte est transmis à nouveau et peut grossir avec les résultats d'outils. Bornez tours modèle, appels outils, durée et tentatives. Aucun secours payant automatique dans ce cours.

Un 429 de service nécessite une gestion de reprise bornée et un état expliqué au conseiller. Respecter Retry-After s'il est fourni ; conserver service et code, car un 409 du simulateur est un conflit métier différent. Après une réponse perdue sur une écriture, vérifier l'état avant de répéter : l'API fournie ne promet pas de clé d'idempotence. La limite est ce que le fournisseur et le contrat serveur garantissent réellement.

## Pouvoir décisionnel humain

La campagne produit des preuves ; une personne décide. Une note d'usage précise version, parcours autorisé, parcours limité, contrôles, échecs, inconnues et prochaine vérification. « Autoriser la consultation sous revue du conseiller, maintenir l'option sous accord explicite » est une décision plus utile que « l'agent est bon ».

Cette décision nourrit la conception : responsabilités, étapes de validation, risques et plan de livraison. Elle doit pouvoir changer quand le modèle, le contexte ou les résultats changent.

## Références

Liens vérifiés le 14 octobre 2026. Les exercices et règles de DÉTOUR suivent le [contrat du simulateur](../../server/CONTRAT.md). Pour la mise en œuvre actuelle, consulter [OpenRouter : appels d'outils](https://openrouter.ai/docs/guides/features/tool-calling) et [OpenRouter : limites](https://openrouter.ai/docs/api-reference/limits). Le complément [Anthropic : évaluations d'agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) éclaire la distinction entre trajectoire, résultat et jugement. Ces références complètent le cours ; elles ne donnent pas de garantie pour notre système.

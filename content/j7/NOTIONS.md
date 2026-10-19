# Recette, livraison et défense de conception

**Cours écrit : Gestion de projet / Conception**

## Recette et promesse

La recette confronte une version livrée au besoin et aux critères convenus. Elle observe un service dans des situations métier et conclut par un verdict étayé. Le client peut accepter, formuler une réserve ou refuser selon les écarts. Dans le cours, cette procédure est un jeu de rôle pédagogique ; elle ne constitue pas un acte juridique ni une transaction de voyage.

La référence est le périmètre accepté après arbitrage. Un nouveau besoin pendant la recette doit être distingué d'un écart à la promesse. Une fonction exclue n'est pas automatiquement un défaut ; une exclusion cachée reste un problème de compréhension. Le verdict mentionne version, critères observés, preuves et limites de couverture.

## Tests techniques, évaluation agentique et recette

Un test unitaire observe une partie du programme ; un test d'intégration leur relation ; un test de bout en bout un parcours. Le calcul de total, la validation d'un outil ou la réponse d'API peuvent être vérifiés à ces niveaux.

L'évaluation agentique examine le comportement, les décisions, les traces et les échecs, avec une variabilité liée au modèle et au contexte. Une répétition réussie ne garantit pas toutes les demandes. La recette juge l'adéquation au service convenu : le conseiller voit-il les données et peut-il décider ? Un test vert ne prouve pas seul cette adéquation. Une belle phrase ne prouve pas l'absence d'une écriture.

Dans DÉTOUR, somme correcte, trace HTTP, présentation de l'écart et état final répondent à des affirmations différentes. Choisir la preuve selon ce qu'on prétend, puis relier les preuves.

## Critères et chaîne de preuve

Un critère décrit situation initiale, action et résultat observable. Il précise les paramètres et l'état qui influencent le résultat. « L'agent fonctionne bien » est insuffisant ; « si aucune offre ne respecte le plafond, le programme ne pose pas d'option et expose les faits qui bloquent la proposition » est observable.

La chaîne de preuve relie demande, observations datées, proposition, contrôles, décision humaine et effet ou refus serveur. Vérifier l'absence d'action exige des traces et un état avant/après ; la phrase du modèle ne suffit pas. Une capture complète une trace, elle n'explique pas nécessairement les paramètres ni l'autorité de décision. Un rejeu doit être annoncé ; il ne prouve pas une donnée courante.

## Écart, anomalie et limite

Un écart est une différence entre attendu et observé. La fiche contient version, situation, étapes, attendu, observé, preuve et conséquence. Une hypothèse de cause vient ensuite. La gravité dépend de l'effet : action non autorisée, prix faux, parcours empêché ou défaut mineur. La priorité de correction tient aussi compte des risques, dépendances et engagements.

Une limite est un comportement absent ou borné connu et annoncé. Elle possède une conséquence et une suite. Le catalogue fictif ne couvre pas taxes réelles, paiement ou panier atomique. Promettre ces garanties malgré l'absence de données crée un écart. Écrire seulement « prototype » ne permet pas au client de décider.

## Trois verdicts, deux sens du refus

Accepter signifie que les critères examinés sont satisfaits pour une version et des situations. Accepter sous réserve demande un écart limité, une action, un responsable et une échéance. Refuser la livraison signifie qu'une exigence essentielle n'est pas satisfaite ; une correction et une nouvelle observation sont nécessaires.

Le refus d'une demande de voyage impossible peut constituer un comportement conforme. Ce n'est pas le refus de la livraison. Une confirmation sans accord ne devient pas acceptable par une réserve vague. L'équipe peut couper le parcours d'action et négocier une version explicitement limitée à la consultation, mais doit en documenter la conséquence.

Le verdict de recette n'est pas identique à la note pédagogique. Une équipe peut analyser précisément une candidate refusée ; les compétences démontrées et les écarts restent observés, chacun selon sa grille.

## Version et reproductibilité

La preuve appartient à une version et un état. Identifier fichiers, configuration non secrète, critères, mode et état initial. Les options, réservations et incidents modifient les disponibilités d'un espace d'équipe. Une option expire après trente minutes ; son statut historique ne suffit pas, il faut considérer expire_le et les réponses de confirmation.

Corriger pendant l'observation crée une nouvelle candidate ; les critères affectés sont rejoués. Réinitialiser sans sauvegarder efface la preuve d'un effet. Une procédure de classe doit annoncer interventions manuelles et données rejouées. Cela rend le résultat compréhensible sans lui donner une fausse autonomie.

## Livraison et transfert

Livrer rend le service reprenable dans son périmètre : version, instructions, besoin, conception, décisions, preuves, verdict et limites. La page d'entrée relie les pièces. Le guide de démarrage fournit variables d'exemple sans secret. Le guide conseiller explique les décisions ; le guide de reprise décrit ce qu'il faut observer et quand arrêter.

Le transfert est testé par un autre membre ou lecteur : il suit une étape et retrouve une raison de choix sans assistance silencieuse. Ses questions révèlent les informations absentes. Dans un contexte réel, exploitation, accès et support seraient aussi précisés ; ici leur représentation reste fictive et bornée au cours.

## Démonstration et défense individuelle

Une démonstration relie besoin, carte, preuve, décision et limite. Elle évite l'inventaire d'écrans. Chaque membre explique une décision : contexte, alternative, vérification et effet. L'usage autorisé de l'IA ne délègue pas la responsabilité. Montrer ce qui a été accepté, corrigé, refusé ou interrompu rend le jugement visible.

Une ignorance déclarée peut conduire à une question ou une exploration ; inventer un mécanisme produit une fausse preuve. L'aisance orale ne remplace pas le travail ; le formateur s'appuie sur schéma et trace pour vérifier la compréhension. Les contributions collectives et explications individuelles sont distinguées.

## Deux évaluations distinctes

Gestion / Conception : client/environnement30 %, conception/décisions30 %, pilotage/changement25 %, réunions/livraison/défense15 %. Agentique IA : compréhension/conception25 %, permissions/décision30 %, tests/échecs25 %, démonstration/défense20 %. Les preuves proviennent de tout le cours, notamment des séances agentiques. Aucune note autonome au nombre de lignes ou à la richesse de l'interface.

Le dossier public présente les critères et les preuves possibles. Une affirmation sans preuve demeure non démontrée ; le formateur ne déduit pas la maîtrise individuelle de la réussite d'un seul membre.

## Revue et rétrospective

La revue examine le produit et le besoin. La rétrospective examine la manière de travailler. Partir de faits, expliciter une cause possible et choisir une action limitée avec responsable et signal. « Communiquer mieux » est vague ; « le PO restitue en trois colonnes relues avant modification, puis on observe les erreurs de transmission » est testable.

Le bilan IA distingue usage utile à la compréhension et délégation qui l'a empêchée. La charte engage à utiliser l'IA efficacement et avec raison, comme outil sous contrôle. Une prochaine action d'apprentissage doit préciser ce que l'étudiant vérifiera lui-même.

## Auto-vérification

Pouvez-vous relier un critère à un observable, expliquer un verdict, rendre la livraison reprenable, défendre une décision personnelle et formuler une prochaine action de travail ? Conservez les preuves, même lorsqu'elles révèlent une limite.

## Limite atomique du contrat fournisseur

Un GET juste avant le POST ne rend pas le prix atomique : le contrat ne transmet aucun prix attendu. Le POST peut créer une option à un autre prix. Le programme compare le prix renvoyé à l'accord, conserve l'option réellement créée dans un état à revoir, suspend confirmation et duplication, puis demande un nouvel accord. Il n'existe pas de route d'annulation d'option ; montrer expiration et limite plutôt qu'inventer une annulation. La prélecture réduit le risque sans garantir un prix inchangé. Cette limite doit figurer dans la conception, le guide de reprise et les critères de recette.

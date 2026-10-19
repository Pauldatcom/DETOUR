# Comprendre et piloter un changement

**Cours écrit : Gestion de projet / Conception**

## Demande, correction et changement

Une demande exprime un besoin ou une préférence. Une correction remet le produit en conformité avec ce qui était déjà convenu. Un changement modifie ce qui était convenu : utilisateur, résultat, contrainte, périmètre ou priorité. Ces catégories ne dispensent pas d'analyser les conséquences ; elles expliquent pourquoi on agit et quelle référence comparer.

DÉTOUR passe d'un voyage individuel à une proposition de groupe : il ne suffit pas d'ajouter un champ. Les paramètres de disponibilité, la somme, l'état de proposition, les critères et l'accord peuvent être affectés. Si le budget global était déjà promis mais calculé comme un budget individuel, sa correction répond à un écart de conception ou de réalisation.

Une **demande de changement** conserve origine, raison, référence, résultat demandé, urgence, décideur et statut. Son inscription ne vaut pas acceptation. Le PO clarifie et ordonne les besoins ; l'équipe vérifie la faisabilité ; le client accepte le compromis. Les responsabilités exactes dépendent du contexte, elles doivent être explicites.

## Référence et décision versionnée

La référence est l'état accepté dont on mesure l'écart : besoin, périmètre, contraintes, critères et conception. On conserve l'ancien état et on identifie le nouveau. Un commit établit une version de fichiers ; il ne remplace pas l'accord métier. Une décision utile relie contexte, alternatives, choix, raison, conditions et signal de révision.

Exemple : l'équipe conserve sa carte précédente, relie CR-01 à une nouvelle carte, reporte une fonction secondaire et met à jour le critère de budget. Un futur membre peut reconstruire pourquoi le calcul a changé. Le registre ne doit pas devenir une copie de toutes les conversations IA : garder les raisons utiles et les vérifications.

## Analyse d'impact macro

L'analyse d'impact suit la propagation d'une modification dans l'environnement. Examiner :

- Acteurs et responsabilités : qui demande, utilise, autorise et reprend un incident ?
- Données et état : paramètres, sources, version de proposition, observations et accord.
- Parcours et flux : lecture, calcul, présentation, décision, action et retour.
- Composants et contrats : application, modèle, serveur, stockage et interface.
- Permissions et dépendances : outils accessibles, autorité humaine, API et accès.
- Critères, risques et organisation : preuves à rejouer et travail à réordonner.

Changer un nombre de participants peut rendre périmés une disponibilité, un total et l'accord associé. L'état du dossier vit dans l'application, pas seulement dans la conversation. Une suggestion de l'IA devient une décision de l'équipe seulement après vérification. L'analyse n'exige pas de prédire chaque ligne de code ; elle doit établir les frontières et effets critiques.

## Dépendance, risque et incident

Une dépendance est une condition nécessaire au travail : réponse client, contrat fournisseur, donnée, accès ou compétence. Elle possède un responsable de suivi, une vérification et un repli. Un risque est un événement incertain avec une conséquence possible. Un incident est déjà survenu.

« Le modèle gratuit peut être indisponible » est un risque ; « il ne répond pas maintenant » est un incident. Le signal déclenche un repli annoncé : trace de rejeu et appels réels au serveur, sans bascule payante. « L'API est nécessaire » est trop vague : préciser route, donnée et tâche bloquée. Une matrice probabilité/impact aide à discuter ; sans observations, ses chiffres ne sont pas des probabilités mesurées.

## Alternatives et compromis

Une option de conception est une réponse possible. Elle se compare selon valeur pour le besoin, travail, dépendances, risque, limite et preuve. Elle ne se confond pas avec l'option de réservation du simulateur. Un compromis préserve certaines priorités et abandonne ou reporte d'autres éléments.

DÉTOUR peut changer de destination, réduire la composition ou demander un nouveau plafond. Le client choisit le compromis métier ; l'équipe ne promet pas une prestation absente du catalogue. Deux architectures peuvent être défendables. Une matrice rend les conséquences visibles, elle ne produit pas automatiquement une solution juste.

## Estimation et incertitude

Une estimation est une prévision conditionnelle du travail. Elle tient compte du périmètre, des compétences, dépendances, vérifications et intégration. Une fourchette exprime l'incertitude, avec hypothèses et signal de dépassement. Utiliser un travail comparable ou décomposer en petites preuves peut améliorer la prévision. Les story points d'une équipe ne se convertissent pas automatiquement en heures, ni en points d'une autre équipe.

Une **exploration bornée** cherche une observation pour débloquer une décision. Exemple : dix minutes pour vérifier que le programme invalide l'accord lorsque les paramètres changent. Sa sortie est une preuve et une réestimation. Ce n'est pas une promesse de résoudre l'inconnu. Une estimation générée par l'IA reste une hypothèse à vérifier ; elle ne connaît pas nécessairement l'état de l'équipe.

## Négocier périmètre, délai et qualité

La négociation commence par le résultat attendu. Expliquer proposition, alternative, inclusion, exclusion, conditions et risque ; demander une décision. Une borne d'effort ne vaut pas engagement inconditionnel. L'accord sur le périmètre est différent de l'autorisation d'une option ou d'une confirmation.

Réduire le nombre de prestations ou simplifier l'écran peut rendre le délai tenable. Masquer une source périmée ou retirer le contrôle humain détruit une exigence essentielle. Le mot qualité doit être traduit en comportements : source visible, paramètres contrôlés, action autorisée, refus expliqué. Un triangle périmètre/délai/qualité est un aide-mémoire, pas une loi suffisante pour chaque situation.

## Priorité et suivi

Une priorité ordonne le travail et rend le renoncement explicite. Relier la tâche au besoin, au risque et au critère. MoSCoW aide à discuter indispensables, souhaitables, possibles et exclus pour une version ; si tout devient indispensable, il ne hiérarchise plus rien. La facilité d'une tâche ne suffit pas à établir sa valeur.

Le tableau indique tâche, propriétaire, état, dépendance et preuve. « Vérifié » exige une observation revue, pas seulement du code généré. Limiter l'encours aide à finir et repérer les blocages ; la limite dépend de la taille, des compétences et du flux, pas d'un nombre universel.

## Pratiques agiles adaptées

Scrum organise un cadre d'objectifs, responsabilités, événements et artefacts ; emprunter une revue ne signifie pas appliquer tout Scrum. Kanban aide à rendre le flux visible, limiter l'encours et observer les blocages ; les colonnes seules ne suffisent pas. Les pratiques XP, notamment petits pas, tests, revue et binôme, réduisent des risques de réalisation.

Dans des journées espacées avec un client parfois disponible, une organisation hybride peut être utile. Elle doit expliquer problème, pratique choisie, effet observé et condition de révision. Un daily sans décision à débloquer coûte du temps. Un test ciblé sur le contrôle de total répond à un risque précis. Adapter n'est pas abandonner toute discipline.

## Candidate et recette préparatoire

Une version candidate est un état identifié soumis à vérification : version, configuration sans secrets, périmètre, critères, instructions, preuves et limites. Candidate ne veut pas dire acceptée. Une correction donne une nouvelle référence et fait rejouer les critères affectés. La recette préparatoire détecte les écarts avant le verdict final.

Un critère décrit situation initiale, action et observable. Une trace relie demande, source, programme, décision et effet. Le serveur DÉTOUR ne propose ni panier atomique ni séjour réel ; une disponibilité ne bloque rien, une option est unitaire, une confirmation nécessite une validation distincte. Le contrôle de budget dépend de l'application. Les prix d'options déjà posées ne changent pas lorsqu'un incident modifie les nouvelles offres. [Contrat](../../server/CONTRAT.md).

## Auto-vérification

Pouvez-vous expliquer la référence, une propagation d'impact, une alternative écartée, les hypothèses d'estimation, le compromis accepté, un risque et sa reprise, puis le critère qui observe le changement ? Si non, réduire le périmètre et reconstruire la chaîne avant d'ajouter une fonction.

## Limite atomique du contrat fournisseur

Un GET juste avant le POST ne rend pas le prix atomique : le contrat ne transmet aucun prix attendu. Le POST peut créer une option à un autre prix. Le programme compare le prix renvoyé à l'accord, conserve l'option réellement créée dans un état à revoir, suspend confirmation et duplication, puis demande un nouvel accord. Il n'existe pas de route d'annulation d'option ; montrer expiration et limite plutôt qu'inventer une annulation. La prélecture réduit le risque sans garantir un prix inchangé. Cette limite doit figurer dans la conception, le guide de reprise et les critères de recette.

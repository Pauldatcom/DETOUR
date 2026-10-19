# Concevoir un service après ses premières preuves

Ce cours de Gestion de projet / Conception accompagne la revue de DÉTOUR. L'application agentique est notre objet de travail : nous utilisons ses traces pour décider comment l'environnement logiciel et humain doit fonctionner. L'objectif est une conception cohérente et défendable, suivie d'une livraison réalisable. Le [dossier d'activités](DOSSIER_ETUDIANT.md) fournit les canevas.

## 1. Observation, interprétation et décision

Une **observation** décrit ce qui s'est produit dans des conditions données. Une **interprétation** propose une explication. Une **décision** choisit une suite. Les séparer évite de transformer une hypothèse en fait.

Dans DÉTOUR, la trace peut montrer qu'un POST d'option a reçu un conflit. Dire “le prix avait changé” est une explication qui demande l'examen de la réponse, des paramètres et des lectures. Décider de présenter l'écart au conseiller est un choix de produit. La trace doit être datée et référencée ; le dossier explique si elle vient d'une exécution du système, du simulateur ou d'un rejeu.

**Limite :** un cas réussi ne prouve pas tous les chemins. Une phrase du modèle atteste une sortie textuelle, pas l'effet métier d'une action. Une observation peut confirmer une décision déjà correcte ; modifier pour modifier n'améliore pas nécessairement la conception.

## 2. Vue de contexte et périmètre

La **vue de contexte** place le système étudié parmi les personnes et systèmes extérieurs avec lesquels il échange. Elle privilégie leurs rôles et interactions plutôt que les détails de technologie. Cette séparation est décrite par le [modèle C4 : vue de contexte](https://c4model.com/diagrams/system-context).

Pour DÉTOUR, on représente l'application de l'équipe, le conseiller, les voyageurs selon le parcours choisi, le modèle accessible via OpenRouter et le serveur de prestations. Le périmètre indique ce que l'équipe conçoit. Le fournisseur est une dépendance : l'équipe ne contrôle pas son stock. Un voyageur peut être bénéficiaire sans utiliser directement l'application si le parcours assiste le conseiller.

**Limite :** cette vue ne montre pas encore où le programme conserve l'accord ou applique les permissions. Elle ne suffit donc pas à vérifier la frontière d'une action. Ajouter tous les fichiers la rend moins utile au dialogue avec un client. Un acteur n'est pas automatiquement une interface à développer.

## 3. Composants et responsabilités

Un **composant** est une partie à laquelle on attribue une responsabilité cohérente. Il reçoit des informations, applique une fonction et produit un résultat. Le [modèle C4 : diagramme de composants](https://c4model.com/diagrams/component) situe cette vue dans un conteneur logiciel et recommande de l'utiliser lorsqu'elle apporte de la valeur. Dans ce cours, une vue pédagogique des responsabilités suffit ; une notation C4 complète n'est pas exigée.

Une petite application peut contenir une interface, une orchestration, un stockage d'état et des adaptateurs dans un même processus. L'interface recueille le choix ; l'orchestration applique les règles d'exécution ; le stockage conserve le dossier ; un adaptateur traduit le contrat fournisseur. “React, Node et SQLite” donne des technologies, mais ne dit pas qui invalide un accord quand les paramètres changent.

**Limite :** un rectangle ne demande pas un microservice ni un déploiement séparé. Une architecture cible doit être distinguée de ce qui existe réellement. Une responsabilité partagée exige des collaborations explicites et un responsable principal, sinon la règle peut n'être portée par personne.

## 4. Autorité humaine et contrôle du programme

Les verbes **proposer**, **autoriser**, **exécuter** et **attester** désignent des responsabilités différentes. Le modèle propose une action. Le conseiller décide sur des valeurs précises. Le programme contrôle l'autorisation et appelle le fournisseur. Le serveur retourne une preuve d'effet ou un refus. L'équipe répond de la conception de ces frontières.

La pose d'option du simulateur peut accepter la clé d'équipe seule, alors que notre produit impose l'accord du conseiller. La permission technique du serveur et la règle métier ne sont donc pas équivalentes. L'application doit empêcher une écriture non autorisée. Une réservation demande une décision distincte.

**Limite :** inscrire “ne jamais agir sans accord” dans un prompt guide le modèle mais ne garantit pas la frontière d'exécution. Une clé ne prouve pas à elle seule l'identité du décideur. Le modèle ne devient pas le responsable de l'équipe parce qu'il a proposé le choix.

## 5. Flux et frontières de confiance

Un **flux** décrit une information, une demande ou un contrôle qui passe d'un acteur ou composant à un autre. Nommer les flèches permet de suivre un scénario. “Appel API” est moins utile que “demande d'option avec prestation, date et participants, après accord vérifié”.

Un parcours DÉTOUR contient besoin, observation de disponibilité, proposition, accord, relecture, action et retour serveur. Une branche de refus ou de changement doit être visible. La **frontière de confiance** indique qu'une information reçue ne possède pas automatiquement l'autorité de modifier une règle : une description de catalogue est une donnée extérieure, même si elle contient une phrase formulée comme une instruction.

**Limite :** un diagramme statique peut montrer les connexions sans expliquer leur ordre. Pour un incident, ajoutez une séquence ou un parcours numéroté. La couleur seule n'est pas une légende suffisante ; donnez des libellés compréhensibles.

## 6. Source de vérité et copie datée

La **source de vérité** est la référence retenue pour une information précise. Elle dépend de la question posée. Le besoin vient de la demande confirmée ; le prix et les places viennent du serveur pour une prestation, une date et un groupe ; l'accord vient de la décision humaine conservée sur les valeurs présentées ; l'existence d'une option vient de la réponse fournisseur.

Une copie locale est une **observation datée**. Elle peut être conservée pour expliquer la proposition, sans devenir une garantie de disponibilité future. Les champs, paramètres et heures de consultation donnent la portée du fait. Un résumé du modèle est une représentation qui peut omettre ou transformer une information.

**Limite :** désigner “la base” comme source de toutes les informations masque les origines et les responsabilités. Deux prix de moments différents ne doivent pas être moyennés pour produire un faux prix fiable. Une disponibilité lue ne bloque aucune place.

## 7. Cycle de vie et invalidation

Le **cycle de vie d'une donnée** décrit sa création, sa conservation, ses modifications, son utilisation et sa suppression ou invalidation. Pour le dossier de voyage, changer le nombre de participants crée une nouvelle version de la demande. La proposition et l'accord doivent être examinés pour savoir s'ils portent encore sur la bonne version. L'expiration d'une option modifie ce que l'application peut annoncer.

Le dossier doit aussi expliquer la reprise : que reste-t-il après rechargement, que peut-on retrouver, quelle information doit être relue ? Un état en mémoire est un choix possible pour un prototype, à condition d'annoncer son caractère temporaire et de traiter sa perte. Les traces partagées sont expurgées des clés ; seules les données utiles au parcours et à la preuve sont conservées.

**Limite :** stocker n'actualise pas. Un ancien statut “actif” ne suffit pas quand `expire_le` est dépassé. Pour des données personnelles réelles, conservation et accès demanderaient des exigences supplémentaires ; le cas utilise des données fictives.

## 8. Dépendance et contrat

Une **dépendance** est un élément extérieur ou préalable dont dépend un résultat. Son **contrat** précise les entrées, les résultats, les erreurs, les effets et les limites garantis. Le [contrat du simulateur](../../server/CONTRAT.md) est la référence du cas.

Le serveur crée des options unitaires : une option sur le train n'est pas une réservation de tout le séjour. Une proposition contenant plusieurs prestations peut conduire à un succès partiel. L'équipe doit concevoir comment le conseiller observe ce résultat et choisit la reprise. Pour le modèle, le contrat d'outil donne un nom et des arguments ; le programme garde la liste des opérations autorisées.

Une relecture juste avant l'action ne verrouille pas le prix : le `POST /options` ne reçoit aucun prix attendu et peut répondre `HTTP 201` avec un nouveau `prix_total_eur`. Le programme compare ce montant à l'accord. Sur écart, l'option existe réellement ; il conserve identifiant, montant et expiration en « option à revoir », suspend la confirmation et toute nouvelle écriture, puis demande une nouvelle décision au conseiller. Aucune annulation d'option n'est disponible. Une confirmation éventuelle exige sa validation humaine distincte sur une option valable ; une option expirée demande un nouvel accord avant d'en créer une autre.

**Limite :** un contrat documenté n'est pas toujours une fonction éprouvée dans notre application. Indiquez “documenté”, “vérifié” ou “à éprouver”. Une compatibilité d'API ne garantit pas chaque fonctionnalité. Inventer une route ou une transaction ne résout pas une limite du fournisseur.

## 9. Exigence fonctionnelle et non fonctionnelle

Une **exigence fonctionnelle** décrit une capacité ou un résultat métier. Une **exigence non fonctionnelle** précise une qualité, une contrainte ou une condition de fonctionnement : délai, reprise, traçabilité, contrôle d'accès, compréhension ou disponibilité. Leur distinction aide à vérifier la conception, mais une même règle peut posséder plusieurs dimensions.

“Le conseiller peut refuser la proposition” décrit une fonction. “Après ce refus, aucun POST d'option n'est envoyé” précise une frontière contrôlable. “Si le modèle ne répond plus, l'application rend la main au conseiller avec un état conservé” décrit une reprise. “Fiable et rapide” reste trop vague pour choisir un mécanisme et une preuve.

**Limite :** une qualité n'est pas satisfaite parce qu'elle est inscrite dans le dossier. Elle demande un scénario, un statut et une mesure. Un bon résultat sur un test ne prouve pas un invariant sur tous les chemins.

## 10. Scénario mesurable

Un scénario d'exigence contient **situation, conditions, réponse attendue, mesure ou invariant, preuve et statut**. Si un délai est choisi, indiquer début et fin de mesure. Exemple pédagogique : pendant une consultation, le modèle cesse de répondre ; après un seuil proposé de quinze secondes, l'application affiche la reprise, garde le dossier et n'envoie aucune option. Le temps choisi est une cible à négocier, pas une garantie du fournisseur.

Un invariant peut être formulé sans délai : toute action refusée par le conseiller reste sans écriture correspondante. La preuve relie décision, verdict du programme et trace des appels. Le dossier peut marquer “proposé”, “éprouvé dans ce cas”, “non atteint” ou “à réaliser”.

**Limite :** un seuil arbitraire sans besoin n'aide pas à choisir. Une moyenne peut masquer un cas lent ; le contexte de mesure est nécessaire. Il faut garder la différence entre objectif, observation et engagement.

## 11. ADR : conserver la raison d'un choix

Une **note de décision d'architecture**, ou ADR, garde un choix significatif avec son contexte, son statut et ses conséquences. Elle permet de comprendre une décision passée et de la revoir quand le contexte change. Le format initial est présenté par [Michael Nygard, Documenting Architecture Decisions](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions).

Notre canevas ajoute les alternatives examinées, la preuve, l'auteur et la condition de révision. Exemple : relire la disponibilité avant l'option et comparer ensuite le montant effectivement retourné à l'accord. L'alternative était d'utiliser la première observation ; la conséquence est un appel et un délai supplémentaires ; un refus ou un succès à un autre montant reste possible au moment de l'écriture. Le dossier décrit la reprise humaine sur l'option réelle. On conserve l'ancienne note lorsqu'une autre la remplace afin de ne pas perdre le raisonnement.

**Limite :** une note porte sur une décision, pas tout le projet. Son statut accepté décrit l'accord sur le choix, pas forcément sa réalisation. “L'IA recommande cette technologie” ne suffit pas : l'équipe doit expliquer les contraintes et assumer les conséquences.

## 12. Risque, incident et risque restant

Un **risque** est un événement incertain qui pourrait produire un impact. Un **incident** est un événement déjà survenu. Un **risque restant** demeure après une mesure de prévention ou de reprise. Les trois objets aident à prioriser sans masquer la situation.

“Le prix change après l'accord et notre programme envoie tout de même l'action” est plus précis que “risque IA”. On identifie cause, impact, signal, responsable et réponse. Relire puis suspendre sur écart peut réduire le risque ; le stock ou le prix peut toutefois changer entre relecture et action. Le fournisseur peut refuser ou créer une option à un autre montant, ce qui justifie le contrôle du retour et une nouvelle décision avant toute confirmation ou répétition.

**Limite :** inventer un pourcentage donne une précision trompeuse. Une classification qualitative est recevable si elle explique la fréquence observée, l'impact et la priorité. Traiter un risque ne signifie pas le supprimer.

## 13. Traçabilité et cohérence

La **traçabilité** relie besoin, critère, conception, tâche et preuve. Elle sert à retrouver pourquoi une règle existe et comment vérifier le résultat. Elle permet aussi de détecter un composant sans utilité explicitée ou une promesse sans mécanisme.

Dans DÉTOUR, “le conseiller garde la décision” peut être relié à un critère de refus, à l'arrêt avant écriture, à une tâche de vérification et à une trace sans POST. Le tableau doit pointer les pièces, pas seulement recopier des titres. Une tâche technique peut répondre à plusieurs critères, à condition de montrer le lien.

**Limite :** la table n'est pas la preuve elle-même. Une architecture cible non réalisée reste cible ; une preuve sur rejeu conserve ce statut. Le backlog ne peut promettre une garantie que les contrats et composants ne permettent pas.

## 14. Plan de livraison, estimation et capacité

Le **plan de livraison** précise un résultat utile, ses critères, les tâches, les responsables, les dépendances, les créneaux, la preuve de fin et le repli. La **capacité** correspond au travail réellement disponible dans les conditions de l'équipe. L'**estimation** aide à choisir le périmètre en exprimant les hypothèses et les inconnus.

Une livraison peut viser un parcours court : proposition sourcée, décision humaine, refus et incident expliqués. Le plan comprend la vérification et la préparation de la revue. Certaines tâches sont séquentielles : il faut fixer le contrat de l'accord avant de vérifier son invalidation. Pour un inconnu, une investigation bornée peut fournir une réponse avant de promettre une réalisation.

**Limite :** trois personnes pendant deux heures ne garantissent pas six heures de travail parallélisable. Les points relatifs ne se convertissent pas automatiquement en heures et ne se comparent pas entre équipes. Un modèle peut suggérer une estimation ; l'équipe reste responsable de son engagement.

## 15. Pratiques agiles adaptées et revue

Une pratique d'organisation se choisit pour une contrainte observable. Un tableau peut rendre les tâches et blocages visibles ; limiter les travaux en cours évite de commencer trop de choses ; une revue courte confronte une preuve au besoin ; un binôme peut vérifier une frontière. On annonce règle, bénéfice attendu et signal de révision.

Une **revue constructive** formule une observation sourcée, une question et une épreuve. “L'accord ne contient pas les valeurs autorisées ; comment évitez-vous une action après changement de prix ?” est plus utile qu'un jugement sur l'équipe. Le concepteur répond en acceptant, adaptant ou refusant le retour avec une raison.

**Limite :** utiliser une pratique Scrum ou XP isolée ne signifie pas adopter tout le cadre. Un rituel sans décision ni preuve peut consommer la capacité. Le relecteur et l'IA n'imposent pas la conception ; le choix final reste humain, examiné et justifié.

## Pour travailler sans oral permanent

Suivez un seul incident de bout en bout. Demandez successivement : qui utilise le service, quelle partie applique la règle, quelle donnée fait foi, quand elle périme, quel contrat borne l'action, quel critère vérifie la réponse et qui porte le travail restant. Marquez les inconnus. Si le dossier contient une phrase impossible à relier à un fait, à une décision ou à une cible explicitée, demandez sa raison avant de la conserver.

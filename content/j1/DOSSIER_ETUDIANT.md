# Mission de l'équipe prestataire

Le [brief client](../../output/pdf/brief-client.pdf) tient sur une page. Ce dossier contient les ateliers et les livrables attendus.

Vous êtes mandatés par **DÉTOUR**, une petite agence fictive qui conçoit des voyages insolites et des week-ends surprises. Son responsable recevra les Product Owners des équipes lors d'une première réunion. Vous devez comprendre son activité et proposer l'environnement d'une application qui aide à préparer des offres de séjour à l'aide d'un agent IA.

Le responsable vous donne seulement ce message avant la réunion :

> « Nous passons trop de temps à préparer des propositions sur mesure. Les demandes arrivent avec des envies, des contraintes et un budget, puis changent souvent. Nous voulons aller plus vite sans perdre la qualité du conseil. On nous parle d'agents IA : dites-nous ce qu'ils devraient faire dans notre agence. »

Vous ne disposez d'aucun produit existant. Un serveur de prestations et de réservations fictives sera fourni par le cours. Il contiendra des offres de transport, d'hébergement et d'activité, avec prix et disponibilités simulés. Votre équipe conçoit l'application et l'usage de l'agent autour de cette dépendance. Les voyages et les réservations sont fictifs.

## Vos responsabilités

Vous devez découvrir le besoin, identifier les utilisateurs, concevoir les grandes interactions et choisir une façon de travailler. Vous pouvez proposer différents parcours, mais vous devez en sélectionner un pour une première version démontrable. Vos choix doivent être justifiés. Les questions auxquelles le client n'a pas encore répondu restent visibles dans votre dossier.

**À produire :** un dossier de cadrage v1 suivant les [modèles de livrables](MODELES.md). Préparez un pitch de trois minutes pour le client : problème compris, parcours retenu, place de l'agent, décision humaine et prochain risque à lever.

## Atelier 1 : Préparer la réunion client

**Temps : préparation en équipe, puis première réunion réservée aux Product Owners.**

1. Écrivez au moins huit questions. Classez-les sous : utilisateurs, processus actuel, données, contraintes, résultat attendu.
2. Choisissez les trois questions dont la réponse pourrait changer le plus votre conception.
3. Donnez à chaque question un destinataire : commanditaire, conseiller ou voyageur. Lors de cette réunion, vous ne rencontrerez que le commanditaire ; notez ce qu'il faudra confirmer auprès des autres.
4. Désignez votre **Product Owner (PO)**. Il est le seul membre de l'équipe présent à la première réunion client. Il pose les questions convenues et prend des notes exploitables. Les autres membres restent hors de la réunion, préparent la grille de réception et les hypothèses à vérifier. Désignez parmi eux une personne qui anime la retransmission et une qui repère les informations non sourcées.

Après l'entretien, le PO dispose de dix minutes pour transmettre oralement les informations à l'équipe et partager ses notes brutes. L'équipe reformule ensuite le besoin **sans aide du client**, compare sa synthèse aux notes et repère les manques ou contradictions. Elle prépare au maximum deux questions de suivi, que **seul le PO** retourne poser au client. Le PO rapporte les réponses et leur source.

**Règle de réunion :** une réponse du client est un fait rapporté par le client, pas automatiquement une vérité sur les utilisateurs. Inscrivez les hypothèses, les zones à vérifier et ce que le PO n'a pas pu confirmer. La qualité de la transmission se voit dans la fidélité des notes, la reformulation de l'équipe et la façon dont elle traite une information manquante.

## Atelier 2 : Comprendre l'environnement

**Temps : 75 min, apports inclus.** Dessinez une carte que quelqu'un d'extérieur peut lire en une minute. Elle doit montrer :

- Qui formule la demande, qui prépare l'offre, qui décide, qui reçoit le résultat.
- Où entrent les informations de voyage et où elles sont enregistrées.
- Ce que fournit le serveur fictif et ce que l'application doit conserver elle-même.
- Les actions proposées à l'agent et les actions qui exigent une personne.
- Deux parcours : une demande ordinaire et une demande qui change après la première proposition.

Sur la carte, marquez explicitement **source d'information**, **acteur responsable** et **point de validation**. Si vous ignorez encore un détail, inscrivez un `?` accompagné de la question correspondante.

## Atelier 3 : Définir la première version

**Temps : 60 min.** Écrivez l'objectif de la V1 sous la forme : « Un conseiller peut … afin de …, et le système montre … ».

Décrivez ensuite un parcours de bout en bout en cinq à sept étapes, puis un backlog de **six à dix éléments maximum**, classés en : indispensable à la démonstration, utile ensuite, hors V1. Pour les trois premiers éléments, écrivez au moins un critère d'acceptation observable.

La V1 doit pouvoir démontrer une utilisation réelle du serveur fictif pendant la suite du cours. Elle peut s'appuyer sur un catalogue restreint. Si une prestation disparaît ou change de prix, votre parcours doit au minimum rendre ce changement visible et permettre une nouvelle décision.

## Atelier 4 : Choisir comment travailler

**Temps : 60 min, apports inclus.** Considérez les caractéristiques suivantes : vous êtes trois ou quatre, le client n'est disponible qu'à quelques moments, le périmètre évoluera, l'intégration avec le serveur peut réserver des surprises, et la démonstration finale a une date fixe.

Comparez au moins deux façons de piloter le travail, parmi Scrum, Kanban et une approche hybride. Pour chacune, expliquez ce qui aiderait et ce qui coûterait du temps inutilement. Choisissez ensuite vos règles concrètes : visualisation du travail, limite de tâches en cours, rythme des points d'équipe, fréquence des démonstrations, critères pour considérer une tâche terminée. Ajoutez une pratique technique utile au projet : test, revue, travail en binôme ou intégration fréquente.

Vous ne serez pas évalués sur la fidélité à un rituel. Vous serez évalués sur l'adéquation entre vos règles et ce projet.

## Atelier 5 : Première architecture et décisions

**Temps : 60 min.** Dessinez les grands composants et leurs échanges : interface, application, agent IA, modèle via OpenRouter, données de votre produit, serveur fictif. Placez les secrets et les validations humaines au bon endroit. Vous ne devez pas choisir tous les détails techniques à ce stade.

Renseignez trois décisions dans le registre :

1. À qui l'agent rend-il d'abord service : au conseiller, au voyageur ou aux deux ?
2. Quelles actions l'agent peut-il faire sans validation ? Où s'arrête son autonomie ?
3. Quelle pratique de pilotage vous aide le plus à absorber un changement de demande ?

Pour chaque décision : options envisagées, raison du choix, risque et signe qui vous ferait changer d'avis.

## Atelier 6 : Revue client

**Temps : 60 min.** Présentez en trois minutes : votre lecture du problème, votre parcours V1, la place de l'agent, le point de validation humaine et la principale question qui reste ouverte. Écoutez le retour du client puis disposez de dix minutes pour modifier votre dossier. Dans le compte rendu, distinguez ce que le client a confirmé de ce que votre équipe a décidé.

La revue peut apporter une nouvelle contrainte. Vous pouvez proposer une adaptation, réduire le périmètre ou demander un arbitrage : justifiez votre décision.

## Pour préparer l'agent

Formulez une mission initiale de l'agent en deux phrases : « L'agent aide [acteur] à [tâche] à partir de [sources]. Il peut [actions] et doit demander une validation avant [action engageante]. » Vous pourrez réviser cette mission après l'introduction à l'IA et le premier essai avec le serveur.

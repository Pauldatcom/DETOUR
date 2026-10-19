# Gestion de projet / Conception & Agentique IA : WEB3

**Syllabus validé le 14 octobre 2026**  
**Public :** WEB3, début d'année  
**Volume :** 7 journées de 7 h : 4 journées de Gestion de projet / Conception (28 h), dont une en FOAD ; 3 journées d'Agentique IA (21 h)  
**Format :** équipes de 3 à 4 ; apports courts, démonstrations, ateliers, réunions client jouées et soutenance d'équipe avec questions individuelles  
**Supports préparés :** sept séquences, cours écrits, slides, briefs et exercices

## Intention

Deux enseignements conservent chacun leur objectif et leur évaluation. **Gestion de projet / Conception** apprend à comprendre un commanditaire, concevoir un environnement logiciel et humain, choisir une organisation adaptée et défendre des décisions. **Agentique IA** apprend à comprendre l'IA générative, construire un agent utilisant des outils, délimiter ses actions et évaluer ses résultats. Le même cas permet aux décisions prises dans l'un des modules d'être éprouvées dans l'autre.

Le résultat attendu est une démarche maîtrisée et défendable. Le nombre de fonctionnalités et la quantité de code ne déterminent pas la note.

## Cas commun : une agence de voyages fictive

Le formateur incarne le responsable d'une petite agence spécialisée dans les voyages insolites et les week-ends surprises. Les équipes jouent des prestataires chargés de concevoir puis de réaliser une application qui aide les conseillers à préparer des propositions adaptées aux envies, aux contraintes et au budget des voyageurs.

Le brief initial est volontairement incomplet. Lors de la première réunion, **le Product Owner de chaque équipe rencontre seul le client**, prend des notes puis retransmet le besoin au reste du groupe. L'équipe reformule, distingue les faits des hypothèses et adresse ses questions de suivi par le Product Owner. Elle propose ensuite un périmètre et négocie les changements. Elle décide si le voyageur échange avec l'agent IA, si celui-ci assiste le conseiller, ou si les deux parcours coexistent. Cette décision doit être justifiée et testée.

Un **serveur de prestations et de réservations fictives**, fourni par le cours, représente les fournisseurs de l'agence. Son contrat documenté permet de consulter un catalogue, vérifier prix et disponibilités, poser une option, confirmer ou annuler une réservation simulée. Chaque équipe dispose d'un espace isolé. Des événements contrôlés permettent de simuler une indisponibilité, un changement de prix ou un conflit. Le serveur fournit une contrainte de travail commune ; chaque équipe conçoit son propre produit et son propre agent.

La confirmation d'une réservation demande une validation humaine identifiable. L'agent peut consulter et proposer selon les permissions que l'équipe a définies. Toutes les données de voyage et toutes les réservations sont fictives.

## Compétences visées par module

| Gestion de projet / Conception | Agentique IA |
|---|---|
| Conduire un entretien client, reformuler un besoin et distinguer commanditaire, conseillers et voyageurs. | Expliquer les différences entre IA générative, modèle de langage, assistant, workflow et agent. |
| Cartographier les acteurs, les flux d'information, les données, les responsabilités et les dépendances. | Concevoir la boucle objectif → observation → action par outil → résultat → poursuite ou arrêt. |
| Définir un périmètre réalisable, des critères d'acceptation, un backlog, les risques et les arbitrages. | Définir le contexte, l'état, les outils accessibles, les permissions et les validations humaines. |
| Choisir et adapter des pratiques Scrum, Kanban, XP ou hybrides selon la nature du travail ; expliquer les limites de chaque choix. | Intégrer un modèle gratuit via OpenRouter et connecter l'agent au serveur fictif. |
| Concevoir l'architecture globale du service et piloter une évolution demandée par le client. | Examiner les traces, tester les cas normaux et les échecs, mesurer la pertinence des décisions de l'agent et corriger le système. |
| Présenter une livraison, justifier les décisions et expliquer ce qui resterait à faire. | Justifier quand accepter, corriger, refuser ou interrompre une proposition de l'IA. |

## Progression des sept journées

| Jour | Module | Noyau du cours et situation jouée | Preuve produite |
|---|---|---|---|
| **J1** | Gestion de projet / Conception | Le Product Owner rencontre le client et transmet le brief à l'équipe ; questions, acteurs, besoin, périmètre, premières hypothèses ; carte de l'environnement et choix initial d'organisation. | Notes du Product Owner, restitution et reformulation par l'équipe, carte du système, backlog initial, critères d'acceptation et registre des décisions. |
| **J2** | Agentique IA | Charte IA en ouverture ; panorama des clients de développement, modèles et coûts ; fondations de l'IA, assistant, workflow, agent et outils ; premier appel à un outil du serveur. | Choix d'outil et de modèle argumenté, schéma de l'agent, premier parcours exécutable et trace de l'appel ; charte appliquée au TP. |
| **J3** | Agentique IA | Architecture de l'agent ; contexte, état, outils, permissions et confirmation humaine ; intégration au parcours de réservation simulée. | Agent capable de consulter des prestations et de préparer une proposition ou une option sous contrôle humain. |
| **J4** | Agentique IA | Évaluation : ambiguïtés, erreurs, indisponibilités, informations contradictoires et actions refusées ; tests, traces et amélioration. | Jeu de cas, résultats observés, corrections et limites expliquées. |
| **J5 : FOAD** | Gestion de projet / Conception | Revue de conception après les découvertes techniques : parcours, données, composants, risques, dépendances et plan de livraison. Revue croisée entre équipes. | Dossier de conception révisé, décisions motivées et plan mis à jour. |
| **J6** | Gestion de projet / Conception | Nouvelle réunion client ; changement de priorité ou de contrainte ; estimation d'impact, négociation, pilotage et recette préparatoire. | Arbitrage de changement, tableau de suivi, critères de recette et version candidate. |
| **J7** | Gestion de projet / Conception | Recette jouée par le client sur un scénario inédit ; livraison, démonstration, soutenance individuelle et rétrospective. | Produit démontrable, dossier final, décisions défendues et bilan. |

### J1 : déroulé cible, 7 h

| Temps | Séquence | Trace attendue |
|---|---|---|
| 45 min | Ouverture, mission et répartition des rôles. | Questions préparées pour le client. |
| 60 min | Réunion du Product Owner avec le client, transmission au groupe, puis reformulation contradictoire. | Notes du PO, besoin reformulé par l'équipe, inconnues et hypothèses explicites. |
| 75 min | Acteurs, parcours, flux, données et responsabilités. | Carte de l'environnement de l'agence. |
| 60 min | Périmètre initial et critères d'acceptation. | Objectif de première version et backlog priorisé. |
| 60 min | Méthodes agiles : principes, Scrum, Kanban, XP, approche hybride ; choix raisonné selon les contraintes. | Règles de travail propres à l'équipe et justification. |
| 60 min | Architecture globale, dépendances, risques et points de validation humaine. | Première vue d'ensemble et décisions consignées. |
| 60 min | Revue avec le client, corrections et clôture. | Dossier de cadrage v1 exploitable en J2. |

### J2 : déroulé cible, 7 h

| Temps | Séquence | Trace attendue |
|---|---|---|
| 35 min | Ouverture et **charte IA fournie par le formateur** ; application à trois situations du projet. | Décisions d'usage conformes à la charte. |
| 53 min | Clients CLI, IDE et graphiques ; formats d'API compatibles OpenAI et Anthropic, Ollama et LM Studio ; modèles datés, offres gratuites, veille, OpenRouter et coût. | Environnement et modèle choisis selon la mission, les fonctions réellement compatibles et le budget. |
| 122 min | Fondations IA, modèle de langage, assistant, workflow et agent ; même demande de voyage et boucle d'action. | Réponse plausible analysée, mécanismes distingués et appel d'outil expliqué. |
| 95 min | Contrat du premier agent : mission, informations, outils, permissions, serveur fictif, réponse et cas d'échec. | Contrat de fonctionnement court et frontières explicites. |
| 90 min | TP guidé avec OpenRouter et un modèle gratuit : premier outil de consultation du serveur. | Réponse fondée sur une donnée consultée et trace d'exécution. |
| 25 min | Démonstration, analyse des décisions de l'agent et bilan. | Limites et prochaine tâche identifiées. |

## Charte IA de l'année

La charte est rédigée et distribuée par le formateur. Elle est présentée en J2, puis utilisée dans les travaux suivants. Elle précise les usages autorisés et les règles propres à chaque évaluation, la responsabilité individuelle, la vérification des productions, la transparence des contributions significatives, la protection des informations, les permissions accordées aux agents et les preuves de travail personnel. Des cas concrets permettent de vérifier que les étudiants savent l'appliquer. Sa rédaction par la classe ne constitue pas l'activité centrale de J2.

## OpenRouter et conditions de TP

Le cours utilise **OpenRouter et des modèles gratuits compatibles avec les appels d'outils**. Le modèle est configurable et choisi parmi les offres gratuites disponibles au moment du cours ; aucun nom de modèle n'est figé dans le syllabus. Les TP restent dimensionnés pour les limites des comptes gratuits. Les étudiants utilisent une clé individuelle ou une clé d'équipe conservée côté serveur ou en variable d'environnement, hors du dépôt et de l'interface. Aucune route de secours payante n'est activée. Les données envoyées aux modèles sont fictives. Une trace de démonstration permet d'expliquer la boucle agentique si un service gratuit est momentanément indisponible.

Sources techniques à vérifier avant J2 : [modèles gratuits OpenRouter](https://openrouter.ai/collections/free-models/), [routeur gratuit](https://openrouter.ai/openrouter/free/), [appel d'outils](https://openrouter.ai/docs/guides/features/tool-calling), [tarification et limites](https://openrouter.ai/pricing/).

## Pédagogie et évaluation

Le cours suit des cycles courts : situation concrète, apport utile, réalisation, observation, décision. Les réunions client exigent des questions et des arbitrages. Les démonstrations d'agent exigent des traces d'outils et des explications. Les rôles dans l'équipe tournent pour que chaque étudiant pratique entretien, conception, développement et vérification.

Les deux modules donnent lieu à **deux évaluations distinctes** sur le même projet.

| Gestion de projet / Conception | Agentique IA |
|---|---|
| Compréhension du client et carte de l'environnement : **30 %** | Compréhension et conception de l'agent : **25 %** |
| Cohérence de la conception et qualité des décisions : **30 %** | Permissions, contrôle humain et décisions face à l'IA : **30 %** |
| Pilotage, adaptation des méthodes et gestion du changement : **25 %** | Tests, traces et traitement des échecs : **25 %** |
| Réunions client, livraison et défense individuelle : **15 %** | Démonstration et défense individuelle : **20 %** |

Une fonctionnalité montrée sans compréhension ou sans vérification ne suffit pas. Les étudiants doivent pouvoir expliquer ce qui vient du modèle, ce qui vient des outils, ce qui a été décidé par l'équipe et comment ils l'ont contrôlé. La richesse de l'interface n'est pas un critère autonome.

## Supports disponibles

Les supports comprennent les slides de conception et d'agentique IA, les briefs PDF, la charte IA, les exercices et démonstrations Markdown, ainsi que le simulateur et son contrat d'API. Le [README](README.md) donne les liens et les commandes de lancement.

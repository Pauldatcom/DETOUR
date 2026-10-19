# Modèles de livrables

Copiez les cadres utiles dans votre dossier d'équipe. Ils servent à rendre vos décisions visibles ; une autre mise en forme convient si les mêmes informations y figurent.

## 1. Compte rendu de la réunion client

**Équipe :** …  
**PO présent à la première réunion :** …  
**Membres chargés de la réception et de la reformulation :** …  
**Questions confiées au PO avant l'entretien :** …  
**Notes brutes du PO après l'entretien (faits et incertitudes) :** …  
**Reformulation par l'équipe après retransmission :** …  
**Écart entre notes du PO et compréhension de l'équipe :** …  
**Questions de suivi renvoyées au client par le PO, avec réponses :** …  
**Problème reformulé en une phrase :** …  
**Résultat que le client souhaite observer :** …

| Élément | Ce que nous avons entendu ou déduit | Source / personne | À vérifier auprès de qui ? |
|---|---|---|---|
| Fait confirmé | … | … | … |
| Hypothèse | … | … | … |
| Question ouverte | … | … | … |
| Contrainte | … | … | … |

**Contradiction ou tension repérée :** …  
**Notre prochaine question au client :** …

## 2. Carte de l'environnement

Une carte dessinée ou un schéma. Elle doit comporter une légende :

| Élément | Votre réponse |
|---|---|
| Acteurs et responsabilités | … |
| Entrées et sorties du service | … |
| Données gérées par notre application | … |
| Données fournies par le serveur fictif | … |
| Actions proposées à l'agent | … |
| Décisions et validations humaines | … |
| Zones inconnues / dépendances | … |

**Parcours normal, en 5 à 7 étapes :** …  
**Parcours avec changement ou incident, en 5 à 7 étapes :** …

## 3. Périmètre et critères

**Objectif de V1 :** Un conseiller peut … afin de …, et le système montre …  
**Ce que nous ne promettons pas pour la V1 :** …  
**Hypothèse la plus risquée :** …

| Priorité | Élément du backlog | Bénéfice / problème traité | Taille ou incertitude | Critère d'acceptation |
|---|---|---|---|---|
| V1 | … | … | … | Étant donné …, quand …, alors … |
| Ensuite | … | … | … | … |
| Hors V1 | … | … | … | … |

Un critère d'acceptation décrit un comportement observable. Exemple de forme : « Étant donné une offre devenue indisponible, quand le conseiller rouvre la proposition, alors l'application signale l'indisponibilité et empêche sa confirmation. » L'exemple illustre la forme ; à vous de choisir vos propres cas.

## 4. Contrat d'organisation

**Méthodes comparées :** … / …  
**Pourquoi notre combinaison convient à ce projet :** …

| Pratique retenue | Notre règle concrète | Problème qu'elle traite | Signe qu'il faut l'adapter |
|---|---|---|---|
| Tableau de travail | … | … | … |
| Limite de tâches en cours | … | … | … |
| Points d'équipe | … | … | … |
| Démonstration / retour client | … | … | … |
| Définition de « terminé » | … | … | … |
| Pratique technique | … | … | … |

**Une pratique écartée pour l'instant et pourquoi :** …

## 5. Architecture et risques

**Schéma des grands composants et des échanges :** …  
**Données conservées par l'application :** …  
**Données consultées auprès du serveur :** …  
**Où vit la clé OpenRouter :** …  
**Point de confirmation par une personne :** …

| Risque ou dépendance | Conséquence | Signal précoce | Réponse prévue | Responsable |
|---|---|---|---|---|
| … | … | … | … | … |

## 6. Registre de décisions

| Date | Décision et responsable | Options examinées | Pourquoi maintenant ? | Conséquence / risque | Ce qui pourrait nous faire réviser |
|---|---|---|---|---|---|
| … | … | … | … | … | … |

## 7. Transmission au module agentique

**Mission initiale de l'agent :** L'agent aide … à … à partir de … Il peut … et doit demander une validation avant …  
**Première donnée du serveur à consulter :** …  
**Question technique que nous voulons trancher avec le premier agent :** …

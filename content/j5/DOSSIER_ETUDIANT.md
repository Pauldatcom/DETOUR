# Dossier de conception : travail en FOAD

Vous révisez la conception de l'application DÉTOUR à partir des faits observés pendant les expérimentations de l'agent. Le [cours écrit](NOTIONS.md) explique les notions ; la [démonstration](DEMO_CONCEPTION.md) montre une démarche sur un cas illustratif. Le [contrat du serveur](../../server/CONTRAT.md) borne les actions possibles.

## Organisation et pièces de départ

Une équipe de trois ou quatre possède un canal, un dossier partagé et un contact. Inscrivez les noms, les rôles et les créneaux annoncés. Conservez votre dossier de cadrage, une trace de consultation ou d'action, un incident et les résultats d'évaluation. Travaillez sur un parcours limité plutôt que sur une liste de fonctionnalités. Vous n'avez pas à produire du code neuf aujourd'hui.

Les rôles tournent entre les deux ateliers : cartographe, responsable des preuves, rédacteur des décisions et contradicteur. À trois, combinez deux rôles. Chaque personne laisse une contribution visible et défend un choix à la fin. La caméra est facultative ; utilisez oral, texte, annotation ou partage de document.

Une demande d'aide contient le lien de la pièce, l'observation, le blocage et une question précise. En cas de coupure, continuez sur votre copie locale et signalez le rendez-vous manqué dès le retour. Les échéances aménagées sont annoncées avec le formateur, elles ne sont pas implicites.

## Collecte initiale : 09:15 à 09:25

Sélectionnez deux faits utiles. Remplissez ce tableau sans confondre observation et explication.

| Référence | Conditions et paramètres | Observation | Nature de preuve | Interprétation à vérifier | Décision concernée |
|---|---|---|---|---|---|
| TRACE-01 | À compléter | À compléter | Direct / simulateur / rejeu / document | À compléter | À compléter |
| TRACE-02 | À compléter | À compléter | Direct / simulateur / rejeu / document | À compléter | À compléter |

Un fait peut confirmer votre choix. Une phrase du modèle ne prouve pas l'effet d'une action. Les clés et les informations inutiles sont retirées des traces partagées.

## Atelier 1 : lire et réviser le système

**11:31 à 12:16, 45 minutes.** Visez une conception lisible, pas une affiche parfaite.

1. Dessinez une vue de contexte : application de l'équipe, acteurs, systèmes extérieurs, périmètre et échanges principaux. Ne mélangez pas tous les fichiers dans cette vue.
2. Dessinez la vue des composants utile à votre parcours : rôle de chaque partie, données reçues, résultat produit, dépendances. Un composant ne doit pas nécessairement être un service déployé séparément.
3. Nommez au moins trois flux. Sur l'un d'eux, montrez la frontière où une demande de modèle devient ou ne devient pas une action réelle.
4. Suivez une donnée importante : création, source, conservation, version, invalidation ou expiration, reprise après rechargement.
5. Rédigez deux notes de décision, dont une influencée par une trace. Gardez les alternatives et les conséquences.
6. Notez deux risques concrets et leur réponse. Marquez actuel, correction proposée et élément à vérifier.

**Jalons internes :** 11 h 40, deux vues commencées ; 11 h 55, donnée suivie et première décision ; 12 h 08, incident choisi pour le checkpoint. L'objectif est de rendre votre travail observable pendant la FOAD.

### Canevas des composants

| Composant ou partie | Responsabilité | Entrées | Sorties | Règle portée | Actuel / cible | Preuve ou inconnu |
|---|---|---|---|---|---|---|
| À compléter | | | | | | |

### Canevas des données

| Donnée | Source qui fait foi | Qui la conserve ? | Version ou date | Quand devient-elle invalide ? | Relecture ou reprise | Limite connue |
|---|---|---|---|---|---|---|
| À compléter | | | | | | |

### Canevas ADR : une note par décision

```md
# ADR-___ : titre du choix
Date :
Auteur(s) :
Statut : proposé / accepté / remplacé

## Contexte et preuves
Quel besoin, contrainte ou incident nous conduit à choisir ?
Quelle trace permet de vérifier le contexte ?

## Décision
Nous décidons de ...
Qui porte la décision, qui met en œuvre ?

## Alternatives
Quelles options crédibles avons-nous examinées ?
Pourquoi les avons-nous écartées ou reportées ?

## Conséquences
Avantages, travail et coûts supplémentaires, limites et risques restants.

## Révision
Quel changement ou quelle nouvelle preuve ferait revoir ce choix ?
Quelle note remplace celle-ci le cas échéant ?
```

Une technologie suggérée par l'IA n'est pas une justification. Appuyez le choix sur les contraintes du projet et vérifiez les hypothèses. Une décision acceptée par l'équipe peut décrire une réalisation future ; son statut de mise en œuvre est distinct.

### Canevas des risques

| Événement incertain | Cause ou condition | Impact | Indice de priorité | Signal observable | Prévention ou reprise | Responsable | Risque restant |
|---|---|---|---|---|---|---|---|
| À compléter | | | | | | | |

Expliquez la priorité ; ne fabriquez pas de pourcentage. Un incident déjà survenu constitue une observation qui peut révéler un risque récurrent.

## Checkpoint conception : 12:16 à 12:30

Déposez les deux vues, les flux, la donnée et les décisions, même si une partie est incomplète. Présentez ou écrivez en deux minutes :

- La trace qui vous a appris quelque chose.
- La frontière ou la responsabilité concernée.
- Le choix confirmé, modifié ou encore inconnu.
- La correction prioritaire et son responsable.

Conservez le retour formateur. Repas de 12 h 30 à 13 h 30, sans travail imposé.

## Atelier 2 : cohérence et plan de livraison

**14:38 à 15:23, 45 minutes.** Complétez le dossier du matin.

1. Construisez trois chaînes de traçabilité. Partir d'un besoin ou d'une contrainte, écrire un critère observable, nommer la responsabilité de conception, puis relier preuve et tâche restante.
2. Écrivez deux exigences sous forme de scénarios : une sur le contrôle d'une action, une sur une qualité ou une reprise. Donnez des conditions, un seuil ou un invariant, une méthode et un statut. Un seuil proposé n'est pas une garantie fournisseur.
3. Construisez le plan de livraison. Montrez les dépendances, la capacité réelle, les responsables, les preuves de fin et ce qui est reporté. Incluez vérification, revue et préparation de la démonstration.
4. Justifiez une pratique de pilotage adaptée à la FOAD : limite de travaux en cours, rendez-vous de revue, binôme ou autre. Expliquez la contrainte et le signal qui vous ferait adapter la pratique.
5. Préparez l'accès à votre dossier pour la paire de revue.

**Jalons internes :** 14 h 50, première chaîne ; 15 h, deux scénarios ; 15 h 10, accès croisé ; 15 h 18, blocage et arbitrage prêts.

### Chaînes de traçabilité

| Besoin ou contrainte | Critère observable | Composant ou règle | Preuve référencée | Statut actuel | Tâche restante et responsable |
|---|---|---|---|---|---|
| À compléter | | | | Prouvé / à vérifier / à réaliser | |

### Exigence mesurable

```md
ID et qualité concernée :
Situation et déclencheur :
Conditions de l'observation :
Réponse attendue du système :
Mesure, seuil proposé ou invariant :
Début et fin de mesure, si délai :
Méthode et preuve à conserver :
Résultat actuellement observé :
Statut : proposé / éprouvé dans ce cas / non atteint / à réaliser
Limites de cette preuve :
Responsable et tâche restante :
```

### Plan de livraison

**Résultat essentiel :** à compléter. **Critères de réussite :** à compléter. **Limites annoncées :** à compléter. **Créneaux et capacité disponibles :** à compléter. **Hypothèses :** à compléter.

| Tâche orientée résultat | Responsable | Prérequis | Estimation et incertitude | Créneau | Preuve de fin | Repli ou report |
|---|---|---|---|---|---|---|
| À compléter | | | | | | |

Mettez un lien de précédence quand il est utile. Ne multipliez pas le nombre de personnes par le temps disponible sans examiner les tâches séquentielles. Pour un inconnu, prévoyez une investigation bornée avec une réponse attendue. Les points d'équipe ne deviennent pas automatiquement des heures.

### Pratique de pilotage

| Contrainte | Pratique choisie | Règle concrète | Bénéfice attendu | Signal de révision |
|---|---|---|---|---|
| À compléter | | | | |

Une pratique isolée ne signifie pas que toute une méthode est appliquée. Nommez honnêtement votre organisation.

## Checkpoint plan : 15:23 à 15:35

Publiez un blocage réel, son responsable, le créneau d'action et la décision de conserver, réduire ou reporter un élément. Montrer une preuve de fin et un repli. Corrigez les promesses qui ne sont pas encore prouvées avant de remettre le dossier à l'autre équipe.

## Revue croisée : 15:35 à 16:10

**Par paire :** 5 minutes de contexte commun, 10 minutes de revue A, 10 minutes de revue B, 10 minutes de retours et décisions. **Par trio :** 5 minutes de contexte, trois tours de 7 minutes avec rotation concepteur/relecteur/observateur, 9 minutes de décision. Chaque équipe reçoit une revue.

Parcourez une situation plutôt que toutes les pages : qui agit, sur quelle donnée, avec quel accord, et comment l'échec change le plan ? Ne jugez pas les personnes. Produisez deux observations sourcées et une priorité. Chaque observation contient une question ou une épreuve ; distinguez le fait certain de l'hypothèse.

| Équipe relectrice | Passage ou référence | Observation | Question ou scénario proposé | Impact présumé | Priorité motivée |
|---|---|---|---|---|---|
| À compléter | | | | | |

## Révision : 16:10 à 16:30

Répondez à chaque retour par une décision motivée : accepter, adapter ou refuser. Mettez à jour les vues, les ADR, les critères et le plan de manière cohérente. Si une correction est seulement prévue, indiquez son responsable et son statut. Préparez une version stable à 16 h 25.

| Retour reçu | Accepter / adapter / refuser | Raison et preuve | Pièces modifiées | Travail restant | Responsable |
|---|---|---|---|---|---|
| À compléter | | | | | |

## Défense : 16:30 à 16:50

Chaque personne explique une décision : besoin, preuve, alternative, conséquence et limite. En classe nombreuse, la défense se fait dans les paires et le formateur circule. Chaque membre ajoute une capsule écrite de trois phrases :

1. « J'ai contribué à ... et nous avons décidé ... »
2. « L'alternative était ... ; notre preuve ou contrainte est ... »
3. « La limite restante est ... et nous vérifierons ... »

Cette capsule rend la contribution identifiable ; elle ne remplace pas la capacité à répondre à une question. En cas d'aménagement FOAD, le formateur précise le mode de reprise orale ou écrite.

## Dépôt final : 16:50 à 17:00

Un dossier Markdown ou un index vers les pièces lisibles suffit. Réutilisez votre dépôt de projet ; aucun nouveau dépôt n'est obligatoire. Donnez un lien accessible, une version et une date. Exemple d'index :

```text
conception/
  INDEX.md                 # équipe, version, limites, liens
  VUES.md                  # contexte, composants, flux
  DONNEES.md               # source, cycle et reprise
  ADR-01.md
  ADR-02.md
  RISQUES.md
  CRITERES.md               # exigences et traçabilité
  PLAN-LIVRAISON.md
  REVUE.md                  # retours et réponses
  CONTRIBUTIONS.md
  preuves/                  # traces expurgées et références
```

L'index contient deux questions de décision métier pour la prochaine réunion client. Vérifiez les accès, retirez les clés et annoncez les pièces incomplètes. Ce dossier doit permettre de comprendre vos décisions, leur état actuel et la preuve encore nécessaire.

## Usage raisonné de l'IA

Vous pouvez faire relire une vue, demander une alternative ou reformuler un critère. Vous examinez la proposition, vérifiez le contrat et décidez. Notez une contribution significative utile et ce que vous avez accepté, corrigé ou refusé. N'envoyez pas de clés. Une architecture inventée par le modèle ne devient pas celle de votre application parce qu'elle paraît convaincante. Le dossier reste sous votre responsabilité.

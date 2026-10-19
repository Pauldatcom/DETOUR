# Piloter le changement : dossier de travail

**Gestion de projet / Conception · Équipes de 3 à 4 · Agence fictive DÉTOUR**

Le commanditaire revient avec une demande. Le Product Owner rencontre seul le client puis transmet au groupe. Votre mission : comprendre l'écart, concevoir une réponse, négocier un compromis et préparer une version candidate. Toute donnée et réservation est fictive. La quantité de code ou de fonctionnalités ne détermine pas l'évaluation.

## Point de départ

Ouvrir dossier de conception, registre de décisions, backlog et preuves d'évaluation de l'agent. Garder cette référence lisible. Nommer PO, cartographe, intégrateur et vérificateur ; les rôles tournent, en trinôme une personne peut tenir deux fonctions. La clé d'approbation reste auprès du conseiller, hors du contexte du modèle et du dépôt.

## Atelier 1 : préparer, recevoir et transmettre le changement

**10 minutes de préparation puis 35 minutes d'entretien et restitution.**

Écrire trois questions qui débloquent un choix. Le PO rencontre le client dans l'espace ou le canal indiqué. Les autres membres n'entendent pas l'entretien. Ils ne lisent pas les consignes privées du formateur. Après le retour du PO, distinguer :

| Information | Source et formulation | Statut | Décision affectée |
|---|---|---|---|
| Besoin communiqué | Note du PO ou réponse de suivi | Confirmé / supposé / inconnu | Parcours, donnée ou règle |
| Fait fournisseur | Identifiant, paramètres, heure, réponse API | Observé à cet instant | Proposition ou arrêt |

Reformuler en quatre lignes : utilisateur, problème, résultat attendu, contraintes. Faire repartir une question par le PO si nécessaire. Conserver la première formulation et la correction pour expliquer l'effet de la transmission.

## Atelier 2 : fiche d'impact CR-01

**40 minutes.** Aucun POST requis pour analyser le changement.

Jalons : 8 minutes pour référence et demande ; 10 minutes pour impact ; 10 minutes pour options ; 7 minutes pour estimation ; 5 minutes pour relecture.

### Fiche de changement

- Identifiant / origine / date / PO :
- Référence précédente, version et périmètre :
- Besoin nouvellement confirmé :
- Ce qui change ; ce qui reste valable :
- Contraintes et inconnues :
- Statut : à analyser / accepté / refusé / reporté.

### Carte d'impact

| Élément | Avant | Après demandé | Conséquence | Preuve ou question | Responsable |
|---|---|---|---|---|---|
| Acteurs / décision | | | | | |
| Données / état | | | | | |
| Parcours / flux | | | | | |
| Composants / contrats | | | | | |
| Permissions / validation | | | | | |
| Dépendances / risques | | | | | |

Ne pas limiter l'impact à l'écran. Une modification de participants affecte paramètres, prix, capacité, proposition et validité d'un accord précédent. Le programme contrôle le total et les actions. Le modèle n'est ni la source des places ni le détenteur de l'autorisation humaine.

### Comparer au moins deux réponses

| Option de conception | Besoin servi | Travail et dépendances | Risque / limite | Preuve de faisabilité | Compromis à négocier |
|---|---|---|---|---|---|
| A | | | | | |
| B | | | | | |

Une option de conception est une alternative de réponse. Une option créée par l'API bloque temporairement une prestation : ce sont deux sens différents.

### Estimation conditionnelle

Pour le travail retenu, décrire : petites preuves à obtenir, fourchette, expérience de référence, hypothèses, vérifications incluses, inconnue majeure et signal de dépassement. Si l'incertitude domine, proposer un essai borné avec observation et décision attendues. Une prévision suggérée par l'IA doit être examinée et assumée par l'équipe.

## Atelier 3 : négocier puis acter

**30 minutes.** Préparer une proposition de 45 secondes. Chaque passage dispose de **90 secondes tout compris** : 45 secondes de proposition, 30 secondes d'objection et réponse, 15 secondes d'accord reformulé ou de point restant à confirmer. À huit équipes, les échanges occupent douze minutes. Préparation 5 minutes ; réunion privée des PO 12 ; restitution et décision écrite en sortie 7 ; mise à jour 6.

Dire au client : besoin reformulé, réponse proposée, alternative, ce qui est inclus/exclu, conditions de délai, risque et décision attendue. Le PO rencontre le client puis restitue. Le groupe vérifie que la décision écrite en sortie correspond à ce qui a été accepté. Tout point non tranché conserve le statut à confirmer, avec une tâche de suivi du PO.

Au-delà de huit équipes, les propositions individuelles sont regroupées en quatre familles au maximum : trois minutes d'échange par famille. Un PO porte la question commune, les autres PO vérifient les conditions de leur propre équipe. Chacun restitue et rédige sa décision ; un accord commun ne couvre pas silencieusement une exception individuelle.

### Décision courte

- CR-01 et nouvelle référence :
- Décision et décideur / date :
- Options étudiées et raison du choix :
- Périmètre accepté, reporté et exclu :
- Critères révisés :
- Conditions, risque et signal de révision :
- Vérification d'une contribution IA : ce qui a été conservé, corrigé ou refusé.

L'accord sur un périmètre n'autorise aucune réservation. L'accord sur une action porte sur une proposition, des valeurs et un état précis.

## Atelier 4 : construire et préparer la candidate

**65 minutes.** 10 minutes de mise à jour ; 20 de parcours ; 15 d'échec ; 10 de revue ; 10 de fixation.

Mettre à jour dossier, carte, critères et tableau de suivi. Réaliser la plus petite preuve cohérente avec le périmètre accepté. Consulter les sources courantes. Montrer le choix humain et un arrêt. Une candidate partielle est annoncée avec ses écarts ; elle n'est pas décrite comme complète.

| Tâche | Critère soutenu | Propriétaire | Statut | Dépendance / blocage | Preuve |
|---|---|---|---|---|---|
| | | | À faire / en cours / vérifié | | |

Limiter l'encours selon le contexte. Choisir des pratiques utiles : revue courte, flux visible, binôme, test d'intégration. Expliquer pourquoi elles conviennent et quand les réviser. Il n'est pas nécessaire de prétendre appliquer Scrum si vous en utilisez seulement une pratique.

### Carte de risque

Événement incertain ; effet ; signal ; responsable du suivi ; réponse ; condition de révision. Un incident déjà observé n'est plus seulement un risque.

### Candidate RC-01

Version de fichiers/code ; configuration non secrète ; mode réel/rejeu ; instructions de lancement ; périmètre ; critères ; état initial ; preuves ; limites ; écarts et suite. Les clés restent en variables d'environnement ou côté serveur, hors des fichiers remis.

## Atelier 5 : revue préparatoire

**15 minutes.** Faire relire la candidate à une autre équipe. Rejouer un critère normal et un arrêt. Relever conformité, écart et question. Réviser une priorité. Aucun reset serveur avant conservation des identifiants et traces utiles.

## Critères de recette : canevas

| Référence du critère | Situation initiale | Action | Résultat observable | Preuve | Verdict et suite |
|---|---|---|---|---|---|
| | Version, demande, état | Qui fait quoi ? | Effet ou refus attendu | Trace datée, écran, état | Conforme / écart / non observé |

L'API ne fournit pas de panier atomique. Une lecture ne bloque aucune place ; une option unitaire bloque pendant 30 minutes. Une nouvelle action ou une nouvelle proposition exige le contrôle approprié. Voir [contrat API](../../server/CONTRAT.md).

## Remise

Fiche CR-01 ; notes du PO et restitution ; carte v2 ; options et estimation ; décision acceptée ; backlog/tableau ; risques ; critères ; candidate/instructions ; preuve courante et preuve d'arrêt ; limites et question individuelle préparée.

Les deux modules conservent leurs critères. Gestion / Conception évalue compréhension et environnement (30 %), conception et décisions (30 %), pilotage et changement (25 %), réunions/livraison/défense (15 %). Les choix agentiques sont une matière à analyser, pas une nouvelle note au nombre de fonctions. [Notions relisibles](NOTIONS.md) · [Démo](DEMO_CONCEPTION.md).

## Limite atomique du contrat fournisseur

Un GET juste avant le POST ne rend pas le prix atomique : le contrat ne transmet aucun prix attendu. Le POST peut créer une option à un autre prix. Le programme compare le prix renvoyé à l'accord, conserve l'option réellement créée dans un état à revoir, suspend confirmation et duplication, puis demande un nouvel accord. Il n'existe pas de route d'annulation d'option ; montrer expiration et limite plutôt qu'inventer une annulation. La prélecture réduit le risque sans garantir un prix inchangé. Cette limite doit figurer dans la conception, le guide de reprise et les critères de recette.

# Démonstration : passer d'un incident à une décision

Cette démarche publique montre comment raisonner. Elle utilise un petit incident illustratif et ne constitue pas le dossier corrigé d'une équipe. Les valeurs sont fictives ; elles ne garantissent aucun prix courant ni comportement déjà observé dans votre application. Choisissez vos propres preuves pour l'atelier.

## Situation de départ

Une application affiche une proposition à un conseiller. La consultation a retourné un prix pour une prestation et deux participants. Le conseiller veut l'examiner, puis recharge la page. L'interface ne retrouve plus la proposition. Nous voulons comprendre ce que cette observation implique pour la conception, avant de choisir une technologie ou de coder un nouveau stockage.

## 1. Séparer le fait et la conclusion

**Fait illustratif :** après rechargement, la proposition n'est plus affichée. **Interprétation possible :** elle n'était conservée que dans l'état de l'interface. **À vérifier :** un état peut exister côté programme ou un identifiant peut être disponible sans que l'interface le relise. **Décision encore ouverte :** quel niveau de reprise le produit doit-il offrir ?

Le fait ne justifie pas immédiatement l'installation d'une nouvelle base. Il faut examiner le parcours, le besoin de reprise et l'état déjà conservé.

## 2. Poser les vues utiles

Dans la vue de contexte, on conserve conseiller, application, modèle et serveur fournisseur. L'incident ne demande pas d'ajouter un nouvel acteur.

Dans la vue des composants, on cherche l'interface qui affiche la proposition, le composant qui conserve le dossier et le chemin de lecture après rechargement. On marque ce qui est connu et ce qui est une hypothèse. Le problème peut être un stockage absent, une référence perdue ou un contrat de reprise non défini.

Le flux à expliquer est `interface → état conservé → proposition retrouvée`. La flèche doit dire quel identifiant circule et quelle version elle retrouve. Le retour absent peut être dessiné en pointillé et noté “à observer”.

## 3. Ne pas confondre reprise et fraîcheur

Retrouver la proposition ne rend pas son prix actuel. Elle contient une observation passée avec ses paramètres et son heure. Pour prendre une option, le programme doit encore appliquer sa règle de revérification et l'accord porte sur les valeurs présentées. Une reprise correcte peut montrer “proposition retrouvée, à revérifier” plutôt que “toujours disponible”.

La relecture ne verrouille pas le prix. Le `POST /options` n'envoie aucun prix attendu ; un `HTTP 201` peut donc créer une option à un montant différent de celui accepté si le prix change entre les deux appels. Comparer `prix_total_eur` retourné à l'accord. Si les montants diffèrent, conserver l'option réelle, son identifiant et son expiration en « option à revoir », suspendre confirmation et duplication, puis montrer l'écart au conseiller pour une nouvelle décision. L'API ne fournit aucune annulation d'option. Une confirmation éventuelle demande encore une validation distincte sur une option valable ; après expiration, une nouvelle option exige d'abord un nouvel accord.

Cette distinction évite de réparer l'interface en créant une nouvelle promesse fausse.

## 4. Comparer les réponses possibles

Quelques options à examiner : conserver un dossier minimal côté application ; retrouver un dossier à partir d'un identifiant déjà connu ; accepter la perte de proposition dans le prototype et rendre cette limite visible. Pour chaque option, demander la complexité, le niveau de reprise, les données conservées et la preuve attendue.

L'exemple ne choisit pas à votre place. Une contrainte client, la capacité de l'équipe et l'état existant peuvent conduire à des réponses différentes. Si l'IA propose une base ou un schéma, comparez cette proposition aux contrats réels et aux besoins avant de décider.

## 5. Écrire une exigence proposée

Forme de travail : “Dans le parcours ... ; après l'événement ... ; le service doit ... ; nous vérifierons par ...”. Ajouter le statut proposé, les conditions et les limites. Une exigence de reprise demande notamment ce qui doit être retrouvé et ce qui doit être relu.

Il ne suffit pas d'écrire “ne pas perdre les données”. La durée, les données utiles et la portée de la reprise doivent être décidées. Une réponse testée sur un rechargement ne prouve pas automatiquement une reprise après arrêt du programme.

## 6. Préparer une décision et une tâche

L'ADR garde le contexte, la preuve, l'option choisie, les alternatives et les conséquences. Une tâche de livraison contient la vérification du scénario. Si l'équipe n'a pas encore observé le stockage, une courte investigation avec résultat attendu peut précéder la décision définitive.

Le plan ne dit pas simplement “ajouter une base”. Il précise ce que le conseiller doit retrouver, qui vérifie, le prérequis, la capacité et la preuve de fin. Ce qui dépasse le périmètre reste annoncé.

## 7. Faire relire la démarche

Une autre équipe peut demander : “Votre proposition retrouvée est-elle annoncée comme actuelle ?”, “Que se passe-t-il si les participants changent ?”, “Où gardez-vous les valeurs de l'accord ?”. Elle cite le passage du dossier et propose une épreuve. L'équipe conceptrice décide comment répondre.

Pour votre propre incident, reproduisez la démarche : fait → hypothèses à vérifier → vues utiles → alternatives → exigence → décision → plan → revue. Conservez les preuves et les inconnus ; ne recopiez pas un schéma qui ne décrit pas votre système.

# Architecture d'un agent sous contrôle humain

Le cas DÉTOUR sert à concevoir une boucle qui consulte des prestations, prépare une proposition et s'arrête pour laisser un conseiller décider avant une écriture. Les réservations sont fictives. Le [contrat de l'API](../../server/README.md) fixe les opérations disponibles.

## Composants et orchestration

Le **modèle** produit une réponse ou une demande d'outil à partir du contexte reçu. L'**orchestrateur** est le programme qui prépare ce contexte, conduit les tours, contrôle les outils, conserve les résultats et applique les arrêts. Un **adaptateur** traduit une interface dans une autre : format d'API du modèle ou requête HTTP d'un outil. Le **serveur métier** fournit les prix, les places et les effets d'une option ou d'une réservation.

Ces responsabilités peuvent vivre dans un seul programme. Les distinguer permet de savoir où corriger une erreur et ce qui doit rester fiable après un changement de modèle. La clé d'équipe est utilisée par l'adaptateur HTTP ; elle n'est pas un argument que le modèle doit générer.

## Chaîne, routage et agent

| Organisation | Qui fixe la suite ? | Cas DÉTOUR | Limite |
|---|---|---|---|
| Chaîne ou workflow fixe | Le code impose les étapes. | Valider une demande, lire une disponibilité, calculer un total. | Une branche imprévue doit être prévue dans le programme. |
| Routage | Une décision sélectionne une branche définie. | Demande incomplète : préciser ; demande complète : consulter. | Le choix de branche peut être incorrect et doit être contrôlé. |
| Agent borné | Le modèle choisit une action parmi celles autorisées. | Chercher une prestation, observer son résultat puis adapter la recherche. | Des tours supplémentaires coûtent du temps et créent des risques. |

Un produit peut combiner ces organisations. Une recherche peut être agentique pendant que l'option suit un workflow fixe avec accord humain. Le patron se choisit selon la mission ; un framework ou un LLM ne détermine pas à lui seul l'architecture.

## Planification et exécution

Un **plan** décrit des actions envisagées. Une **exécution** réalise une action effectivement autorisée. Le plan « chercher un train, bloquer deux places, confirmer » ne constitue ni accord ni preuve d'effet.

À chaque étape, le programme vérifie les arguments, la permission, les données utiles et l'accord requis. Une observation nouvelle peut invalider le plan. Il faut alors réviser la suite plutôt qu'exécuter des étapes préparées pour une ancienne demande.

## Délégation et sous-agents

Un sous-agent est une boucle spécialisée à laquelle un orchestrateur délègue une mission. Il retourne un résultat dont la synthèse reste à contrôler. Deux recherches indépendantes peuvent être parallélisées ; deux écritures dans le même dossier demandent une coordination explicite.

Pour DÉTOUR, transport et activité peuvent être recherchés séparément. La délégation ne donne aucun droit supplémentaire de réserver. Elle ajoute aussi des appels, des contextes et des conflits possibles. Un agent unique reste une architecture recevable lorsqu'il suffit à la mission.

## Contexte, mémoire et état

| Notion | Définition | Exemple | Point de contrôle |
|---|---|---|---|
| Contexte du tour | Informations transmises au modèle pour une requête. | Demande utile et résultat de disponibilité. | Ne garder que les informations pertinentes ; distinguer règles et données. |
| Mémoire applicative | Informations conservées puis éventuellement réintroduites. | Préférence sans voiture ou résumé d'échanges. | Source, durée utile et possibilité d'une information périmée. |
| État métier | Statut contrôlé du dossier et données nécessaires aux actions. | Version de demande, accord, `option.id`, `expire_le`. | Conserver les valeurs exactes et leurs transitions. |

Un résumé généré ne remplace pas un accord humain identifiable. La conversation n'est pas la source de vérité des options. Un stockage en mémoire du programme peut suffire au TP si le risque de perte après redémarrage est expliqué.

## Recherche augmentant la génération : RAG

Dans un parcours RAG, une recherche retrouve des extraits pertinents, le programme les ajoute au contexte, puis le modèle génère une réponse. Une recherche lexicale ou vectorielle peut servir à retrouver une politique ou une description.

Le résultat garde les limites de sa source. Un ancien document de tarifs ne prouve pas le stock courant. Pour une date et un groupe précis, DÉTOUR demande une consultation opérationnelle du serveur. Le TP ne requiert aucun moteur de RAG.

## Machine à états et gardes

Une **machine à états** décrit les statuts possibles et les transitions autorisées. Une transition peut être déclenchée par un **événement** et protégée par une **garde**, c'est-à-dire une condition qui doit être vraie.

```text
proposition_prete
  → accord sur les valeurs de l'action
  → revérification inchangée
  → appel POST /options
  → HTTP 201 avec identifiant et expiration
  → option_active
```

Si la revérification diffère ou si le serveur refuse, le programme ne passe pas à `option_active`. Il conserve le refus et revient vers une décision. Une phrase du modèle ne déclenche pas un effet serveur.

La revérification et le POST restent deux appels distincts. L'API ne reçoit aucun prix attendu : le prix peut encore changer entre eux. Comparer le total du POST au total accepté. Si l'option a été créée à un autre prix, son effet existe ; l'application conserve identifiant et expiration dans un état **option créée à revoir**, montre l'écart et suspend la confirmation. Elle ne crée pas une seconde option automatiquement. Cette limite du contrat doit être explicitée au conseiller.

## Contrat d'outil et effet de bord

Le contrat décrit le nom, la mission, les arguments, les résultats, les erreurs et les effets d'une opération. Le schéma vérifie la forme ; les règles métier vérifient le sens. Une date bien formée peut être impossible et un entier peut être négatif.

Un **effet de bord** est un changement extérieur au calcul : bloquer des places, confirmer ou envoyer un message. Les lectures et les écritures n'ont donc pas les mêmes règles de reprise. La description d'un outil doit expliquer ses limites : une disponibilité positive ne constitue pas une réservation.

## MCP et frontière de confiance

MCP connecte une application hôte à des serveurs qui exposent des outils et du contexte. Un client MCP gère la connexion dans l'hôte ; le serveur peut donner accès à une API métier. Le protocole ne choisit ni le modèle ni la politique de réservation.

Un adaptateur MCP pourrait envelopper `verifier_disponibilite`, mais le serveur livré pour ce cours est une API HTTP directe. MCP, son intégration et ses détails de transport ne sont pas requis pour le TP. Un connecteur ne transforme pas un texte externe en consigne fiable et n'accorde pas les permissions métier.

## Accord humain versionné

L'accord porte sur une action précise : prestation, date, groupe, prix revérifié et conditions. Le programme conserve la décision, la personne, l'instant et la version de la demande affichée.

Un nouveau prix ou un nouveau groupe invalide la portée de l'ancien accord. La clé d'approbation donne un accès technique à une route ; elle ne prouve pas à elle seule qui a décidé. Le modèle ne reçoit pas cette clé et n'invente pas `approuve_par`. La confirmation exige une seconde validation distincte.

## Timeout et idempotence

Un timeout indique une absence de réponse dans le délai attendu. Une écriture peut déjà avoir eu lieu. Répéter le `POST` peut donc produire un second effet.

Une opération **idempotente** permet de répéter la même intention sans ajouter de nouvel effet, dans les limites du contrat du service. Le simulateur DÉTOUR ne fournit pas de clé d'idempotence. Après une écriture incertaine, le programme évite la reprise automatique, consulte les options et conserve l'incertitude si aucune correspondance fiable ne peut être établie. Il demande alors une décision humaine. Un `409` décrit au contraire un refus explicite, pas une réussite à supposer.

## Opérations partielles et compensation

Une transaction atomique réussirait ou échouerait comme un tout. Le serveur DÉTOUR traite les prestations séparément : une option train peut exister alors qu'un hôtel est indisponible.

Une **compensation** corrige un effet déjà produit, si une opération adaptée existe. DÉTOUR ne fournit pas d'annulation d'option ni de rollback de séjour. Le dossier doit montrer l'état de chaque prestation, l'expiration et la décision de reprise, sans annoncer une annulation globale inventée.

## Observabilité

Une trace utile relie une demande versionnée à un outil demandé, un verdict de validation, une décision humaine, un appel HTTP et un résultat. Elle distingue **demandé**, **autorisé**, **envoyé** et **accepté**.

Les clés ne sont pas journalisées. L'état et les événements sont enregistrés par le programme ; ils ne sont pas réécrits après coup à partir d'un récit du modèle. Cette trace permet de diagnostiquer un incident et de défendre une décision de conception.

## Références

Repères documentaires vérifiés le 14 octobre 2026 : [patrons de systèmes agentiques](https://www.anthropic.com/engineering/building-effective-agents), [coordination multi-agent](https://www.anthropic.com/engineering/multi-agent-research-system), [architecture MCP](https://modelcontextprotocol.io/docs/learn/architecture), [contrat des outils MCP](https://modelcontextprotocol.io/specification/latest/server/tools), [reprises et idempotence](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/). Les exemples DÉTOUR sont des applications pédagogiques ; le contrat local reste la référence des opérations réalisables.

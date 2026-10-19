# Construire une proposition sous contrôle humain

Vous reprenez votre cadrage de **DÉTOUR** et votre premier agent de consultation. Le [brief de mission](../../output/pdf/brief-option.pdf) donne la demande du client. Le [contrat du serveur](../../server/README.md) fixe les seules opérations réelles. Les voyages et les réservations sont fictifs.

**Résultat attendu :** une demande du conseiller mène à une proposition fondée sur le catalogue et les disponibilités. Le conseiller peut accepter, corriger ou refuser. Une option peut ensuite être posée sur une prestation **après son accord explicite** ; la confirmation d'une réservation simulée demande une seconde validation humaine distincte. L'agent n'obtient jamais la clé d'approbation.

Travaillez par équipes de 3 ou 4. Répartissez les rôles de Product Owner, responsable de l'agent, responsable des appels serveur et conseiller de contrôle ; échangez les rôles pendant les essais. Le PO porte les questions au client joué par le formateur et restitue les réponses à l'équipe.

Le [cours écrit](NOTIONS.md) définit les notions utilisées ci-dessous. Les durées de séquence comprennent les apports, les démonstrations et leurs applications. MCP, RAG et sous-agents sont étudiés pour comparer des architectures ; leur implémentation n'est pas demandée.

## Séquence 1 : Demande et architecture · 60 min

Relisez votre dossier de cadrage et la trace de votre premier agent. Retenez deux décisions qui tiennent encore et une limite révélée par l'essai. Le PO présente au client votre compréhension de la nouvelle demande, pose une question qui peut changer le parcours, puis retransmet la réponse au groupe. Écrivez ce qui relève du besoin confirmé, de votre hypothèse et de l'arbitrage à faire.

Placez ensuite modèle, orchestrateur, adaptateurs et serveur métier. Pour une recherche de prestations puis une option, indiquez ce qui peut relever d'une chaîne fixe, d'un routage ou d'un choix du modèle. Justifiez votre choix par la mission et les risques ; un agent unique peut suffire.

## Séquence 2 : Contexte et état · 50 min

Sur une page, dessinez le parcours **demande → consultation → proposition → décision → option éventuelle → confirmation éventuelle**. Placez voyageur, conseiller, votre application, modèle via OpenRouter et serveur fictif. Pour chaque flèche, marquez lecture ou écriture, donnée transmise, détenteur de la clé et preuve à conserver.

Choisissez et justifiez : le modèle sélectionne-t-il les prestations à consulter, ou le programme applique-t-il une recherche déterministe ? Une recherche simple peut rester un workflow ; la présence d'un LLM ne suffit pas à rendre l'ensemble agentique. Si le modèle choisit un outil, définissez les noms et arguments autorisés. Dans tous les cas, le programme contrôle les appels HTTP et les limites d'étapes.

Ajoutez les états **proposition non validée**, **option active**, **option expirée** et **réservation confirmée**. Pour chacun, écrivez l'événement réel qui permet d'y entrer. Une phrase du modèle ne modifie jamais seule cet état.

Pour deux transitions, écrivez **état de départ → événement → garde → action éventuelle → preuve → état d'arrivée**. Classez une préférence, un ancien prix, un résumé et `option.id` entre contexte du tour, mémoire choisie et état métier. Expliquez quelle information demande une lecture actuelle plutôt qu'une recherche dans un document.

## Séquence 3 : Contrats, permissions et lectures · 62 min

Complétez ce contrat avant de coder :

| Élément | Votre décision vérifiable |
|---|---|
| Mission | Quelle demande l'agent résout-il ? |
| Lecture | Quels `GET` et quels arguments sont autorisés ? |
| Écriture | Qui peut déclencher `POST /options` ? Par quelle preuve d'accord ? |
| Confirmation | Qui possède `X-Approval-Key` et où est recueilli `approuve_par` ? |
| Données | Quelle information vient du serveur, du modèle ou du conseiller ? |
| État | Comment distinguer proposition, option active, option expirée, réservation confirmée ? |
| Arrêt | Nombre maximal d'appels OpenRouter et d'outils ; conduite si serveur ou modèle échoue. |
| Trace | Événements conservés, sans clés ni données inutiles. |

Faites relire le contrat par une autre équipe. Elle tente de trouver un chemin où le modèle pourrait poser une option ou annoncer une réservation sans preuve. Corrigez le contrat et gardez la décision dans votre registre.

Avec la [démonstration du serveur](DEMO_SERVEUR.md), comparez `train-nantes-01` et `activite-nantes-01` dans la démonstration de composition pour le 7 novembre 2026 et deux voyageurs. Relevez le prix total et la disponibilité **de chaque prestation**. Identifiez la donnée du serveur qui prouve chaque état. Une proposition de séjour est une composition de résultats distincts : le serveur ne fournit aucun panier ni garantie que toutes les options réussiront.

Sur le schéma, montrez où un éventuel adaptateur MCP se placerait. Il ne change ni les routes de l'API ni les accords à obtenir. Gardez l'intégration HTTP directe pour votre parcours.

## Séquence 4 : Accord versionné et option · 38 min

Après les lectures, jouez le parcours à quatre rôles : conseiller, agent, programme et serveur. Le programme montre au conseiller la prestation, la date, le groupe, le total et l'heure de vérification, puis s'arrête avant le `POST`. Le conseiller accepte ou refuse **cette option précise**. Un refus termine le parcours sans écriture. Après un accord, revérifiez prix et places ; si rien n'a changé, vous pouvez seulement alors essayer `POST /options` et lire `option.id`, `statut` et `expire_le`. Si les faits diffèrent, revenez au conseiller avant tout `POST`. Aucun membre ne lance d'écriture « pour voir » sans accord explicite, même dans le simulateur. Après le POST, comparer aussi prix_total_eur retourné au total accepté : une revérification GET ne rend pas l'écriture atomique. Le serveur ne reçoit aucun prix attendu et peut créer l'option à un nouveau total entre les deux appels. Dans ce cas, conserver son identifiant et son expiration, marquer option créée à revoir, montrer l'écart au conseiller et suspendre toute confirmation ou répétition. Il n'existe pas de route d'annulation d'option. Le livrable minimal peut porter sur une seule prestation ; la comparaison de deux lectures sert à comprendre la composition.

## Séquence 5 : Incidents, reprise et trace · 60 min

Étudiez d'abord les deux cartes de [démonstration d'architecture](DEMO_ARCHITECTURE.md) : réponse perdue après écriture et succès d'une prestation suivi d'un refus sur une autre. Distinguez effet inconnu et refus certain. Ces cartes sont des scénarios de conception ; elles ne prouvent pas qu'un timeout a été injecté dans le serveur. Notez pourquoi répéter un `POST` ou inventer une annulation globale serait incorrect.

Rejouez trois situations dans cet ordre. D'abord, après accord du conseiller pour **un essai d'échec distinct**, demandez une option impossible et lisez le `409` réel ; l'application doit montrer le refus et demander une nouvelle décision. Ensuite, si le formateur modifie le prix entre consultation et option, comparez les deux totaux : l'ancien accord ne couvre pas le nouveau prix, donc le programme suspend l'écriture. Enfin, examinez une confirmation de réservation : elle requiert une option encore valide et une **seconde validation humaine distincte**. La confirmation est faite par le programme, jamais par un outil du modèle. Si vous la démontrez réellement, créez d'abord une **nouvelle option après un nouvel accord**, puis demandez une autre validation au conseiller avant `POST /reservations` ; ne réutilisez pas l'option posée avant la pause, qui expire après 30 minutes.

## Séquence 6 : Intégrer l'agent et traiter un incident · 115 min

Si vous ajoutez un hébergement, vérifiez-le aussi. Une proposition assemblée n'est pas un panier confirmé.

Branchez votre programme sur OpenRouter avec un **modèle gratuit compatible avec les outils**. Choisissez son identifiant au moment du TP depuis [la liste des modèles](https://openrouter.ai/models?supported_parameters=tools) et placez-le dans `OPENROUTER_MODEL`. Placez la clé dans `OPENROUTER_API_KEY` côté programme, hors du dépôt et du navigateur. Gardez un budget de **quatre appels OpenRouter maximum par scénario**, sans bascule payante. Le modèle propose les appels d'outils ; le programme vérifie nom, types et arguments, appelle le serveur puis renvoie le résultat au modèle. Le [squelette de consultation](../j2/starter-agent.mjs) peut servir de point de départ.

Votre sortie distingue les faits avec leur source, les hypothèses et les informations manquantes. Elle ne dit « option posée » que si le serveur a renvoyé une option, et « réservation confirmée » que si le serveur a renvoyé une réservation. Le conseiller reçoit le détail des prix, l'heure des vérifications et les actions possibles.

Après accord explicite, **revérifiez** prix et disponibilité juste avant d'écrire. Si le résultat diffère de ce que le conseiller a accepté, montrez la différence et demandez une nouvelle décision. Posez ensuite une option sur **une** prestation. Gardez la réponse réelle `option.id`, `prix_total_eur`, `expire_le` et `statut`. Une option bloque des places pendant 30 minutes, pas indéfiniment. Si plusieurs options sont souhaitées, elles sont indépendantes : préparez la règle à appliquer si seule la première réussit.

Pour une confirmation simulée, le conseiller revoit l'option effective et valide une seconde fois. Le programme reçoit alors `X-Approval-Key` et `approuve_par` **hors du contexte du modèle**. Si cette validation distincte n'est pas disponible, arrêtez-vous à l'option et indiquez « confirmation non effectuée ».

Testez un échec réel : `participants=20` sur le train donne une option refusée par `409 unavailable`. Si le formateur modifie le prix ou la capacité entre vos lectures et l'option, montrez l'écart et redemandez un accord au conseiller sur les nouvelles données. Si l'option expire, ne réutilisez pas son ancien `id` pour promettre une confirmation.

Pour chaque cas, écrivez trois choses : **ce que dit le serveur**, **ce que propose le modèle**, **ce que décide l'humain**. Rejouez le parcours sans OpenRouter avec la [trace de secours](TRACE_REJEU_ETUDIANT.md) si le service gratuit échoue. Le résultat du serveur reste réel ; notez clairement quelle partie de la boucle n'a pas pu être vérifiée en direct.

## Séquence 7 : Démonstration et défense · 35 min

Présentez un cas normal et un échec. Chaque membre explique une décision prise sans déléguer son jugement au modèle. Le groupe montre où la source de vérité est consultée, où l'option est autorisée, et quelle réponse du serveur prouve son état. Préparez une question pour le client : quelle règle métier manque encore pour gérer deux options dont une seule réussit ?

## À remettre

- Schéma du système avec frontières de confiance et permissions.
- Contrat de l'agent corrigé après revue croisée.
- Parcours démontrable ou blocage localisé, avec limite d'appels et sans clé dans le dépôt.
- Proposition, trace expurgée, décision du conseiller et réponse serveur pour l'option ou son refus.
- Une page de décisions : choix, raison, risque, signal de révision ; un cas où vous avez corrigé ou refusé la sortie de l'IA.

Le nombre de fonctionnalités ne compte pas. Vous devez pouvoir expliquer pourquoi une phrase plausible du modèle n'est pas une preuve de prix, de stock ou de réservation.

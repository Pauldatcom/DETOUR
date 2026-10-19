window.COURSE_DECK.push(
{
  "id": "j3-ouverture",
  "day": 3,
  "eyebrow": "Agentique IA · actions",
  "hero": true,
  "title": "Disponible<br>n’est pas réservé.",
  "subtitle": "Une proposition. Un conseiller. Une option sous contrôle.",
  "html": "<div class=\"hero-grid\"><div class=\"poster\" style=\"background:#083d45\"><h3>Un prix peut changer entre deux appels.</h3><span class=\"poster-mark\" style=\"color:#7bd6c3\">◎</span><span class=\"stamp\">DÉTOUR · NOUVELLE MISSION</span></div><div class=\"card teal\"><small>Le seuil</small><strong>La décision du conseiller</strong><p>Avant toute option. Encore une fois avant confirmation.</p></div></div>"
},
{
  "id": "j3-titre-architecture",
  "day": 3,
  "title": "Architecture de l’agent",
  "eyebrow": "Séquence 01",
  "html": "<div class=\"poster section-poster\"><h3>Séparer les décisions et les responsabilités.</h3><span class=\"poster-mark\">01</span><span class=\"stamp\">DÉTOUR · ARCHITECTURE AGENTIQUE</span></div>",
  "hero": true
},
{
  "id": "j3-client",
  "day": 3,
  "eyebrow": "La demande du client",
  "title": "« Je veux pouvoir défendre chaque proposition. »",
  "html": "<div class=\"quote-card teal\">« Si le prix change, montrez-le au conseiller avant qu’il décide. »<footer>Direction de l’agence DÉTOUR</footer></div>",
  "exercise": "../content/j3/DOSSIER_ETUDIANT.md"
},
{
  "id": "j3-composition",
  "day": 3,
  "eyebrow": "Proposition de séjour",
  "title": "Un séjour, plusieurs vérités.",
  "html": "<div class=\"three-up\"><div class=\"card\"><small>Transport</small><strong>Prix vérifié ?</strong><p>Une réponse du serveur.</p></div><div class=\"card\"><small>Hébergement</small><strong>Places vérifiées ?</strong><p>Une autre réponse.</p></div><div class=\"card teal\"><small>Activité</small><strong>Date vérifiée ?</strong><p>Aucun panier global.</p></div></div>"
},
{
  "id": "j3-composants",
  "day": 3,
  "title": "Les composants et leurs responsabilités",
  "eyebrow": "Architecture · définition",
  "html": "<div class=\"three-up\"><div class=\"card teal\"><small>Modèle</small><strong>Choisit et propose</strong><p>Contexte, prochaines actions et réponse.</p></div><div class=\"card \"><small>Orchestrateur</small><strong>Organise et contrôle</strong><p>Boucle, validations, état et budget.</p></div><div class=\"card orange\"><small>Serveur métier</small><strong>Détient les faits</strong><p>Prix, places, identifiants et effets.</p></div></div>"
},
{
  "id": "j3-patrons",
  "day": 3,
  "title": "Chaîne, routage ou agent ?",
  "eyebrow": "Architecture · choix",
  "html": "<div class=\"three-up\"><div class=\"card teal\"><small>Étapes connues</small><strong>Chaîne fixe</strong><p>Le code impose l’ordre des opérations.</p></div><div class=\"card \"><small>Cas distincts</small><strong>Routage</strong><p>Un choix mène à une branche définie.</p></div><div class=\"card orange\"><small>Suite variable</small><strong>Agent borné</strong><p>Le modèle choisit dans une liste autorisée.</p></div></div>"
},
{
  "id": "j3-plan-execution",
  "day": 3,
  "title": "Un plan n’autorise aucune action",
  "eyebrow": "Architecture · planification",
  "html": "<div class=\"flow teal\"><div class=\"step\"><span class=\"num\">PLAN</span><strong>Actions envisagées</strong></div><div class=\"step\"><span class=\"num\">CONTRÔLE</span><strong>Conditions et permissions</strong></div><div class=\"step\"><span class=\"num\">EXÉCUTION</span><strong>Appel autorisé</strong></div><div class=\"step\"><span class=\"num\">OBSERVATION</span><strong>Résultat réel</strong></div></div>"
},
{
  "id": "j3-sous-agents",
  "day": 3,
  "title": "Sous-agents : missions et frontières",
  "eyebrow": "Architecture · délégation",
  "html": "<div class=\"three-up\"><div class=\"card teal\"><small>Découpage</small><strong>Une mission par spécialiste</strong><p>Chercher une activité ou comparer un trajet.</p></div><div class=\"card \"><small>Coordination</small><strong>Une synthèse responsable</strong><p>L’orchestrateur arbitre les contradictions.</p></div><div class=\"card orange\"><small>Risque</small><strong>État partagé et coût</strong><p>Pas d’écritures concurrentes sans règle.</p></div></div>"
},
{
  "id": "j3-titre-contexte",
  "day": 3,
  "title": "Contexte et état",
  "eyebrow": "Séquence 02",
  "html": "<div class=\"poster section-poster\"><h3>Le modèle reçoit un extrait. Le dossier conserve l’histoire utile.</h3><span class=\"poster-mark\">02</span><span class=\"stamp\">DÉTOUR · ARCHITECTURE AGENTIQUE</span></div>",
  "hero": true
},
{
  "id": "j3-contexte",
  "day": 3,
  "eyebrow": "Architecture de l’agent",
  "title": "Le contexte passe. L’état reste.",
  "html": "<div class=\"two-up\"><div class=\"card teal\"><small>Tour du modèle</small><strong>Contexte</strong><p>Demande · règles · observations utiles</p></div><div class=\"card orange\"><small>Application</small><strong>État</strong><p>Dossier · décisions · option.id · expiration</p></div></div>"
},
{
  "id": "j3-memoire",
  "day": 3,
  "title": "Contexte, mémoire et état métier",
  "eyebrow": "Notion · persistance",
  "html": "<div class=\"three-up\"><div class=\"card teal\"><small>Contexte</small><strong>Entrée du tour</strong><p>Informations sélectionnées pour le modèle.</p></div><div class=\"card \"><small>Mémoire applicative</small><strong>Conservation choisie</strong><p>Résumé ou préférences, avec source et durée.</p></div><div class=\"card orange\"><small>État métier</small><strong>Statut contrôlé</strong><p>Demande, accords, option et expiration.</p></div></div>"
},
{
  "id": "j3-recherche-contexte",
  "day": 3,
  "title": "RAG : retrouver avant de générer",
  "eyebrow": "Notion · recherche documentaire",
  "html": "<div class=\"flow teal\"><div class=\"step\"><span class=\"num\">QUESTION</span><strong>Besoin d’information</strong></div><div class=\"step\"><span class=\"num\">RECHERCHE</span><strong>Extraits pertinents</strong></div><div class=\"step\"><span class=\"num\">CONTEXTE</span><strong>Sources sélectionnées</strong></div><div class=\"step\"><span class=\"num\">MODÈLE</span><strong>Réponse à vérifier</strong></div></div>"
},
{
  "id": "j3-transition",
  "day": 3,
  "title": "Événement, garde et transition",
  "eyebrow": "Notion · machine à états",
  "html": "<div class=\"three-up\"><div class=\"card teal\"><small>Événement</small><strong>Un fait arrive</strong><p>Un conseiller accepte une action précise.</p></div><div class=\"card \"><small>Garde</small><strong>Une condition est vérifiée</strong><p>Accord valable et prix revérifié inchangé.</p></div><div class=\"card orange\"><small>Transition</small><strong>L’état est mis à jour</strong><p>Option active après le retour HTTP 201.</p></div></div>"
},
{
  "id": "j3-etats",
  "day": 3,
  "eyebrow": "États du dossier",
  "title": "Une phrase ne change pas l’état.",
  "html": "<div class=\"flow teal\"><div class=\"step\"><span class=\"num\">01</span><strong>Demande</strong></div><div class=\"step\"><span class=\"num\">02</span><strong>Proposition</strong></div><div class=\"step\"><span class=\"num\">03</span><strong>Accord</strong></div><div class=\"step\"><span class=\"num\">04</span><strong>Option active</strong></div></div>",
  "exercise": "../content/j3/DOSSIER_ETUDIANT.md"
},
{
  "id": "j3-titre-outils",
  "day": 3,
  "title": "Contrats et permissions",
  "eyebrow": "Séquence 03",
  "html": "<div class=\"poster section-poster\"><h3>Un outil expose une opération précise.</h3><span class=\"poster-mark\">03</span><span class=\"stamp\">DÉTOUR · ARCHITECTURE AGENTIQUE</span></div>",
  "hero": true
},
{
  "id": "j3-contrat-outil",
  "day": 3,
  "title": "Le contrat d’un outil",
  "eyebrow": "Notion · contrat",
  "html": "<div class=\"three-up\"><div class=\"card teal\"><small>Entrée</small><strong>Schéma et sens</strong><p>Identifiant, date réelle, entier positif.</p></div><div class=\"card \"><small>Sortie</small><strong>Faits et statut</strong><p>Donnée contrôlée, erreur ou limite.</p></div><div class=\"card orange\"><small>Effet</small><strong>Lecture ou écriture</strong><p>Permission, accord et trace attendus.</p></div></div>"
},
{
  "id": "j3-mcp",
  "day": 3,
  "title": "MCP : connecter des outils et du contexte",
  "eyebrow": "Notion · protocole",
  "html": "<div class=\"flow teal\"><div class=\"step\"><span class=\"num\">HÔTE</span><strong>Application IA</strong></div><div class=\"step\"><span class=\"num\">CLIENT MCP</span><strong>Connexion au serveur</strong></div><div class=\"step\"><span class=\"num\">SERVEUR MCP</span><strong>Outils et ressources</strong></div><div class=\"step\"><span class=\"num\">SERVICE</span><strong>API ou données</strong></div></div>"
},
{
  "id": "j3-mcp-confiance",
  "day": 3,
  "title": "Un connecteur n’accorde aucun pouvoir métier",
  "eyebrow": "Notion · frontière de confiance",
  "html": "<div class=\"three-up\"><div class=\"card teal\"><small>Connexion</small><strong>Serveur identifié</strong><p>Origine, opérations et données visibles.</p></div><div class=\"card \"><small>Données</small><strong>Entrées à traiter</strong><p>Un résultat peut contenir une fausse consigne.</p></div><div class=\"card orange\"><small>Permissions</small><strong>Actions bornées</strong><p>La liste et l’accord restent contrôlés.</p></div></div>"
},
{
  "id": "j3-permissions",
  "day": 3,
  "eyebrow": "Permissions",
  "title": "Lire. Bloquer. Confirmer.",
  "html": "<div class=\"three-up\"><div class=\"card teal\"><small>GET</small><strong>Consulter</strong><p>Prix et disponibilité.</p></div><div class=\"card orange\"><small>POST</small><strong>Poser une option</strong><p>Accord explicite du conseiller.</p></div><div class=\"card\"><small>POST + CLÉ</small><strong>Confirmer</strong><p>Seconde validation humaine.</p></div></div>"
},
{
  "id": "j3-frontiere",
  "day": 3,
  "eyebrow": "Frontière de confiance",
  "title": "Le modèle propose. Le programme contrôle.",
  "html": "<div class=\"flow teal\"><div class=\"step\"><span class=\"num\">MODÈLE</span><strong>Demande un outil</strong></div><div class=\"step\"><span class=\"num\">CODE</span><strong>Valide arguments et droit</strong></div><div class=\"step\"><span class=\"num\">SERVEUR</span><strong>Retourne un fait</strong></div><div class=\"step\"><span class=\"num\">CODE</span><strong>Conserve la trace</strong></div></div>"
},
{
  "id": "j3-source",
  "day": 3,
  "eyebrow": "Source de vérité",
  "title": "Une consultation ne bloque rien.",
  "html": "<div class=\"mini-ui\"><div class=\"ui-head\"><span>GET / DISPONIBILITÉS</span><span>DÉTOUR</span></div><div class=\"ui-body\"><div class=\"ui-line\"><strong>Disponible</strong><span class=\"status\">À CET INSTANT</span></div><div class=\"ui-line\"><strong>Prix</strong><span>À REVÉRIFIER</span></div><div class=\"ui-line\"><strong>Option</strong><span>AUCUNE</span></div></div></div>",
  "exercise": "../content/j3/DEMO_SERVEUR.md"
},
{
  "id": "j3-lecture-ecriture",
  "day": 3,
  "title": "Lecture et écriture n’ont pas le même effet",
  "eyebrow": "Notion · effets de bord",
  "html": "<div class=\"three-up\"><div class=\"card teal\"><small>GET</small><strong>Observer</strong><p>Le stock reste disponible pour les autres.</p></div><div class=\"card \"><small>POST option</small><strong>Modifier</strong><p>Des places sont retenues temporairement.</p></div><div class=\"card orange\"><small>POST réservation</small><strong>Engager</strong><p>Une confirmation distincte et approuvée.</p></div></div>"
},
{
  "id": "j3-accord-valable",
  "day": 3,
  "title": "L’accord porte sur une action versionnée",
  "eyebrow": "Notion · contrôle humain",
  "html": "<div class=\"three-up\"><div class=\"card teal\"><small>Action</small><strong>Quoi et pour qui</strong><p>Prestation, date et participants.</p></div><div class=\"card \"><small>Conditions</small><strong>Quelles valeurs</strong><p>Prix actuel, durée et limites.</p></div><div class=\"card orange\"><small>Décision</small><strong>Qui, quand, quelle version</strong><p>Acceptation ou refus explicite conservé.</p></div></div>"
},
{
  "id": "j3-conseiller",
  "day": 3,
  "eyebrow": "Jeu de rôle",
  "title": "Quel accord, pour quelle action ?",
  "html": "<div class=\"timeline\"><div class=\"moment\"><small>01 · PROPOSITION</small>Afficher les faits</div><div class=\"moment\"><small>02 · CONSEILLER</small>Accepter ou corriger</div><div class=\"moment\"><small>03 · APPLICATION</small>Revérifier</div><div class=\"moment\"><small>04 · SERVEUR</small>Poser l’option</div></div>",
  "exercise": "../content/j3/DOSSIER_ETUDIANT.md"
},
{
  "id": "j3-option",
  "day": 3,
  "eyebrow": "Option simulée",
  "title": "Trente minutes. Une prestation.",
  "html": "<div class=\"mini-ui\"><div class=\"ui-head\"><span>POST / OPTIONS</span><span>201</span></div><div class=\"ui-body\"><div class=\"ui-line\"><strong>option.id</strong><span>opt_…</span></div><div class=\"ui-line\"><strong>statut</strong><span class=\"status\">active</span></div><div class=\"ui-line\"><strong>expire_le</strong><span>À LIRE DANS LE JSON</span></div></div></div><div class=\"pill orange\" style=\"margin-top:18px\">Après POST : comparer le total reçu au total approuvé.</div>",
  "exercise": "../content/j3/DEMO_SERVEUR.md"
},
{
  "id": "j3-titre-incidents",
  "day": 3,
  "title": "Actions, échecs et reprise",
  "eyebrow": "Séquence 04",
  "html": "<div class=\"poster section-poster\"><h3>Un résultat incertain exige une décision explicite.</h3><span class=\"poster-mark\">04</span><span class=\"stamp\">DÉTOUR · ARCHITECTURE AGENTIQUE</span></div>",
  "hero": true
},
{
  "id": "j3-timeout",
  "day": 3,
  "title": "Timeout : effet inconnu",
  "eyebrow": "Notion · reprise et idempotence",
  "html": "<div class=\"flow teal\"><div class=\"step\"><span class=\"num\">POST</span><strong>Action envoyée</strong></div><div class=\"step\"><span class=\"num\">SERVEUR</span><strong>Effet possible</strong></div><div class=\"step\"><span class=\"num\">RÉSEAU</span><strong>Réponse absente</strong></div><div class=\"step\"><span class=\"num\">PROGRAMME</span><strong>Vérifier avant reprise</strong></div></div>"
},
{
  "id": "j3-effet-partiel",
  "day": 3,
  "title": "Une option réussie ne garantit pas le séjour",
  "eyebrow": "Notion · opérations composées",
  "html": "<div class=\"three-up\"><div class=\"card teal\"><small>Train</small><strong>Option créée</strong><p>Identifiant et expiration conservés.</p></div><div class=\"card \"><small>Hôtel</small><strong>Disponibilité refusée</strong><p>Aucune option hôtel à annoncer.</p></div><div class=\"card orange\"><small>Dossier</small><strong>Résultat partiel</strong><p>Le conseiller choisit la suite.</p></div></div>"
},
{
  "id": "j3-conflit",
  "day": 3,
  "eyebrow": "Incident",
  "title": "Le serveur répond 409.",
  "html": "<div class=\"two-up\"><div class=\"card orange\"><small>Avant</small><strong>« Il reste des places. »</strong><p>Une observation passée.</p></div><div class=\"card teal\"><small>Maintenant</small><strong>409 · unavailable</strong><p>Nouvelle décision du conseiller.</p></div></div>",
  "exercise": "../content/j3/TRACE_REJEU_ETUDIANT.md"
},
{
  "id": "j3-prix",
  "day": 3,
  "eyebrow": "Changement de prix",
  "title": "Un ancien accord ne suffit plus.",
  "html": "<div class=\"case-file\"><div class=\"case-main\"><div class=\"field\"><b>Prix présenté</b><span>Ancienne lecture</span></div><div class=\"field\"><b>Prix revérifié</b><span class=\"status\">Différent</span></div></div><div class=\"case-side\"><span class=\"label\">Décision attendue</span><p>Montrer l’écart. Redemander l’accord.</p></div></div>"
},
{
  "id": "j3-confirmation",
  "day": 3,
  "eyebrow": "Seconde validation",
  "title": "Une option n’est pas une réservation.",
  "html": "<div class=\"flow teal\"><div class=\"step\"><span class=\"num\">OPTION</span><strong>Identifiant et prix</strong></div><div class=\"step\"><span class=\"num\">CONSEILLER</span><strong>Valide à nouveau</strong></div><div class=\"step\"><span class=\"num\">APPLICATION</span><strong>Envoie la clé</strong></div><div class=\"step\"><span class=\"num\">SERVEUR</span><strong>Confirme ou refuse</strong></div></div>"
},
{
  "id": "j3-trace-architecture",
  "day": 3,
  "title": "La trace relie décision et effet",
  "eyebrow": "Notion · observabilité",
  "html": "<div class=\"flow teal\"><div class=\"step\"><span class=\"num\">DEMANDE</span><strong>Version du dossier</strong></div><div class=\"step\"><span class=\"num\">OUTIL</span><strong>Nom et verdict</strong></div><div class=\"step\"><span class=\"num\">ACCORD</span><strong>Valeurs et décision</strong></div><div class=\"step\"><span class=\"num\">SERVEUR</span><strong>Statut et identifiant</strong></div></div>"
},
{
  "id": "j3-atelier",
  "day": 3,
  "eyebrow": "Atelier · intégration",
  "title": "Une trace de bout en bout.",
  "html": "<div class=\"flow teal\"><div class=\"step\"><span class=\"num\">01</span><strong>Consulter</strong></div><div class=\"step\"><span class=\"num\">02</span><strong>Proposer</strong></div><div class=\"step\"><span class=\"num\">03</span><strong>Faire décider</strong></div><div class=\"step\"><span class=\"num\">04</span><strong>Observer l’effet</strong></div></div>",
  "exercise": "../content/j3/DOSSIER_ETUDIANT.md"
},
{
  "id": "j3-preuve",
  "day": 3,
  "eyebrow": "Synthèse · actions IA",
  "title": "La preuve suit la décision.",
  "html": "<div class=\"three-up\"><div class=\"card\"><span class=\"icon\">◎</span><strong>Proposition sourcée</strong><p>Prix · date · disponibilité</p></div><div class=\"card teal\"><span class=\"icon\">✓</span><strong>Accord humain</strong><p>Action précise · avant l’écriture</p></div><div class=\"card\"><span class=\"icon\">▤</span><strong>Trace de l’effet</strong><p>Option · erreur · reprise</p></div></div>"
}
);

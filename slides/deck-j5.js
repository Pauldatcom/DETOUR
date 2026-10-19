window.COURSE_DECK.push(
  {
    id:'j5-ouverture',day:5,eyebrow:'Gestion de projet / Conception · FOAD',hero:true,
    title:'Les preuves changent<br>la conception.',subtitle:'DÉTOUR · revue du système après expérimentation',
    html:`<div class="two-up"><div class="card orange"><small>Point de départ</small><strong>Le système que vous avez éprouvé.</strong><p>Parcours, traces, incidents et décisions.</p></div><div class="card teal"><small>Point d’arrivée</small><strong>Une conception que vous pouvez défendre.</strong><p>Responsabilités, limites et livraison réalisable.</p></div></div>`,
  },
  {
    id:'j5-foad',day:5,eyebrow:'Cadre de travail',title:'À distance. Des rendez-vous précis.',
    html:`<div class="timeline"><div class="moment"><small>09:00</small>Connexion & apports</div><div class="moment"><small>12:16</small>Conception vérifiable</div><div class="moment"><small>15:23</small>Plan & critères</div><div class="moment"><small>16:30</small>Décisions défendues</div></div><div class="card" style="margin-top:18px"><small>Canal commun</small><strong>Un dossier partagé, un contact, des preuves accessibles.</strong><p>Caméra facultative. Une contribution identifiable pour chacun.</p></div>`,exercise:'../content/j5/DOSSIER_ETUDIANT.md',
  },
  {
    id:'j5-preuves',day:5,eyebrow:'Reprendre le projet',title:'« Ça fonctionne » : dans quel cas ?',
    html:`<div class="three-up"><div class="card teal"><small>Observation</small><strong>L’option est refusée.</strong><p>Trace serveur et paramètres.</p></div><div class="card orange"><small>Interprétation</small><strong>Notre accord porte sur un prix ancien.</strong><p>Une explication à vérifier.</p></div><div class="card"><small>Décision</small><strong>Revérifier avant l’action.</strong><p>Responsable et conséquence.</p></div></div>`,
  },
  {
    id:'j5-titre-systeme',day:5,eyebrow:'01 · Lire le système',hero:true,title:'Qui agit ?<br>Sur quoi ?',subtitle:'Acteurs · composants · données · frontières',
    html:`<div class="quote-card">Un schéma sert à poser une question et à prendre une décision.</div>`,
  },
  {
    id:'j5-contexte',day:5,eyebrow:'Vue de contexte',title:'Le système dans son environnement.',
    html:`<div class="role-map"><div class="side"><div class="tile"><small>Décide</small><strong>Conseiller</strong></div><div class="tile"><small>Exprime le besoin</small><strong>Voyageur</strong></div></div><div class="center"><div><strong style="font-size:30px">Application DÉTOUR</strong><p>Périmètre de l’équipe</p></div></div><div class="side"><div class="tile"><small>Propose</small><strong>Modèle via OpenRouter</strong></div><div class="tile"><small>Atteste les effets</small><strong>Serveur de prestations</strong></div></div></div>`,
  },
  {
    id:'j5-composants',day:5,eyebrow:'Vue des composants',title:'Ouvrir la boîte sans perdre la vue d’ensemble.',
    html:`<div class="flow"><div class="step"><span class="num">INTERFACE</span><strong>Montrer & recueillir</strong></div><div class="step"><span class="num">ORCHESTRATION</span><strong>Contrôler & exécuter</strong></div><div class="step"><span class="num">ÉTAT</span><strong>Conserver & retrouver</strong></div><div class="step"><span class="num">ADAPTATEURS</span><strong>Relier aux contrats</strong></div></div><div class="card" style="margin-top:18px"><small>Question de conception</small><strong>Où modifierait-on la règle d’autorisation ?</strong></div>`,
  },
  {
    id:'j5-responsabilites',day:5,eyebrow:'Responsabilités',title:'Une décision. Un responsable.',
    html:`<div class="three-up"><div class="card"><small>Modèle</small><strong>Propose une action.</strong></div><div class="card orange"><small>Conseiller</small><strong>Autorise une action précise.</strong></div><div class="card teal"><small>Programme</small><strong>Vérifie puis exécute.</strong></div></div><div class="quote-card" style="margin-top:18px">Le serveur confirme l’effet. L’équipe répond de la conception.</div>`,
  },
  {
    id:'j5-flux',day:5,eyebrow:'Flux et frontières',title:'Nommez ce qui traverse chaque flèche.',
    html:`<div class="flow"><div class="step"><span class="num">CONSEILLER → APP</span><strong>Accord lié à la proposition</strong></div><div class="step"><span class="num">APP → SERVEUR</span><strong>Action & arguments validés</strong></div><div class="step"><span class="num">SERVEUR → APP</span><strong>Résultat & identifiant</strong></div></div><div class="two-up" style="margin-top:18px"><div class="card orange"><small>Informations</small><strong>Prix, date, participants, sources.</strong></div><div class="card teal"><small>Contrôle</small><strong>Autorisation, refus, arrêt, expiration.</strong></div></div>`,
  },
  {
    id:'j5-source-verite',day:5,eyebrow:'Données',title:'Qui fait foi pour cette information ?',
    html:`<div class="three-up"><div class="card"><small>Besoin voyageur</small><strong>Demande confirmée.</strong><p>Version et hypothèses visibles.</p></div><div class="card teal"><small>Prix & disponibilité</small><strong>Réponse serveur datée.</strong><p>Une lecture n’immobilise rien.</p></div><div class="card orange"><small>Accord conseiller</small><strong>Décision sur une version.</strong><p>Une modification exige une reprise.</p></div></div>`,
  },
  {
    id:'j5-cycle-donnees',day:5,eyebrow:'Cycle de vie',title:'Créer. Mettre à jour. Expirer. Retrouver.',
    html:`<div class="timeline"><div class="moment"><small>DEMANDE</small>Versionnée</div><div class="moment"><small>OBSERVATION</small>Datée</div><div class="moment"><small>ACCORD</small>Lié aux valeurs</div><div class="moment"><small>OPTION</small>Expiration vérifiée</div></div><div class="card orange" style="margin-top:18px"><small>Au rechargement</small><strong>Que reste-t-il ? Que faut-il relire ?</strong></div>`,
  },
  {
    id:'j5-contrats',day:5,eyebrow:'Dépendances',title:'Une dépendance possède un contrat.',
    html:`<div class="two-up"><div class="card teal"><small>Ce que le serveur garantit</small><strong>Une option pour une prestation.</strong><p>Identifiant, montant et expiration retournés.</p></div><div class="card orange"><small>Ce que le produit doit décider</small><strong>Que faire si la suivante échoue ?</strong><p>Aucun panier atomique de séjour.</p></div></div><div style="display:flex;flex-wrap:wrap;gap:10px;margin-top:18px"><span class="pill">Entrées</span><span class="pill">Résultats</span><span class="pill">Erreurs</span><span class="pill">Limites</span><span class="pill">Reprise</span></div>`,
  },
  {
    id:'j5-exigences',day:5,eyebrow:'Exigences non fonctionnelles',title:'« Fiable » doit devenir observable.',
    html:`<div class="two-up"><div class="card"><small>Formulation vague</small><strong>Le service doit être rapide et sûr.</strong></div><div class="card teal"><small>Scénario vérifiable</small><strong>Le modèle ne répond plus.</strong><p>Après le délai choisi : arrêt visible, état conservé, aucune option envoyée.</p></div></div>`,
  },
  {
    id:'j5-mesure',day:5,eyebrow:'Mesurer une exigence',title:'Situation → réponse → seuil → preuve.',
    html:`<div class="flow"><div class="step"><span class="num">SITUATION</span><strong>Modèle indisponible</strong></div><div class="step"><span class="num">RÉPONSE</span><strong>Passage au conseiller</strong></div><div class="step"><span class="num">SEUIL PROPOSÉ</span><strong>Après 15 secondes</strong></div><div class="step"><span class="num">PREUVE</span><strong>Trace & état affiché</strong></div></div><div class="card orange" style="margin-top:18px"><small>À négocier</small><strong>15 secondes est une proposition, pas une garantie du fournisseur.</strong></div>`,
  },
  {
    id:'j5-adr',day:5,eyebrow:'Décision d’architecture',title:'Un choix garde sa raison.',
    html:`<div class="case-file"><div class="case-main"><div class="field"><b>Contexte</b><span>Une observation périme.</span></div><div class="field"><b>Décision</b><span>Relire avant option.</span></div><div class="field"><b>Alternative</b><span>Se fier à la première lecture.</span></div><div class="field"><b>Conséquence</b><span>Appel et délai supplémentaires.</span></div><div class="field"><b>Révision</b><span>Si le contrat fournisseur change.</span></div></div><div class="case-side"><span class="label">ADR</span><p>Une note courte, une décision, un statut.</p></div></div>`,
  },
  {
    id:'j5-risques',day:5,eyebrow:'Risque concret',title:'Un événement. Un impact. Une réponse.',
    html:`<div class="three-up"><div class="card orange"><small>Événement</small><strong>Le prix change après accord.</strong></div><div class="card"><small>Impact</small><strong>Une action différente serait envoyée.</strong></div><div class="card teal"><small>Réponse</small><strong>Suspendre et redemander.</strong></div></div><div style="display:flex;flex-wrap:wrap;gap:10px;margin-top:18px"><span class="pill">Signal observable</span><span class="pill">Responsable</span><span class="pill">Risque restant</span></div>`,
  },
  {
    id:'j5-atelier-systeme',day:5,eyebrow:'Travail d’équipe · 45 min',title:'Reconcevoir à partir de vos preuves.',
    html:`<div class="three-up"><div class="card"><small>01</small><strong>Deux vues, trois flux.</strong><p>Acteurs, composants, responsabilités.</p></div><div class="card orange"><small>02</small><strong>Une donnée suivie.</strong><p>Source, version, expiration, reprise.</p></div><div class="card teal"><small>03</small><strong>Deux décisions motivées.</strong><p>Preuve, alternative et conséquence.</p></div></div>`,exercise:'../content/j5/DOSSIER_ETUDIANT.md',
  },
  {
    id:'j5-checkpoint-systeme',day:5,eyebrow:'Checkpoint · 12:16',title:'Votre schéma explique-t-il l’incident ?',
    html:`<div class="two-up"><div class="card orange"><small>À montrer</small><strong>Trace → frontière → décision.</strong></div><div class="card teal"><small>À annoncer</small><strong>Confirmé, modifié ou encore inconnu.</strong></div></div><div class="quote-card" style="margin-top:18px">Une vue lisible. Une correction prioritaire. Un responsable.</div>`,
  },
  {
    id:'j5-titre-livrer',day:5,eyebrow:'02 · Organiser la suite',hero:true,title:'Concevoir<br>une livraison possible.',subtitle:'Critères · dépendances · capacité · revue',
    html:`<div class="quote-card">Votre plan relie les décisions du système au travail restant.</div>`,
  },
  {
    id:'j5-coherence',day:5,eyebrow:'Traçabilité',title:'Le besoin doit traverser tout le dossier.',
    html:`<div class="flow"><div class="step"><span class="num">BESOIN</span><strong>Le conseiller garde le choix.</strong></div><div class="step"><span class="num">CRITÈRE</span><strong>Refus ⇒ aucune option.</strong></div><div class="step"><span class="num">CONCEPTION</span><strong>Arrêt avant écriture.</strong></div><div class="step"><span class="num">PREUVE</span><strong>Trace sans POST.</strong></div></div>`,
  },
  {
    id:'j5-dependances',day:5,eyebrow:'Ordre de travail',title:'Tout n’est pas parallélisable.',
    html:`<div class="timeline"><div class="moment"><small>CONTRAT</small>Définir l’accord</div><div class="moment"><small>CONTRÔLE</small>Suspendre l’action</div><div class="moment"><small>ÉPREUVE</small>Tester le refus</div><div class="moment"><small>REVUE</small>Montrer la preuve</div></div><div class="card orange" style="margin-top:18px"><small>Dépendance externe</small><strong>Un fournisseur indisponible exige une stratégie de reprise.</strong></div>`,
  },
  {
    id:'j5-livraison',day:5,eyebrow:'Plan de livraison',title:'Un résultat, une preuve, une limite.',
    html:`<div class="three-up"><div class="card teal"><small>Résultat</small><strong>Une proposition sous contrôle.</strong></div><div class="card"><small>Preuve</small><strong>Accord, refus, prix modifié.</strong></div><div class="card orange"><small>Limite</small><strong>Pas de séjour garanti d’un bloc.</strong></div></div><div style="display:flex;flex-wrap:wrap;gap:10px;margin-top:18px"><span class="pill">Qui ?</span><span class="pill">Quand ?</span><span class="pill">Prérequis ?</span><span class="pill">Repli ?</span></div>`,
  },
  {
    id:'j5-estimation',day:5,eyebrow:'Capacité et incertitude',title:'Estimer pour choisir un périmètre.',
    html:`<div class="two-up"><div class="card orange"><small>Inconnu</small><strong>Peut-on retrouver une option après rechargement ?</strong><p>Une investigation courte réduit l’incertitude.</p></div><div class="card teal"><small>Plan</small><strong>Intégration + vérification + revue.</strong><p>La capacité disponible borne la livraison.</p></div></div>`,
  },
  {
    id:'j5-agile-adapte',day:5,eyebrow:'Pratiques adaptées',title:'Choisir les pratiques qui aident ici.',
    html:`<div class="three-up"><div class="card"><small>Kanban</small><strong>Rendre le travail visible.</strong><p>Limiter les travaux simultanés.</p></div><div class="card orange"><small>Revue courte</small><strong>Partager une preuve.</strong><p>Un rendez-vous avec une décision.</p></div><div class="card teal"><small>Travail en binôme</small><strong>Éprouver une frontière.</strong><p>Faire tourner les rôles.</p></div></div><div class="quote-card" style="margin-top:18px">La pratique se justifie par une contrainte et s’ajuste après observation.</div>`,
  },
  {
    id:'j5-revue',day:5,eyebrow:'Revue constructive',title:'Questionner un choix. Proposer une épreuve.',
    html:`<div class="two-up"><div class="card"><small>Observation</small><strong>« L’accord n’a pas de version. »</strong><p>Pointer le passage du dossier.</p></div><div class="card teal"><small>Question et épreuve</small><strong>« Que se passe-t-il si le prix change ? »</strong><p>Proposer le scénario, laisser l’équipe décider.</p></div></div>`,
  },
  {
    id:'j5-atelier-livraison',day:5,eyebrow:'Travail d’équipe · 45 min',title:'Relier architecture, critères et plan.',
    html:`<div class="three-up"><div class="card"><small>TRAÇABILITÉ</small><strong>Trois besoins reliés.</strong></div><div class="card orange"><small>CONCEPTION</small><strong>Deux scénarios mesurables.</strong></div><div class="card teal"><small>LIVRAISON</small><strong>Un plan réalisable.</strong></div></div><div class="quote-card" style="margin-top:18px">Inclure la vérification, la revue et le repli. Aucun code neuf imposé.</div>`,exercise:'../content/j5/DOSSIER_ETUDIANT.md',
  },
  {
    id:'j5-checkpoint-plan',day:5,eyebrow:'Checkpoint · 15:23',title:'Qu’est-ce qui bloque réellement la livraison ?',
    html:`<div class="three-up"><div class="card orange"><small>Blocage</small><strong>Une dépendance nommée.</strong></div><div class="card"><small>Action</small><strong>Un responsable, un créneau.</strong></div><div class="card teal"><small>Arbitrage</small><strong>Conserver, réduire ou reporter.</strong></div></div>`,
  },
  {
    id:'j5-revue-croisee',day:5,eyebrow:'Revue croisée · 35 min',title:'Une autre équipe éprouve votre dossier.',
    html:`<div class="timeline"><div class="moment"><small>05 MIN</small>Présenter le contexte</div><div class="moment"><small>10 MIN</small>Éprouver l’équipe A</div><div class="moment"><small>10 MIN</small>Éprouver l’équipe B</div><div class="moment"><small>10 MIN</small>Décider des retours</div></div><div class="card" style="margin-top:18px"><small>Sortie</small><strong>Deux observations, une priorité, une réponse motivée.</strong></div>`,exercise:'../content/j5/DOSSIER_ETUDIANT.md',
  },
  {
    id:'j5-reviser',day:5,eyebrow:'Révision · 20 min',title:'Accepter, adapter ou refuser un retour.',
    html:`<div class="three-up"><div class="card teal"><small>Accepter</small><strong>Le retour révèle un risque prouvé.</strong></div><div class="card orange"><small>Adapter</small><strong>Le problème existe, une autre réponse convient.</strong></div><div class="card"><small>Refuser</small><strong>Le retour repose sur une hypothèse contredite.</strong></div></div><div style="display:flex;flex-wrap:wrap;gap:10px;margin-top:18px"><span class="pill">Raison</span><span class="pill">Preuve</span><span class="pill">Impact</span><span class="pill">Décision humaine</span></div>`,
  },
  {
    id:'j5-defense',day:5,eyebrow:'Checkpoint · 16:30',title:'Défendre une décision et son coût.',
    html:`<div class="two-up"><div class="card orange"><small>Équipe</small><strong>Une conception révisée, une livraison bornée.</strong></div><div class="card teal"><small>Chaque personne</small><strong>Un choix, une alternative, une preuve.</strong></div></div><div class="quote-card" style="margin-top:18px">Expliquez aussi ce que votre décision ne résout pas.</div>`,
  },
  {
    id:'j5-cloture',day:5,eyebrow:'Dossier de conception',title:'Une version assumée. Une suite décidée.',
    html:`<div class="flow"><div class="step"><span class="num">CONSERVER</span><strong>Preuves et limites</strong></div><div class="step"><span class="num">METTRE À JOUR</span><strong>Décisions et plan</strong></div><div class="step"><span class="num">PRÉPARER</span><strong>Questions au client</strong></div></div>`,
  }
);

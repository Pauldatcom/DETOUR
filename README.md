# DÉTOUR : Gestion de projet / Conception & Agentique IA

Supports WEB3 pour les sept séquences du projet d'agence de voyages fictive.

- [Syllabus](SYLLABUS.md)
- [Slides : conception, fondations IA, actions IA](slides/index.html)
- [Brief client](output/pdf/brief-client.pdf), [brief agent](output/pdf/brief-agent.pdf) et [brief option](output/pdf/brief-option.pdf)
- [Brief évaluation](output/pdf/brief-evaluation.pdf), [brief conception](output/pdf/brief-conception.pdf), [brief changement](output/pdf/brief-changement.pdf) et [brief livraison](output/pdf/brief-livraison.pdf)
- [Mission de conception](content/j1/DOSSIER_ETUDIANT.md) et [modèles](content/j1/MODELES.md)
- [Fondations IA](content/j2/exercices-etudiants.md), [squelette d'agent](content/j2/starter-agent.mjs), [démonstration serveur](content/j2/DEMO_SERVEUR.md) et [trace de rejeu](content/j2/TRACE_REJEU_ETUDIANT.md)
- [Veille sur les clients, modèles et coûts](content/j2/VEILLE_OUTILS_MODELES.md)
- [Actions IA](content/j3/DOSSIER_ETUDIANT.md), [démonstration serveur](content/j3/DEMO_SERVEUR.md) et [trace de rejeu](content/j3/TRACE_REJEU_ETUDIANT.md)
- [Architecture de l'agent : cours écrit](content/j3/NOTIONS.md) et [cartes d'application](content/j3/DEMO_ARCHITECTURE.md)
- [Évaluer l'agent](content/j4/DOSSIER_ETUDIANT.md) et [cours écrit](content/j4/NOTIONS.md)
- [Revue de conception en FOAD](content/j5/DOSSIER_ETUDIANT.md) et [cours écrit](content/j5/NOTIONS.md)
- [Négocier un changement](content/j6/DOSSIER_ETUDIANT.md) et [cours écrit](content/j6/NOTIONS.md)
- [Recette et livraison](content/j7/DOSSIER_ETUDIANT.md) et [cours écrit](content/j7/NOTIONS.md)
- [Charte IA de l'année](output/pdf/charte-ia-web3.pdf) et [version Markdown](content/charte-ia.md)
- [Simulateur de voyage et API de prestations fictives](server/README.md)
- [Parcours client avec assistant conversationnel](conseiller/app.py)

Lancer les slides avec `python3 scripts/serve.py`, puis ouvrir `http://127.0.0.1:8000/`.
Lancer le simulateur dans un autre terminal avec `python3 server/app.py --demo`, puis ouvrir `http://127.0.0.1:8765/dashboard`.
Lancer le parcours client avec `python3 conseiller/app.py` (le simulateur doit tourner), puis ouvrir `http://127.0.0.1:8766/` : sans session, la page renvoie au portail. Les voyageurs créent un compte (e-mail + mot de passe) sur `/login` ; leurs demandes et conversations sont liées au compte et reprises à la reconnexion. L'espace conseiller s'ouvre sur `/login` avec la clé d'équipe `TRAVEL_TEAM_KEY` : tableau de bord des demandes, suivi des statuts (`a_analyser`, `propose`, `valide`, `refuse`) et détail des prestations vérifiées. Copiez `.env.example` en `.env` et renseignez `OPENROUTER_API_KEY` pour activer le chat ; le modèle se règle via `OPENROUTER_MODEL` (défaut : un modèle compatible tool-calling, voir [les modèles OpenRouter](https://openrouter.ai/models)). Les mots de passe sont hachés (PBKDF2), les clés restent côté serveur, hors du dépôt, du navigateur et des traces.
Tester le parcours avec `python3 -m unittest discover -s conseiller/tests -v`, et la recherche du simulateur avec `python3 -m unittest discover -s server/tests -v`.

Pour les TP d'agentique avec le squelette Node.js, il faut Node.js 20+, une clé OpenRouter, un modèle gratuit compatible avec les appels d'outils et la clé d'équipe transmise par le formateur. Gardez les clés hors du dépôt et de la page web.

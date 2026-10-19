# Démo : relier un changement à la conception

**Support public · 15 minutes d'exemple · Données fictives**

Ce cas illustre une démarche ; il ne remplace pas votre entretien ni votre arbitrage. Exemple : une proposition à Lyon pour deux personnes, le21 novembre2026, sur transport, hébergement et activité, plafond400 euros total. Puis le groupe demande trois personnes sans modifier le plafond. Aucun appel d'écriture n'est requis.

## 1. Consulter les faits

Serveur local démarré selon [contrat](../../server/CONTRAT.md). Depuis votre programme ou terminal, garder la clé en variable et copier seulement les réponses expurgées :

```bash
curl -fsS -H "X-Team-Key: ${TEAM_KEY:-demo-key}"   'http://127.0.0.1:8765/api/v1/catalogue?destination=Lyon'
curl -fsS -H "X-Team-Key: ${TEAM_KEY:-demo-key}"   'http://127.0.0.1:8765/api/v1/disponibilites?prestation_id=train-lyon-01&date=2026-11-21&participants=2'
```

Consulter séparément hotel-lyon-01 et activite-lyon-01 avec mêmes date/participants. Conserver identifiant, paramètres, heure, prix_total_eur et disponible. Aux prix initiaux, la composition pour deux atteint358 euros ; votre source doit rester la réponse courante de votre espace, pas cette phrase.

## 2. Dessiner la propagation

Voyageur → demande versionnée → consultations → total déterministe → proposition → conseiller. Ajouter programme, modèle et fournisseur. Le modèle peut proposer la composition ; le programme calcule et applique le contrôle du plafond. Le serveur reste la source des prix/places.

Changer participants de2 à3. Refaire chaque consultation. Aux prix initiaux, total537, supérieur à400. Une lecture pour deux ne prouve ni total ni capacité pour trois. L'ancien accord lié à la proposition pour deux ne couvre pas trois.

## 3. Comparer les réponses

A : négocier le plafond. B : proposer une autre composition/destination vérifiée. C : ne pas poursuivre l'action et expliquer l'écart. Comparer besoin préservé, travail, risque, limite et preuve ; ne pas inventer d'offre ni ajouter silencieusement une route fournisseur.

## 4. Enregistrer une décision

Référence précédente ; CR de démonstration ; nouvelle demande ; réponse retenue ; raison ; critère ; condition de révision ; tâche et responsable. Estimer avec hypothèses et fourchette. L'exemple ne pose pas d'option : le refus ou report est un résultat de conception valable.

## 5. Expliquer

Un membre raconte le besoin ; un autre la carte ; un troisième la preuve et le compromis. Demander : « Qu'est-ce qui a changé au-delà du champ ? Quelle source justifie la décision ? Quel accord est devenu invalide ? » Si une hypothèse reste ouverte, la nommer plutôt que laisser l'IA la transformer en fait.

En cas d'API inaccessible, utiliser une réponse antérieure comme exemple clairement annoncé. Elle ne constitue pas un prix actuel. Aucune réservation réelle, aucune route payante.

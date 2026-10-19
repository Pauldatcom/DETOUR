# Démo : passer d'une preuve à un verdict

**Support public · Exemple de recette et transfert · Données fictives**

Exemple déjà connu : préparer une proposition pour deux voyageurs à Lyon, le21 novembre2026, plafond400 euros global sur les trois prestations. Cette démonstration enseigne la procédure ; le scénario final sera différent et fourni par le client.

## 1. Annoncer la candidate et le critère

« Nous observons la version RC-exemple, en mode [réel/rejeu annoncé]. Le critère est : la proposition montre paramètres, total contrôlé, sources et décision du conseiller avant toute action. »

Faire ouvrir [contrat API](../../server/CONTRAT.md) et la page d'entrée du dossier. Relever l'état avant :

```bash
curl -fsS -H "X-Team-Key: ${TEAM_KEY:-demo-key}"   'http://127.0.0.1:8765/api/v1/options'
curl -fsS -H "X-Team-Key: ${TEAM_KEY:-demo-key}"   'http://127.0.0.1:8765/api/v1/reservations'
```

Ces routes consultent l'espace de l'équipe ; ne pas projeter la clé. Les options antérieures ou réservations peuvent expliquer des places déjà bloquées.

## 2. Observer le parcours

Recevoir demande ; consulter catalogue et disponibilité de chaque prestation ; calculer total ; présenter les sources et les limites ; faire décider le conseiller. Dans cet exemple, il refuse la pose d'option. Le programme n'envoie donc aucun POST.

L'observateur écrit : attendu, observé, paramètres, heure, version, trace. Le modèle disant « rien n'est réservé » ne constitue pas à lui seul la preuve. Refaire les lectures d'état et vérifier absence de nouvelle action dans la trace. L'exemple n'a ni transaction réelle ni panier atomique.

## 3. Donner un verdict borné

Si les faits et le refus sont présentés correctement, le critère observé est conforme pour cette version et ce cas. On ne conclut pas « tout est validé ». Si un prix est inventé ou un POST part sans accord, décrire l'écart et sa conséquence, puis corriger/rejouer. Une indisponibilité correctement expliquée peut satisfaire un critère de reprise.

La fiche contient candidate, critère, état initial, attendu, observé, preuve, intervention, verdict et suite. Une correction donne une nouvelle version. Une réserve possède responsable et échéance ; elle ne cache pas une action non autorisée.

## 4. Tester le transfert

Un membre qui n'a pas écrit le dossier suit les instructions. Il explique où retrouver la source, qui décide et quoi faire après un refus. Le rédacteur ne l'aide pas en silence. Noter une information manquante et corriger le guide.

## 5. Défendre une décision

Chaque membre complète : « Nous avons choisi…, plutôt que…, parce que la preuve… ; nous avons contrôlé la proposition IA en… ; notre limite reste… ». Montrer un fait situé, pas une opinion générale. Le volume de code et la qualité décorative de l'interface ne déterminent pas la maîtrise de conception.

Si le modèle gratuit est indisponible, annoncer le rejeu, garder consultations serveur réelles si possible, et préciser ce que cette preuve démontre. Aucun basculement payant.

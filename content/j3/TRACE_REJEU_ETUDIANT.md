# Rejouer une décision d'agent sans modèle disponible

Le rejeu remplace uniquement la sortie du modèle. **Les appels au serveur fictif restent réels.** Il sert à examiner les permissions et les preuves si le modèle gratuit ou OpenRouter ne répond pas. Travaillez en binôme : une personne joue le conseiller, l'autre le programme. Inversez les rôles au second essai.

**Demande :** « Pour deux personnes le 7 novembre 2026, pouvez-vous proposer un trajet sans voiture et une activité créative à Nantes ? Je veux voir le prix avant de décider. »

## Message simulé A : le modèle demande une lecture

```json
{
  "role": "assistant",
  "content": null,
  "tool_calls": [{
    "id": "replay_catalogue_1",
    "type": "function",
    "function": {
      "name": "chercher_prestations",
      "arguments": "{\"destination\":\"Nantes\"}"
    }
  }]
}
```

1. Qui a proposé l'appel ? Qui décide de l'exécuter ? Le catalogue est-il déjà consulté à ce point ?
2. Validez le nom de l'outil et les arguments. Appelez `GET /api/v1/catalogue?destination=Nantes` avec votre clé d'équipe. Relevez les identifiants du train et de l'activité.
3. Construisez le message `role: tool` lié à `tool_call_id: replay_catalogue_1`, avec le résultat utile et sans clé. Les réponses du serveur, pas ce message simulé, font foi.
4. Pour chacun des deux identifiants, appelez réellement `GET /api/v1/disponibilites` avec `date=2026-11-07` et `participants=2`. Relevez les totaux et les places ; calculez le total proposé.

## Message simulé B : le modèle dépasse sa permission

Après les lectures, le modèle produit :

> « Le train et l'activité sont disponibles. J'ai posé les options et votre réservation est confirmée. »

Barrez ce qui ne correspond à **aucun appel HTTP effectué**. Écrivez au conseiller une réponse exacte en quatre lignes maximum : prestations consultées, prix vérifié, limite de la disponibilité, décision demandée. Votre programme ne doit exposer au modèle ni `POST /options` ni `POST /reservations` dans cet essai.

Le conseiller peut ensuite autoriser une option sur le train. Notez son choix, puis exécutez `POST /api/v1/options` avec le programme ou la [démonstration serveur](DEMO_SERVEUR.md). Comparez le prix et l'expiration retournés aux données montrées au conseiller. Si une seconde option échoue, décrivez l'état partiel obtenu : il n'existe pas de panier atomique.

## Deuxième essai : conflit

Demandez une disponibilité puis une option pour `participants=20` sur le train. Notez le code HTTP et `erreur.code`. Si l'option renvoie `409 unavailable`, que montre l'application ? Que doit décider le conseiller avant de rechercher une autre prestation ? Une phrase du modèle peut suggérer une alternative, mais ne transforme pas le `409` en succès.

## Trace à remettre

| Étape | Acteur | Entrée et sortie utiles | Preuve ou décision |
|---|---|---|---|
| Demande | Conseiller |  |  |
| Appel d'outil proposé | Modèle simulé |  |  |
| Validation de l'appel | Programme |  |  |
| Catalogue et disponibilités | Serveur fictif |  |  |
| Proposition | Modèle simulé puis programme |  |  |
| Accord pour l'option | Conseiller |  |  |
| Option ou erreur | Serveur fictif |  |  |
| Suite choisie | Conseiller |  |  |

Conservez les identifiants d'option utiles, mais retirez clés, en-têtes d'authentification et données inutiles avant de partager la trace. Marquez séparément : **fait vérifié**, **hypothèse**, **action autorisée** et **action réellement exécutée**.

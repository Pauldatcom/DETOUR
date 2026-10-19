# Lire une trace agent quand le modèle est hors ligne

**Atelier de secours, 12 à 15 min.** Le modèle simulé demande l'outil ; votre équipe exécute réellement la consultation du serveur fictif. Vous n'avez besoin d'aucune clé OpenRouter.

Un conseiller demande : « Pour deux personnes le 7 novembre 2026, le train `train-nantes-01` est-il disponible et combien coûterait-il ? »

Le premier message simulé du modèle est :

```json
{
  "role": "assistant",
  "content": null,
  "tool_calls": [{
    "id": "replay_call_1",
    "type": "function",
    "function": {
      "name": "verifier_disponibilite",
      "arguments": "{\"prestation_id\":\"train-nantes-01\",\"date\":\"2026-11-07\",\"participants\":2}"
    }
  }]
}
```

1. Soulignez le **nom de l'outil**, les **arguments** et l'**identifiant de l'appel**. Ce message prouve-t-il que le serveur a déjà été consulté ?
2. Validez les arguments : identifiant de prestation, date réelle au format `AAAA-MM-JJ`, entier entre 1 et 20. Écrivez ce que votre programme refuserait si `participants` valait `-2`.
3. Lancez le serveur avec `python3 server/app.py --demo`, puis interrogez sa disponibilité avec la commande de la [démonstration serveur](DEMO_SERVEUR.md). Relevez `disponible`, `places_restantes`, `prix_total_eur` et `simulation`.
4. Dessinez le message d'outil que le programme doit renvoyer au modèle. Indiquez son `tool_call_id`. N'y inscrivez pas de clé d'équipe.
5. Rédigez deux phrases au conseiller : une avec le **fait vérifié**, une avec la **limite de l'action**. La consultation n'a posé aucune option et n'a confirmé aucune réservation.

**Trace à rendre :** `question → appel demandé → arguments validés → réponse du serveur → réponse au conseiller`. Annotez sous chaque flèche qui agit : modèle, programme ou serveur. Si la consultation échoue, remplacez prix et disponibilité par « non vérifiés » et expliquez la prochaine action humaine.

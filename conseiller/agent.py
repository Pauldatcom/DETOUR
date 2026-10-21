"""Agent conversationnel DÉTOUR : le modèle propose, le programme valide et exécute.
"""

import json
import os
import ssl
import urllib.error
import urllib.request
from pathlib import Path

from fournisseur import SupplierError
from propositions import PropositionError, aligner_sur_serveur
from store import ValidationError, analyser_informations, criteres_depuis_demande
from utils import (DEFAULT_MODEL, MAX_MESSAGES, MAX_TOOL_ITERATIONS,
                   OPENROUTER_URL, TOOL_NAME)


def _ssl_context():
    ctx = ssl.create_default_context()
    for path in (
        os.environ.get("SSL_CERT_FILE"),
        "/etc/ssl/cert.pem",
        "/etc/ssl/certs/ca-certificates.crt",
    ):
        if path and Path(path).exists():
            try:
                ctx.load_verify_locations(path)
            except (OSError, ssl.SSLError):
                pass
    return ctx


class OpenRouterError(Exception):
    def __init__(self, message, status=502):
        super().__init__(message)
        self.status = status


SYSTEM_PROMPT = """Tu es l'assistant voyage de DÉTOUR, une agence de voyages insolites et de week-ends surprises. Tu discutes avec un voyageur pour préparer sa demande.

CONTEXTE
- Le catalogue est fictif et restreint : destinations possibles uniquement Nantes, Lyon et Lille.
- Chaque destination propose un transport, un hébergement et une activité.
- Toutes les données sont fictives : c'est une démonstration.

TON TRAVAIL
1. Recueillir les informations du voyageur avec des questions courtes et amicales.
2. Une fois le minimum réuni, appeler l'outil chercher_voyages pour enregistrer la demande et vérifier les prestations.
3. Présenter les résultats en t'appuyant uniquement sur ce que l'outil renvoie.

INFORMATIONS REQUISES AVANT L'APPEL DE L'OUTIL (minimum)
- type_voyage : "trek-randonnee", "lune-de-miel", "voyage-familial" ou "autres"
- destination : "Nantes", "Lyon" ou "Lille"
- date_depart et date_retour : format AAAA-MM-JJ
- nombre_voyageurs : entier de 1 à 20
- budget_max_par_personne : entier positif en euros
- niveau_aventure : "calme", "modere" ou "intense"

CONTRÔLE DES INFORMATIONS (fait par le programme, pas par toi)
- Tu peux appeler l'outil dès que tu as un brouillon : s'il manque des champs obligatoires, l'outil renvoie `informations.manquants` et `informations.fournis`.
- Demande uniquement les champs dans `manquants`. Ne redemande jamais un champ listé dans `fournis`.
- Distingue clairement ce qui est déjà fourni de ce qui manque.

AUTRES INFORMATIONS À RECUEILLIR AUSSI AVANT L'APPEL
Pose une question à la fois pour chacune (une seule par tour) :
- présence d'enfants et leur nombre (has_enfants, nombre_enfants), si le voyageur n'en a pas parlé
- activites préférées (activites) : "créatif", "jeu", "cuisine", "intérieur", "extérieur"
- souhaits : "Décrivez en quelques mots l'ambiance et les envies pour ce voyage" (texte libre)
- allergies ou contraintes (contraintes, texte libre)
Si le voyageur presse de finir, appelez l'outil avec ce que vous avez, sans inventer le reste.

QUESTIONS SELON LE VOYAGE (choisies par le programme, pas par toi)
- L'outil renvoie `informations.questions_conditionnelles` : les seules questions en plus utiles pour ce voyage.
- Pose uniquement ces questions-là, une par tour, si le voyageur n'y a pas déjà répondu :
  - niveau_aventure (trek) : "Quel est votre niveau pour la randonnée : calme, modéré ou intense ?"
  - besoin_guide : "Souhaitez-vous un guide pour ce voyage ?"
  - permis_conduire : "Avez-vous le permis de conduire ?"
- Ne pose jamais une question absente de cette liste (pas de question sur le guide pour une lune de miel, par exemple).
- Si le voyageur parle de voiture ou de road trip, enregistre avec_voiture à true : l'outil ajoutera alors la question du permis.

MISE À JOUR D'UNE DEMANDE EXISTANTE
- Les réponses du voyageur sont enregistrées sur la demande en cours (pas une nouvelle à chaque fois).
- Quand l'outil confirme l'enregistrement, dis-le clairement au voyageur.
- Si l'outil renvoie une erreur, ne prétends pas que la réponse a été sauvée.

RÈGLES ABSOLUES
- Ne devine rien : si une information requise manque, pose la question (seulement pour les manquants).
- N'invente jamais un prix, une disponibilité, une prestation ou une date de mise à jour : ils viennent uniquement de l'outil.
- Tu ne prends aucune réservation et ne poses aucune option. Aucune réservation n'existe à l'issue de la conversation.
- Si le voyageur veut une autre destination, explique que le catalogue est restreint pour le moment.
- Si l'outil renvoie une erreur, explique-la honnêtement au voyageur sans inventer de résultat.

APRÈS L'OUTIL
- Présente chaque prestation vérifiée : nom, type, prix par personne et total pour le groupe, disponibilité.
- Précise que les prix et disponibilités ont été vérifiés auprès du serveur à la date indiquée ; la disponibilité est vérifiée à la date de départ uniquement.
- Signale ce qui n'est pas vérifiable au catalogue : le niveau d'aventure, le besoin de guide et les allergies ne figurent pas dans le serveur.
- Un conseiller humain préparera ensuite la proposition définitive.

STYLE
- Réponses courtes, en français, une question à la fois quand tu collectes les informations."""


TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": TOOL_NAME,
        "description": (
            "Enregistre la demande de voyage du voyageur et recherche les prestations "
            "disponibles dans le catalogue fictif DÉTOUR (transport, hébergement, activité). "
            "À appeler une fois les informations essentielles réunies. Ne réserve rien."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "type_voyage": {"type": "string", "enum": ["trek-randonnee", "lune-de-miel", "voyage-familial", "autres"]},
                "destination": {"type": "string", "enum": ["Nantes", "Lyon", "Lille"]},
                "date_depart": {"type": "string", "description": "Date de départ, format AAAA-MM-JJ."},
                "date_retour": {"type": "string", "description": "Date de retour, format AAAA-MM-JJ."},
                "nombre_voyageurs": {"type": "integer", "description": "Nombre total de voyageurs, de 1 à 20."},
                "has_enfants": {"type": "boolean", "description": "Des enfants participent-ils au voyage ?"},
                "nombre_enfants": {"type": "integer", "description": "Nombre d'enfants, si has_enfants est vrai."},
                "budget_max_par_personne": {"type": "integer", "description": "Budget maximum par personne, en euros."},
                "niveau_aventure": {"type": "string", "enum": ["calme", "modere", "intense"]},
                "besoin_guide": {"type": "boolean", "description": "Un guide est-il requis ?"},
                "avec_voiture": {"type": "boolean",
                                 "description": "Le voyageur veut-il se déplacer en voiture sur place ?"},
                "permis_conduire": {"type": "boolean",
                                    "description": "Le voyageur a-t-il le permis de conduire ? Seulement si avec_voiture."},
                "activites": {"type": "array", "items": {"type": "string"},
                              "description": "Activités souhaitées : créatif, jeu, cuisine, intérieur, extérieur."},
                "contraintes": {"type": "string", "description": "Allergies ou contraintes importantes."},
                "souhaits": {"type": "string",
                             "description": "Description libre de l'ambiance et des envies du voyageur pour ce voyage."},
            },
            "required": ["type_voyage", "destination", "date_depart", "date_retour",
                         "nombre_voyageurs", "budget_max_par_personne", "niveau_aventure"],
        },
    },
}


PROPOSITION_SYSTEM = (
    "Tu es l'assistant DÉTOUR. Un conseiller te demande de préparer une proposition "
    "de voyage basée sur les prestations vérifiées par le serveur fictif. "
    "Tu réponds uniquement avec un objet JSON valide."
)


def _extraire_json(content):
    content = (content or "").strip()
    if "```json" in content:
        content = content.split("```json", 1)[1]
        content = content.split("```", 1)[0]
    elif "```" in content:
        parts = content.split("```")
        if len(parts) >= 3:
            content = parts[1]
    return json.loads(content.strip())


class Agent:
    def __init__(self, supplier, store, api_key="", model=DEFAULT_MODEL,
                 base_url=OPENROUTER_URL, timeout=60):
        self.supplier = supplier
        self.store = store
        self._api_key = api_key
        self.model = model
        self.base_url = base_url
        self.timeout = timeout

    def chat(self, messages, user_id="", demande_id=None):
        """Exécute un tour de conversation et retourne reply, demande, recherche, trace.

        `user_id` and `demande_id` come from the server session / client thread:
        they are never taken from the model."""
        if not self._api_key:
            raise OpenRouterError("Clé OpenRouter absente : définir OPENROUTER_API_KEY.", 503)
        trace = {"model": self.model, "tool_calls": [], "simulation": True}
        conversation: list = [{"role": "system", "content": SYSTEM_PROMPT}]
        conversation += [{"role": m["role"], "content": m["content"]}
                         for m in messages[-MAX_MESSAGES:]]
        demande, recherche = None, None
        if demande_id:
            demande = self.store.obtenir(demande_id)

        for _ in range(MAX_TOOL_ITERATIONS):
            message = self._call_model(conversation)
            tool_calls = message.get("tool_calls") or []
            if not tool_calls:
                return {"reply": message.get("content") or "",
                        "demande": demande, "recherche": recherche, "trace": trace}
            conversation.append({"role": "assistant", "content": message.get("content") or "",
                                 "tool_calls": tool_calls})
            for call in tool_calls:
                outcome = self._execute_tool(
                    call, trace, user_id=user_id, demande_id=demande_id)
                if outcome.get("demande"):
                    demande = outcome["demande"]
                    demande_id = demande.get("id") or demande_id
                recherche = outcome.get("recherche") or recherche
                conversation.append({
                    "role": "tool",
                    "tool_call_id": call.get("id") or "call_inconnu",
                    "content": json.dumps(outcome["payload"], ensure_ascii=False),
                })

        message = self._call_model(conversation, with_tools=False)
        return {"reply": message.get("content") or "",
                "demande": demande, "recherche": recherche, "trace": trace}

    def generer_proposition(self, demande_record, recherche):
        """Generate a structured proposition via OpenRouter (no tools)."""
        if not self._api_key:
            raise OpenRouterError("Clé OpenRouter absente : définir OPENROUTER_API_KEY.", 503)
        d = demande_record.get("demande", demande_record)
        resultats = (recherche or {}).get("resultats", [])
        prompt = (
            f"Prépare une proposition de voyage au format JSON.\n\n"
            f"Demande du voyageur :\n"
            f"- Destination : {d.get('destination', '')}\n"
            f"- Dates : {d.get('date_depart', '')} → {d.get('date_retour', '')}\n"
            f"- Voyageurs : {d.get('nombre_voyageurs', 1)}\n"
            f"- Budget max/pers : {d.get('budget_max_par_personne', 0)} €\n"
            f"- Type : {d.get('type_voyage', '')}\n"
            f"- Niveau aventure : {d.get('niveau_aventure', '')}\n"
            f"- Souhaits : {d.get('souhaits', '')}\n\n"
            f"Prestations disponibles :\n"
            f"{json.dumps(resultats, ensure_ascii=False)}\n\n"
            f"Réponds avec un objet JSON : "
            f'{{"titre": "...", "description": "...", '
            f'"prestations": [{{"id": "...", "nom": "...", '
            f'"type": "...", "prix_unitaire_eur": 0, "quantite": 1}}]}}\n'
            f"Réponds uniquement avec le JSON."
        )
        conversation = [
            {"role": "system", "content": PROPOSITION_SYSTEM},
            {"role": "user", "content": prompt},
        ]
        message = self._call_model(conversation, with_tools=False)
        try:
            prop_data = _extraire_json(message.get("content", ""))
        except (json.JSONDecodeError, IndexError) as err:
            raise OpenRouterError("Réponse du modèle illisible (JSON attendu).") from err
        if not isinstance(prop_data, dict):
            raise OpenRouterError("Réponse du modèle invalide (objet attendu).")
        try:
            # Stamp source and consultation time from the search; never invent them.
            return aligner_sur_serveur(
                prop_data,
                resultats,
                source_label=(recherche or {}).get("source_label"),
                consulte_le=(recherche or {}).get("consulte_le"),
            )
        except PropositionError as err:
            raise OpenRouterError(f"Proposition refusée : {err}") from err

    def _call_model(self, conversation, with_tools=True):
        payload = {"model": self.model, "messages": conversation}
        if with_tools:
            payload["tools"] = [TOOL_DEFINITION]
            payload["tool_choice"] = "auto"
        request = urllib.request.Request(
            self.base_url,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Authorization": f"Bearer {self._api_key}",
                     "Content-Type": "application/json"},
            method="POST")
        try:
            with urllib.request.urlopen(request, timeout=self.timeout, context=_ssl_context()) as response:
                data = json.loads(response.read())
        except urllib.error.HTTPError as err:
            detail = f"HTTP {err.code}"
            try:
                detail = json.loads(err.read()).get("error", {}).get("message", detail)
            except Exception:
                pass
            if err.code in (401, 403):
                raise OpenRouterError("OpenRouter a refusé la clé API (vérifiez OPENROUTER_API_KEY).") from err
            if err.code == 429:
                raise OpenRouterError("Limite d'appels OpenRouter atteinte, réessayez dans un instant.") from err
            raise OpenRouterError(f"OpenRouter : {detail}") from err
        except (urllib.error.URLError, TimeoutError, OSError) as err:
            raise OpenRouterError("OpenRouter injoignable, vérifiez votre connexion.") from err
        except json.JSONDecodeError as err:
            raise OpenRouterError("Réponse illisible d'OpenRouter.") from err
        try:
            return data["choices"][0]["message"]
        except (KeyError, IndexError, TypeError) as err:
            raise OpenRouterError("OpenRouter : réponse sans message exploitable.") from err

    def _execute_tool(self, call, trace, user_id="", demande_id=None):
        function = call.get("function") or {}
        name = function.get("name")
        entry = {"outil": name, "statut": "refuse"}
        if name != TOOL_NAME:
            entry["erreur"] = f"Outil inconnu : {name}. Seul {TOOL_NAME} est autorisé."
            trace["tool_calls"].append(entry)
            return {"payload": {"erreur": entry["erreur"]}}
        try:
            args = json.loads(function.get("arguments") or "{}")
            if not isinstance(args, dict):
                raise ValueError
        except (json.JSONDecodeError, ValueError):
            entry["erreur"] = "Arguments invalides : un objet JSON était attendu."
            trace["tool_calls"].append(entry)
            return {"payload": {"erreur": entry["erreur"]}}
        if args.get("qualification") == "pret_proposition":
            entry["qualification_refusee"] = (
                "L'agent ne peut pas marquer une demande prête pour proposition.")
        # Never trust model-supplied ids; only the server thread id is used.
        args.pop("qualification", None)
        args.pop("user_id", None)
        args.pop("demande_id", None)

        try:
            record, mis_a_jour = self.store.enregistrer_reponses(
                demande_id, args, user_id=user_id)
        except ValidationError as err:
            entry["statut"] = "echec_mise_a_jour"
            entry["erreur"] = str(err)
            trace["tool_calls"].append(entry)
            return {"payload": {
                "erreur": str(err),
                "confirmation": None,
                "consigne": (
                    "L'enregistrement a échoué. Ne dis pas que la réponse a été "
                    "sauvée. Explique l'erreur et redemande une valeur valide."
                ),
            }}
        if record is None:
            entry["statut"] = "echec_mise_a_jour"
            entry["erreur"] = "Demande introuvable."
            trace["tool_calls"].append(entry)
            return {"payload": {
                "erreur": "Demande introuvable.",
                "confirmation": None,
                "consigne": (
                    "L'enregistrement a échoué. Ne dis pas que la réponse a été sauvée."
                ),
            }}

        analyse = analyser_informations(record["demande"])
        entry["demande_id"] = record["id"]
        entry["champs_mis_a_jour"] = mis_a_jour
        entry["informations"] = {
            "fournis": analyse["fournis"],
            "manquants": analyse["manquants"],
        }
        labels = analyse["labels"]
        confirmation = (
            f"Réponse enregistrée sur la demande {record['id']}."
            if mis_a_jour else
            f"Demande {record['id']} à jour (aucun nouveau champ)."
        )
        if not analyse["complet"]:
            entry["statut"] = "informations_manquantes"
            trace["tool_calls"].append(entry)
            manquants_lisible = [labels.get(c, c) for c in analyse["manquants"]]
            fournis_lisible = [labels.get(c, c) for c in analyse["fournis"]]
            return {
                "demande": record,
                "payload": {
                    "confirmation": confirmation,
                    "champs_mis_a_jour": mis_a_jour,
                    "demande_id": record["id"],
                    "informations": analyse,
                    "consigne": (
                        "Réponse bien enregistrée. Confirme brièvement la sauvegarde. "
                        "Demande ensuite uniquement : "
                        + ", ".join(manquants_lisible)
                        + ". Ne redemande pas : "
                        + (", ".join(fournis_lisible) if fournis_lisible else "(rien encore)")
                        + "."
                    ),
                },
            }

        entry["statut"] = "enregistree"
        try:
            resultat = self.supplier.rechercher(criteres_depuis_demande(record))
            recherche = self.store.ajouter_recherche(record["id"], resultat)
        except SupplierError as err:
            entry["statut"] = "serveur_indisponible"
            entry["erreur"] = str(err)
            trace["tool_calls"].append(entry)
            return {"demande": record,
                    "payload": {
                        "confirmation": confirmation,
                        "erreur": str(err),
                        "consigne": (
                            "La demande est enregistrée mais le serveur de prestations "
                            "est indisponible. Informe le voyageur sans inventer de prestation."
                        ),
                    }}
        entry["statut"] = "ok"
        trace["tool_calls"].append(entry)
        payload = dict(recherche) if isinstance(recherche, dict) else {"recherche": recherche}
        payload["confirmation"] = confirmation
        payload["champs_mis_a_jour"] = mis_a_jour
        payload["demande_id"] = record["id"]
        payload["informations"] = analyse
        return {"demande": record, "recherche": recherche, "payload": payload}
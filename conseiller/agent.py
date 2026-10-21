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
from store import ValidationError, criteres_depuis_demande

from utils import (
    ACTIVITES_POSSIBLES,
    DEFAULT_MODEL,
    MAX_MESSAGES,
    MAX_TOOL_ITERATIONS,
    NIVEAUX_AVENTURE,
    OPENROUTER_URL,
    TOOL_NAME,
    TYPES_VOYAGE,
)

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



SYSTEM_PROMPT = """Tu es l'assistant voyage de DÉTOUR, une agence de voyages insolites et de week-ends surprises.

CONTEXTE
- Le catalogue est fictif et limité à Nantes, Lyon et Lille.
- Chaque destination propose un transport, un hébergement et une activité.
- Toutes les données sont fictives : c'est une démonstration.

TON TRAVAIL
1. Recueillir les informations avec des questions courtes et amicales.
2. Sauvegarder progressivement les réponses dans le brouillon existant.
3. Quand toutes les informations minimales sont disponibles, appeler chercher_voyages pour rechercher les prestations.
4. Présenter les résultats uniquement à partir des données renvoyées par l'outil.

SAUVEGARDE PROGRESSIVE
- Après chaque nouvelle réponse utile du voyageur, appelle sauvegarder_brouillon avec uniquement les champs connus grâce à la conversation.
- Ne transmets jamais de valeur inventée ou supposée.
- Ne remplace pas une réponse connue par une valeur vide ou une valeur par défaut non confirmée.
- Utilise uniquement les champs autorisés par cet outil.
- La sauvegarde ne lance aucune recherche de prestations.
- Si la sauvegarde échoue, explique le problème honnêtement et ne prétends pas que les réponses sont enregistrées.

INFORMATIONS MINIMALES POUR LA RECHERCHE
- type_voyage : trek-randonnee, lune-de-miel, voyage-familial ou autres
- destination : Nantes, Lyon ou Lille
- date_depart et date_retour : format AAAA-MM-JJ
- nombre_voyageurs : entier de 1 à 20
- budget_max_par_personne : entier positif en euros
- niveau_aventure : calme, modere ou intense

AUTRES INFORMATIONS À RECUEILLIR
Pose une seule question à la fois :
- présence d'enfants et nombre d'enfants ;
- besoin d'un guide ;
- activités souhaitées : créatif, jeu, cuisine, intérieur, extérieur, train ou sans voiture ;
- souhaits et ambiance du voyage ;
- allergies ou autres contraintes.

RECHERCHE DE PRESTATIONS
- Appelle chercher_voyages uniquement lorsque toutes les informations minimales sont connues et valides.
- Transmets les informations confirmées, sans en inventer.
- Ne lance pas une recherche simplement parce que le voyageur a donné une nouvelle réponse.
- Si le voyageur souhaite terminer plus tôt, explique quelles informations minimales manquent ; ne lance pas une recherche incomplète.

RÈGLES ABSOLUES
- Ne devine rien.
- N'invente jamais de prix, de disponibilité, de prestation ou de date de mise à jour.
- Tu ne prends aucune réservation et ne poses aucune option.
- Si le voyageur demande une destination hors catalogue, explique la limitation.
- Si un outil renvoie une erreur, explique-la honnêtement.

APRÈS LA RECHERCHE
- Présente les prestations vérifiées, leurs prix par personne, le total du groupe et leur disponibilité, uniquement si ces données sont renvoyées.
- Précise que la disponibilité est vérifiée à la date de départ uniquement, si le résultat de l'outil le confirme.
- Signale que le niveau d'aventure, le besoin de guide et les allergies ne sont pas vérifiables dans le catalogue.
- Indique qu'un conseiller humain préparera la proposition définitive.

STYLE
- Réponses courtes, en français.
- Une seule question à la fois.
- N'affirme jamais qu'une sauvegarde ou une recherche a réussi sans confirmation de l'outil."""
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

SAVE_DRAFT_TOOL = {
    "type": "function",
    "function": {
        "name": "sauvegarder_brouillon",
        "description": (
            "Enregistre dans le brouillon existant les réponses que le "
            "voyageur vient de donner. N'invente aucune information. "
            "N'effectue aucune recherche de prestations."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "type_voyage": {
                    "type": "string",
                    "enum": list(TYPES_VOYAGE),
                },
                "destination": {
                    "type": "string",
                    "enum": ["Nantes", "Lyon", "Lille"],
                },
                "date_depart": {"type": "string"},
                "date_retour": {"type": "string"},
                "nombre_voyageurs": {"type": "integer"},
                "has_enfants": {"type": "boolean"},
                "nombre_enfants": {"type": "integer"},
                "budget_max_par_personne": {"type": "integer"},
                "niveau_aventure": {
                    "type": "string",
                    "enum": list(NIVEAUX_AVENTURE),
                },
                "besoin_guide": {"type": "boolean"},
                "activites": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": list(ACTIVITES_POSSIBLES),
                    },
                },
                "contraintes": {"type": "string"},
                "souhaits": {"type": "string"},
            },
            "minProperties": 1,
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

        `user_id` provient de la session serveur : il n'est jamais demandé au
        modèle ni exposé dans le schéma de l'outil."""
        if not self._api_key:
            raise OpenRouterError("Clé OpenRouter absente : définir OPENROUTER_API_KEY.", 503)

        trace = {"model": self.model, "tool_calls": [], "simulation": True}
        conversation: list = [{"role": "system", "content": SYSTEM_PROMPT}]

        demande, recherche = None, None

        if demande_id:
            demande = self.store.get_draft(demande_id, user_id)
        elif isinstance(user_id, str) and user_id.strip():
            demande = self.store.create_draft(user_id)
            demande_id = demande["id"]

        conversation += [{"role": m["role"], "content": m["content"]}
                         for m in messages[-MAX_MESSAGES:]]

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
                    call,
                    trace,
                    user_id=user_id,
                    demande_id=demande_id,
                )
                demande = outcome.get("demande") or demande
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
            return aligner_sur_serveur(prop_data, resultats)
        except PropositionError as err:
            raise OpenRouterError(f"Proposition refusée : {err}") from err

    def _call_model(self, conversation, with_tools=True):
        payload = {"model": self.model, "messages": conversation}
        if with_tools:
            payload["tools"] = [TOOL_DEFINITION, SAVE_DRAFT_TOOL]
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

        if name not in {TOOL_NAME, "sauvegarder_brouillon"}:
            entry["erreur"] = (
                f"Outil inconnu : {name}. "
                "Seuls les outils autorisés sont acceptés."
            )
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

        args.pop("user_id", None)
        args["user_id"] = user_id

        if name == "sauvegarder_brouillon":
            if not demande_id:
                entry["statut"] = "invalide"
                entry["erreur"] = "Aucun brouillon actif à mettre à jour."
                trace["tool_calls"].append(entry)
                return {"payload": {"erreur": entry["erreur"]}}

            try:
                record = self.store.update_draft_answers(
                    demande_id,
                    user_id,
                    {key: value for key, value in args.items() if key != "user_id"},
                )
            except ValidationError as err:
                entry["statut"] = "invalide"
                entry["erreur"] = str(err)
                trace["tool_calls"].append(entry)
                return {"payload": {"erreur": f"Sauvegarde refusée : {err}"}}

            entry["statut"] = "brouillon_mis_a_jour"
            entry["demande_id"] = record["id"]
            entry["arguments"] = {
                key: value for key, value in args.items() if key != "user_id"
            }
            trace["tool_calls"].append(entry)
            return {
                "demande": record,
                "payload": {
                    "message": "Réponses enregistrées dans le brouillon.",
                    "demande_id": record["id"],
                },
            }


        try:
            if demande_id:
                record = self.store.finaliser_brouillon(
                    demande_id,
                    user_id,
                    {
                        key: value
                        for key, value in args.items()
                        if key != "user_id"
                    },
                )
            else:
                record = self.store.creer(args)
        except ValidationError as err:
            entry["statut"] = "invalide"
            entry["erreur"] = str(err)
            trace["tool_calls"].append(entry)
            return {"payload": {"erreur": f"Demande refusée : {err}"}}
            entry["statut"] = "invalide"
            entry["erreur"] = str(err)
            trace["tool_calls"].append(entry)
            return {"payload": {"erreur": f"Demande refusée : {err}"}}
        except ValidationError as err:
            entry["statut"] = "invalide"
            entry["erreur"] = str(err)
            trace["tool_calls"].append(entry)
            return {"payload": {"erreur": f"Demande refusée : {err}"}}
        entry["demande_id"] = record["id"]
        entry["arguments"] = record["demande"]
        entry["statut"] = "enregistree"
        try:
            resultat = self.supplier.rechercher(criteres_depuis_demande(record))
            recherche = self.store.ajouter_recherche(record["id"], resultat)
        except SupplierError as err:
            entry["statut"] = "serveur_indisponible"
            entry["erreur"] = str(err)
            trace["tool_calls"].append(entry)
            return {"demande": record,
                    "payload": {"erreur": str(err),
                                "consigne": "Le serveur de prestations est indisponible. Informe le voyageur sans inventer de prestation."}}
        entry["statut"] = "ok"
        trace["tool_calls"].append(entry)
        return {"demande": record, "recherche": recherche, "payload": recherche}

"""Agent conversationnel DÉTOUR : le modèle propose, le programme valide et exécute.
"""

import json
import os
import ssl
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

from fournisseur import SupplierError
from horaires import fenetre_reponse
from propositions import PropositionError, aligner_sur_serveur, apply_quantities
from store import ValidationError, analyser_informations, business_today, criteres_depuis_demande
from traces import resume_reponse_serveur
from utils import (DEFAULT_MODEL, GENERE_PAR_ASSISTANT, MAX_MESSAGES,
                   MAX_TOOL_ITERATIONS, OPENROUTER_URL, PRENOM_CONSEILLER_DEFAUT,
                   TOOL_NAME)
from verification import ETAT_ERROR, marquer_etats


def _rapport_erreur_fournisseur(err):
    """Map SupplierError to a distinct trace statut + model consigne (#6).

    The model must not invent a service when the server refused the call.
    """
    status = getattr(err, "status", 502)
    base = (
        "La demande est enregistrée mais le serveur de prestations a renvoyé "
        "une erreur. Informe le voyageur sans inventer de prestation. "
    )
    if status in (401, 403):
        return "auth_refusee", base + (
            "Explique qu'il s'agit d'un problème d'authentification ou de permission."
        )
    if status == 404:
        return "prestation_introuvable", base + (
            "Explique qu'une prestation ou ressource est introuvable."
        )
    if status == 409:
        return "prestation_indisponible", base + (
            "Explique qu'une prestation est indisponible ou inutilisable."
        )
    return "serveur_indisponible", base + (
        "Explique que le résultat n'a pas pu être vérifié (serveur injoignable)."
    )


def _contexte_reprise(demande_record):
    """Build a short system note so the model resumes on missing fields (#23)."""
    if not isinstance(demande_record, dict):
        return None
    dem_id = demande_record.get("id") or ""
    corps = demande_record.get("demande") or {}
    if not isinstance(corps, dict):
        corps = {}
    analyse = analyser_informations(corps)
    labels = analyse.get("labels") or {}
    fournis_cles = analyse.get("fournis") or []
    manquants_cles = analyse.get("manquants") or []
    if fournis_cles:
        details = []
        for cle in fournis_cles:
            valeur = corps.get(cle)
            details.append(f"{labels.get(cle, cle)}={valeur!r}")
        fournis_txt = ", ".join(details)
    else:
        fournis_txt = "(aucun)"
    manquants_txt = (
        ", ".join(labels.get(c, c) for c in manquants_cles)
        if manquants_cles else "(aucun — demande complète)"
    )
    return "\n".join([
        f"DEMANDE EN COURS (id={dem_id}).",
        f"Champs déjà enregistrés : {fournis_txt}",
        f"Champs manquants : {manquants_txt}",
        "Ne redemande pas les champs déjà enregistrés. "
        "Pose la prochaine question uniquement sur les manquants.",
    ])

# Arguments de décision : le modèle ne tranche jamais. Toute tentative est
# refusée, tracée, puis ignorée. Seul le conseiller humain décide.
DECISION_ARGS = (
    "qualification",
    "statut",
    "motif",
    "raison",
    "decisions",
    "validee_par",
    "proposition",
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


# ---------------------------------------------------------------------------
# Advisor chat (#115): the assistant helps a human advisor, it never decides.
# ---------------------------------------------------------------------------

ADVISOR_TOOL_NAME = "verifier_prestations"

ADVISOR_SYSTEM_PROMPT = """Tu es l'assistant des conseillers DÉTOUR. Tu parles à un conseiller humain, pas au voyageur. Tu l'aides à vérifier des prestations et à préparer sa réponse ; c'est lui qui décide, signe et envoie.

CE QUE TU FAIS
- Chercher et vérifier des prestations du catalogue fictif (Nantes, Lyon, Lille) avec l'outil verifier_prestations.
- Comparer, résumer, suggérer, et rédiger un brouillon de message quand le conseiller le demande.

CE QUE TU NE FAIS JAMAIS
- Réserver, poser une option, confirmer une réservation, signer une proposition, changer un statut ou envoyer quoi que ce soit au voyageur.
- Présenter un prix non vérifié comme sûr, ou une prestation indisponible comme disponible.
- Cacher une information manquante ou ancienne.

TON
- Précis d'abord, chaleureux ensuite, légèrement malicieux seulement en fin de message.
- « nous » pour l'agence, « je » pour le conseiller dans les brouillons destinés au voyageur.
- Jamais pressé, jamais criard : pas de « ! » en série.
- Aucune plaisanterie sur un prix, une indisponibilité ou une erreur.

CE QUI A ÉTÉ VÉRIFIÉ
- Pour chaque prestation : prix par personne, total du groupe, disponibilité à la date de départ, et l'heure de la vérification (consulte_le).
- Dis clairement ce qui n'est pas vérifiable au catalogue : horaires, niveau d'aventure, besoin de guide, allergies.
- Si la dernière lecture du dossier date de plus de 24 h, dis qu'elle est ancienne et propose de revérifier.

INFORMATIONS MANQUANTES
- S'il manque la destination, les dates, le nombre de voyageurs ou le budget pour vérifier, demande-les au conseiller avant d'appeler l'outil.
- N'invente jamais une valeur manquante et ne présente pas une hypothèse comme un fait.

ERREURS
- Si l'outil renvoie une erreur, explique simplement ce qui n'a pas pu être vérifié et ce que le conseiller peut faire. Jamais de « Erreur : … » brut.

STYLE
- Réponses courtes, en français, en listes quand tu compares des prestations."""

ADVISOR_TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": ADVISOR_TOOL_NAME,
        "description": (
            "Vérifie auprès du serveur fictif DÉTOUR les prix et disponibilités des "
            "prestations (transport, hébergement, activité) pour une destination et des "
            "dates. Lecture seule : ne modifie aucune demande et ne réserve rien."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "destination": {"type": "string", "enum": ["Nantes", "Lyon", "Lille"]},
                "date_depart": {"type": "string", "description": "Format AAAA-MM-JJ."},
                "date_retour": {"type": "string", "description": "Format AAAA-MM-JJ."},
                "participants": {"type": "integer", "description": "De 1 à 20."},
                "budget_max_par_personne": {"type": "integer",
                                            "description": "Euros par personne (facultatif)."},
                "type_voyage": {"type": "string",
                                "enum": ["trek-randonnee", "lune-de-miel",
                                         "voyage-familial", "autres"]},
                "activites": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["destination", "date_depart", "date_retour", "participants"],
        },
    },
}

TYPES_VOYAGE = ("trek-randonnee", "lune-de-miel", "voyage-familial", "autres")


def criteres_conseiller(args):
    """Validate the advisor search arguments; raise ValueError in French."""
    if not isinstance(args, dict):
        raise ValueError("Arguments invalides : un objet JSON était attendu.")
    destination = args.get("destination")
    if not isinstance(destination, str) or not destination.strip():
        raise ValueError("La destination est obligatoire.")
    depart, retour = args.get("date_depart"), args.get("date_retour")
    try:
        jour_depart = date.fromisoformat(depart)
        jour_retour = date.fromisoformat(retour)
    except (TypeError, ValueError):
        raise ValueError("Les dates doivent suivre le format AAAA-MM-JJ.") from None
    if jour_retour < jour_depart:
        raise ValueError("La date de retour doit suivre la date de départ.")
    participants = args.get("participants")
    if type(participants) is not int or not 1 <= participants <= 20:
        raise ValueError("Le nombre de voyageurs doit être un entier de 1 à 20.")
    budget = args.get("budget_max_par_personne")
    if budget is not None and (type(budget) is not int or budget <= 0):
        raise ValueError("Le budget doit être un entier positif, en euros par personne.")
    type_voyage = args.get("type_voyage")
    if type_voyage is not None and type_voyage not in TYPES_VOYAGE:
        raise ValueError("Type de voyage inconnu.")
    activites = args.get("activites") or []
    if not isinstance(activites, list) or not all(isinstance(a, str) for a in activites):
        raise ValueError("Les activités doivent être une liste de textes.")
    return {
        "destination": destination.strip(),
        "date_depart": depart,
        "date_retour": retour,
        "participants": participants,
        "budget_max": budget,
        "type_voyage": type_voyage,
        "activites": [a.strip() for a in activites if a.strip()],
    }


ASSISTANT_INDISPONIBLE = (
    "L'assistant ne répond pas pour le moment. Le dossier reste consultable ; "
    "réessayez dans un instant.")


def verifier_messages(messages):
    """Same message rules as the traveler chat; raise ValueError in French."""
    if not isinstance(messages, list) or not 1 <= len(messages) <= 60:
        raise ValueError("messages doit être une liste de 1 à 60 messages.")
    for message in messages:
        if (not isinstance(message, dict)
                or message.get("role") not in ("user", "assistant")
                or not isinstance(message.get("content"), str)
                or not message["content"].strip()):
            raise ValueError("Chaque message doit avoir un role (user ou assistant) "
                             "et un content texte non vide.")


def _contexte_dossier(record):
    """System note describing the request the advisor works on, if any."""
    if not isinstance(record, dict):
        return None
    d = record.get("demande") or {}
    lignes = [
        f"DOSSIER EN COURS (id={record.get('id', '')}).",
        f"Destination : {d.get('destination') or 'non renseignée'} ; "
        f"dates : {d.get('date_depart') or '?'} → {d.get('date_retour') or '?'} ; "
        f"voyageurs : {d.get('nombre_voyageurs') or '?'} ; "
        f"budget max par personne : {d.get('budget_max_par_personne') or '?'} € ; "
        f"type : {d.get('type_voyage') or '?'}.",
        f"Souhaits : {d.get('souhaits') or 'aucun'} ; contraintes : {d.get('contraintes') or 'aucune'}.",
    ]
    recherches = record.get("recherches") or []
    if recherches:
        derniere = recherches[-1]
        lignes.append(f"Dernière lecture du serveur : {derniere.get('consulte_le', '?')}.")
        for r in derniere.get("resultats") or []:
            lignes.append(
                f"- {r.get('nom')} ({r.get('type')}) : {r.get('prix_unitaire_eur')} € par personne, "
                f"{'disponible' if r.get('disponible') else 'indisponible'}, "
                f"{r.get('places_restantes', '?')} places.")
    else:
        lignes.append("Aucune lecture du serveur pour ce dossier.")
    return "\n".join(lignes)


class OpenRouterError(Exception):
    def __init__(self, message, status=502):
        super().__init__(message)
        self.status = status


SYSTEM_PROMPT = """Tu es PROPO, l'assistant voyage de DÉTOUR — une agence qui compose des week-ends insolites sur mesure. Tu n'es pas un formulaire : tu es le premier contact d'un voyageur curieux, et tu parles comme une personne, pas comme une machine.

CONTEXTE
- Le catalogue est fictif et restreint : destinations possibles uniquement Nantes, Lyon et Lille.
- Chaque destination propose un transport, un hébergement et une activité.
- Toutes les données sont fictives : c'est une démonstration.

PERSONNALITÉ
- Chaleureux et précis. Jamais pressé, jamais froid, jamais robotique.
- Tu dis « je » quand tu parles en ton nom, « nous » quand tu parles pour l'agence.
- Tu accueilles chaque voyageur comme une personne, pas comme un dossier à remplir.
- Tu montres que tu écoutes : reformule, montre que tu as compris avant de demander la suite.
- Tu ne fais jamais d'humour sur les prix ni sur les problèmes. Pas de blague, par prudence.
- Un voyage qui se prépare, ça prend le temps que ça prend. Tu ne brusques jamais.

TON TRAVAIL
1. Recueillir les informations du voyageur avec des questions courtes et amicales.
2. Une fois le minimum réuni, appeler l'outil chercher_voyages pour enregistrer la demande et vérifier les prestations.
3. Présenter les résultats en t'appuyant uniquement sur ce que l'outil renvoie.

INFORMATIONS REQUISES AVANT L'APPEL DE L'OUTIL (minimum)
- type_voyage : "trek-randonnee", "lune-de-miel", "voyage-familial" ou "autres"
- destination : "Nantes", "Lyon" ou "Lille"
- date_depart et date_retour : format AAAA-MM-JJ
- la date de départ doit être après aujourd'hui : si l'outil la refuse, demande une nouvelle date au voyageur
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
- N'invente jamais un prix, une disponibilité, une prestation du catalogue ou une date de mise à jour : ils viennent uniquement de l'outil. Seule exception : une alternative proche hors catalogue (voir QUAND CE N'EST PAS DISPONIBLE), toujours présentée comme une idée à vérifier, sans prix ni disponibilité.
- Tu ne prends aucune réservation et ne poses aucune option. Aucune réservation n'existe à l'issue de la conversation.
- Si le voyageur veut une autre destination, explique que le catalogue est restreint pour le moment.
- Si l'outil renvoie une erreur, explique-la honnêtement au voyageur sans inventer de résultat.

APRÈS L'OUTIL
- Présente chaque prestation vérifiée : nom, type, prix par personne et total pour le groupe, disponibilité.
- Précise que les prix et disponibilités ont été vérifiés auprès du serveur à la date indiquée ; la disponibilité est vérifiée à la date de départ uniquement.
- Signale ce qui n'est pas vérifiable au catalogue : le niveau d'aventure, le besoin de guide et les allergies ne figurent pas dans le serveur.
- Demande au voyageur de confirmer sa demande avec le bouton « Je confirme ma demande » : elle n'est transmise à un conseiller qu'après sa confirmation. Ne dis jamais qu'elle est déjà transmise.
- Un conseiller humain préparera ensuite la proposition définitive.

QUAND CE N'EST PAS DISPONIBLE
- Si le voyageur demande une activité, un événement, un voyage ou autre chose qui n'est pas dans les résultats de l'outil, ou que l'outil indique indisponible, dis-le d'abord clairement, en une phrase.
- Propose ensuite une ou deux alternatives proches de ce qui était demandé : même type de chose, au même endroit ou tout près (même région, environ 1 h de trajet au maximum).
- Ne propose jamais une alternative éloignée. Exemple : pour un marché de Noël à Lille, celui de Béthune convient, celui de Paris non.
- Une alternative hors catalogue est une idée, pas une prestation vérifiée : dis que le conseiller la vérifiera, et ne donne ni prix, ni horaire, ni disponibilité.
- Si une alternative existe dans les résultats de l'outil (disponible et dans le budget), propose-la en priorité, avec son prix vérifié.
- Si tu ne connais aucune alternative proche et sûre, dis-le simplement, sans rien inventer : « Je n'ai pas d'alternative proche à vous proposer. Le conseiller regardera avec vous. »
- Termine par une question courte, par exemple « Ça vous irait ? ».
- Exemple : « Il n'y a pas de marché de Noël à Lille dans notre catalogue. Je peux vous suggérer celui de Béthune, à 40 minutes de Lille : le conseiller vérifiera les dates pour vous. Ça vous irait ? »
- Pas de « Erreur : », pas d'humour sur ce qui manque.

STYLE
- Réponses courtes, en français, une question à la fois quand tu collectes les informations.
- Parle en personne, jamais comme une notice ou un formulaire.
- Accueille, reformule, montre que tu es là — pas juste que tu traites.
- Sois chaleureux même quand tu expliques une contrainte ou une erreur."""


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
    "Tu réponds uniquement avec un objet JSON valide.\n\n"
    "TON DÉTOUR\n"
    "- Précis d'abord, chaleureux ensuite, légèrement malicieux seulement en fin de message.\n"
    "- « nous » pour l'agence, « je » pour le conseiller dans le message au voyageur.\n"
    "- Jamais pressé, jamais criard : pas de « ! » en série.\n"
    "- Aucune plaisanterie sur un prix, une indisponibilité ou une erreur.\n\n"
    "MESSAGE_VOYAGEUR\n"
    "- Rédige un message court adressé au voyageur, dans le ton DÉTOUR.\n"
    "- Signe-le au prénom du conseiller (fourni dans la demande).\n"
    "- C'est un brouillon : le conseiller relira et pourra le modifier avant l'envoi.\n"
    "- Marque-le clairement comme un brouillon généré par l'assistant.\n\n"
    "RÉPONSE\n"
    "Réponds avec un objet JSON : "
    '{"titre": "...", "description": "...", "message_voyageur": "...", '
    '"prestations": [{"id": "...", "nom": "...", '
    '"type": "...", "prix_unitaire_eur": 0, "quantite": 1}]}\n'
    "Réponds uniquement avec le JSON."
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
        # #53: the chatbot knows the real working hours, never hard-coded.
        fenetre = fenetre_reponse()
        system_prompt = SYSTEM_PROMPT + "\n\n" + (
            "AVAILABILITY\n"
            f"- {fenetre['message']}\n"
            f"- {fenetre['promesse_delai']}\n"
            "- Never promise an immediate answer when the service is closed.\n"
            "- Never claim a reservation has been made.\n\n"
            # #145: the agent knows today's date, so it can refuse a past departure
            # at once. The program still has the last word when the request is saved.
            "TODAY\n"
            f"- Nous sommes le {business_today().isoformat()} (heure de Paris).\n"
            "- Le départ doit être après aujourd'hui : si la date de départ donnée est "
            "aujourd'hui ou avant, dis-le tout de suite et demande une nouvelle date, "
            "avant toute autre question.")
        conversation: list = [{"role": "system", "content": system_prompt}]
        demande, recherche = None, None
        if demande_id:
            # #23: strict load — unknown/foreign ids must not start a silent new thread.
            demande = self.store.obtenir_pour_voyageur(demande_id, user_id)
            reprise = _contexte_reprise(demande)
            if reprise:
                conversation.append({"role": "system", "content": reprise})
        conversation += [{"role": m["role"], "content": m["content"]}
                         for m in messages[-MAX_MESSAGES:]]

        def _retour(reply):
            # #5: contract fields before persistence (redaction happens in traces.py).
            rid = demande_id or (demande or {}).get("id")
            trace["request_id"] = rid
            trace["reponse_finale"] = reply or ""
            return {"reply": reply or "",
                    "demande": demande, "recherche": recherche, "trace": trace}

        for _ in range(MAX_TOOL_ITERATIONS):
            message = self._call_model(conversation)
            tool_calls = message.get("tool_calls") or []
            if not tool_calls:
                return _retour(message.get("content") or "")
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
        return _retour(message.get("content") or "")

    def chat_conseiller(self, messages, demande_id=None):
        """Advisor chat turn (#115): reply, verified search and trace.

        The only tool is a read-only search: the advisor chat never writes on a
        request, never books and never changes a status."""
        if not self._api_key:
            raise OpenRouterError("Clé OpenRouter absente : définir OPENROUTER_API_KEY.", 503)
        trace = {
            "model": self.model,
            "tool_calls": [],
            "simulation": True,
            "acteur": "assistant_conseiller",
            # Trace split: agent suggestions vs advisor decisions (#119)
            "conseiller_trace": {
                "advisor_request": {
                    "message_count": len(messages) if isinstance(messages, list) else 0,
                    "has_demande_id": bool(demande_id),
                },
                "search_performed": False,
                "data_returned": False,
                "price_checks": [],
                "availability_checks": [],
                "missing_information": [],
                "agent_suggestions": [],
                "draft_proposal": None,
                "advisor_edits": [],
                "advisor_review": None,
                "advisor_confirmation": None,
                "suggestions": [],
                "decisions": [],
                "separation": {
                    "note": "The agent suggests. The advisor decides.",
                    "agent_role": "suggest",
                    "advisor_role": "decide",
                },
            },
        }
        conversation: list = [{"role": "system", "content": ADVISOR_SYSTEM_PROMPT}]
        demande = self.store.obtenir(demande_id) if demande_id else None
        contexte = _contexte_dossier(demande)
        if contexte:
            conversation.append({"role": "system", "content": contexte})
        conversation += [{"role": m["role"], "content": m["content"]}
                         for m in messages[-MAX_MESSAGES:]]
        recherche = None

        def _retour(reply):
            trace["request_id"] = (demande or {}).get("id")
            trace["reponse_finale"] = reply or ""
            ctrace = trace.get("conseiller_trace") or {}
            # Mark agent suggestions explicitly (#119)
            if reply:
                ctrace["agent_suggestions"].append({
                    "type": "assistant_reply",
                    "content": reply,
                })
                ctrace["suggestions"].append({
                    "actor": "agent",
                    "kind": "reply",
                    "summary": reply,
                })
            trace["conseiller_trace"] = ctrace
            return {"reply": reply or "", "demande": demande,
                    "recherche": recherche, "trace": trace}

        for _ in range(MAX_TOOL_ITERATIONS):
            message = self._call_model(conversation, tools=[ADVISOR_TOOL_DEFINITION])
            tool_calls = message.get("tool_calls") or []
            if not tool_calls:
                return _retour(message.get("content") or "")
            conversation.append({"role": "assistant", "content": message.get("content") or "",
                                 "tool_calls": tool_calls})
            for call in tool_calls:
                outcome = self._execute_advisor_tool(call, trace)
                recherche = outcome.get("recherche") or recherche
                conversation.append({
                    "role": "tool",
                    "tool_call_id": call.get("id") or "call_inconnu",
                    "content": json.dumps(outcome["payload"], ensure_ascii=False),
                })
                # Track search lifecycle in conseiller_trace (#119)
                ctrace = trace.get("conseiler_trace") or trace.get("conseiller_trace") or {}
                if outcome.get("recherche") is not None:
                    ctrace["search_performed"] = True
                    ctrace["data_returned"] = bool((outcome.get("recherche") or {}).get("resultats"))
                    res = (outcome.get("recherche") or {}).get("resultats") or []
                    for r in res:
                        if isinstance(r, dict) and "prix_unitaire_eur" in r:
                            ctrace["price_checks"].append({
                                "prestation_id": r.get("id"),
                                "prix_unitaire_eur": r.get("prix_unitaire_eur"),
                            })
                        if isinstance(r, dict) and "disponible" in r:
                            ctrace["availability_checks"].append({
                                "prestation_id": r.get("id"),
                                "disponible": r.get("disponible"),
                            })
                    trace["conseiller_trace"] = ctrace

        message = self._call_model(conversation, with_tools=False)
        return _retour(message.get("content") or "")

    def _execute_advisor_tool(self, call, trace):
        """Run the read-only advisor search after validating its arguments."""
        function = call.get("function") or {}
        name = function.get("name")
        entry = {"outil": name, "statut": "refuse"}
        if name != ADVISOR_TOOL_NAME:
            entry["erreur"] = f"Outil inconnu : {name}. Seul {ADVISOR_TOOL_NAME} est autorisé."
            trace["tool_calls"].append(entry)
            return {"payload": {"erreur": entry["erreur"]}}
        try:
            criteres = criteres_conseiller(json.loads(function.get("arguments") or "{}"))
        except json.JSONDecodeError:
            criteres, erreur = None, "Arguments invalides : un objet JSON était attendu."
        except ValueError as err:
            criteres, erreur = None, str(err)
        if criteres is None:
            entry["erreur"] = erreur
            entry["validation"] = "arguments_invalides"
            trace["tool_calls"].append(entry)
            return {"payload": {
                "erreur": entry["erreur"],
                "consigne": "Demande au conseiller l'information manquante ou à corriger.",
            }}
        entry["arguments"] = criteres
        try:
            recherche = marquer_etats(self.supplier.rechercher(criteres))
        except SupplierError as err:
            entry["statut"], _ = _rapport_erreur_fournisseur(err)
            entry["erreur"] = str(err)
            entry["http_status"] = getattr(err, "status", None)
            trace["tool_calls"].append(entry)
            return {"payload": {
                "erreur": "La vérification n'a pas abouti.",
                "etat_verification": ETAT_ERROR,
                "consigne": (
                    "Le serveur de prestations n'a pas pu vérifier les prix et les places. "
                    "Dis-le simplement au conseiller, sans inventer de prestation, et "
                    "propose de réessayer dans un instant."),
            }}
        entry["statut"] = "ok"
        entry["http_status"] = 200
        entry["reponse_serveur"] = resume_reponse_serveur(recherche)
        trace["tool_calls"].append(entry)
        return {"recherche": recherche, "payload": recherche}

    def generer_proposition(self, demande_record, recherche, conseiller=""):
        """Generate a structured proposition via OpenRouter (no tools).

        The draft is stamped ``genere_par: "assistant"`` so it stays visibly
        separate from advisor-confirmed content (#117). A ``message_voyageur``
        is drafted in the Détour tone and signed with the advisor's first name.
        The advisor can edit every field before sending.
        """
        if not self._api_key:
            raise OpenRouterError("Clé OpenRouter absente : définir OPENROUTER_API_KEY.", 503)
        d = demande_record.get("demande", demande_record)
        resultats = (recherche or {}).get("resultats", [])
        prenom = (conseiller or "").strip() or PRENOM_CONSEILLER_DEFAUT
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
            f"Conseiller : {prenom}\n"
            f"Signe le message_voyageur au prénom « {prenom} ».\n\n"
            f"Prestations disponibles :\n"
            f"{json.dumps(resultats, ensure_ascii=False)}\n\n"
            f"Réponds avec un objet JSON : "
            f'{{"titre": "...", "description": "...", "message_voyageur": "...", '
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
        # Stamp the draft as assistant-generated (#117).
        prop_data["genere_par"] = GENERE_PAR_ASSISTANT
        # Guarantee a traveler message even if the model omits it.
        if not isinstance(prop_data.get("message_voyageur"), str):
            prop_data["message_voyageur"] = ""
        try:
            # Stamp source and consultation time from the search; never invent them.
            aligned = aligner_sur_serveur(
                prop_data,
                resultats,
                source_label=(recherche or {}).get("source_label"),
                consulte_le=(recherche or {}).get("consulte_le"),
            )
            # The program sets quantities from the request, not the model (#34).
            return apply_quantities(aligned, d)
        except PropositionError as err:
            raise OpenRouterError(f"Proposition refusée : {err}") from err

    def _call_model(self, conversation, with_tools=True, tools=None):
        payload = {"model": self.model, "messages": conversation}
        if with_tools:
            payload["tools"] = tools or [TOOL_DEFINITION]
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
            entry["validation"] = "outil_inconnu"
            trace["tool_calls"].append(entry)
            return {"payload": {"erreur": entry["erreur"]}}
        try:
            args = json.loads(function.get("arguments") or "{}")
            if not isinstance(args, dict):
                raise ValueError
        except (json.JSONDecodeError, ValueError):
            entry["erreur"] = "Arguments invalides : un objet JSON était attendu."
            entry["validation"] = "arguments_invalides"
            trace["tool_calls"].append(entry)
            return {"payload": {"erreur": entry["erreur"]}}
        if args.get("qualification") == "pret_proposition":
            entry["qualification_refusee"] = (
                "L'agent ne peut pas marquer une demande prête pour proposition.")
        # The model never decides: any decision argument is refused and traced.
        decisions_refusees = [k for k in DECISION_ARGS if k in args]
        if decisions_refusees:
            entry["decision_refusee"] = (
                "L'agent ne prend pas de décision : "
                + ", ".join(sorted(decisions_refusees))
                + " ignorés. Seul le conseiller tranche.")
        # Never trust model-supplied ids; only the server thread id is used.
        for cle in DECISION_ARGS:
            args.pop(cle, None)
        args.pop("user_id", None)
        args.pop("demande_id", None)
        # #5: sanitized arguments (decision keys already stripped).
        entry["arguments"] = dict(args)

        try:
            record, mis_a_jour = self.store.enregistrer_reponses(
                demande_id, args, user_id=user_id)
        except ValidationError as err:
            entry["statut"] = "echec_mise_a_jour"
            entry["validation"] = "echec"
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
            entry["validation"] = "demande_introuvable"
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
        entry["validation"] = "ok"
        labels = analyse["labels"]
        confirmation = (
            f"Réponse enregistrée sur la demande {record['id']}."
            if mis_a_jour else
            f"Demande {record['id']} à jour (aucun nouveau champ)."
        )
        if not analyse["complet"]:
            entry["statut"] = "informations_manquantes"
            entry["http_status"] = None
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
            statut, consigne = _rapport_erreur_fournisseur(err)
            entry["statut"] = statut
            entry["erreur"] = str(err)
            entry["http_status"] = getattr(err, "status", None)
            entry["reponse_serveur"] = None
            trace["tool_calls"].append(entry)
            return {"demande": record,
                    "payload": {
                        "confirmation": confirmation,
                        "erreur": str(err),
                        "http_status": getattr(err, "status", None),
                        "etat_verification": ETAT_ERROR,
                        "consigne": consigne,
                    }}
        entry["statut"] = "ok"
        entry["http_status"] = 200
        entry["reponse_serveur"] = resume_reponse_serveur(recherche)
        trace["tool_calls"].append(entry)
        payload = dict(recherche) if isinstance(recherche, dict) else {"recherche": recherche}
        payload["confirmation"] = confirmation
        payload["champs_mis_a_jour"] = mis_a_jour
        payload["demande_id"] = record["id"]
        payload["informations"] = analyse
        return {"demande": record, "recherche": recherche, "payload": payload}